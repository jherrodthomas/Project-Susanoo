// SPDX-License-Identifier: Apache-2.0
// Rasterise drawing sheets for review: node tools/cad/sheet_png.cjs cad/drawings/CL-01.svg [...]  -> same name .png
// Also writes cad/drawings/concept-layouts.pdf with every sheet when called with --pdf. A sheet is A3 (420 x 297 mm)
// plus the terms strip that tools/terms/terms.py adds under it, so each page takes the sheet's own size.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
(async () => {
  const args = process.argv.slice(2);
  const pdf = args.includes('--pdf');
  const files = args.filter(a => a.endsWith('.svg'));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1587, height: 1123 }, deviceScaleFactor: 1.5 });
  const MM = 96 / 25.4;
  const size = svg => {  // the sheet's own width and height in mm
    const root = svg.match(/<svg\b[^>]*>/)[0];
    return [parseFloat(root.match(/\bwidth="([0-9.]+)mm"/)[1]), parseFloat(root.match(/\bheight="([0-9.]+)mm"/)[1])];
  };
  for (const f of files) {
    const svg = fs.readFileSync(f, 'utf8');
    const [w, h] = size(svg).map(v => Math.round(v * MM));
    await page.setViewportSize({ width: w, height: h });
    await page.setContent(`<html><body style="margin:0">${svg.replace(/(<svg\b[^>]*?)\bwidth="[^"]+" height="[^"]+"/, `$1width="${w}" height="${h}"`)}</body></html>`);
    await page.screenshot({ path: f.replace(/\.svg$/, '.png'), clip: { x: 0, y: 0, width: w, height: h } });
    console.log('wrote', f.replace(/\.svg$/, '.png'));
  }
  if (pdf && files.length) {  // one page per sheet at its own size (CSS named pages)
    const css = [], body = [];
    files.forEach((f, i) => {
      const svg = fs.readFileSync(f, 'utf8');
      const [w, h] = size(svg);
      css.push(`@page s${i}{size:${w}mm ${h}mm;margin:0} .s${i}{page:s${i};break-after:page}`);
      body.push(`<div class="s${i}">${svg}</div>`);
    });
    await page.setContent(`<html><head><style>body{margin:0} svg{display:block} ${css.join(' ')}</style></head><body>${body.join('')}</body></html>`);
    const out = path.join(path.dirname(files[0]), 'concept-layouts.pdf');
    await page.pdf({ path: out, preferCSSPageSize: true, printBackground: true });
    console.log('wrote', out);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
