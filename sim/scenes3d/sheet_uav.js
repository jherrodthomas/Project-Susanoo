// Susanoo sheet 2: SUS-A1 on the CL-05 dock and in the air (three.js r170). Embedded in docs/3d/SUS-A1.html by build_sheet.py.
// window.SHEET: UAV figures, hazards, interfaces and the PX4 SITL runs from the records; window.SUS_M1_GEOMETRY: CL-05
// meshes (the walker, dock and docked quadrotor of tools/cad/b3d/cl05.py). Nothing here computes flight: the airspace
// view replays stored PX4 SITL traces (local NED from the take-off point, SIH over flat ground at the dock's level).
// URL: ?mode=air&run=SU-02&t=end&hazard=HAZ-INT-001&render=xray&view=top
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

THREE.Object3D.DEFAULT_UP.set(0, 0, 1);
const D = window.SHEET, G = window.SUS_M1_GEOMETRY, M = G.meta;
const q = new URLSearchParams(location.search);
const $ = (id) => document.getElementById(id);
const C = { ink: '#1e293b', mute: '#64748b', line: '#c3ccd7', haz: '#ea580c', sel: '#4f46e5', ok: '#0d9488', warn: '#d97706', bad: '#dc2626', bg: '#e4e9ef' };
const MODE_COL = { LOITER: '#4f46e5', RTL: '#ea580c', LAND: '#d97706', MISSION: '#0d9488', TAKEOFF: '#0d9488', HOLD: '#4f46e5' };
const modeCol = (m) => MODE_COL[(m || '').replace('AUTO.', '')] || '#64748b';
const f2 = (v) => Number(v).toFixed(2);

