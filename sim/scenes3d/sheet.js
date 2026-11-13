// Susanoo SUS-M1 interactive general-arrangement sheet (three.js r170). Embedded in docs/3d/SUS-M1.html by build_sheet.py.
// window.SHEET: sheet data from the records (metrics, hazards, replay); window.SUS_M1_GEOMETRY: CL-05 meshes and pose
// clips from tools/cad/b3d/cl05_web.py. Nothing here computes dynamics: poses are the CAD's, figures are the records',
// the tip check is static geometry and the replay plots stored simulation output.
// URL: ?posture=kneel&render=xray&hazard=HAZ-WLK-002&explode=1&dims=1&cg=1&view=side&settle=1 (settle: no transition).
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

THREE.Object3D.DEFAULT_UP.set(0, 0, 1);
const D = window.SHEET, G = window.SUS_M1_GEOMETRY, M = G.meta;
const q = new URLSearchParams(location.search);
const $ = (id) => document.getElementById(id);
const C = { ink: '#1e293b', mute: '#64748b', line: '#c3ccd7', haz: '#ea580c', sel: '#4f46e5', ok: '#0d9488', warn: '#d97706', bad: '#dc2626', bg: '#e4e9ef' };

// ------------------------------------------------------------------ geometry
const raw = Uint8Array.from(atob(G.bin), (c) => c.charCodeAt(0)).buffer;
const sl = ([o, n]) => raw.slice(o, o + n);
const P16 = new Int16Array(sl(M.layout.positions)), I16 = new Uint16Array(sl(M.layout.indices)), MAT = new Float32Array(sl(M.layout.matrices));
const geoms = new Map();
function geom(i) {
  if (geoms.has(i)) return geoms.get(i);
  const m = M.meshes[i], [vo, vn] = m.v, [io, inn] = m.i, s = M.quantum_m, o = M.origin_m;
  const pos = new Float32Array(vn * 3);
  for (let k = 0; k < vn * 3; k++) pos[k] = P16[vo * 3 + k] * s + o[k % 3];
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setIndex(new THREE.BufferAttribute(I16.slice(io, io + inn), 1));
  g.computeVertexNormals(); g.computeBoundingBox();
  geoms.set(i, g); return g;
}

// ------------------------------------------------------------------ renderer, scene
const canvas = $('gl');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
const labels = new CSS2DRenderer();
Object.assign(labels.domElement.style, { position: 'fixed', inset: '0', pointerEvents: 'none', zIndex: 1 });
document.body.appendChild(labels.domElement);

const scene = new THREE.Scene();
scene.add(new THREE.HemisphereLight('#ffffff', '#aab4c2', 1.7));
const sun = new THREE.DirectionalLight('#ffffff', 2.1);
sun.position.set(7, -9, 15); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -8, right: 8, top: 8, bottom: -8, near: 1, far: 50 }); sun.shadow.bias = -0.0004;
scene.add(sun, sun.target);
const fill = new THREE.DirectionalLight('#dfe7ff', 0.55); fill.position.set(-8, 6, 5); scene.add(fill);

const tilt = new THREE.Group(); scene.add(tilt);                 // ground slope for the static tip check
const groundG = new THREE.Group(); tilt.add(groundG);
const shadowPlane = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.ShadowMaterial({ opacity: 0.18 }));
shadowPlane.receiveShadow = true; groundG.add(shadowPlane);
const grid = new THREE.GridHelper(60, 60, '#b4bfcc', '#cfd7e0'); grid.rotation.x = Math.PI / 2; grid.position.z = 0.002; groundG.add(grid);
const walker = new THREE.Group(); tilt.add(walker);              // moves and turns when walking
const model = new THREE.Group(); walker.add(model);

// ------------------------------------------------------------------ materials per render mode
const MODES = ['shaded', 'line', 'xray'];
const mats = {};
for (const [cls, [color, op]] of Object.entries(D.classes)) {
  mats[cls] = {
    shaded: new THREE.MeshStandardMaterial({ color, roughness: 0.62, metalness: cls === 'actuator' ? 0.35 : 0.12, transparent: op < 1, opacity: op, depthWrite: op >= 1, side: THREE.DoubleSide }),
    line: new THREE.MeshBasicMaterial({ color: '#f8fafc', polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1, side: THREE.DoubleSide }),
    xray: new THREE.MeshStandardMaterial({ color, roughness: 0.5, transparent: true, opacity: 0.16, depthWrite: false, side: THREE.DoubleSide }),
    hl: new THREE.MeshStandardMaterial({ color: C.haz, emissive: C.haz, emissiveIntensity: 0.35, roughness: 0.5, side: THREE.DoubleSide }),
  };
}
// with a hazard selected, every other part is drawn plain so the highlighted parts stand out
const dimMat = new THREE.MeshStandardMaterial({ color: '#d5dbe3', roughness: 0.8, side: THREE.DoubleSide });
function matFor(cls) {
  const h = S.hazard && D.anchors[S.hazard] ? D.anchors[S.hazard].cls : null;
  if (!h || h === 'cg') return mats[cls][S.render];
  if (cls === h) return mats[cls].hl;
  return S.render === 'shaded' ? dimMat : mats[cls][S.render];
}
const edgeMat = { shaded: new THREE.LineBasicMaterial({ color: C.ink, transparent: true, opacity: 0.22 }),
  line: new THREE.LineBasicMaterial({ color: C.ink }), xray: new THREE.LineBasicMaterial({ color: '#334155', transparent: true, opacity: 0.35 }) };

