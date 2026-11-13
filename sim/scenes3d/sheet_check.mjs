// Check the general-arrangement sheets (docs/3d/SUS-M1.html, docs/3d/SUS-A1.html) and render their stills.
// Usage: node sim/scenes3d/sheet_check.mjs THREE_DIR [--check-only] [--all] [--out DIR]
//   THREE_DIR: an unpacked npm package of three matching the SHA-256 pinned in sim/scenes3d/scenes.yaml; requests to the
//   pinned jsDelivr URLs are served from it. Loads the page in Chromium, goes through every posture, a hazard selection,
//   the render modes and the replay, and fails on a console error, a missing synthetic label or a posture that does
//   not settle; on sheet 2, that every PX4 SITL run replays to its own outcome. Unless --check-only, writes
//   docs/wiki/images/3d-sus-m1.png, 3d-sus-a1.png and 3d-sus-a1-air.png (1600x900); --all also 3d-sus-m1-<posture>.png.
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const { chromium } = createRequire(import.meta.url)('playwright');
const root = resolve(new URL('../..', import.meta.url).pathname);
const threeDir = resolve(process.argv[2] || '');
const checkOnly = process.argv.includes('--check-only');
const oi = process.argv.indexOf('--out');
const out = oi > 0 ? resolve(process.argv[oi + 1]) : join(root, 'docs/wiki/images');
const cfg = readFileSync(join(root, 'sim/scenes3d/scenes.yaml'), 'utf8');
const version = cfg.match(/version: "([^"]+)"/)[1];
const pinned = cfg.match(/sha256: "([0-9a-f]{64})"/)[1];
if (createHash('sha256').update(readFileSync(join(threeDir, 'build/three.module.min.js'))).digest('hex') !== pinned) {
  console.error('three.module.min.js does not match the pinned SHA-256'); process.exit(1);
}
const prefix = `https://cdn.jsdelivr.net/npm/three@${version}/`;
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
await page.route(prefix + '**', (route) => {
  route.fulfill({ status: 200, contentType: 'application/javascript', body: readFileSync(join(threeDir, route.request().url().slice(prefix.length))) });
});
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
const url = (qs) => 'file://' + join(root, 'docs/3d/SUS-M1.html') + qs;
const problems = [];
const settled = async (posture) => {
  await page.waitForFunction((p) => window.__state && window.__state.posture === p && window.__state.settled, posture, { timeout: 30000 })
    .catch(() => problems.push(`${posture} did not settle`));
  await page.waitForTimeout(400);
};

const shots = [['', 'stand', '?view=iso&dims=1&settle=1'], ['-kneel', 'kneel', '?posture=kneel&settle=1&hazard=HAZ-PIL-001'],
  ['-carry', 'carry', '?posture=carry&settle=1&render=line&hazard=HAZ-MAN-002'], ['-egress', 'egress', '?posture=egress&settle=1&render=xray&hazard=HAZ-PIL-003'],
  ['-walk', 'walk', '?posture=walk&settle=1&cg=0']];
for (const [suffix, posture, qs] of shots) {
  await page.goto(url(qs));
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
  await settled(posture);
  const banner = await page.textContent('#banner');
  if (!/no evidence credit/i.test(banner)) problems.push('missing synthetic label');
  if (!checkOnly && (suffix === '' || process.argv.includes('--all'))) await page.screenshot({ path: join(out, `3d-sus-m1${suffix}.png`) });
  console.log(`ok   ${posture}`);
}
// live transitions: stand -> kneel -> walk (walk a little) -> stand, replay play
await page.goto(url('?'));
await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
for (const k of ['2', '5']) { await page.keyboard.press(k); await settled(k === '2' ? 'kneel' : 'walk'); }
// walking without a keyboard: choosing Walk with the mouse must make it walk on its own, the pad must steer it,
// Pause must stop it, and leaving the walk must return it to standing (regression: it used to stand still until W was held)
const walkState = () => page.evaluate(() => window.__state.walk);
await page.keyboard.press('1'); await settled('stand');
await page.click('#posture button:nth-child(5)');
await page.waitForFunction(() => window.__state.posture === 'walk' && window.__state.clipPos >= 6, null, { timeout: 60000 });
const w0 = await walkState();
await page.waitForFunction((a) => Math.hypot(window.__state.walk.x - a.x, window.__state.walk.y - a.y) > 0.3, w0, { timeout: 30000 })
  .catch(() => problems.push('Walk chosen with the mouse: the walker does not walk on its own'));
