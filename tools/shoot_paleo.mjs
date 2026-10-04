// PaleoWave: live check of the project page and the blog post.
import { chromium } from 'playwright';
import fs from 'fs';
const b = await chromium.launch();
const log = [];
for (const [name, url, w] of [['paleo', 'https://brooksgroves.com/project-paleowave/', 1280], ['paleo-phone', 'https://brooksgroves.com/project-paleowave/', 390],
                              ['paleopost', 'https://brooksgroves.com/blog/paleowave-rechecked-post.html', 1280]]) {
  const p = await b.newPage({ viewport: { width: w, height: 900 }, deviceScaleFactor: w < 500 ? 2 : 1 });
  p.on('pageerror', e => log.push(`${name} pageerror: ${e.message}`));
  p.on('response', r => { if (r.status() >= 400) log.push(`${name} ${r.status()} ${r.url().slice(0, 140)}`); });
  const resp = await p.goto(url + '?v=' + Date.now(), { waitUntil: 'networkidle', timeout: 90000 }).catch(e => null);
  log.push(`${name}: HTTP ${resp ? resp.status() : 'none'}`);
  await p.waitForTimeout(4000);
  const info = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth, title: document.title,
    status: document.getElementById('status')?.innerText.replace(/\s+/g, ' '), markers: document.querySelectorAll('path.leaflet-interactive').length,
    tiles: document.querySelectorAll('img.leaflet-tile-loaded').length, cards: document.querySelectorAll('.card').length,
    gallery: document.querySelectorAll('#gallery img').length, imgs: [...document.images].filter(i => !i.naturalWidth).map(i => i.src).slice(0, 5) }));
  log.push(`${name}: ${JSON.stringify(info)}`);
  await p.screenshot({ path: `tools/shots/${name}.png`, fullPage: name !== 'paleo' });
  if (name === 'paleo') { const m = await p.$('#map'); if (m) { await m.scrollIntoViewIfNeeded(); await p.waitForTimeout(1500); await m.screenshot({ path: 'tools/shots/paleo-map.png' }); } }
}
fs.writeFileSync('tools/shots/errors.txt', log.join('\n'));
await b.close();
