"""Build the SUS-M1 level-2 MuJoCo model (planar two-legged walker) from the plant specs.

The model is generated, never hand-edited: sim/spec/walker.yaml + sim/spec/walker_l2.yaml -> MJCF string.
Planar: the torso has slide-x, slide-z and pitch joints; each leg has hip, knee and ankle hinges about y and a box
foot in contact with the ground. Positive joint angles rotate a leg's tip backwards (-x), so a positive knee angle is
flexion. The slope is applied by tilting gravity, so +x is downhill, as in the level-1 plant.
"""
from __future__ import annotations

import math

from sim.plant import spec as plant_spec
from sim.plant.spec import SIM, check
from tools.pdac.load import _read_yaml

L2_SPEC = SIM / "spec" / "walker_l2.yaml"
LEGS = ("s", "w")          # stance, swing
JOINTS = [f"{j}_{leg}" for leg in LEGS for j in ("hip", "knee", "ankle")]


def load_params() -> dict:
    p = plant_spec.load()
    p.update(check(_read_yaml(L2_SPEC)))
    return p


def mjcf(p: dict, slope_deg: float) -> str:
    th = math.radians(slope_deg)
    g = p["gravity_mps2"]
    gx, gz = g * math.sin(th), -g * math.cos(th)
    lt, ls, ha = p["thigh_length_m"], p["shank_length_m"], p["ankle_height_m"]
    foot = p["foot_half_length_m"]
    lm = p["leg_mass_kg"]

    def leg(side: str, y: float) -> str:
        return f"""
      <body name="thigh_{side}" pos="0 {y} 0">
        <joint name="hip_{side}" range="-2.0 2.0"/>
        <geom type="capsule" fromto="0 0 0 0 0 -{lt}" size="0.12" mass="{0.5 * lm}" contype="0" conaffinity="0"/>
        <body name="shank_{side}" pos="0 0 -{lt}">
          <joint name="knee_{side}" range="-0.05 2.6"/>
          <geom type="capsule" fromto="0 0 0 0 0 -{ls}" size="0.1" mass="{0.4 * lm}" contype="0" conaffinity="0"/>
          <body name="foot_{side}" pos="0 0 -{ls}">
            <joint name="ankle_{side}" range="-1.2 1.2"/>
            <geom name="sole_{side}" type="box" size="{foot} 0.25 {ha / 2}" pos="0 0 -{ha / 2}" mass="{0.1 * lm}"/>
            <site name="sole_{side}" pos="0 0 -{ha}"/>
          </body>
        </body>
      </body>"""

    return f"""<mujoco model="sus-m1-l2">
  <compiler angle="radian" autolimits="true"/>
  <option timestep="{p['timestep_s']}" gravity="{gx:.6f} 0 {gz:.6f}" integrator="implicitfast"/>
  <default>
    <joint type="hinge" axis="0 1 0" damping="500" armature="50"/>
    <geom friction="{p['ground_friction']} 0.01 0.001" solref="0.005 1" solimp="0.95 0.99 0.001" contype="1" conaffinity="1"/>
  </default>
  <worldbody>
    <geom name="ground" type="plane" size="60 5 0.1" contype="1" conaffinity="1"/>
    <body name="torso" pos="0 0 {p['hip_height_m'] + 0.2}">
      <joint name="root_x" type="slide" axis="1 0 0" damping="0" armature="0"/>
      <joint name="root_z" type="slide" axis="0 0 1" damping="0" armature="0"/>
      <joint name="root_pitch" type="hinge" axis="0 1 0" damping="0" armature="0"/>
      <geom name="cockpit" type="box" size="0.65 0.6 0.5" pos="0 0 {p['torso_com_above_hip_m']}" mass="{p['torso_mass_kg']}"
            contype="0" conaffinity="0"/>{leg('s', 0.35)}{leg('w', -0.35)}
    </body>
  </worldbody>
  <actuator>
{chr(10).join(f'    <motor name="{j}" joint="{j}" gear="1"/>' for j in JOINTS)}
  </actuator>
</mujoco>
"""
