// SPDX-License-Identifier: Apache-2.0
// README banner from the CAD-true Blender renders of the reference layout (not from AI concept art).
//   node tools/cad/banner.cjs        -> docs/assets/banner.png (2400 x 800)
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..', '..');
const R = p => 'data:image/jpeg;base64,' + fs.readFileSync(path.join(ROOT, 'cad/renders/blender', p)).toString('base64');
const metrics = JSON.parse(fs.readFileSync(path.join(ROOT, 'cad/metrics.json'), 'utf8')).concepts['CL-05'];

const html = `<!doctype html><html><head><meta charset="utf-8"><style>
  html,body{margin:0;background:#0f1418}
  #b{position:relative;width:1200px;height:400px;overflow:hidden;font-family:'DejaVu Sans','Liberation Sans',Arial,sans-serif;
     background:#0f1418}
  .hero{position:absolute;left:400px;top:0;width:470px;height:400px;background:url(${R('CL-05-hero.jpg')}) center 40%/cover}
  .hero::after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,#0f1418 0%,rgba(15,20,24,.55) 12%,rgba(15,20,24,0) 34%,rgba(15,20,24,0) 100%)}
  .side{position:absolute;left:878px;width:314px;height:192px;background-size:cover;background-position:center 45%;border-radius:4px}
  .s1{top:6px;background-image:url(${R('CL-05-kneel.jpg')})}
  .s2{top:202px;background-image:url(${R('CL-05-hero-military.jpg')})}
  .tag{position:absolute;left:8px;bottom:7px;font-size:10.5px;color:#e8edf1;background:rgba(15,20,24,.72);padding:2px 7px;border-radius:3px;letter-spacing:.3px}
  .t{position:absolute;left:40px;top:62px;width:350px;color:#eef2f5}
  .t .k{font-size:13px;letter-spacing:3px;color:#f2b705;font-weight:700}
  .t h1{margin:10px 0 8px;font-size:46px;line-height:1.02;font-weight:800;letter-spacing:.5px}
  .t p{margin:0 0 18px;font-size:15.5px;line-height:1.4;color:#c4ced6}
  .chips span{display:inline-block;margin:0 6px 7px 0;padding:4px 9px;border:1px solid #3a4852;border-radius:3px;font-size:12px;color:#d7dee4}
  .foot{position:absolute;left:40px;bottom:18px;width:330px;font-size:10.5px;line-height:1.4;color:#8a98a3;letter-spacing:.3px}
  .stripe{position:absolute;left:0;top:0;width:8px;height:400px;background:repeating-linear-gradient(135deg,#f2b705 0 14px,#11171b 14px 28px)}
</style></head><body><div id="b">
  <div class="stripe"></div>
  <div class="hero"></div>
  <div class="side s1"><span class="tag">Kneel for egress · ladder deployed</span></div>
  <div class="side s2"><span class="tag">Military livery · unarmed</span></div>
  <div class="t">
    <div class="k">PROJECT</div>
    <h1>SUSANOO</h1>
    <p>Human-piloted bipedal walker (SUS-M1) with a dockable observation UAV (SUS-A1), developed simulation-first as Product Development as Code.</p>
    <div class="chips"><span>Reference layout CL-05</span><span>${metrics.height_m.toFixed(1)} m · reverse-jointed</span><span>Unarmed</span><span>MIL-STD-882E · ARP4761A</span></div>
  </div>
  <div class="foot">Concept renders from the project CAD (placeholder geometry, not a design) · CC BY 4.0</div>
</div></body></html>`;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 400 }, deviceScaleFactor: 2 });
  await page.setContent(html, { waitUntil: 'load' });
  const out = path.join(ROOT, 'docs/assets/banner.png');
  fs.mkdirSync(path.dirname(out), { recursive: true });
  await page.locator('#b').screenshot({ path: out });
  await browser.close();
  console.log('wrote', path.relative(ROOT, out));
})().catch(e => { console.error(e); process.exit(1); });