// ------------------------------------------------------------------ state
const S = {
  posture: 'stand', target: 'stand', clipPos: 0,  // position along the current clip (0 = standing)
  show: { hazards: true, dims: false, explode: false, cg: true, person: true, uav: false },
  render: 'shaded', hazard: null, explode: 0, uavLift: 0,
  walk: { phase: 0, heading: 0, x: 0, y: 0, key: 0, turn: 0 },
  pitch: 0, roll: 0,
};
// ------------------------------------------------------------------ meshes: standing base set, per-frame extras on demand
const isBase = new Set(M.base);
const objs = new Map();   // mesh id -> THREE.Mesh
function obj(i) {
  if (objs.has(i)) return objs.get(i);
  const cls = M.meshes[i].cls;
  const m = new THREE.Mesh(geom(i), matFor(cls));
  m.matrixAutoUpdate = false; m.castShadow = D.classes[cls][1] >= 1; m.receiveShadow = true; m.userData = { cls, id: i };
  const e = new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry, 35), edgeMat[S.render]); e.matrixAutoUpdate = false;
  m.add(e); m.userData.edges = e;
  const c = new THREE.Vector3(); m.geometry.boundingBox.getCenter(c); m.userData.side = Math.sign(c.y) || 1;
  model.add(m); objs.set(i, m); return m;
}
M.base.forEach(obj);

// Clip frames: frame 0 is the standing pose (every base mesh, identity); then the exported frames.
const CLIPS = {};
for (const [name, rows] of Object.entries(M.clips)) {
  CLIPS[name] = [{ label: 'standing', body_x: 0, map: new Map(M.base.map((b) => [b, -1])), extras: [] },
    ...rows.map((r) => ({ label: r.label, body_x: r.body_x, map: new Map(r.vis.filter(([i]) => isBase.has(i))), extras: r.vis.filter(([i]) => !isBase.has(i)).map(([i]) => i) }))];
}
const walkFrames = CLIPS.walk;
const cycle0 = walkFrames.findIndex((f) => f.label.startsWith('walk '));
const cycleN = walkFrames.length - cycle0;

const tmpA = new THREE.Matrix4(), tmpB = new THREE.Matrix4(), I4 = new THREE.Matrix4();
function setMat(m, k) { if (k < 0) return m.copy(I4); const a = MAT.subarray(k * 12, k * 12 + 12);
  return m.set(a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8], a[9], a[10], a[11], 0, 0, 0, 1); }
function lerpMat(out, a, b, f) { for (let i = 0; i < 16; i++) out.elements[i] = a.elements[i] + (b.elements[i] - a.elements[i]) * f; return out; }

// Pose = two frames and a fraction between them
function applyPose(A, B, f) {
  const near = f < 0.5 ? A : B;
  for (const b of M.base) {
    const m = objs.get(b), ka = A.map.get(b), kb = B.map.get(b);
    if (ka !== undefined && kb !== undefined) { lerpMat(m.matrix, setMat(tmpA, ka), setMat(tmpB, kb), f); m.visible = true; }
    else if (near.map.has(b)) { setMat(m.matrix, near.map.get(b)); m.visible = true; }
    else m.visible = false;
  }
  for (const [i, m] of objs) if (!isBase.has(i)) m.visible = false;
  for (const i of near.extras) { const m = obj(i); m.matrix.identity(); m.visible = true; }
}

const postureDef = Object.fromEntries(D.postures.map((p) => [p.key, p]));
const clipOf = (key) => postureDef[key].clip;

// ------------------------------------------------------------------ person, CG, support polygon, dims, callouts
const person = new THREE.Group();
{ const pm = new THREE.MeshStandardMaterial({ color: '#a3acb9', roughness: 0.8 });
  const part = (g, x, y, z) => { const o = new THREE.Mesh(g, pm); o.position.set(x, y, z); o.castShadow = true; person.add(o); return o; };
  for (const y of [-0.1, 0.1]) part(new THREE.CapsuleGeometry(0.075, 0.72, 4, 12), 0, y, 0.44).rotation.x = Math.PI / 2;
  part(new THREE.CapsuleGeometry(0.17, 0.42, 4, 14), 0, 0, 1.22).rotation.x = Math.PI / 2;
  part(new THREE.SphereGeometry(0.11, 18, 12), 0, 0, 1.64);
  for (const y of [-0.24, 0.24]) part(new THREE.CapsuleGeometry(0.05, 0.56, 4, 10), 0, y, 1.12).rotation.x = Math.PI / 2;
  person.position.set(0.6, -2.4, 0); tilt.add(person); }

const overlay = new THREE.Group(); walker.add(overlay);
const cgGroup = new THREE.Group(); overlay.add(cgGroup);
const cgBall = new THREE.Group();
for (let k = 0; k < 4; k++) { const s = new THREE.Mesh(new THREE.SphereGeometry(0.09, 24, 12, k * Math.PI / 2, Math.PI / 2),
  new THREE.MeshBasicMaterial({ color: k % 2 ? '#111827' : '#eab308', depthTest: false })); s.renderOrder = 10; cgBall.add(s); }
cgGroup.add(cgBall);
const polyMesh = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({ color: '#14b8a6', transparent: true, opacity: 0.25, depthWrite: false, side: THREE.DoubleSide }));
const polyLine = new THREE.LineLoop(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: C.ok }));
polyMesh.position.z = 0.01; polyLine.position.z = 0.012; cgGroup.add(polyMesh, polyLine);
const plumb = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
  new THREE.LineDashedMaterial({ color: '#111827', dashSize: 0.08, gapSize: 0.06, depthTest: false }));
plumb.renderOrder = 9; scene.add(plumb);
const plumbHit = new THREE.Mesh(new THREE.RingGeometry(0.05, 0.08, 24), new THREE.MeshBasicMaterial({ color: C.haz, depthTest: false }));
plumbHit.renderOrder = 11; scene.add(plumbHit);

function css(cls, text) { const el = document.createElement('div'); el.className = cls; el.textContent = text; return new CSS2DObject(el); }
const dims = new THREE.Group(); overlay.add(dims);
const dimLines = new THREE.LineSegments(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: C.ink }));
dims.add(dimLines);
const dimL = css('dim', ''), dimW = css('dim', ''), dimH = css('dim', ''); dims.add(dimL, dimW, dimH);

