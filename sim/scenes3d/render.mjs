// Render stills of the 3D scene pages and check each page (no console errors, the synthetic stamp, the outcome).
// Usage: node sim/scenes3d/render.mjs THREE_DIR [--check-only]
//   THREE_DIR: an unpacked npm package of three (npm pack three@<version>); its build/three.module.min.js must match
//   the SHA-256 pinned in sim/scenes3d/scenes.yaml. Requests to the pinned jsDelivr URLs are served from it.
// Writes docs/wiki/images/3d-<id>.png (1200x675) at the end state, unless --check-only.
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const { chromium } = createRequire(import.meta.url)('playwright');   // global (NODE_PATH) or local install
const root = resolve(new URL('../..', import.meta.url).pathname);
const threeDir = resolve(process.argv[2] || '');
const checkOnly = process.argv.includes('--check-only');
const cfg = readFileSync(join(root, 'sim/scenes3d/scenes.yaml'), 'utf8');
const version = cfg.match(/version: "([^"]+)"/)[1];
const pinned = cfg.match(/sha256: "([0-9a-f]{64})"/)[1];
const lib = readFileSync(join(threeDir, 'build/three.module.min.js'));
if (createHash('sha256').update(lib).digest('hex') !== pinned) { console.error('three.module.min.js does not match the pinned SHA-256'); process.exit(1); }
const prefix = `https://cdn.jsdelivr.net/npm/three@${version}/`;

const pages = readdirSync(join(root, 'docs/3d')).filter(f => f.endsWith('.html') && f !== 'index.html').sort();
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1200, height: 675 }, deviceScaleFactor: 1 });
await page.route(prefix + '**', route => {
  const rel = route.request().url().slice(prefix.length);
  route.fulfill({ status: 200, contentType: 'application/javascript', body: readFileSync(join(threeDir, rel)) });
});
let bad = 0;
for (const f of pages) {
  const errors = [];
  const onErr = e => errors.push(String(e));
  page.on('pageerror', onErr);
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto('file://' + join(root, 'docs/3d', f) + '?t=end&paused=1');
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 30000 });
  await page.waitForTimeout(300);
  const st = await page.evaluate(() => ({ ...window.__state, stamp: document.getElementById('stamp').textContent, hud: document.getElementById('hud').textContent }));
  const scene = JSON.parse(readFileSync(join(root, 'docs/3d', f), 'utf8').match(/window\.SCENE = (.*);<\/script>/)[1]);
  const A = scene.analysis;
  const want = A.kind === 'walker' ? A.performed.outcome : A.outcome;
  const problems = [...errors];
  if (!st.stamp.includes('no evidence credit')) problems.push('missing synthetic stamp');
  if (st.outcome !== want || !st.hud.includes(want)) problems.push(`outcome ${st.outcome} / HUD does not show ${want}`);
  if (problems.length) { bad++; console.log(`FAIL ${f}: ${problems.join('; ')}`); } else console.log(`ok   ${f} (${want})`);
  if (!checkOnly) writeFileSync(join(root, 'docs/wiki/images', '3d-' + f.replace('.html', '').toLowerCase() + '.png'), await page.screenshot());
  page.removeAllListeners('pageerror'); page.removeAllListeners('console');
}
await browser.close();
process.exit(bad ? 1 : 0);
