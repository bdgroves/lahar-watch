// Live check of the 2026 #30DayMapChallenge gallery.
import { chromium } from 'playwright';
import fs from 'fs';
const b = await chromium.launch();
const log = [];
for (const [name, w] of [['dmc', 1280], ['dmc-phone', 390]]) {
  const p = await b.newPage({ viewport: { width: w, height: 900 } });
  p.on('pageerror', e => log.push(`${name} pageerror: ${e.message}`));
  p.on('response', r => { if (r.status() >= 400) log.push(`${name} ${r.status()} ${r.url().slice(0, 140)}`); });
  try {
    await p.goto('https://brooksgroves.com/30DayMapChallenge/2026/?v=' + Date.now(), { waitUntil: 'networkidle', timeout: 60000 });
    await p.waitForTimeout(2000);
    const info = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth, cells: document.querySelectorAll('.cell[data-d]').length,
      imgs: [...document.querySelectorAll('.cell img')].map(i => i.naturalWidth), count: document.getElementById('count').innerText.replace(/\s+/g, ' ') }));
    log.push(`${name}: ${JSON.stringify(info)}`);
    await p.screenshot({ path: `tools/shots/${name}.png`, fullPage: true });
    if (name === 'dmc') { await p.click('.cell[data-d="28"]'); await p.waitForTimeout(1200); await p.screenshot({ path: 'tools/shots/dmc-dlg.png' }); }
  } catch (e) { log.push(`${name} failed: ${e.message.split('\n')[0]}`); }
}
fs.writeFileSync('tools/shots/errors.txt', log.join('\n'));
await b.close();
