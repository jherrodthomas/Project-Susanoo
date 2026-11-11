// SPDX-License-Identifier: Apache-2.0
// Rasterise drawing sheets for review: node tools/cad/sheet_png.cjs cad/drawings/CL-01.svg [...]  -> same name .png
// Also writes cad/drawings/concept-layouts.pdf with every sheet when called with --pdf.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
(async () => {
  const args = process.argv.slice(2);
  const pdf = args.includes('--pdf');
  const files = args.filter(a => a.endsWith('.svg'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1587, height: 1123 }, deviceScaleFactor: 1.5 });
  for (const f of files) {
    const svg = fs.readFileSync(f, 'utf8');
    await page.setContent(`<html><body style="margin:0">${svg.replace(/width="420mm" height="297mm"/, 'width="1587" height="1123"')}</body></html>`);
    await page.screenshot({ path: f.replace(/\.svg$/, '.png'), clip: { x: 0, y: 0, width: 1587, height: 1123 } });
    console.log('wrote', f.replace(/\.svg$/, '.png'));
  }
  if (pdf && files.length) {
    const sheets = files.map(f => `<div style="page-break-after:always">${fs.readFileSync(f, 'utf8')}</div>`).join('');
    await page.setContent(`<html><head><style>@page{size:420mm 297mm;margin:0}body{margin:0}</style></head><body>${sheets}</body></html>`);
    const out = path.join(path.dirname(files[0]), 'concept-layouts.pdf');
    await page.pdf({ path: out, width: '420mm', height: '297mm', printBackground: true });
    console.log('wrote', out);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
