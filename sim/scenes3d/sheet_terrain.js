// Susanoo sheet 3: the CL-05 walk on the terrain course (three.js r170). Embedded in docs/3d/SUS-M1-terrain.html by build_sheet.py.
// window.SHEET: terrains with the static figures computed from the records (cad/metrics.json, sim/spec/walker.yaml,
// SYS-008, HAZ-WLK-002); window.SUS_M1_GEOMETRY: the CL-05 standing meshes; window.SUS_M1_TERRAIN: one walk cycle per
// terrain posed by the CAD (tools/cad/b3d/cl05_terrain.py) with its ground height map and kinematic findings.
// Nothing here computes motion: it loops the CAD's frames and draws the ground they were posed on.
// URL: ?terrain=up20&t=1.5&paused=1&view=side&render=xray
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

THREE.Object3D.DEFAULT_UP.set(0, 0, 1);
const D = window.SHEET, G = window.SUS_M1_GEOMETRY.meta;
// two posed courses: the walk (stowed arms) and the loaded walk (carry pose, placeholder load)
const COURSE = { unloaded: window.SUS_M1_TERRAIN, loaded: window.SUS_M1_TERRAIN_LOADED };
const q = new URLSearchParams(location.search);
const $ = (id) => document.getElementById(id);
const C = { ink: '#1e293b', mute: '#64748b', line: '#c3ccd7', haz: '#ea580c', sel: '#4f46e5', ok: '#0d9488', warn: '#d97706', bad: '#dc2626', bg: '#e4e9ef' };
const f2 = (v) => Number(v).toFixed(2), f1 = (v) => Number(v).toFixed(1);

// ------------------------------------------------------------------ geometry: CL-05 standing meshes and the terrain clips' own meshes
function decode(src, meta) {
  const raw = Uint8Array.from(atob(src.bin), (c) => c.charCodeAt(0)).buffer, sl = ([o, n]) => raw.slice(o, o + n);
  return { P: new Int16Array(sl(meta.layout.positions)), I: new Uint16Array(sl(meta.layout.indices)), M: new Float32Array(sl(meta.layout.matrices)) };
}
const GB = decode(window.SUS_M1_GEOMETRY, G);
const BUF = { unloaded: decode(COURSE.unloaded, COURSE.unloaded.meta), loaded: decode(COURSE.loaded, COURSE.loaded.meta) };
const PFX = { t: 'unloaded', l: 'loaded' };
function geom(meta, buf, i) {
  const m = meta.meshes[i], [vo, vn] = m.v, [io, inn] = m.i, s = meta.quantum_m, o = meta.origin_m;
  const pos = new Float32Array(vn * 3);
  for (let k = 0; k < vn * 3; k++) pos[k] = buf.P[vo * 3 + k] * s + o[k % 3];
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setIndex(new THREE.BufferAttribute(buf.I.slice(io, io + inn), 1));
  g.computeVertexNormals(); g.computeBoundingBox(); return g;
}

// ------------------------------------------------------------------ renderer, scene
const canvas = $('gl');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
const scene = new THREE.Scene();
scene.add(new THREE.HemisphereLight('#ffffff', '#aab4c2', 1.6));
const sun = new THREE.DirectionalLight('#ffffff', 2.0); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.0005;
Object.assign(sun.shadow.camera, { left: -10, right: 10, top: 10, bottom: -10, near: 1, far: 60 }); scene.add(sun, sun.target);
const fill = new THREE.DirectionalLight('#dfe7ff', 0.5); fill.position.set(-8, 6, 5); scene.add(fill);
const walker = new THREE.Group(); scene.add(walker);

// ------------------------------------------------------------------ state
const S = { key: 'flat', mode: 'unloaded', mass: 0, u: 0, playing: !q.has('paused'), speed: 1, render: 'shaded', show: { plumb: true, stripes: true, person: true } };
const T = () => COURSE[S.mode].meta;
const terr = () => T().terrains.find((t) => t.key === S.key), info = () => D.terrains.find((t) => t.key === S.key);
const posed = (mode, key) => { const t = COURSE[mode].meta.terrains.find((x) => x.key === key); return t && !t.skipped ? t : null; };
const STRIDE = () => T().stride_m, N = () => T().frames_per_cycle, RATE = 0.55;   // walk cycles per second at 1x (viewing pace)