// Hazard callouts: drawn in screen space like a drawing's balloons, in two columns beside the model, never overlapping.
const coLayer = $('co'), coSvg = $('cosvg');
const co = {};
for (const h of D.hazards) {
  if (!D.anchors[h.id]) continue;
  const el = document.createElement('div'); el.className = 'co'; el.textContent = h.id; el.title = h.title;
  el.onclick = () => selectHazard(h.id); coLayer.appendChild(el); co[h.id] = { el, p: null };
}
function drawCallouts() {
  const w = innerWidth, h = canvas.clientHeight || innerHeight;
  const L = $('left').getBoundingClientRect(), Rr = $('right').getBoundingClientRect(), wide = w > 1100;
  const scr = (v) => { const p = walker.localToWorld(v.clone()).project(cam); return [(p.x + 1) / 2 * w, (1 - p.y) / 2 * h]; };
  const b = modelBox(), xs = [], c = scr(b.getCenter(new THREE.Vector3()));
  for (const x of [b.min.x, b.max.x]) for (const y of [b.min.y, b.max.y]) for (const z of [b.min.z, b.max.z]) xs.push(scr(new THREE.Vector3(x, y, z))[0]);
  const colL = Math.max(wide ? L.right + 16 : 8, Math.min(...xs) - 150), colR = Math.min(wide ? Rr.left - 116 : w - 110, Math.max(...xs) + 40);
  const items = Object.entries(co).filter(([, k]) => k.p).map(([id, k]) => ({ id, k, a: scr(k.p) }));
  let svg = '';
  for (const side of [0, 1]) {
    const col = items.filter((it) => (it.a[0] >= c[0]) === !!side).sort((u, v) => u.a[1] - v.a[1]);
    let y = -1e9;
    for (const it of col) { it.y = Math.max(it.a[1], y + 24); y = it.y; }
    const over = y - (h - 200); if (over > 0) for (const it of col) it.y -= over;   // keep the column above the replay panel
    for (const it of col) {
      const x = side ? colR : colL, ex = side ? x : x + 100;
      it.k.el.style.left = `${x}px`; it.k.el.style.top = `${it.y - 9}px`;
      const sel = it.id === S.hazard;
      svg += `<polyline points="${it.a[0].toFixed(1)},${it.a[1].toFixed(1)} ${(side ? ex - 14 : ex + 14)},${it.y.toFixed(1)} ${ex},${it.y.toFixed(1)}" fill="none" stroke="${C.haz}" stroke-width="${sel ? 2 : 1}"/>` +
        `<circle cx="${it.a[0].toFixed(1)}" cy="${it.a[1].toFixed(1)}" r="${sel ? 4 : 3}" fill="${C.haz}"/>`;
    }
  }
  for (const k of Object.values(co)) k.el.style.display = k.p ? '' : 'none';
  coSvg.innerHTML = svg;
}

// ------------------------------------------------------------------ metrics for the shown posture
function metricsNow() {
  const p = postureDef[S.posture], settled = S.posture === S.target && (S.posture === 'stand' || S.clipPos >= CLIPS[clipOf(S.posture)].length - 1);
  if (S.posture === 'walk') return { m: D.metrics.postures.standing, analysed: false, note: 'walk: concept gait, not analysed; standing figures shown' };
  if (!settled) return { m: null, analysed: false, note: 'between postures: concept kinematics, not analysed' };
  const key = p.metrics || 'standing';
  return { m: D.metrics.postures[key], analysed: true, note: `${key} · cad/metrics.json (placeholder geometry)` };
}

// ------------------------------------------------------------------ class bounds in model space (the walker with its docked UAV; carried load excluded)
const bb = new THREE.Box3(), bt = new THREE.Box3();
function classBox(cls) {
  bb.makeEmpty();
  for (const m of objs.values()) if (m.visible && m.userData.cls === cls) { bt.copy(m.geometry.boundingBox).applyMatrix4(m.matrix); bb.union(bt); }
  return bb.isEmpty() ? null : bb.clone();
}
function modelBox() {
  bb.makeEmpty();
  for (const m of objs.values()) if (m.visible && m.userData.cls !== 'payload') { bt.copy(m.geometry.boundingBox).applyMatrix4(m.matrix); bb.union(bt); }
  return bb.clone();
}
function anchorPoint(box, at) {
  const c = box.getCenter(new THREE.Vector3());
  return ({ top: [c.x, c.y, box.max.z], bottom: [c.x, c.y, box.min.z], front: [box.max.x, c.y, c.z], rear: [box.min.x, c.y, c.z],
    side: [c.x, box.min.y, c.z], centre: [c.x, c.y, c.z] })[at || 'centre'];
}

// ------------------------------------------------------------------ explode offsets (model space, metres)
const EXPLODE = { cage: [0, 0, 0.7], uav: [0, 0, 1.0], rotor: [0, 0, 1.0], dock: [-0.5, 0, 0.6], armor: [0, 0.45, 0.35], power: [-1.0, 0, 0],
  hose: [-0.5, 0, 0], arm: [0, 0.8, 0], actuator: [0, 0.35, 0], safety: [0.8, 0, 0.2], access: [1.0, 0, 0], escape: [0, 0.9, 0],
  seat: [0.9, 0, 0.9], occupant: [0.9, 0, 0.9], payload: [0.8, 0, 0], structure: [0, 0, 0] };
const tOff = new THREE.Matrix4();
function postProcess() {
  for (const m of objs.values()) {
    if (!m.visible) continue;
    const e = EXPLODE[m.userData.cls] || [0, 0, 0], sd = ['armor', 'arm', 'actuator', 'escape'].includes(m.userData.cls) ? m.userData.side : 1;
    let x = e[0] * S.explode, y = e[1] * S.explode * sd, z = e[2] * S.explode;
    if (m.userData.cls === 'uav' || m.userData.cls === 'rotor') z += 1.5 * S.uavLift;   // illustration: lifted clear of the dock, not a flight
    if (x || y || z) m.matrix.premultiply(tOff.makeTranslation(x, y, z));
    m.matrixWorldNeedsUpdate = true;
  }
}

