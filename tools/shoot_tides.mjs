// Live check of brooksgroves.com/puget-tides/, plus crops for the blog post.
import { chromium } from 'playwright';
import fs from 'fs';
const b = await chromium.launch();
const log = [];
for (const [name, w] of [['tides', 1280], ['tides-phone', 390]]) {
  const p = await b.newPage({ viewport: { width: w, height: 900 }, deviceScaleFactor: w < 500 ? 2 : 1 });
  p.on('pageerror', e => log.push(`${name} pageerror: ${e.message}`));
  p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') log.push(`${name} console ${m.type()}: ${m.text().slice(0, 200)}`); });
  p.on('response', r => { if (r.status() >= 400) log.push(`${name} ${r.status()} ${r.url().slice(0, 140)}`); });
  await p.goto('https://brooksgroves.com/puget-tides/?v=' + Date.now(), { waitUntil: 'networkidle', timeout: 90000 });
  await p.waitForTimeout(9000);                       // let the job log finish typing
  const info = await p.evaluate(() => ({
    sw: document.documentElement.scrollWidth, title: document.title,
    cards: [...document.querySelectorAll('.card')].map(c => c.innerText.split('\n').slice(0, 5).join(' | ')),
    status: document.getElementById('status').innerText.replace(/\s+/g, ' '),
    wk: document.querySelectorAll('#wk path').length, surgeBand: document.querySelectorAll('#surge polygon').length,
    hilo: document.querySelectorAll('#hilo tbody tr').length, ver: document.getElementById('ver-sub').innerText,
    kings: document.querySelectorAll('#kings tbody tr').length, minus: document.querySelectorAll('#minus circle').length,
    slr: document.querySelectorAll('#slr path').length, trend: document.querySelectorAll('#trend tbody tr').length,
    markers: document.querySelectorAll('path.leaflet-interactive').length, form: document.querySelectorAll('#sheet .row').length }));
  log.push(`${name}: ${JSON.stringify(info, null, 1)}`);
  await p.screenshot({ path: `tools/shots/${name}-full.png`, fullPage: true });
  if (w > 500) {
    const shot = async (sel, file) => { const el = await p.$(sel); if (el) { await el.scrollIntoViewIfNeeded(); await p.waitForTimeout(700); await el.screenshot({ path: `tools/shots/${file}.png` }); } };
    await shot('#cards', 'tides-cards');
    await shot('section:has(#wk)', 'tides-week');
    await shot('section:has(#hilo)', 'tides-hilo');
    await shot('section:has(#map)', 'tides-map');
    await shot('section:has(#kings)', 'tides-kings');
    await shot('section:has(#minus)', 'tides-minus');
    await shot('section:has(#slr)', 'tides-sealevel');
    await shot('.printout', 'tides-printout');
    await shot('.form', 'tides-form');
  }
}
fs.writeFileSync('tools/shots/errors.txt', log.join('\n'));
await b.close();