// ------------------------------------------------------------------ materials and meshes
const MODES = ['shaded', 'line', 'xray'], mats = {};
for (const [cls, [color, op]] of Object.entries(D.classes)) mats[cls] = {
  shaded: new THREE.MeshStandardMaterial({ color, roughness: 0.62, metalness: cls === 'actuator' ? 0.35 : 0.12, transparent: op < 1, opacity: op, depthWrite: op >= 1, side: THREE.DoubleSide }),
  line: new THREE.MeshBasicMaterial({ color: '#f8fafc', polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1, side: THREE.DoubleSide }),
  xray: new THREE.MeshStandardMaterial({ color, roughness: 0.5, transparent: true, opacity: 0.16, depthWrite: false, side: THREE.DoubleSide }) };
const edgeMat = { shaded: new THREE.LineBasicMaterial({ color: C.ink, transparent: true, opacity: 0.22 }), line: new THREE.LineBasicMaterial({ color: C.ink }),
  xray: new THREE.LineBasicMaterial({ color: '#334155', transparent: true, opacity: 0.35 }) };
const objs = new Map();   // 'b<id>' standing mesh of sus-m1.js, 't<k>' / 'l<k>' mesh of the unloaded / loaded course
function obj(key) {
  if (objs.has(key)) return objs.get(key);
  const isB = key[0] === 'b', id = +key.slice(1), meta = isB ? G : COURSE[PFX[key[0]]].meta, cls = meta.meshes[id].cls;
  const m = new THREE.Mesh(geom(meta, isB ? GB : BUF[PFX[key[0]]], id), mats[cls][S.render]);
  m.matrixAutoUpdate = false; m.castShadow = D.classes[cls][1] >= 1; m.receiveShadow = true; m.userData = { cls };
  const e = new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry, 35), edgeMat[S.render]); m.add(e); m.userData.edges = e;
  walker.add(m); objs.set(key, m); return m;
}
G.base.forEach((b) => obj('b' + b));
function applyMaterials() { for (const m of objs.values()) { m.material = mats[m.userData.cls][S.render]; m.userData.edges.material = edgeMat[S.render]; } }
const tA = new THREE.Matrix4(), tB = new THREE.Matrix4();
const setMat = (m, k) => { const a = BUF[S.mode].M.subarray(k * 12, k * 12 + 12); return m.set(a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8], a[9], a[10], a[11], 0, 0, 0, 1); };

// pose at u (walk cycles, continuous): frames i and i+1 of the cycle, the body moved by whole cycles and the cycle's rise
function pose(u) {
  const t = terr(), n = N(), st = STRIDE(), k = Math.floor(u), f = (u - k) * n, i = Math.floor(f) % n, j = (i + 1) % n, fr = f - Math.floor(f);
  const A = t.frames[i], B = t.frames[j], wrap = j === 0 ? 1 : 0;
  const ma = new Map(A.map), mb = new Map(B.map), near = fr < 0.5 ? A : B;
  for (const [key, m] of objs) {
    if (key[0] !== 'b') { m.visible = false; continue; }
    const id = +key.slice(1), ka = ma.get(id), kb = mb.get(id);
    if (ka !== undefined && kb !== undefined) { const ea = setMat(tA, ka).elements, eb = setMat(tB, kb).elements; for (let n = 0; n < 16; n++) m.matrix.elements[n] = ea[n] + (eb[n] - ea[n]) * fr; m.visible = true; }
    else if ((fr < 0.5 ? ma : mb).has(id)) { setMat(m.matrix, (fr < 0.5 ? ma : mb).get(id)); m.visible = true; }
    else m.visible = false;
    m.matrixWorldNeedsUpdate = true;
  }
  const pf = S.mode === 'loaded' ? 'l' : 't';
  for (const e of near.extras) { const m = obj(pf + e); m.matrix.identity(); m.visible = true; }
  const xb = A.xb + ((B.xb + wrap * st) - A.xb) * fr, gz = A.gref + ((B.gref + wrap * t.rise) - A.gref) * fr;
  walker.position.set(k * st + xb, 0, k * t.rise + gz);
  return { k, i, x: k * st + xb };
}

