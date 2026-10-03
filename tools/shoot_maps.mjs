// Live check of brooksgroves.com/maps.html: the 30DayMapChallenge section.
import { chromium } from 'playwright';
import fs from 'fs';
const b = await chromium.launch();
const log = [];
for (const [name, w] of [['maps', 1280], ['maps-phone', 390]]) {
  const p = await b.newPage({ viewport: { width: w, height: 900 } });
  p.on('pageerror', e => log.push(`${name} pageerror: ${e.message}`));
  p.on('response', r => { if (r.status() >= 400) log.push(`${name} ${r.status()} ${r.url().slice(0, 140)}`); });
  await p.goto('https://brooksgroves.com/maps.html?v=' + Date.now(), { waitUntil: 'networkidle', timeout: 60000 });
  await p.waitForTimeout(2500);
  const info = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth, cards: document.querySelectorAll('.dmc-card').length,
    imgs: [...document.querySelectorAll('.dmc-card img')].filter(i => i.naturalWidth > 0).length,
    count: (document.getElementById('dmc-count') || {}).innerText, legend: (document.getElementById('dmc-legend') || {}).innerText }));
  log.push(`${name}: ${JSON.stringify(info)}`);
  const el = await p.$('.dmc');
  if (el) { await el.scrollIntoViewIfNeeded(); await p.waitForTimeout(800); await el.screenshot({ path: `tools/shots/${name}.png` }); }
}
fs.writeFileSync('tools/shots/errors.txt', log.join('\n'));
await b.close();