// ------------------------------------------------------------------ geometry (standing pose of the CL-05 export)
const raw = Uint8Array.from(atob(G.bin), (c) => c.charCodeAt(0)).buffer;
const sl = ([o, n]) => raw.slice(o, o + n);
const P16 = new Int16Array(sl(M.layout.positions)), I16 = new Uint16Array(sl(M.layout.indices));
function geom(i) {
  const m = M.meshes[i], [vo, vn] = m.v, [io, inn] = m.i, s = M.quantum_m, o = M.origin_m;
  const pos = new Float32Array(vn * 3);
  for (let k = 0; k < vn * 3; k++) pos[k] = P16[vo * 3 + k] * s + o[k % 3];
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setIndex(new THREE.BufferAttribute(I16.slice(io, io + inn), 1));
  g.computeVertexNormals(); g.computeBoundingBox(); return g;
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
const sun = new THREE.DirectionalLight('#ffffff', 2.1); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.0004;
scene.add(sun, sun.target);
const fill = new THREE.DirectionalLight('#dfe7ff', 0.55); fill.position.set(-8, 6, 5); scene.add(fill);
const shadowPlane = new THREE.Mesh(new THREE.PlaneGeometry(600, 600), new THREE.ShadowMaterial({ opacity: 0.18 }));
shadowPlane.receiveShadow = true; scene.add(shadowPlane);
const gridFine = new THREE.GridHelper(40, 40, '#b4bfcc', '#cfd7e0'); gridFine.rotation.x = Math.PI / 2; gridFine.position.z = 0.002;
const gridAir = new THREE.GridHelper(300, 30, '#b4bfcc', '#cfd7e0'); gridAir.rotation.x = Math.PI / 2; gridAir.position.z = 0.002;
scene.add(gridFine, gridAir);

// ------------------------------------------------------------------ state
const S = { mode: 'dock', show: { hazards: true, keepout: true, fence: true, trail: true, walker: true, dims: true }, render: 'shaded', hazard: null };
const R = { i: 0, t: 0, playing: false };

// ------------------------------------------------------------------ materials
const mats = {};
for (const [cls, [color, op]] of Object.entries(D.classes)) {
  mats[cls] = {
    shaded: new THREE.MeshStandardMaterial({ color, roughness: 0.62, metalness: cls === 'actuator' ? 0.35 : 0.12, transparent: op < 1, opacity: op, depthWrite: op >= 1, side: THREE.DoubleSide }),
    line: new THREE.MeshBasicMaterial({ color: '#f8fafc', polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1, side: THREE.DoubleSide }),
    xray: new THREE.MeshStandardMaterial({ color, roughness: 0.5, transparent: true, opacity: 0.16, depthWrite: false, side: THREE.DoubleSide }),
    hl: new THREE.MeshStandardMaterial({ color: C.haz, emissive: C.haz, emissiveIntensity: 0.35, roughness: 0.5, side: THREE.DoubleSide }),
  };
}
const dimMat = new THREE.MeshStandardMaterial({ color: '#d5dbe3', roughness: 0.8, side: THREE.DoubleSide });
const edgeMat = { shaded: new THREE.LineBasicMaterial({ color: C.ink, transparent: true, opacity: 0.22 }),
  line: new THREE.LineBasicMaterial({ color: C.ink }), xray: new THREE.LineBasicMaterial({ color: '#334155', transparent: true, opacity: 0.35 }) };
const UAVC = new Set(['uav', 'rotor']);
function hlClasses() {
  const a = S.hazard && D.anchors[S.hazard];
  if (!a) return null;
  return a.cls === 'uav' || a.cls === 'rotor' ? (S.hazard === 'HAZ-INT-001' ? UAVC : new Set([a.cls])) : new Set([a.cls]);
}
function matFor(cls) {
  const h = hlClasses();
  if (!h) return mats[cls][S.render];
  if (h.has(cls)) return mats[cls].hl;
  return S.render === 'shaded' ? dimMat : mats[cls][S.render];
}

// ------------------------------------------------------------------ the walker (standing) with its dock and docked UAV
const walker = new THREE.Group(); scene.add(walker);
const parts = [];
function addMesh(i, parent) {
  const cls = M.meshes[i].cls, g = geom(i);
  const m = new THREE.Mesh(g, matFor(cls)); m.castShadow = D.classes[cls][1] >= 1; m.receiveShadow = true; m.userData = { cls };
  const e = new THREE.LineSegments(new THREE.EdgesGeometry(g, 35), edgeMat[S.render]); m.add(e); m.userData.edges = e;
  parent.add(m); parts.push(m); return m;
}
M.base.forEach((i) => addMesh(i, walker));
const box3 = (pred, root) => { const b = new THREE.Box3(), t = new THREE.Box3(); root.updateMatrixWorld(true);
  for (const m of parts) if (pred(m) && m.visible) { t.copy(m.geometry.boundingBox).applyMatrix4(m.matrixWorld); b.union(t); } return b; };
walker.updateMatrixWorld(true);
const dockBox = box3((m) => m.userData.cls === 'dock', walker), dockC = dockBox.getCenter(new THREE.Vector3());
const uavBox = box3((m) => UAVC.has(m.userData.cls) && m.parent === walker, walker), uavC = uavBox.getCenter(new THREE.Vector3());
const headBox = box3((m) => m.userData.cls === 'occupant', walker);

// The flying quadrotor: copies of the docked UAV's meshes, origin at the skid bottom centre.
const flyer = new THREE.Group(), flyerInner = new THREE.Group(); flyer.add(flyerInner); scene.add(flyer);
M.base.filter((i) => UAVC.has(M.meshes[i].cls)).forEach((i) => addMesh(i, flyerInner));
flyerInner.position.set(-uavC.x, -uavC.y, -uavBox.min.z);
const dockedUav = parts.filter((m) => m.parent === walker && UAVC.has(m.userData.cls));
const ned = (n, e, alt) => new THREE.Vector3(n, -e, alt);   // world: x north, y west, z up; ground = SITL home level

// ------------------------------------------------------------------ airspace overlays
const air = new THREE.Group(); scene.add(air);
function css(cls, text) { const el = document.createElement('div'); el.className = cls; el.textContent = text; return new CSS2DObject(el); }
const fenceR = D.spec.geofence_radius_m.value;
const fence = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(Array.from({ length: 128 }, (_, i) => {
  const a = i / 128 * Math.PI * 2; return new THREE.Vector3(Math.cos(a) * fenceR, Math.sin(a) * fenceR, 0.05); })),
  new THREE.LineDashedMaterial({ color: C.warn, dashSize: 3, gapSize: 2 }));
fence.computeLineDistances(); air.add(fence);
const fenceLab = css('dim', `GEOFENCE ${fenceR} m (take-off point)`); fenceLab.position.set(-fenceR, 0, 0.5); air.add(fenceLab);
const koR = D.spec.pilot_keepout_m.value, koH = D.spec.keepout_alt_m.value;
const keep = new THREE.Group(); scene.add(keep);
const koMesh = new THREE.Mesh(new THREE.CylinderGeometry(koR, koR, koH, 48, 1, true), new THREE.MeshBasicMaterial({ color: C.bad, transparent: true, opacity: 0.12, side: THREE.DoubleSide, depthWrite: false }));
koMesh.rotation.x = Math.PI / 2; koMesh.position.z = koH / 2; keep.add(koMesh);
const koRing = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(Array.from({ length: 64 }, (_, i) => { const a = i / 64 * Math.PI * 2;
  return new THREE.Vector3(Math.cos(a) * koR, Math.sin(a) * koR, koH); })), new THREE.LineBasicMaterial({ color: C.bad }));