// ------------------------------------------------------------------ ground: the exported height map of one period, tiled with the cycle's rise
function groundAt(x, y) {
  const t = terr(), dx = T().sample_m, H = t.hmap, nx = H.length, ny = H[0].length, st = STRIDE();
  const c = Math.floor(x / st), xr = (x - c * st) / dx, i0 = Math.floor(xr) % nx, i1 = (i0 + 1) % nx, fx = xr - Math.floor(xr);
  const yr = Math.min(ny - 1.001, Math.max(0, (y + T().width_m / 2) / dx)), j0 = Math.floor(yr), fy = yr - j0;
  const h = (i, j) => H[i][j];
  const top = i1 === 0 ? t.rise : 0;   // the next sample after the period's end belongs to the next cycle
  const a = h(i0, j0) * (1 - fy) + h(i0, j0 + 1) * fy, b = (h(i1, j0) * (1 - fy) + h(i1, j0 + 1) * fy) + top;
  return c * t.rise + a + (b - a) * fx;
}
const groundMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95, side: THREE.DoubleSide });
let ground = null, groundC = null, groundKey = null;
function buildGround(c0) {
  const t = terr(), dx = T().sample_m, nx = t.hmap.length, ny = t.hmap[0].length, cyc = Math.ceil(12 / STRIDE()), X = cyc * nx + 1, st = STRIDE(), W = T().width_m;
  const pos = new Float32Array(X * ny * 3), col = new Float32Array(X * ny * 3), idx = [];
  const ca = new THREE.Color('#d6dccd'), cb = new THREE.Color('#c5ccbb'), cw = new THREE.Color('#e3e7dc');
  for (let gi = 0; gi < X; gi++) {
    const c = c0 + Math.floor(gi / nx), i = gi % nx, x = c * st + i * dx;
    for (let j = 0; j < ny; j++) {
      const n = (gi * ny + j) * 3, y = -W / 2 + j * dx, edge = Math.abs(y) > W / 2 - 0.4;
      pos[n] = x; pos[n + 1] = y; pos[n + 2] = t.hmap[i][j] + c * t.rise;
      const k = edge ? cw : (S.show.stripes && ((Math.floor(x + 1e-6) % 2) + 2) % 2 ? cb : ca); col[n] = k.r; col[n + 1] = k.g; col[n + 2] = k.b;
    }
  }
  for (let gi = 0; gi < X - 1; gi++) for (let j = 0; j < ny - 1; j++) { const a = gi * ny + j, b = a + ny; idx.push(a, b, a + 1, b, b + 1, a + 1); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  g.setIndex(idx); g.computeVertexNormals();
  if (ground) { scene.remove(ground); ground.geometry.dispose(); }
  ground = new THREE.Mesh(g, groundMat); ground.receiveShadow = true; scene.add(ground); groundC = c0; groundKey = S.mode + S.key + S.show.stripes;
}

// ------------------------------------------------------------------ person, CG plumb
const person = new THREE.Group();
{ const pm = new THREE.MeshStandardMaterial({ color: '#a3acb9', roughness: 0.8 });
  const part = (g, x, y, z) => { const o = new THREE.Mesh(g, pm); o.position.set(x, y, z); o.castShadow = true; person.add(o); return o; };
  for (const y of [-0.1, 0.1]) part(new THREE.CapsuleGeometry(0.075, 0.72, 4, 12), 0, y, 0.44).rotation.x = Math.PI / 2;
  part(new THREE.CapsuleGeometry(0.17, 0.42, 4, 14), 0, 0, 1.22).rotation.x = Math.PI / 2; part(new THREE.SphereGeometry(0.11, 18, 12), 0, 0, 1.64);
  scene.add(person); }
const cg = new THREE.Mesh(new THREE.SphereGeometry(0.09, 20, 12), new THREE.MeshBasicMaterial({ color: '#eab308', depthTest: false })); cg.renderOrder = 10; scene.add(cg);
const plumb = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]), new THREE.LineDashedMaterial({ color: C.ink, dashSize: 0.08, gapSize: 0.06, depthTest: false }));
plumb.renderOrder = 9; scene.add(plumb);
const hit = new THREE.Mesh(new THREE.RingGeometry(0.05, 0.09, 24), new THREE.MeshBasicMaterial({ color: C.haz, depthTest: false })); hit.renderOrder = 11; scene.add(hit);

// ------------------------------------------------------------------ camera
const cam = new THREE.PerspectiveCamera(30, 1, 0.1, 500);
const controls = new OrbitControls(cam, canvas); controls.enableDamping = true; controls.dampingFactor = 0.08;
const VIEWS = { iso: [300, 16, 17], side: [270, 4, 16], front: [0, 6, 16], rear: [180, 8, 16], top: [270, 89, 18] };
let camTween = null;
function setView(v, instant) {
  const [az, el, r] = VIEWS[v], a = THREE.MathUtils.degToRad(az), e = THREE.MathUtils.degToRad(el);
  const to = new THREE.Vector3(Math.cos(e) * Math.cos(a) * r, Math.cos(e) * Math.sin(a) * r, Math.sin(e) * r).add(controls.target);
  document.querySelectorAll('#view button').forEach((b) => b.classList.toggle('on', b.dataset.v === v));
  if (instant) { cam.position.copy(to); controls.update(); } else camTween = { from: cam.position.clone(), to, t: 0 };
}

