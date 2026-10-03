// Screenshots of the live lahar-watch pages, with errors and the key numbers each page shows.
import { chromium } from 'playwright';
import fs from 'fs';
const b = await chromium.launch();
const log = [];
const base = 'https://brooksgroves.com/lahar-watch/';
for (const [name, path, w] of [['dash', 'index.html', 1440], ['dash-phone', 'index.html', 390], ['seismic', 'seismic.html', 1440], ['warning', 'travel-time.html', 1440], ['status', 'status.html', 1440]]) {
  const p = await b.newPage({ viewport: { width: w, height: 900 } });
  p.on('pageerror', e => log.push(`${name} pageerror: ${e.message}`));
  p.on('console', m => { if (m.type() === 'error') log.push(`${name} console: ${m.text().slice(0, 160)}`); });
  try {
    await p.goto(base + path + '?v=' + Date.now(), { waitUntil: 'networkidle', timeout: 60000 });
    await p.waitForTimeout(6000);
    const info = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth,
      cards: [...document.querySelectorAll('.grid4 .card')].map(c => c.innerText.replace(/\s+/g, ' ').slice(0, 220)),
      notice: (document.getElementById('notice')?.innerText || '').slice(0, 300),
      chk: (document.getElementById('chk')?.innerText || '').replace(/\s+/g, ' ').slice(0, 500) }));
    log.push(`${name}: ${JSON.stringify(info)}`);
    await p.screenshot({ path: `tools/shots/${name}.png`, fullPage: true });
  } catch (e) { log.push(`${name} failed: ${e.message.split('\n')[0]}`); }
}
fs.writeFileSync('tools/shots/errors.txt', log.join('\n'));
await b.close();
