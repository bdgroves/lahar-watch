// Which elements stick out past a phone screen on the live page?
import { chromium } from 'playwright';
import fs from 'fs';
const b = await chromium.launch();
const out = [];
for (const url of ['https://brooksgroves.com/puget-tides/', 'https://brooksgroves.com/cascadia-wx/']){
  const p = await b.newPage({ viewport: { width: 390, height: 900 }, deviceScaleFactor: 2 });
  await p.goto(url + '?v=' + Date.now(), { waitUntil: 'networkidle', timeout: 90000 }); await p.waitForTimeout(4000);
  out.push(url + ' ' + JSON.stringify(await p.evaluate(() => { const W = document.documentElement.clientWidth, o = [];
    for (const e of document.querySelectorAll('body *')){ if (e.closest('.console,.tbl-wrap,.printout,.form,#map')) continue; const r = e.getBoundingClientRect(); if (r.right > W + 0.1) o.push(`${e.tagName}.${e.className}#${e.id} ${r.right.toFixed(1)}`); }
    return [document.documentElement.scrollWidth, W, o.slice(0, 10)]; })));
}
fs.mkdirSync('tools/shots', { recursive: true }); fs.writeFileSync('tools/shots/errors.txt', out.join('\n')); await b.close();