// ------------------------------------------------------------------ panels
$('banner').textContent = 'CONCEPT GEOMETRY & KINEMATICS · DESIGN AID ONLY · NO EVIDENCE CREDIT';
$('tbdoc').textContent = D.sheet.document; $('tbsheet').textContent = D.sheet.sheet; $('tbrev').textContent = D.sheet.revision; $('tbtitle').textContent = D.sheet.title;
const tlist = $('tlist');
tlist.innerHTML = `<div class="seg tg">${D.terrains.map((t) => `<button data-k="${t.key}" title="${t.note || t.label}">${t.label}</button>`).join('')}</div>`;
tlist.querySelectorAll('button').forEach((b) => { b.onclick = () => setTerrain(b.dataset.k); });
const status = (ok, warn) => ok ? `<span style="color:${C.ok}">✓</span>` : `<span style="color:${warn ? C.warn : C.bad}">${warn ? '!' : '✗'}</span>`;
const row = (k, v) => `<div class="row"><span class="k">${k}</span><span>${v}</span></div>`;
// Static margin, the same geometry as sim/scenes3d/build_sheet.py static_margin(): signed distance from the support
// polygon's edge to the centre of gravity projected along gravity on ground pitched/rolled by the given degrees, with
// `lean` the share of the slope-induced shift left uncompensated. Used live for the load-mass slider.
function inPoly(p, poly) { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const [xi, yi] = poly[i], [xj, yj] = poly[j];
  if ((yi > p[1]) !== (yj > p[1]) && p[0] < (xj - xi) * (p[1] - yi) / (yj - yi) + xi) c = !c; } return c; }
function edge(p, poly) { let d = 1e9; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const [ax, ay] = poly[j], [bx, by] = poly[i], dx = bx - ax, dy = by - ay;
  const t = Math.max(0, Math.min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy))); d = Math.min(d, Math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)); } return d; }
function margin(cg, poly, pitch, roll, lean = 1) { const tp = Math.tan(pitch * Math.PI / 180), tr = Math.tan(roll * Math.PI / 180);
  const p = [cg[0] - lean * cg[2] * tp, cg[1] + lean * cg[2] * tr], d = edge(p, poly); return inPoly(p, poly) ? d : -d; }