// ------------------------------------------------------------------ hazard highlight and render mode
function applyMaterials() {
  for (const m of objs.values()) { m.material = matFor(m.userData.cls); m.userData.edges.material = edgeMat[S.render]; }
}

// ------------------------------------------------------------------ camera, controls, views
const cam = new THREE.PerspectiveCamera(30, 1, 0.1, 400);
const controls = new OrbitControls(cam, canvas);
controls.enableDamping = true; controls.dampingFactor = 0.08; controls.target.set(0, 0, 2.1);
const VIEWS = { iso: [315, 18, 17.5], front: [0, 5, 17], side: [270, 5, 17], top: [270, 89, 17], rear: [180, 6, 17] };
let camTween = null;
function sph(az, el, r) { const a = THREE.MathUtils.degToRad(az), e = THREE.MathUtils.degToRad(el);
  return new THREE.Vector3(Math.cos(e) * Math.cos(a) * r, Math.cos(e) * Math.sin(a) * r, Math.sin(e) * r); }
function setView(v, instant) {
  const [az, el, r] = VIEWS[v]; const to = sph(az, el, r).add(controls.target);
  document.querySelectorAll('#view button').forEach((b) => b.classList.toggle('on', b.dataset.v === v));
  if (instant) { cam.position.copy(to); controls.update(); return; }
  camTween = { from: cam.position.clone(), to, t: 0 };
}
const ortho = { front: new THREE.OrthographicCamera(), side: new THREE.OrthographicCamera(), top: new THREE.OrthographicCamera() };

// ------------------------------------------------------------------ UI: postures, toggles, render, views
const pbar = $('posture');
for (const p of D.postures) {
  const b = document.createElement('button'); b.textContent = p.label; b.dataset.p = p.key;
  b.title = `key ${D.postures.indexOf(p) + 1}`; b.onclick = () => goPosture(p.key); pbar.appendChild(b);
}
function goPosture(k) { S.target = k; refreshButtons(); }
function refreshButtons() {
  pbar.querySelectorAll('button').forEach((b) => b.classList.toggle('on', b.dataset.p === S.target));
  document.querySelectorAll('[data-t]').forEach((b) => b.classList.toggle('on', !!S.show[b.dataset.t]));
  document.querySelectorAll('#render button').forEach((b) => b.classList.toggle('on', b.dataset.r === S.render));
  $('drive').style.display = S.target === 'walk' ? 'block' : 'none';
}
document.querySelectorAll('[data-t]').forEach((b) => { b.onclick = () => { S.show[b.dataset.t] = !S.show[b.dataset.t]; refreshButtons(); }; });
document.querySelectorAll('#render button').forEach((b) => { b.onclick = () => { S.render = b.dataset.r; applyMaterials(); refreshButtons(); }; });
document.querySelectorAll('#view button').forEach((b) => { b.onclick = () => setView(b.dataset.v); });
$('helpbtn').onclick = () => $('help').classList.toggle('open');
$('help').onclick = (e) => { if (e.target.id === 'help') $('help').classList.remove('open'); };
$('terms').onclick = () => $('terms').classList.toggle('open');

// ------------------------------------------------------------------ spec panel
$('ltitle').textContent = D.metrics.title.toUpperCase();
const f2 = (v) => Number(v).toFixed(2);
function renderSpec() {
  const { m, note } = metricsNow();
  const rows = m ? [['Envelope', `${f2(m.envelope_m[0])}×${f2(m.envelope_m[1])} m`], ['Height', `${f2(m.height_m)} m`],
    ['Mass*', `${m.placeholder_mass_kg.toLocaleString('en')} kg`], ['CG height', `${f2(m.cg_m[2])} m`],
    ['Margin', `${f2(m.static_margin_m)} m`], ['Tip angle', `${m.static_tip_angle_deg.toFixed(1)}°`],
    ['Pilot eye', `${f2(m.pilot_eye_m)} m`], ['Floor', `${f2(m.cockpit_floor_m)} m`],
    ['Rotor↔pilot', `${f2(m.rotor_to_pilot_m)} m`], ['Egress sill', `${f2(m.egress_sill_m)} m`]]
    : [['Envelope', '—'], ['Height', '—'], ['Mass*', '—'], ['CG height', '—'], ['Margin', '—'], ['Tip angle', '—']];
  $('spec').innerHTML = rows.map(([k, v]) => `<div class="row"><span class="k">${k}</span><span>${v}</span></div>`).join('');
  $('specnote').textContent = `* placeholder mass · ${note}`;
}

// ------------------------------------------------------------------ hazard list
const RAC = (r) => (r ? `r${r[0]}` : '');
$('hzcount').textContent = `${D.hazards.length} · ${D.hazards.every((h) => h.status === 'open') ? 'all open' : D.hazards.filter((h) => h.status === 'open').length + ' open'}`;
$('hzlist').innerHTML = D.hazards.map((h) => `<div class="hz${D.anchors[h.id] ? '' : ' off'}" tabindex="0" data-h="${h.id}" title="${h.title}">` +
  `<b>${h.id}</b><span>${h.title}</span><span class="tag ${RAC(h.rac)}" title="initial risk ${h.rac} ${h.level}">${h.rac || '—'}</span></div>`).join('');
