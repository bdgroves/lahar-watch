// PaleoWave v4 + IceWave pits: live check.
import { chromium } from 'playwright';
import fs from 'fs';
const b = await chromium.launch();
const log = [];
for (const [name, url, w, ids] of [['pw4', 'https://brooksgroves.com/project-paleowave/', 1280, ['cards4', 'note4']],
                                    ['pw4-phone', 'https://brooksgroves.com/project-paleowave/', 390, ['cards4']],
                                    ['iwpits', 'https://brooksgroves.com/project-ice-wave/', 1280, ['pitcards', 'pitnote']],
                                    ['iwpits-phone', 'https://brooksgroves.com/project-ice-wave/', 390, ['pitcards']]]) {
  const p = await b.newPage({ viewport: { width: w, height: 900 } });
  p.on('pageerror', e => log.push(`${name} pageerror: ${e.message}`));
  p.on('console', m => { if (m.type() === 'error') log.push(`${name} console: ${m.text()}`); });
  p.on('response', r => { if (r.status() >= 400) log.push(`${name} ${r.status()} ${r.url().slice(0, 140)}`); });
  const resp = await p.goto(url + '?v=' + Date.now(), { waitUntil: 'networkidle', timeout: 90000 }).catch(e => null);
  log.push(`${name}: HTTP ${resp ? resp.status() : 'none'}`);
  await p.waitForTimeout(4000);
  const info = await p.evaluate((ids) => ({ sw: document.documentElement.scrollWidth,
    markers4: document.querySelectorAll('#map4 .leaflet-marker-icon').length, paths4: document.querySelectorAll('#map4 path.leaflet-interactive').length,
    overlay: document.querySelectorAll('#map4 img.leaflet-image-layer').length,
    pitpaths: document.querySelectorAll('#pitmap path.leaflet-interactive').length, pitrows: document.querySelectorAll('#pittable tbody tr').length,
    t4rows: document.querySelectorAll('#targets4 tbody tr').length, g4: document.querySelectorAll('#gallery4 img').length,
    text: Object.fromEntries(ids.map(i => [i, (document.getElementById(i)?.innerText || 'MISSING').replace(/\s+/g, ' ').slice(0, 400)])) }), ids);
  log.push(`${name}: ${JSON.stringify(info)}`);
  await p.screenshot({ path: `tools/shots/${name}.png`, fullPage: false });
  for (const id of ['map4', 'pitmap']) { const m = await p.$('#' + id); if (m && w > 500) { await m.scrollIntoViewIfNeeded(); await p.waitForTimeout(2500); await m.screenshot({ path: `tools/shots/${name}-${id}.png` }); } }
}
fs.writeFileSync('tools/shots/errors.txt', log.join('\n'));
await b.close();