function tipAt(cg, poly, sp, sr, lean = 1) { let lo = 0, hi = 89; for (let n = 0; n < 60; n++) { const mid = (lo + hi) / 2; if (margin(cg, poly, sp * mid, sr * mid, lean) > 0) lo = mid; else hi = mid; } return lo; }
function loadedCg(kg) { const c = D.carry, M = c.mass_kg; return c.cg_m.map((v, i) => (M * v + kg * c.load_centre_m[i]) / (M + kg)); }
const info2 = (k) => D.terrains.find((t) => t.key === k);
let lastMargins = null;
function renderPanels() {
  if (S.mode === 'loaded') return renderLoaded();
  $('loadrow').style.display = 'none';
  const t = terr(), d = info(), fnd = t.findings, slope = d.slope_deg;
  $('tname').textContent = d.label.toUpperCase();
  $('tsub').textContent = d.kind === 'plane' ? `${d.pitch_deg ? 'pitch ' + d.pitch_deg + '°' : ''}${d.roll_deg ? 'roll ' + d.roll_deg + '° (right side down)' : ''}${!d.pitch_deg && !d.roll_deg ? 'level ground' : ''} · rise ${f2(t.rise)} m per cycle`
    : d.kind === 'ledges' ? `treads ${d.run_m} m, risers ${d.rise_m} m · average incline ${d.slope_deg}° · rise ${f2(t.rise)} m per cycle` : `bumps up to ±${d.amp_m} m across the track`;
  const solved = fnd.unsolved_frames.length === 0, clr = fnd.min_body_clearance_m;
  $('kin').innerHTML = row('Leg reach', `${status(solved)} ${solved ? 'every frame solved' : fnd.unsolved_frames.length + ' frames unsolved'}`) +
    row('Hip lowered', `${status(fnd.max_hip_drop_m < 0.005, true)} ${fnd.max_hip_drop_m < 0.005 ? 'not needed' : f2(fnd.max_hip_drop_m) + ' m to reach'}`) +
    row('Lowest body/arm clearance', `${status(clr > 0.3, clr > 0)} ${clr == null ? '—' : f2(clr) + ' m'}`);
  if (d.kind === 'plane') {
    const lim = D.sys008.limit_deg, s = slope;
    $('stat').innerHTML = row('Frozen joints: margin', `<b style="color:${d.frozen_margin_m > 0 ? C.ok : C.bad}">${d.frozen_margin_m > 0 ? f2(d.frozen_margin_m) + ' m' : 'tips (' + f2(d.frozen_margin_m) + ' m)'}</b>`) +
      row('Frozen joints: tips at', `${f1(d.frozen_tip_deg)}° this way`) +
      row(`Gait lean (${Math.round((1 - D.lean.value) * 100)}% compensated)`, `<b style="color:${d.lean_margin_m > 0 ? C.ok : C.bad}">${d.lean_margin_m > 0 ? f2(d.lean_margin_m) + ' m' : 'tips'}</b>`) +
      row('With that lean: tips at', `${f1(d.lean_tip_deg)}° this way`) +
      row(`SYS-008 limit ${lim}°`, s === 0 ? 'level' : `${status(s <= lim, false)} ${f1(s)}° ${s < lim ? 'within' : s === lim ? 'at the limit' : 'beyond'}`);
    $('statnote').textContent = `Standing CL-05 (cad/metrics.json): centre of gravity ${f2(D.standing.cg_m[2])} m high over the double-support polygon, projected along gravity on this slope. ` +
      `"Gait lean" leaves ${D.lean.value} of the slope-induced shift uncompensated, the level-1 simulation's assumption (sim/spec/walker.yaml: ${D.lean.source}). Single-support phases are not checked.`;
  } else {
    $('stat').innerHTML = row('Static margin', 'not computed: no single slope') + (d.slope_deg ? row(`SYS-008 limit ${D.sys008.limit_deg}°`, `average incline ${d.slope_deg}°`) : '');
    $('statnote').textContent = 'Uneven ground: only the leg kinematics above are checked.';
  }
  $('req').innerHTML = `<div class="row" style="display:block"><b>${D.sys008.id}</b> ${D.sys008.title} · ${D.sys008.status}<br><span class="k">${D.sys008.statement}</span></div>` +
    `<div class="row" style="display:block"><b>${D.hazard.id}</b> ${D.hazard.title} · ${D.hazard.status} · initial risk ${D.hazard.rac}</div>`;
  tlist.querySelectorAll('button').forEach((b) => b.classList.toggle('on', b.dataset.k === S.key));
  lastMargins = d.kind === 'plane' ? { frozen: d.frozen_margin_m, lean: d.lean_margin_m } : null;
}
function kinRows(t) {
  const fnd = t.findings, solved = fnd.unsolved_frames.length === 0, clr = fnd.min_body_clearance_m;
  return row('Leg reach', `${status(solved)} ${solved ? 'every frame solved' : fnd.unsolved_frames.length + ' frames unsolved'}`) +
    row('Hip lowered', `${status(fnd.max_hip_drop_m < 0.005, true)} ${fnd.max_hip_drop_m < 0.005 ? 'not needed' : f2(fnd.max_hip_drop_m) + ' m to reach'}`) +
    row('Lowest body/arm/load clearance', `${status(clr > 0.3, clr > 0)} ${clr == null ? '—' : f2(clr) + ' m'}`);
}
function renderLoaded() {
  const t = terr(), d = info(), c = D.carry, kg = S.mass, cg = loadedCg(kg), poly = c.support_polygon_m, T0 = T();
  $('tname').textContent = d.label.toUpperCase() + ' · LOADED';
  $('tsub').textContent = `loaded walk: stride ${T0.stride_m} m, foot lift ${T0.lift_m} m · rise ${f2(t.rise)} m per cycle` + (d.kind === 'rubble' ? ` · bumps repeat every ${T0.stride_m} m` : '');
  $('kin').innerHTML = kinRows(t);
  $('loadrow').style.display = 'block';
  $('massv').textContent = `${kg.toLocaleString('en')} kg`;
  $('massnote').innerHTML = `Placeholder load ${c.load_envelope_m.map(f2).join('×')} m, centre ${f2(c.load_centre_m[0])} m ahead and ${f2(c.load_centre_m[2])} m up · mass TBD (SYS-019). ` +
    `CAD marks: margin peak ${c.peak.load_kg} kg · ${c.flag_margin_m} m flag ${c.flag_kg} kg · tips on level ground ${c.tipover_kg} kg.`;
  const lvl = margin(cg, poly, 0, 0), col = (m) => m >= c.flag_margin_m ? C.ok : m > 0 ? C.warn : C.bad;
  let html = row('Level ground: margin', `<b style="color:${col(lvl)}">${lvl > 0 ? f2(lvl) + ' m' : 'tips'}</b>${lvl > 0 && lvl < c.flag_margin_m ? ` · under the ${c.flag_margin_m} m flag` : ''}`);
  const out = { level: +lvl.toFixed(4) };
  if (d.kind === 'plane') {
    const pi = d.pitch_deg || 0, ro = d.roll_deg || 0, s = Math.hypot(pi, ro), sp = s ? pi / s : 1, sr = s ? ro / s : 0;
    const fz = margin(cg, poly, pi, ro), ln = margin(cg, poly, pi, ro, D.lean.value);
    out.frozen = +fz.toFixed(4); out.lean = +ln.toFixed(4);
    html += row('Frozen joints: margin', `<b style="color:${col(fz)}">${fz > 0 ? f2(fz) + ' m' : 'tips (' + f2(fz) + ' m)'}</b>`) +
      row('Frozen joints: tips at', `${f1(tipAt(cg, poly, sp, sr))}° this way`) +
      row(`Gait lean (${Math.round((1 - D.lean.value) * 100)}% compensated)`, `<b style="color:${col(ln)}">${ln > 0 ? f2(ln) + ' m' : 'tips'}</b>`) +
      row('With that lean: tips at', `${f1(tipAt(cg, poly, sp, sr, D.lean.value))}° this way`) +
      row(`SYS-008 limit ${D.sys008.limit_deg}°`, s === 0 ? 'level' : `${status(s <= D.sys008.limit_deg, false)} ${f1(s)}°`) +
      row('SYS-019 loaded slope limit', '<span style="color:' + C.warn + '">TBD</span>');
  } else html += row('On this ground', 'uneven: only the level margin and the leg kinematics are checked') + row('SYS-019 loaded step-height limit', '<span style="color:' + C.warn + '">TBD</span>');
  $('stat').innerHTML = html;
  $('statnote').textContent = `Carry posture of CL-05 (cad/metrics.json, ${c.mass_kg.toLocaleString('en')} kg placeholder) with the load's mass added at its centre: the same static check as the CAD's carry figures. ` +
    `A load ahead of the walker moves the centre of gravity forward: more margin uphill (rear edge), less downhill (front edge). Single-support phases and load dynamics are not checked.`;
  $('req').innerHTML = `<div class="row" style="display:block"><b>${D.sys019.id}</b> ${D.sys019.title} · ${D.sys019.status}<br><span class="k">${D.sys019.statement}</span></div>` +
    `<div class="row" style="display:block"><b>${D.sys008.id}</b> ${D.sys008.title} · ${D.sys008.status}</div>` +
    `<div class="row" style="display:block"><b>${D.hazard_load.id}</b> ${D.hazard_load.title} · ${D.hazard_load.status} · initial risk ${D.hazard_load.rac}</div>` +
    `<div class="row" style="display:block"><b>${D.hazard.id}</b> ${D.hazard.title} · ${D.hazard.status} · initial risk ${D.hazard.rac}</div>`;
  tlist.querySelectorAll('button').forEach((b) => b.classList.toggle('on', b.dataset.k === S.key));
  lastMargins = out;
}
function drawProfile(x0) {
  const W = 1000, H = 110, a = x0 - 4, b = x0 + 8, X = (x) => (x - a) / (b - a) * W;
  const zs = [];
  for (let x = a; x <= b; x += 0.05) zs.push(groundAt(x, 0.55), groundAt(x, -0.55));
  const zmin = Math.min(...zs), zmax = Math.max(...zs, zmin + 1), Z = (z) => H - 14 - (z - zmin) / (zmax - zmin) * (H - 34);
  const line = (y, col) => { let d = ''; for (let x = a; x <= b; x += 0.05) d += `${d ? 'L' : 'M'}${X(x).toFixed(1)},${Z(groundAt(x, y)).toFixed(1)}`; return `<path d="${d}" fill="none" stroke="${col}" stroke-width="1.6"/>`; };
  const g0 = groundAt(x0, 0), r = Math.tan(THREE.MathUtils.degToRad(D.sys008.limit_deg));
  $('prof').innerHTML = line(0.55, C.sel) + line(-0.55, C.haz) +
    `<path d="M${X(x0)},${Z(g0)} L${X(b)},${Z(g0 + (b - x0) * r)}" stroke="${C.mute}" stroke-dasharray="5 4" fill="none"/>` +
    `<text x="${X(b) - 190}" y="${Math.max(24, Z(g0 + (b - x0) * r) + 14)}" font-size="10" fill="${C.mute}">SYS-008 20° from here</text>` +
    `<line x1="${X(x0)}" y1="4" x2="${X(x0)}" y2="${H}" stroke="${C.ink}" stroke-width="2"/><text x="${X(x0) + 4}" y="12" font-size="10" fill="${C.ink}">hip</text>` +
    `<text x="6" y="${H - 2}" font-size="10" fill="${C.mute}"><tspan fill="${C.sel}">— left foot track</tspan>  <tspan fill="${C.haz}">— right foot track</tspan>  · vertical exaggerated · 12 m window</text>`;
  $('ptitle').textContent = `${info().label}${S.mode === 'loaded' ? ' · loaded' : ''} · ground at the hip ${f2(g0)} m`;
}

