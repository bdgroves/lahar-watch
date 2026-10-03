// Live check of brooksgroves.com/cascadia-wx/ (v3, the balloons), plus crops for the blog post.
import { chromium } from 'playwright';
import fs from 'fs';
const b = await chromium.launch();
const log = [];
for (const [name, w] of [['cwx', 1280], ['cwx-phone', 390]]) {
  const p = await b.newPage({ viewport: { width: w, height: 900 }, deviceScaleFactor: w < 500 ? 2 : 1 });
  p.on('pageerror', e => log.push(`${name} pageerror: ${e.message}`));
  p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') log.push(`${name} console ${m.type()}: ${m.text().slice(0, 200)}`); });
  p.on('response', r => { if (r.status() >= 400) log.push(`${name} ${r.status()} ${r.url().slice(0, 140)}`); });
  await p.goto('https://brooksgroves.com/cascadia-wx/?v=' + Date.now(), { waitUntil: 'networkidle', timeout: 90000 });
  await p.waitForTimeout(9000);                       // let the job log finish typing
  const info = await p.evaluate(() => ({
    sw: document.documentElement.scrollWidth, title: document.title,
    sites: document.querySelectorAll('.site').length, status: document.getElementById('status').innerText.replace(/\s+/g, ' '),
    cards: [...document.querySelectorAll('.site')].map(s => s.innerText.split('\n').slice(0, 5).join(' | ')),
    bands: document.querySelectorAll('#fl polygon').length, ar: document.querySelectorAll('#ar tbody tr').length,
    snow: document.getElementById('snow-body').innerText.slice(0, 160), form: document.querySelectorAll('#sheet .row').length,
    markers: document.querySelectorAll('.leaflet-marker-icon, path.leaflet-interactive').length }));
  log.push(`${name}: ${JSON.stringify(info, null, 1)}`);
  await p.screenshot({ path: `tools/shots/${name}-full.png`, fullPage: true });
  if (w > 500) {
    const shot = async (sel, file) => { const el = await p.$(sel); if (el) { await el.scrollIntoViewIfNeeded(); await p.waitForTimeout(700); await el.screenshot({ path: `tools/shots/${file}.png` }); } };
    await shot('#sites', 'cwx-sites');
    await shot('section:has(#profile)', 'cwx-profile');
    await shot('section:has(#fl)', 'cwx-series');
    await shot('#console', 'cwx-console');
    await shot('section:has(#ar)', 'cwx-ar');
    await shot('section:has(#map)', 'cwx-map');
    await shot('.printout', 'cwx-printout');
    await shot('.form', 'cwx-form');
  }
}
fs.writeFileSync('tools/shots/errors.txt', log.join('\n'));
await b.close();