keep.add(koRing);
const koLab = css('dim', `PILOT KEEP-OUT ${koR} m below ${koH} m`); koLab.position.set(0, 0, koH + 1); keep.add(koLab);
const marker = (col, r = 0.6) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, 0.12, 24), new THREE.MeshBasicMaterial({ color: col })); m.rotation.x = Math.PI / 2; m.position.z = 0.06; return m; };
const home = marker(C.ink); air.add(home); const homeLab = css('dim', 'HOME = take-off point'); homeLab.element.style.marginTop = '-22px'; home.add(homeLab);
const obsP = ned(D.spec.observe_n_m.value, D.spec.observe_e_m.value, D.spec.observe_alt_m.value);
const obs = new THREE.Mesh(new THREE.SphereGeometry(0.8, 16, 12), new THREE.MeshBasicMaterial({ color: C.ok })); obs.position.copy(obsP); air.add(obs);
const obsLab = css('dim', 'OBSERVATION POINT'); obsLab.position.copy(obsP).add(new THREE.Vector3(0, 0, 3)); air.add(obsLab);
const land = marker(C.haz, 0.9); air.add(land); const landLab = css('dim', 'LANDED'); landLab.element.style.marginTop = '22px'; land.add(landLab);
const ghost = new THREE.Group(); air.add(ghost); // the walker where it stood at take-off, when it has moved since
{ const gm = new THREE.MeshBasicMaterial({ color: C.sel, transparent: true, opacity: 0.18, depthWrite: false });
  for (const m of parts) if (m.parent === walker) { const c = new THREE.Mesh(m.geometry, gm); ghost.add(c); } }
const ghostLab = css('dim', 'WALKER AT TAKE-OFF'); ghostLab.position.set(dockC.x, dockC.y, 12); ghost.add(ghostLab);
const trail = new THREE.Group(); air.add(trail);
const drop = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]), new THREE.LineDashedMaterial({ color: C.ink, dashSize: 0.6, gapSize: 0.4 }));
air.add(drop);

// dock close-up dimension: rotor to the pilot's head (figure from cad/metrics.json)
const dims = new THREE.Group(); scene.add(dims);
const dimLine = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: C.ink, depthTest: false })); dimLine.renderOrder = 12; dims.add(dimLine);
const dimLab = css('dim', `rotor ↔ pilot ${f2(D.dock.rotor_to_pilot_m)} m`); dims.add(dimLab);
{ const head = new THREE.Vector3(headBox.getCenter(new THREE.Vector3()).x, headBox.getCenter(new THREE.Vector3()).y, headBox.max.z);
  let best = null;
  for (const m of dockedUav) if (m.userData.cls === 'rotor') { const b = new THREE.Box3().copy(m.geometry.boundingBox);
    const p = b.clampPoint(head, new THREE.Vector3()); if (!best || p.distanceTo(head) < best.distanceTo(head)) best = p; }
  dimLine.geometry.setFromPoints([best, head]); dimLab.position.copy(best).lerp(head, 0.5).add(new THREE.Vector3(0, -0.15, 0.15)); }

// ------------------------------------------------------------------ hazard callouts (screen space, as on sheet 1)
const coLayer = $('co'), coSvg = $('cosvg'), co = {};
for (const h of D.hazards) { if (!D.anchors[h.id]) continue; const el = document.createElement('div'); el.className = 'co'; el.textContent = h.id; el.title = h.title;
  el.onclick = () => selectHazard(h.id); coLayer.appendChild(el); co[h.id] = { el, p: null }; }
