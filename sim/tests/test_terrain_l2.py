"""Tests for the level-2 terrain walk (sim/mujoco/terrain.py)."""
import json
import math
import re
import unittest

from sim.common import ROOT

try:
    import mujoco
    import numpy as np
    from sim.mujoco import terrain as T
    HAVE = True
except ImportError:          # runs in the CI job that installs sim/mujoco/requirements.txt
    HAVE = False


def _meta(path):
    return json.loads(re.search(r"meta: (\{.*?\}),\nbin:", (ROOT / path).read_text(), re.S).group(1))


@unittest.skipUnless(HAVE, "mujoco not installed")
class Terrain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = T.load_params()
        cls.terrains = {t["key"]: t for t in cls.p["course"]["terrains"]}

    def test_ground_is_the_kinematic_course_ground(self):
        """The ground walked here is the height map the kinematic course exported to the page."""
        for path, loaded in (("docs/3d/assets/sus-m1-terrain.js", False), ("docs/3d/assets/sus-m1-terrain-loaded.js", True)):
            meta = _meta(path)
            dx, W = meta["sample_m"], meta["width_m"]
            for row in meta["terrains"]:
                if row.get("skipped"):
                    continue
                G = T.Ground(self.terrains[row["key"]], T.gait_of(self.p, loaded)["stride"])
                H = row["hmap"]
                for i in range(0, len(H), 3):
                    for j in range(0, len(H[0]), 5):
                        self.assertAlmostEqual(G(i * dx, -W / 2 + j * dx), H[i][j], delta=2e-3, msg=f"{path} {row['key']} [{i}][{j}]")

    def test_zero_pose_is_the_cad_standing_pose(self):
        m = T.build(self.p, T.Ground(self.terrains["flat"], 1.0), (-1, 1))
        d = mujoco.MjData(m)
        mujoco.mj_forward(m, d)
        total = self.p["links"]["total"]
        self.assertAlmostEqual(float(sum(m.body_mass)), total["mass_kg"], delta=1.0)
        np.testing.assert_allclose(d.subtree_com[1], total["com_m"], atol=5e-3)
        sole = d.site_xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, "sole_left")]
        self.assertAlmostEqual(sole[2], 0.0, delta=1e-6)

    def test_inverse_kinematics_reaches_its_target(self):
        m = T.build(self.p, T.Ground(self.terrains["flat"], 1.0), (-1, 1))
        d, ik = mujoco.MjData(m), T.IK(self.p)
        rng = np.random.default_rng(1)
        site = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, "sole_right")
        for _ in range(20):
            torso = np.array([rng.uniform(-0.3, 0.3), rng.uniform(-0.1, 0.1), rng.uniform(2.1, 2.3)])
            R = T.rot_y(rng.uniform(-0.1, 0.1)) @ T.rot_x(rng.uniform(-0.1, 0.1))
            sole = np.array([rng.uniform(-0.5, 0.6), -0.55 + rng.uniform(-0.1, 0.1), rng.uniform(-0.2, 0.25)])
            ry, rx = rng.uniform(-0.3, 0.3), rng.uniform(-0.2, 0.2)
            q = ik.leg("right", torso, sole, ry, rx, R)
            quat = np.zeros(4); mujoco.mju_mat2Quat(quat, R.ravel())
            d.qpos[:] = 0
            d.qpos[:3], d.qpos[3:7], d.qpos[12:17] = torso, quat, q
            mujoco.mj_kinematics(m, d)
            np.testing.assert_allclose(d.site_xpos[site], sole, atol=1e-6)
            Rf = d.site_xmat[site].reshape(3, 3)
            np.testing.assert_allclose(Rf[:, 2], (T.rot_y(ry) @ T.rot_x(rx))[:, 2], atol=1e-6)   # up axis exact
            self.assertLess(abs(math.atan2(Rf[1, 0], Rf[0, 0])), 0.05)                         # heading near

    def test_footholds_stay_put_on_a_plane_and_bear_on_a_tread(self):
        W = T.gait_of(self.p, False)
        g = T.Gait(self.p, T.Ground(self.terrains["up10"], W["stride"]), W)
        for x in (0.4, 1.4, -0.1):
            self.assertEqual(g.place(x, 0.55), x)
            z, ry, rx, cx, _ = g.hold(x, 0.55)
            self.assertAlmostEqual(ry, -math.radians(10), places=6)
        led = T.Gait(self.p, T.Ground(self.terrains["ledges"], W["stride"]), W)
        for side in ("left", "right"):
            x, y, z, ry, rx, _, cx = led.foot(side, 0)
            self.assertEqual((ry, rx), (0.0, 0.0))          # level on a tread, not tilted across a riser
            self.assertAlmostEqual(z, led.G(x + cx, y), delta=1e-9)   # and bearing on the tread under it

    def test_flat_walk_stays_up_and_moves_on(self):
        res = T.simulate(self.p, self.terrains["flat"], False, frames=True)
        self.assertTrue(res["walked"], res["fall"])
        self.assertLess(res["tilt_max_deg"], 5)
        x0, x1 = res["frames"][0][0], res["frames"][-1][0]
        self.assertGreater(x1 - x0, 0.8 * self.p["cfg"]["cycles"] * self.p["walk"]["stride"])

    def test_every_leg_body_carries_cad_parts(self):
        meshes, origins = T.mesh_bodies(self.p)
        on = {b for _, b in meshes}
        self.assertEqual(on, set(range(len(T.BODIES))))
        self.assertEqual(len(origins), len(T.BODIES))

    def test_committed_outputs_match(self):
        self.assertEqual(T.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()