// ------------------------------------------------------------------ controls
function setTerrain(k) { if (!posed(S.mode, k)) return; S.key = k; S.u = 0; groundKey = null; renderPanels(); }
function setMode(m) {
  if (!COURSE[m]) return;
  S.mode = m; S.u = 0; groundKey = null;
  if (!posed(m, S.key)) S.key = 'flat';
  renderPanels(); refresh();
}
document.querySelectorAll('#mode button').forEach((b) => { b.onclick = () => setMode(b.dataset.mode); });
$('mass').max = D.carry.tipover_kg;
$('mass').oninput = (e) => { S.mass = +e.target.value; renderPanels(); };
function refresh() {
  document.querySelectorAll('[data-t]').forEach((b) => b.classList.toggle('on', !!S.show[b.dataset.t]));
  document.querySelectorAll('#render button').forEach((b) => b.classList.toggle('on', b.dataset.r === S.render));
  document.querySelectorAll('[data-sp]').forEach((b) => b.classList.toggle('on', +b.dataset.sp === S.speed));
  document.querySelectorAll('#mode button').forEach((b) => b.classList.toggle('on', b.dataset.mode === S.mode));
  tlist.querySelectorAll('button').forEach((b) => { const ok = !!posed(S.mode, b.dataset.k); b.disabled = !ok;
    const sk = COURSE[S.mode].meta.terrains.find((x) => x.key === b.dataset.k); b.title = ok ? (info2(b.dataset.k).note || info2(b.dataset.k).label) : (sk && sk.skipped) || 'not posed'; });
  $('bplay').textContent = S.playing ? '❚❚ Pause' : '▶ Play'; $('bplay').classList.toggle('on', S.playing);
}
document.querySelectorAll('[data-t]').forEach((b) => { b.onclick = () => { S.show[b.dataset.t] = !S.show[b.dataset.t]; groundKey = null; refresh(); }; });
document.querySelectorAll('#render button').forEach((b) => { b.onclick = () => { S.render = b.dataset.r; applyMaterials(); refresh(); }; });
document.querySelectorAll('[data-sp]').forEach((b) => { b.onclick = () => { S.speed = +b.dataset.sp; refresh(); }; });
document.querySelectorAll('#view button').forEach((b) => { b.onclick = () => setView(b.dataset.v); });
$('bplay').onclick = () => { S.playing = !S.playing; refresh(); };
$('helpbtn').onclick = () => $('help').classList.toggle('open');
$('help').onclick = (e) => { if (e.target.id === 'help') $('help').classList.remove('open'); };
$('terms').onclick = () => $('terms').classList.toggle('open');
canvas.addEventListener('pointerdown', () => { try { window.focus(); } catch (e) { /* framed page */ } });
addEventListener('keydown', (e) => {
  const k = e.key.toLowerCase(), keys = D.terrains.map((t) => t.key), i = keys.indexOf(S.key);
  const next = (dir) => { for (let n = 1; n <= keys.length; n++) { const kk = keys[(i + dir * n + keys.length * 2) % keys.length]; if (posed(S.mode, kk)) return setTerrain(kk); } };
  if (k === 'arrowright') next(1); if (k === 'arrowleft') next(-1);
  if (k === 'l') setMode(S.mode === 'loaded' ? 'unloaded' : 'loaded');
  if (k === ' ') { e.preventDefault(); S.playing = !S.playing; refresh(); }
  const tg = { g: 'plumb', b: 'stripes', p: 'person' }[k]; if (tg) { S.show[tg] = !S.show[tg]; groundKey = null; refresh(); }
  if (k === 'v') { S.render = MODES[(MODES.indexOf(S.render) + 1) % 3]; applyMaterials(); refresh(); }
  if (k === '?' || (k === '/' && e.shiftKey)) $('help').classList.toggle('open');
  if (k === 'escape') $('help').classList.remove('open');
});
function layout() {
  const w = innerWidth, h = canvas.clientHeight || innerHeight; renderer.setSize(w, h, false); cam.aspect = w / h;
  const L = $('left').getBoundingClientRect(), Rr = $('right').getBoundingClientRect(), B = $('bottom').getBoundingClientRect();
  if (w > 1100) cam.setViewOffset(w, h, w / 2 - (L.right + Rr.left) / 2, h / 2 - (60 + B.top - 40) / 2, w, h); else cam.clearViewOffset();
  cam.updateProjectionMatrix();
}
addEventListener('resize', layout);