function updateAnchors() {
  for (const [id, c] of Object.entries(co)) {
    const a = D.anchors[id]; c.p = null;
    if (!S.show.hazards) continue;
    if (S.mode === 'air') { if (a.air === 'keepout' && S.show.keepout) c.p = keep.localToWorld(new THREE.Vector3(koR, 0, koH)); continue; }
    const b = box3((m) => m.userData.cls === a.cls && m.parent === walker, walker); if (b.isEmpty()) continue;
    const ce = b.getCenter(new THREE.Vector3());
    c.p = new THREE.Vector3(...(({ top: [ce.x, ce.y, b.max.z], rear: [b.min.x, ce.y, ce.z], front: [b.max.x, ce.y, ce.z] })[a.at] || ce.toArray()));
  }
}
function drawCallouts() {
  const w = innerWidth, h = canvas.clientHeight || innerHeight, L = $('left').getBoundingClientRect(), Rr = $('right').getBoundingClientRect();
  const scr = (v) => { const p = v.clone().project(cam); return [(p.x + 1) / 2 * w, (1 - p.y) / 2 * h]; };
  const items = Object.entries(co).filter(([, k]) => k.p).map(([id, k]) => ({ id, k, a: scr(k.p) }));
  const cx = (L.right + Rr.left) / 2;
  let svg = '';
  for (const side of [0, 1]) {
    const col = items.filter((it) => (it.a[0] >= cx) === !!side).sort((u, v) => u.a[1] - v.a[1]); let y = -1e9;
    for (const it of col) { it.y = Math.max(it.a[1] - 40, y + 24); y = it.y; }
    for (const it of col) {
      const x = side ? Math.min(Rr.left - 116, it.a[0] + 120) : Math.max(L.right + 16, it.a[0] - 220), ex = side ? x : x + 100;
      it.k.el.style.left = `${x}px`; it.k.el.style.top = `${it.y - 9}px`;
      const s = it.id === S.hazard;
      svg += `<polyline points="${it.a[0].toFixed(1)},${it.a[1].toFixed(1)} ${(side ? ex - 14 : ex + 14)},${it.y.toFixed(1)} ${ex},${it.y.toFixed(1)}" fill="none" stroke="${C.haz}" stroke-width="${s ? 2 : 1}"/>` +
        `<circle cx="${it.a[0].toFixed(1)}" cy="${it.a[1].toFixed(1)}" r="${s ? 4 : 3}" fill="${C.haz}"/>`;
    }
  }
  for (const k of Object.values(co)) k.el.style.display = k.p ? '' : 'none';
  coSvg.innerHTML = svg;
}

// ------------------------------------------------------------------ camera
const cam = new THREE.PerspectiveCamera(30, 1, 0.05, 2000);
const controls = new OrbitControls(cam, canvas); controls.enableDamping = true; controls.dampingFactor = 0.08;
const VIEWS = { iso: [315, 20], front: [0, 6], side: [270, 6], top: [270, 89], rear: [180, 10] };
// dock close-up: the default looks at the backpack dock from behind and above; airspace top view: north up
const VIEWS_DOCK = { iso: [225, 26], front: [0, 8], side: [270, 8], top: [270, 89], rear: [180, 14] };
const VIEWS_AIR = { ...VIEWS, top: [180, 89.5] };
let camTween = null, curView = 'iso';
const frameOf = () => S.mode === 'dock' ? { target: dockC.clone().add(new THREE.Vector3(0.35, 0, -0.35)), r: 6.2 } : { target: new THREE.Vector3(18, -14, 6), r: 170 };
function sph(az, el, r) { const a = THREE.MathUtils.degToRad(az), e = THREE.MathUtils.degToRad(el);
  return new THREE.Vector3(Math.cos(e) * Math.cos(a) * r, Math.cos(e) * Math.sin(a) * r, Math.sin(e) * r); }
function setView(v, instant) {
  curView = v; const f = frameOf(), [az, el] = (S.mode === 'dock' ? VIEWS_DOCK : VIEWS_AIR)[v], to = sph(az, el, f.r).add(f.target);
  document.querySelectorAll('#view button').forEach((b) => b.classList.toggle('on', b.dataset.v === v));
  if (instant) { controls.target.copy(f.target); cam.position.copy(to); controls.update(); return; }
  camTween = { from: cam.position.clone(), to, tf: controls.target.clone(), tt: f.target, t: 0 };
}
const ortho = { front: new THREE.OrthographicCamera(), side: new THREE.OrthographicCamera(), top: new THREE.OrthographicCamera() };

// ------------------------------------------------------------------ replay data
const run = () => D.runs[R.i];
const tEnd = () => run().trace[run().trace.length - 1][0] + 2;
function at(t) { const T = run().trace; let i = 0; while (i < T.length - 1 && T[i + 1][0] <= t) i++;
  if (i >= T.length - 1 || t <= T[0][0]) { const f = T[Math.min(i, T.length - 1)]; return f; }
  const a = T[i], b = T[i + 1], u = (t - a[0]) / (b[0] - a[0]);
  return [t, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u, a[3] + (b[3] - a[3]) * u, a[4], a[5] + (b[5] - a[5]) * u]; }
function injectT(r) { const j = r.inject; return j.link_loss_at_s ?? j.at_s ?? j.reposition_beyond_fence_at_s ?? null; }
function landT(r) { const ff = r.first_failsafe ? r.first_failsafe[0] : null; if (ff == null) return null;
  const f = r.trace.find((p) => p[0] > ff && p[3] < 0.3); return f ? f[0] : null; }