document.querySelectorAll('.hz').forEach((el) => { el.onclick = () => selectHazard(el.dataset.h); el.onkeydown = (e) => { if (e.key === 'Enter') selectHazard(el.dataset.h); }; });
function selectHazard(id) {
  S.hazard = S.hazard === id ? null : id;
  document.querySelectorAll('.hz').forEach((el) => el.classList.toggle('sel', el.dataset.h === S.hazard));
  for (const [k, c] of Object.entries(co)) c.el.classList.toggle('sel', k === S.hazard);
  const h = D.hazards.find((x) => x.id === S.hazard), a = h && D.anchors[h.id];
  $('hzsel').style.display = h ? 'block' : 'none';
  if (h) $('hzsel').innerHTML = `<b>${h.id}</b> · ${h.status} · initial risk ${h.rac || '—'} ${h.level || ''}<br>${h.title}<br>` +
    `<span class="k">${h.subsystems.join(', ')} · ${a ? (a.cls === 'cg' ? 'centre of gravity' : 'parts: ' + a.cls) : 'no single part on the model'}</span>`;
  applyMaterials();
}

// ------------------------------------------------------------------ static tip margin
const tipsvg = $('tipsvg');
function pointInPoly(p, poly) { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
  const [xi, yi] = poly[i], [xj, yj] = poly[j];
  if ((yi > p[1]) !== (yj > p[1]) && p[0] < (xj - xi) * (p[1] - yi) / (yj - yi) + xi) c = !c; } return c; }
function edgeDist(p, poly) { let d = Infinity; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
  const [ax, ay] = poly[j], [bx, by] = poly[i], dx = bx - ax, dy = by - ay, t = Math.max(0, Math.min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)));
  d = Math.min(d, Math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)); } return d; }
function tipState() {
  const m = metricsNow().m || D.metrics.postures.standing, [cx, cy, cz] = m.cg_m, poly = m.support_polygon_m;
  const p = THREE.MathUtils.degToRad(S.pitch), r = THREE.MathUtils.degToRad(S.roll);
  const proj = [cx - cz * Math.tan(p), cy + cz * Math.tan(r)];          // nose up shifts it back; right side down shifts it right (-y)
  const inside = pointInPoly(proj, poly), d = edgeDist(proj, poly);
  return { m, proj, margin: inside ? d : -d, poly };
}
function renderTip() {
  const { m, proj, margin, poly } = tipState();
  const sc = 62, ox = 120, oy = 60, X = (x) => ox + x * sc, Y = (y) => oy - y * sc;
  const col = margin < 0 ? C.bad : margin < 0.1 ? C.haz : C.ok;
  tipsvg.innerHTML = `<text x="12" y="16" font-size="9" fill="${C.mute}">FWD →  (top view)</text>` +
    `<polygon points="${poly.map(([x, y]) => `${X(x)},${Y(y)}`).join(' ')}" fill="rgba(13,148,136,.15)" stroke="${C.ok}"/>` +
    `<line x1="${X(m.cg_m[0])}" y1="${Y(m.cg_m[1])}" x2="${X(proj[0])}" y2="${Y(proj[1])}" stroke="${col}" stroke-dasharray="3 2"/>` +
    `<circle cx="${X(m.cg_m[0])}" cy="${Y(m.cg_m[1])}" r="5" fill="#eab308" stroke="${C.ink}"/>` +
    `<circle cx="${X(proj[0])}" cy="${Y(proj[1])}" r="4" fill="none" stroke="${col}" stroke-width="2"/>` +
    `<text x="226" y="30" font-size="9" fill="${C.mute}">MARGIN</text><text x="226" y="50" font-size="17" font-weight="700" fill="${col}">${margin < 0 ? 'TIPS' : f2(margin) + ' m'}</text>` +
    `<text x="226" y="72" font-size="9" fill="${C.mute}">LEVEL LIMIT ${m.static_tip_angle_deg.toFixed(1)}°</text>` +
    `<text x="226" y="88" font-size="9" fill="${C.mute}">CG HEIGHT ${f2(m.cg_m[2])} m</text>` +
    `<text x="12" y="114" font-size="8.5" fill="${C.mute}">● CG   ○ CG along gravity on the slope   ▭ support polygon</text>`;
  $('pitchv').textContent = `${S.pitch.toFixed(1)}°`; $('rollv').textContent = `${S.roll.toFixed(1)}°`;
}
$('pitch').oninput = (e) => { S.pitch = +e.target.value; renderTip(); };
$('roll').oninput = (e) => { S.roll = +e.target.value; renderTip(); };