const h0 = (await walkState()).heading;
const pad = page.locator('#drive [data-k="a"]'); await pad.hover(); await page.mouse.down();
await page.waitForFunction((h) => window.__state.walk.heading > h + 0.05, h0, { timeout: 30000 })
  .catch(() => problems.push('the on-screen turn arrow does not turn the walker'));
await page.mouse.up();
await page.click('#dauto');
await page.waitForTimeout(300); const w1 = await walkState(); await page.waitForTimeout(1500); const w2 = await walkState();
if (w2.auto || Math.hypot(w2.x - w1.x, w2.y - w1.y) > 0.01) problems.push('Pause does not stop the walker');
// hold W until the walker has moved (a fixed wait fails on a slow software renderer: motion is per rendered frame)
await page.keyboard.down('w');
await page.waitForFunction((a) => Math.hypot(window.__state.walk.x - a.x, window.__state.walk.y - a.y) > 0.3, w2, { timeout: 30000 })
  .catch(() => problems.push('holding W does not walk'));
await page.keyboard.up('w');
await page.keyboard.press('1'); await settled('stand');
await page.keyboard.press(' '); await page.waitForTimeout(500);
// sheet 2 (SUS-A1): the dock close-up, then every PX4 SITL run at its end in the airspace view shows that run's outcome
const runs = JSON.parse(readFileSync(join(root, 'docs/3d/SUS-A1.html'), 'utf8').match(/window\.SHEET = (.*);<\/script>/)[1]).runs;
const url2 = (qs) => 'file://' + join(root, 'docs/3d/SUS-A1.html') + qs;
await page.goto(url2('?hazard=HAZ-DCK-001'));
await page.waitForFunction(() => window.__ready === true && window.__state.mode === 'dock', null, { timeout: 60000 });
await page.waitForTimeout(400);
if (!/no evidence credit/i.test(await page.textContent('#banner'))) problems.push('SUS-A1: missing synthetic label');
if (!checkOnly) await page.screenshot({ path: join(out, '3d-sus-a1.png') });
console.log('ok   SUS-A1 dock');
for (const r of runs) {
  await page.goto(url2(`?mode=air&run=${r.id}&t=end`));
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
  await page.waitForTimeout(300);
  const st = await page.evaluate(() => ({ ...window.__state, info: document.getElementById('rinfo').textContent }));
  if (st.mode !== 'air' || st.run !== r.id || st.outcome !== r.outcome || !st.info.includes(r.outcome)) problems.push(`SUS-A1 ${r.id}: shows ${st.run} ${st.outcome}`);
  if (!checkOnly && r.id === 'SU-01') {   // still: on the way back, before it enters the keep-out
    await page.goto(url2('?mode=air&run=SU-01&t=40')); await page.waitForFunction(() => window.__ready === true); await page.waitForTimeout(300);
    await page.screenshot({ path: join(out, '3d-sus-a1-air.png') });
  }
  console.log(`ok   SUS-A1 ${r.id} (${r.outcome})`);
}
await page.keyboard.press('1'); await page.keyboard.press(' '); await page.waitForTimeout(600);
await browser.close();
problems.push(...errors);
if (problems.length) { console.log('FAIL ' + problems.join('; ')); process.exit(1); }
console.log('ok   SUS-M1 and SUS-A1 sheets');