function buildTrail() {
  trail.clear(); const T = run().trace;
  for (let i = 1; i < T.length; i++) { const a = T[i - 1], b = T[i];
    trail.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([ned(a[1], a[2], a[3]), ned(b[1], b[2], b[3])]), new THREE.LineBasicMaterial({ color: modeCol(a[4]) }))); }
  const r = run(), dk = r.dock_m, pk = r.pilot_m;
  walker.position.set(dk[0] - dockC.x, -dk[1] - dockC.y, 0);   // the dock where the run says it is (moved walker: 20 m north)
  keep.position.copy(ned(pk[0], pk[1], 0));
  ghost.visible = r.walker_moved; ghost.position.set(-dockC.x, -dockC.y, 0);
  land.visible = !!r.landing_point_m; if (r.landing_point_m) land.position.copy(ned(r.landing_point_m[0], r.landing_point_m[1], 0.06));
}

// ------------------------------------------------------------------ panels
$('banner').textContent = 'CONCEPT GEOMETRY & PX4 SITL SIMULATION · DESIGN AID ONLY · NO EVIDENCE CREDIT';
$('tbdoc').textContent = D.sheet.document; $('tbsheet').textContent = D.sheet.sheet; $('tbrev').textContent = D.sheet.revision; $('tbtitle').textContent = D.sheet.title;
const U = D.uav, span = 2 * U.arm_reach + 2 * U.rotor_radius, sp = (k) => D.spec[k];
$('spec').innerHTML = [['Body', U.body.map(f2).join('×')], ['Span*', `${f2(span)} m`], ['Rotor Ø', `${f2(2 * U.rotor_radius)} m`], ['Motors', '4 · quad X'],
  ['Rotor↔pilot', `${f2(D.dock.rotor_to_pilot_m)} m`], ['Rotor↔hull', `${f2(D.dock.rotor_to_structure_m)} m`],
  ['Keep-out', `${sp('pilot_keepout_m').value} m <${sp('keepout_alt_m').value} m`], ['Geofence', `${sp('geofence_radius_m').value} m`],
  ['Link loss', `${sp('link_loss_timeout_s').value} s`], ['Observe', `${sp('observe_alt_m').value} m alt`]]
  .map(([k, v]) => `<div class="row"><span class="k">${k}</span><span>${v}</span></div>`).join('');
$('specnote').innerHTML = `* placeholder geometry in m, cad/params/common.yaml · dock clearances cad/metrics.json · flight figures ${D.spec_id} (assumed) · ` +
  `${D.runs[0].simulator}, PX4 ${D.runs[0].px4}<br>Elements: ${D.elements.filter((e) => e.id !== 'SUS-A1').map((e) => `${e.id.replace('SUS-A1-', '')} ${e.name.toLowerCase()}`).join(' · ')}`;
$('hzcount').textContent = `${D.hazards.length} · ${D.hazards.every((h) => h.status === 'open') ? 'all open' : ''}`;
$('hzlist').innerHTML = D.hazards.map((h) => `<div class="hz${D.anchors[h.id] ? '' : ' off'}" tabindex="0" data-h="${h.id}" title="${h.title}"><b>${h.id}</b><span>${h.title}</span>` +
  `<span class="tag r${(h.rac || ' ')[0]}" title="initial risk ${h.rac} ${h.level}">${h.rac || '—'}</span></div>`).join('');
document.querySelectorAll('.hz').forEach((el) => { el.onclick = () => selectHazard(el.dataset.h); el.onkeydown = (e) => { if (e.key === 'Enter') selectHazard(el.dataset.h); }; });
$('ifcount').textContent = `${D.interfaces.length}`;
$('iflist').innerHTML = D.interfaces.map((f) => `<div class="ifr"><b>${f.id}</b><span>${f.name}</span><span class="k">${f.from} → ${f.to}${(f.hazard_ids || []).length ? ' · ' + f.hazard_ids.join(', ') : ''}</span></div>`).join('');
function selectHazard(id) {
  S.hazard = S.hazard === id ? null : id;
  document.querySelectorAll('.hz').forEach((el) => el.classList.toggle('sel', el.dataset.h === S.hazard));
  for (const [k, c] of Object.entries(co)) c.el.classList.toggle('sel', k === S.hazard);
  const h = D.hazards.find((x) => x.id === S.hazard);
  $('hzsel').style.display = h ? 'block' : 'none';
  if (h) $('hzsel').innerHTML = `<b>${h.id}</b> · ${h.status} · initial risk ${h.rac || '—'} ${h.level || ''}<br>${h.title}<br><span class="k">${h.subsystems.join(', ')}</span>`;
  applyMaterials();
}
function applyMaterials() { for (const m of parts) { m.material = matFor(m.userData.cls); m.userData.edges.material = edgeMat[S.render]; } }