// ------------------------------------------------------------------ replay of the walker scenes (plots, stored results)
const R = { i: 0, t: 0, playing: false };
const rtabs = $('rtabs');
D.replay.forEach((r, i) => { const b = document.createElement('button'); b.textContent = r.id; b.onclick = () => { R.i = i; R.t = 0; drawReplay(); }; rtabs.appendChild(b); });
$('rplay').onclick = () => { R.playing = !R.playing; $('rplay').textContent = R.playing ? 'Pause' : 'Play'; };
const at = (F, t) => { let i = 0; while (i < F.length - 1 && F[i + 1][0] <= t) i++; return F[Math.min(i, F.length - 1)]; };
function drawReplay() {
  const r = D.replay[R.i], P = r.performed.frames, I = r.intended.frames, ev = r.performed.events, sp = r.spec;
  const tEnd = Math.max(P[P.length - 1][0], I[I.length - 1][0], 1) + 0.5;
  rtabs.querySelectorAll('button').forEach((b, i) => b.classList.toggle('on', i === R.i));
  $('rtitle').innerHTML = `<a id="rlink" href="${r.id}.html" title="open the scene's own 3D page">${r.id} 3D ↗</a> · ${r.title}`;
  const W = 1000, x = (t) => 40 + t / tEnd * (W - 60);
  const y1 = (v) => 38 - v / Math.max(sp.tip_offset_m * 1.2, 0.1) * 30, y2 = (v) => 80 - v / sp.com_height_m * 30;
  const path = (F, k, fy) => F.map((f, i) => `${i ? 'L' : 'M'}${x(f[0]).toFixed(1)},${fy(f[k]).toFixed(1)}`).join('');
  const mark = (t, txt, col) => t == null ? '' : `<line x1="${x(t)}" y1="4" x2="${x(t)}" y2="82" stroke="${col}" stroke-width="1.5"/><text x="${x(t) + 3}" y="12" font-size="10" fill="${col}">${txt}</text>`;
  $('rplot').innerHTML = `<text x="2" y="24" font-size="9" fill="${C.mute}">CG off</text><text x="2" y="70" font-size="9" fill="${C.mute}">height</text>` +
    `<line x1="40" y1="${y1(sp.tip_offset_m)}" x2="${W - 20}" y2="${y1(sp.tip_offset_m)}" stroke="${C.bad}" stroke-dasharray="6 4"/>` +
    `<text x="${W - 120}" y="${y1(sp.tip_offset_m) - 2}" font-size="9" fill="${C.bad}">tip limit ${sp.tip_offset_m} m</text>` +
    `<line x1="40" y1="${y2(sp.crouch_height_m)}" x2="${W - 20}" y2="${y2(sp.crouch_height_m)}" stroke="${C.mute}" stroke-dasharray="2 4"/>` +
    `<path d="${path(I, 1, y1)}" fill="none" stroke="${C.sel}" stroke-dasharray="5 3"/><path d="${path(P, 1, y1)}" fill="none" stroke="${C.haz}" stroke-width="2"/>` +
    `<path d="${path(I, 2, y2)}" fill="none" stroke="${C.sel}" stroke-dasharray="5 3"/><path d="${path(P, 2, y2)}" fill="none" stroke="${C.haz}" stroke-width="2"/>` +
    mark(ev.alarm_t, 'alarm', C.warn) + mark(ev.stop_t, 'stop', C.ink) + mark(ev.lock_t, 'lock', C.ink) +
    mark(ev.mishap_t, r.performed.outcome, C.bad) + `<line id="rcur" x1="${x(R.t)}" y1="2" x2="${x(R.t)}" y2="84" stroke="${C.ink}" stroke-width="2"/>`;
  const f = at(P, R.t);
  $('rt').textContent = `t ${R.t.toFixed(2)} s`;
  $('rinfo').innerHTML = `<span style="color:${C.haz}">— performed</span> ${r.performed.outcome} · <span style="color:${C.sel}">- - intended</span> ${r.intended.outcome} · ` +
    `CG ${f2(f[1])} m · height ${f2(f[2])} m · point-mass plant on CL-05 mass and CG height`;
  R.tEnd = tEnd; R.x = x;
}
$('rplot').onclick = (e) => { const b = $('rplot').getBoundingClientRect(); const u = (e.clientX - b.left) / b.width * 1000; R.t = Math.max(0, (u - 40) / (1000 - 60) * R.tEnd); drawReplay(); };

// ------------------------------------------------------------------ keyboard
const keys = new Set();
addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;
  const k = e.key.toLowerCase(); keys.add(k);
  const n = parseInt(k, 10); if (n >= 1 && n <= D.postures.length) goPosture(D.postures[n - 1].key);
  const tg = { h: 'hazards', m: 'dims', x: 'explode', g: 'cg', p: 'person', u: 'uav' }[k];
  if (tg) { S.show[tg] = !S.show[tg]; refreshButtons(); }
  if (k === 'v') { S.render = MODES[(MODES.indexOf(S.render) + 1) % 3]; applyMaterials(); refreshButtons(); }
  if (k === '?' || (k === '/' && e.shiftKey)) $('help').classList.toggle('open');
  if (k === 'escape') $('help').classList.remove('open');
  if (k === ' ') { e.preventDefault(); $('rplay').click(); }
});
addEventListener('keyup', (e) => keys.delete(e.key.toLowerCase()));

// ------------------------------------------------------------------ layout: main view centred between the panels
function layout() {
  const w = innerWidth, h = canvas.clientHeight || innerHeight;
  renderer.setSize(w, h, false); labels.setSize(w, h);
  cam.aspect = w / h;
  const L = $('left').getBoundingClientRect(), Rr = $('right').getBoundingClientRect(), B = $('bottom').getBoundingClientRect();
  if (w > 1100) { const cx = (L.right + Rr.left) / 2, cy = (60 + B.top - 40) / 2; cam.setViewOffset(w, h, w / 2 - cx, h / 2 - cy, w, h); }
  else cam.clearViewOffset();
  cam.updateProjectionMatrix();
}
addEventListener('resize', layout);