// ------------------------------------------------------------------ frame
let last = performance.now(), profT = 0;
function frame(now) {
  const dt = Math.min(0.1, (now - last) / 1000); last = now;
  if (S.playing) S.u += dt * RATE * S.speed;
  const p = pose(S.u), c0 = p.k - Math.ceil(4 / STRIDE());
  if (groundKey !== S.mode + S.key + S.show.stripes || c0 !== groundC) buildGround(c0);
  // CG of the standing layout carried with the body (approximate while walking), its plumb line to the ground
  const cgw = walker.localToWorld(new THREE.Vector3(...D.standing.cg_m)), gz = groundAt(cgw.x, cgw.y);
  cg.position.copy(cgw); plumb.geometry.setFromPoints([cgw, new THREE.Vector3(cgw.x, cgw.y, gz)]); plumb.computeLineDistances();
  hit.position.set(cgw.x, cgw.y, gz + 0.02); cg.visible = plumb.visible = hit.visible = S.show.plumb;
  person.visible = S.show.person; person.position.set(p.x - 1.2, -3.0, groundAt(p.x - 1.2, -3.0));
  const tgt = new THREE.Vector3(p.x, 0, walker.position.z + 2.0), d = tgt.clone().sub(controls.target).multiplyScalar(Math.min(1, 4 * dt));
  controls.target.add(d); cam.position.add(d);
  if (camTween) { camTween.t = Math.min(1, camTween.t + dt * 2.2); const e = 0.5 - 0.5 * Math.cos(Math.PI * camTween.t);
    cam.position.lerpVectors(camTween.from, camTween.to, e); if (camTween.t >= 1) camTween = null; }
  sun.target.position.copy(controls.target); sun.position.copy(controls.target).add(new THREE.Vector3(6, -9, 14));
  controls.update();
  if ((profT += dt) > 0.1) { drawProfile(p.x); profT = 0; }
  $('pnote').textContent = `${S.playing ? 'walking' : 'paused'} · ${S.speed}× viewing pace`; $('pframe').textContent = `cycle ${p.k + 1} · frame ${p.i + 1}/${N()}`;
  renderer.setClearColor(C.bg, 1); renderer.render(scene, cam);
  const az = (THREE.MathUtils.radToDeg(Math.atan2(cam.position.y - controls.target.y, cam.position.x - controls.target.x)) + 360) % 360;
  const dist = cam.position.distanceTo(controls.target), el = THREE.MathUtils.radToDeg(Math.asin((cam.position.z - controls.target.z) / dist));
  $('cam').textContent = `AZ ${az.toFixed(0)}° · EL ${el.toFixed(0)}° · R ${dist.toFixed(1)} M · ${S.render.toUpperCase()} · CL-05 ${S.mode === 'loaded' ? 'LOADED ' : ''}ON ${info().label.toUpperCase()}`;
  window.__state = { terrain: S.key, mode: S.mode, mass: S.mass, u: +S.u.toFixed(3), x: +p.x.toFixed(3), z: +walker.position.z.toFixed(3), playing: S.playing,
    margins: lastMargins };
  window.__ready = true;
  requestAnimationFrame(frame);
}

// ------------------------------------------------------------------ start
if (q.get('mode') === 'loaded') S.mode = 'loaded';
if (q.get('mass')) { S.mass = +q.get('mass'); $('mass').value = S.mass; }
if (q.get('terrain')) setTerrain(q.get('terrain'));
if (q.get('t')) S.u = +q.get('t');
if (MODES.includes(q.get('render'))) S.render = q.get('render');
refresh(); applyMaterials(); renderPanels(); layout();
controls.target.set(0, 0, 2.0); setView(VIEWS[q.get('view')] ? q.get('view') : 'iso', true);
$('load').remove();
requestAnimationFrame(frame);