// ------------------------------------------------------------------ controls
function refresh() {
  document.querySelectorAll('#mode button').forEach((b) => b.classList.toggle('on', b.dataset.m === S.mode));
  document.querySelectorAll('[data-t]').forEach((b) => b.classList.toggle('on', !!S.show[b.dataset.t]));
  document.querySelectorAll('#render button').forEach((b) => b.classList.toggle('on', b.dataset.r === S.render));
  $('mnote').textContent = S.mode === 'dock' ? 'docked on CL-05 · rear backpack dock' : `airspace · UAV drawn ×${D.uav_scale_air} · SITL ground = dock level`;
}
function setMode(m) { if (S.mode === m) return; S.mode = m; refresh(); setView(curView); }
document.querySelectorAll('#mode button').forEach((b) => { b.onclick = () => setMode(b.dataset.m); });
document.querySelectorAll('[data-t]').forEach((b) => { b.onclick = () => { S.show[b.dataset.t] = !S.show[b.dataset.t]; refresh(); }; });
document.querySelectorAll('#render button').forEach((b) => { b.onclick = () => { S.render = b.dataset.r; applyMaterials(); refresh(); }; });
document.querySelectorAll('#view button').forEach((b) => { b.onclick = () => setView(b.dataset.v); });
$('helpbtn').onclick = () => $('help').classList.toggle('open');
$('help').onclick = (e) => { if (e.target.id === 'help') $('help').classList.remove('open'); };
$('terms').onclick = () => $('terms').classList.toggle('open');
const rtabs = $('rtabs');
D.runs.forEach((r, i) => { const b = document.createElement('button'); b.textContent = r.id; b.onclick = () => { R.i = i; R.t = 0; buildTrail(); setMode('air'); drawReplay(); }; rtabs.appendChild(b); });
$('rplay').onclick = () => { R.playing = !R.playing; if (R.playing) setMode('air'); $('rplay').textContent = R.playing ? 'Pause' : 'Play'; };
$('rplot').onclick = (e) => { const b = $('rplot').getBoundingClientRect(), u = (e.clientX - b.left) / b.width * 1000;
  R.t = Math.max(0, (u - 40) / 940 * tEnd()); setMode('air'); drawReplay(); };
addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;
  const k = e.key.toLowerCase();
  if (k === '1') setMode('dock'); if (k === '2') setMode('air');
  const tg = { h: 'hazards', k: 'keepout', f: 'fence', t: 'trail', w: 'walker', m: 'dims' }[k];
  if (tg) { S.show[tg] = !S.show[tg]; refresh(); }
  if (k === 'v') { const RM = ['shaded', 'line', 'xray']; S.render = RM[(RM.indexOf(S.render) + 1) % 3]; applyMaterials(); refresh(); }
  if (k === '?' || (k === '/' && e.shiftKey)) $('help').classList.toggle('open');
  if (k === 'escape') $('help').classList.remove('open');
  if (k === ' ') { e.preventDefault(); $('rplay').click(); }
});