// ------------------------------------------------------------------ per-frame update
let last = performance.now();
const settle = q.has('settle');
function step(dt) {
  // posture transitions: leave the current clip back to standing, then play the target clip forward
  const speed = 7.5; // clip frames per second
  if (S.posture !== S.target) {
    if (S.posture === 'stand' || S.clipPos <= 0) { S.posture = S.target; S.clipPos = 0; }
    else if (S.posture === 'walk' && S.clipPos >= cycle0) { S.clipPos = cycle0 - 1; } // step out of the cycle into the stance
    else S.clipPos = settle ? 0 : Math.max(0, S.clipPos - speed * dt);
  } else if (S.posture !== 'stand') {
    const frames = CLIPS[clipOf(S.posture)];
    if (S.posture === 'walk') {
      if (S.clipPos < cycle0) S.clipPos = settle ? cycle0 : Math.min(cycle0, S.clipPos + speed * dt);
      else {
        const dir = (keys.has('w') || keys.has('arrowup')) - (keys.has('s') || keys.has('arrowdown'));
        const turn = (keys.has('a') || keys.has('arrowleft')) - (keys.has('d') || keys.has('arrowright'));
        const rate = 0.55; // walk cycles per second: concept pace for viewing
        if (dir) {
          const dp = dir * rate * dt; S.walk.phase = (S.walk.phase + dp + cycleN * 10) % cycleN;
          S.walk.phase = ((S.walk.phase % 1) + 1) % 1;
          const adv = dp * walkFrames[walkFrames.length - 1].body_x * cycleN / (cycleN - 1);
          S.walk.x += Math.cos(S.walk.heading) * adv; S.walk.y += Math.sin(S.walk.heading) * adv;
          if (Math.hypot(S.walk.x, S.walk.y) > 14) { S.walk.x = 0; S.walk.y = 0; }
        }
        if (turn) S.walk.heading += turn * 0.6 * dt;
        S.clipPos = cycle0 + S.walk.phase * cycleN;
      }
    } else S.clipPos = settle ? frames.length - 1 : Math.min(frames.length - 1, S.clipPos + speed * dt);
  }
  if (S.posture !== 'walk' && S.posture === S.target) { S.walk.x *= Math.max(0, 1 - 2 * dt); S.walk.y *= Math.max(0, 1 - 2 * dt); }

  // pose
  if (S.posture === 'stand') applyPose(CLIPS.kneel[0], CLIPS.kneel[0], 0);
  else {
    const fr = CLIPS[clipOf(S.posture)];
    if (S.posture === 'walk' && S.clipPos >= cycle0) {
      const u = S.clipPos - cycle0, i = Math.floor(u) % cycleN, j = (i + 1) % cycleN;
      applyPose(fr[cycle0 + i], fr[cycle0 + j], u - Math.floor(u));
    } else { const i = Math.floor(S.clipPos), j = Math.min(i + 1, fr.length - 1); applyPose(fr[i], fr[j], S.clipPos - i); }
  }
  walker.position.set(S.walk.x, S.walk.y, 0); walker.rotation.z = S.walk.heading;

  // smooth toggles
  const ease = (cur, on) => cur + ((on ? 1 : 0) - cur) * Math.min(1, (settle ? 1 : 6 * dt));
  S.explode = ease(S.explode, S.show.explode); S.uavLift = ease(S.uavLift, S.show.uav);
  postProcess();

  // slope
  tilt.rotation.set(THREE.MathUtils.degToRad(S.roll), -THREE.MathUtils.degToRad(S.pitch), 0, 'XYZ');

  // CG, polygon, plumb line
  const met = metricsNow(), mm = met.m || D.metrics.postures.standing;
  cgGroup.visible = S.show.cg && S.posture !== 'walk';
  cgBall.position.set(...mm.cg_m);
  const pg = mm.support_polygon_m.map(([x, y]) => new THREE.Vector3(x, y, 0));
  polyLine.geometry.setFromPoints(pg);
  const shape = new THREE.Shape(mm.support_polygon_m.map(([x, y]) => new THREE.Vector2(x, y)));
  polyMesh.geometry.dispose(); polyMesh.geometry = new THREE.ShapeGeometry(shape);
  scene.updateMatrixWorld(true);
  const cgW = cgBall.getWorldPosition(new THREE.Vector3());
  const n = new THREE.Vector3(0, 0, 1).applyQuaternion(tilt.quaternion), plane = new THREE.Plane().setFromNormalAndCoplanarPoint(n, new THREE.Vector3());
  const hit = new THREE.Ray(cgW, new THREE.Vector3(0, 0, -1)).intersectPlane(plane, new THREE.Vector3()) || cgW.clone();
  plumb.geometry.setFromPoints([cgW, hit]); plumb.computeLineDistances(); plumb.visible = plumbHit.visible = cgGroup.visible;
  plumbHit.position.copy(hit).addScaledVector(n, 0.015); plumbHit.quaternion.copy(tilt.quaternion);

  // dimensions (live bounding box of the walker, UAV and load excluded)
  dims.visible = S.show.dims;
  if (dims.visible) {
    const b = modelBox(), y0 = b.min.y - 0.35, x1 = b.max.x + 0.35, xr = b.min.x - 0.35;
    dimLines.geometry.setFromPoints([new THREE.Vector3(b.min.x, y0, 0.02), new THREE.Vector3(b.max.x, y0, 0.02),
      new THREE.Vector3(x1, b.min.y, 0.02), new THREE.Vector3(x1, b.max.y, 0.02), new THREE.Vector3(xr, b.min.y, 0), new THREE.Vector3(xr, b.min.y, b.max.z),
      new THREE.Vector3(b.min.x, b.min.y, 0.02), new THREE.Vector3(b.min.x, y0 - 0.1, 0.02), new THREE.Vector3(b.max.x, b.min.y, 0.02), new THREE.Vector3(b.max.x, y0 - 0.1, 0.02),
      new THREE.Vector3(xr - 0.1, b.min.y, b.max.z), new THREE.Vector3(b.min.x, b.min.y, b.max.z)]);
    dimL.position.set((b.min.x + b.max.x) / 2, y0, 0.05); dimL.element.textContent = `L ${f2(b.max.x - b.min.x)} m`;
    dimW.position.set(x1, (b.min.y + b.max.y) / 2, 0.05); dimW.element.textContent = `W ${f2(b.max.y - b.min.y)} m`;
    dimH.position.set(xr, b.min.y, b.max.z / 2); dimH.element.textContent = `H ${f2(b.max.z)} m`;
  }
  dimL.visible = dimW.visible = dimH.visible = dims.visible;

  // hazard callouts
  for (const [id, c] of Object.entries(co)) {
    const a = D.anchors[id];
    let p = null;
    if (S.show.hazards && (!a.when || a.when.includes(S.posture))) {
      if (a.cls === 'cg') p = S.posture !== 'walk' ? new THREE.Vector3(...mm.cg_m) : null;
      else { const box = classBox(a.cls); if (box) p = new THREE.Vector3(...anchorPoint(box, a.at)); }
    }
    c.p = p;
  }

  // panel text
  const pd = postureDef[S.posture];
  $('pnote').textContent = S.posture === S.target ? `${pd.label.toLowerCase()} · ${met.analysed ? 'analysed pose' : S.posture === 'walk' ? 'concept gait' : S.posture === 'stand' ? 'analysed pose' : 'moving'}` : `→ ${postureDef[S.target].label.toLowerCase()} · moving`;
  const fr = S.posture === 'stand' ? null : CLIPS[clipOf(S.posture)][Math.round(Math.min(S.clipPos, CLIPS[clipOf(S.posture)].length - 1))];
  $('pframe').textContent = fr ? fr.label : 'standing';
}

