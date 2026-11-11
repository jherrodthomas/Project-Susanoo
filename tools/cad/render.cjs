// SPDX-License-Identifier: Apache-2.0
// Render the concept layouts built by build_concepts.py to review images in cad/renders/.
//   node tools/cad/render.cjs            (needs Playwright with Chromium, and `npm ci` in tools/cad)
// Serves the repository over a local HTTP server and screenshots tools/cad/viewer.html per concept and view.
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..', '..');
const OUT = path.join(ROOT, 'cad', 'renders');
const IDS = fs.readdirSync(path.join(ROOT, 'build', 'cad')).filter(d => /^CL-\d{2}$/.test(d)).sort();
const VIEWS = ['iso', 'side', 'top', 'dock'];
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.stl': 'model/stl' };

const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1500, height: 960 }, deviceScaleFactor: 1.5 });
  page.on('pageerror', e => { console.error('page error:', e.message); process.exitCode = 1; });
  fs.mkdirSync(OUT, { recursive: true });
  const jobs = [...IDS.flatMap(id => VIEWS.map(v => [id, v])), [IDS.join(','), 'lineup']];
  for (const [ids, view] of jobs) {
    await page.goto(`http://127.0.0.1:${port}/tools/cad/viewer.html?ids=${ids}&view=${view}`);
    await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
    const name = view === 'lineup' ? 'lineup.png' : `${ids}-${view}.png`;
    await page.locator('#frame').screenshot({ path: path.join(OUT, name) });
    console.log(`wrote cad/renders/${name}`);
  }
  await browser.close();
  server.close();
})().catch(e => { console.error(e); process.exit(1); });