// ------------------------------------------------------------------ replay plot
function drawReplay() {
  const r = run(), T = r.trace, te = tEnd(), x = (t) => 40 + Math.max(0, t) / te * 940;
  const pk = r.pilot_m, dist = (p) => Math.hypot(p[1] - pk[0], p[2] - pk[1]);
  const yA = (v) => 36 - Math.max(-2, v) / 32 * 30, yD = (v) => 74 - Math.min(v, 70) / 70 * 34;
  rtabs.querySelectorAll('button').forEach((b, i) => b.classList.toggle('on', i === R.i));
  $('rtitle').textContent = `${r.id} · ${r.title}`;
  let bands = ''; const mc = r.mode_changes;
  for (let i = 0; i < mc.length; i++) { const t0 = mc[i][0], t1 = i + 1 < mc.length ? mc[i + 1][0] : te;
    bands += `<rect x="${x(t0)}" y="78" width="${Math.max(0, x(t1) - x(t0))}" height="6" fill="${modeCol(mc[i][1])}"/>` +
      `<text x="${x(t0) + 3}" y="76" font-size="8" fill="${modeCol(mc[i][1])}">${mc[i][1].replace('AUTO.', '')}</text>`; }
  const path = (fy, fv) => T.map((p, i) => `${i ? 'L' : 'M'}${x(p[0]).toFixed(1)},${fy(fv(p)).toFixed(1)}`).join('');
  const mark = (t, txt, col) => t == null ? '' : `<line x1="${x(t)}" y1="2" x2="${x(t)}" y2="78" stroke="${col}" stroke-width="1.5"/><text x="${x(t) + 3}" y="10" font-size="9" fill="${col}">${txt}</text>`;
  const low = T.filter((p) => p[3] < koH).map((p) => [p[0], dist(p)]);
  $('rplot').innerHTML = `<text x="2" y="20" font-size="9" fill="${C.mute}">alt</text><text x="2" y="62" font-size="9" fill="${C.mute}">to pilot</text>` +
    `<line x1="40" y1="${yD(koR)}" x2="980" y2="${yD(koR)}" stroke="${C.bad}" stroke-dasharray="6 4"/><text x="880" y="${yD(koR) - 2}" font-size="8" fill="${C.bad}">keep-out ${koR} m</text>` +
    `<path d="${path(yA, (p) => p[3])}" fill="none" stroke="${C.sel}" stroke-width="1.5"/><path d="${path(yD, dist)}" fill="none" stroke="${C.haz}" stroke-width="1.5"/>` +
    low.map(([t, d]) => d < koR ? `<circle cx="${x(t)}" cy="${yD(d)}" r="2.5" fill="${C.bad}"/>` : '').join('') + bands +
    mark(injectT(r), 'inject', C.ink) + mark(r.first_failsafe && r.first_failsafe[0], 'failsafe', C.warn) + mark(landT(r), 'landed', C.bad) +
    `<line x1="${x(R.t)}" y1="0" x2="${x(R.t)}" y2="84" stroke="${C.ink}" stroke-width="2"/>`;
  const f = at(R.t);
  const find = [r.finding, ...r.metric_findings].filter(Boolean);
  $('rinfo').innerHTML = `<b style="color:${r.outcome === 'landed-clear' || r.outcome === 'contained' ? C.ok : C.bad}">${r.outcome}</b> · ` +
    `${f[4].replace('AUTO.', '')} · alt ${f2(f[3])} m · to pilot ${f2(dist(f))} m · est. error ${f2(f[5])} m · ` +
    `<span title="${(find.join(' | ') || r.contract).replace(/"/g, "'")}">${find.length ? 'finding: ' + find[0] : 'contract: ' + r.contract}</span>`;
  $('rt').textContent = `t ${R.t.toFixed(1)} s`;
}

// ------------------------------------------------------------------ layout
function layout() {
  const w = innerWidth, h = canvas.clientHeight || innerHeight;
  renderer.setSize(w, h, false); labels.setSize(w, h); cam.aspect = w / h;
  const L = $('left').getBoundingClientRect(), Rr = $('right').getBoundingClientRect(), B = $('bottom').getBoundingClientRect();
  if (w > 1100) cam.setViewOffset(w, h, w / 2 - (L.right + Rr.left) / 2, h / 2 - (60 + B.top - 40) / 2, w, h); else cam.clearViewOffset();
  cam.updateProjectionMatrix();
}
addEventListener('resize', layout);

function renderOrtho(el, oc, kind) {
  const r = el.getBoundingClientRect(); if (!r.width) return;
  const h = canvas.clientHeight || innerHeight, f = frameOf(), span = S.mode === 'dock' ? 2.6 : 75, asp = r.width / r.height;
  Object.assign(oc, { left: -span * asp, right: span * asp, top: span, bottom: -span, near: 0.1, far: 1000 });
  const c = S.mode === 'dock' ? f.target : new THREE.Vector3(20, -15, 0);
  if (kind === 'front') { oc.up.set(0, 0, 1); oc.position.copy(c).add(new THREE.Vector3(300, 0, 0)); }
  if (kind === 'side') { oc.up.set(0, 0, 1); oc.position.copy(c).add(new THREE.Vector3(0, -300, 0)); }
  if (kind === 'top') { oc.up.set(1, 0, 0); oc.position.copy(c).add(new THREE.Vector3(0, 0, 300)); }
  oc.lookAt(c); oc.updateProjectionMatrix();
  renderer.setViewport(r.left, h - r.bottom, r.width, r.height); renderer.setScissor(r.left, h - r.bottom, r.width, r.height);
  renderer.setClearColor('#f8fafc', 1); renderer.clear(); renderer.render(scene, oc);
}