function renderOrtho(el, oc, kind) {
  const r = el.getBoundingClientRect(); if (!r.width) return;
  const h = canvas.clientHeight || innerHeight, x = r.left, y = h - r.bottom;
  const b = modelBox(), c = b.getCenter(new THREE.Vector3()), s = b.getSize(new THREE.Vector3());
  const span = Math.max(s.x, s.y, s.z) * 0.62, asp = r.width / r.height;
  Object.assign(oc, { left: -span * asp, right: span * asp, top: span, bottom: -span, near: 0.1, far: 100 });
  const wc = walker.localToWorld(c.clone());
  if (kind === 'front') { oc.up.set(0, 0, 1); oc.position.copy(wc).add(new THREE.Vector3(30, 0, 0).applyQuaternion(walker.getWorldQuaternion(new THREE.Quaternion()))); }
  if (kind === 'side') { oc.up.set(0, 0, 1); oc.position.copy(wc).add(new THREE.Vector3(0, -30, 0).applyQuaternion(walker.getWorldQuaternion(new THREE.Quaternion()))); }
  if (kind === 'top') { oc.up.set(1, 0, 0).applyQuaternion(walker.getWorldQuaternion(new THREE.Quaternion())); oc.position.copy(wc).add(new THREE.Vector3(0, 0, 30)); }
  oc.lookAt(wc); oc.updateProjectionMatrix();
  renderer.setViewport(x, y, r.width, r.height); renderer.setScissor(x, y, r.width, r.height);
  renderer.setClearColor('#f8fafc', 1); renderer.clear();
  const sv = dims.visible; dims.visible = false; renderer.render(scene, oc); dims.visible = sv;
}

function frame(now) {
  const dt = Math.min(0.1, (now - last) / 1000); last = now;
  step(dt);
  if (R.playing) { R.t += dt; if (R.t > R.tEnd) R.t = 0; drawReplay(); }
  if (camTween) { camTween.t = Math.min(1, camTween.t + dt * 2.2); const e = 0.5 - 0.5 * Math.cos(Math.PI * camTween.t);
    cam.position.lerpVectors(camTween.from, camTween.to, e); if (camTween.t >= 1) camTween = null; }
  if (S.posture === 'walk') { const wp = new THREE.Vector3(S.walk.x, S.walk.y, 2.1); controls.target.lerp(wp, Math.min(1, 3 * dt)); }
  else controls.target.lerp(new THREE.Vector3(0, 0, 2.1), Math.min(1, 3 * dt));
  sun.target.position.copy(controls.target); sun.position.copy(controls.target).add(new THREE.Vector3(7, -9, 13));
  controls.update();
  renderSpec(); renderTip();
  person.visible = S.show.person;

  const w = innerWidth, h = canvas.clientHeight || innerHeight;
  renderer.setScissorTest(false); renderer.setViewport(0, 0, w, h); renderer.setClearColor(C.bg, 1); renderer.clear();
  renderer.render(scene, cam); labels.render(scene, cam); drawCallouts();
  if (w > 1100) { renderer.setScissorTest(true);
    renderOrtho($('ov-front'), ortho.front, 'front'); renderOrtho($('ov-side'), ortho.side, 'side'); renderOrtho($('ov-top'), ortho.top, 'top');
    renderer.setScissorTest(false); }
  const s = new THREE.Spherical().setFromVector3(cam.position.clone().sub(controls.target).applyAxisAngle(new THREE.Vector3(1, 0, 0), -Math.PI / 2));
  const az = (THREE.MathUtils.radToDeg(Math.atan2(cam.position.y - controls.target.y, cam.position.x - controls.target.x)) + 360) % 360;
  const el = THREE.MathUtils.radToDeg(Math.asin((cam.position.z - controls.target.z) / cam.position.distanceTo(controls.target)));
  $('cam').textContent = `AZ ${az.toFixed(0)}° · EL ${el.toFixed(0)}° · R ${s.radius.toFixed(1)} M · ${S.render.toUpperCase()} · CL-05 PLACEHOLDER GEOMETRY`;
  window.__state = { posture: S.posture, target: S.target, clipPos: S.clipPos, hazard: S.hazard, settled: S.posture === S.target };
  window.__ready = true;
  requestAnimationFrame(frame);
}

// ------------------------------------------------------------------ start
$('banner').textContent = 'CONCEPT GEOMETRY & SYNTHETIC SIMULATION · DESIGN AID ONLY · NO EVIDENCE CREDIT';
$('tbdoc').textContent = D.sheet.document; $('tbsheet').textContent = D.sheet.sheet; $('tbrev').textContent = D.sheet.revision;
$('tbtitle').textContent = D.sheet.title;
if (q.get('posture') && postureDef[q.get('posture')]) S.target = q.get('posture');
if (MODES.includes(q.get('render'))) S.render = q.get('render');
for (const t of Object.keys(S.show)) if (q.has(t)) S.show[t] = q.get(t) !== '0';
if (q.get('pitch')) S.pitch = +q.get('pitch');
if (q.get('roll')) S.roll = +q.get('roll');
$('pitch').value = S.pitch; $('roll').value = S.roll;
refreshButtons(); applyMaterials(); drawReplay();
if (q.get('hazard')) selectHazard(q.get('hazard'));
layout(); setView(VIEWS[q.get('view')] ? q.get('view') : 'iso', true);
$('load').remove();
requestAnimationFrame(frame);
