// Check the SUS-M1 sheet (docs/3d/SUS-M1.html) and render its stills.
// Usage: node sim/scenes3d/sheet_check.mjs THREE_DIR [--check-only] [--all] [--out DIR]
//   THREE_DIR: an unpacked npm package of three matching the SHA-256 pinned in sim/scenes3d/scenes.yaml; requests to the
//   pinned jsDelivr URLs are served from it. Loads the page in Chromium, goes through every posture, a hazard selection,
//   the render modes and the replay, and fails on a console error, a missing synthetic label or a posture that does
//   not settle. Unless --check-only, writes docs/wiki/images/3d-sus-m1.png (1600x900); --all also 3d-sus-m1-<posture>.png.
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
await page.keyboard.down('w'); await page.waitForTimeout(1200); await page.keyboard.up('w');
await page.keyboard.press('1'); await settled('stand');
await page.keyboard.press(' '); await page.waitForTimeout(500);
await browser.close();
problems.push(...errors);
if (problems.length) { console.log('FAIL ' + problems.join('; ')); process.exit(1); }
console.log('ok   SUS-M1 sheet');