// ------------------------------------------------------------------ frame
let last = performance.now();
function frame(now) {
  const dt = Math.min(0.1, (now - last) / 1000); last = now;
  if (R.playing) { R.t += dt * 2; if (R.t > tEnd()) R.t = 0; drawReplay(); }   // 2x real time
  const isAir = S.mode === 'air', r = run();
  air.visible = isAir; gridAir.visible = isAir; gridFine.visible = !isAir; dims.visible = !isAir && S.show.dims; dimLab.visible = dims.visible;
  keep.visible = isAir && S.show.keepout; fence.visible = fenceLab.visible = S.show.fence; trail.visible = S.show.trail;
  for (const o of [homeLab, obsLab, landLab, ghostLab, koLab]) o.visible = isAir;
  if (!isAir) { walker.position.set(0, 0, 0); }
  else { walker.position.set(r.dock_m[0] - dockC.x, -r.dock_m[1] - dockC.y, 0); }
  walker.visible = S.show.walker || !isAir;
  for (const m of dockedUav) m.visible = !isAir;
  flyer.visible = isAir;
  if (isAir) { const f = at(R.t); flyer.position.copy(ned(f[1], f[2], Math.max(0, f[3]))); flyer.scale.setScalar(D.uav_scale_air);
    drop.geometry.setFromPoints([flyer.position.clone(), flyer.position.clone().setZ(0)]); drop.computeLineDistances(); }
  if (camTween) { camTween.t = Math.min(1, camTween.t + dt * 1.8); const e = 0.5 - 0.5 * Math.cos(Math.PI * camTween.t);
    cam.position.lerpVectors(camTween.from, camTween.to, e); controls.target.lerpVectors(camTween.tf, camTween.tt, e); if (camTween.t >= 1) camTween = null; }
  const sc = isAir ? 90 : 8, st = controls.target;
  Object.assign(sun.shadow.camera, { left: -sc, right: sc, top: sc, bottom: -sc, near: 1, far: isAir ? 600 : 60 }); sun.shadow.camera.updateProjectionMatrix();
  sun.target.position.copy(st); sun.position.copy(st).add(new THREE.Vector3(7, -9, 13).multiplyScalar(isAir ? 12 : 1));
  controls.update(); updateAnchors();
  const w = innerWidth, h = canvas.clientHeight || innerHeight;
  renderer.setScissorTest(false); renderer.setViewport(0, 0, w, h); renderer.setClearColor(C.bg, 1); renderer.clear();
  renderer.render(scene, cam); labels.render(scene, cam); drawCallouts();
  if (w > 1100) { renderer.setScissorTest(true); const lv = labels.domElement.style.display;
    renderOrtho($('ov-front'), ortho.front, 'front'); renderOrtho($('ov-side'), ortho.side, 'side'); renderOrtho($('ov-top'), ortho.top, 'top');
    renderer.setScissorTest(false); labels.domElement.style.display = lv; }
  const d = cam.position.distanceTo(controls.target);
  const az = (THREE.MathUtils.radToDeg(Math.atan2(cam.position.y - controls.target.y, cam.position.x - controls.target.x)) + 360) % 360;
  const el = THREE.MathUtils.radToDeg(Math.asin((cam.position.z - controls.target.z) / d));
  $('cam').textContent = `AZ ${az.toFixed(0)}° · EL ${el.toFixed(0)}° · R ${d.toFixed(1)} M · ${S.render.toUpperCase()} · ${isAir ? 'X NORTH · SITL LOCAL NED FROM TAKE-OFF' : 'CL-05 PLACEHOLDER GEOMETRY'}`;
  window.__state = { mode: S.mode, run: r.id, t: R.t, outcome: r.outcome, hazard: S.hazard, settled: !camTween };
  window.__ready = true;
  requestAnimationFrame(frame);
}

// ------------------------------------------------------------------ start
if (q.get('mode') === 'air') S.mode = 'air';
if (['shaded', 'line', 'xray'].includes(q.get('render'))) S.render = q.get('render');
for (const t of Object.keys(S.show)) if (q.has(t)) S.show[t] = q.get(t) !== '0';
const ri = D.runs.findIndex((r) => r.id === q.get('run')); if (ri >= 0) R.i = ri;
buildTrail();
if (q.get('t')) R.t = q.get('t') === 'end' ? tEnd() - 2 : +q.get('t');
refresh(); applyMaterials(); drawReplay();
if (q.get('hazard')) selectHazard(q.get('hazard'));
layout(); setView(VIEWS[q.get('view')] ? q.get('view') : 'iso', true);
$('load').remove();
requestAnimationFrame(frame);
