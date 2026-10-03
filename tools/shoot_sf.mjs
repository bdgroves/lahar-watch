// Live check of brooksgroves.com/sierra-flow-cobol: errors, live readings, screenshots.
import { chromium } from 'playwright';
import fs from 'fs';
const b = await chromium.launch();
const log = [];
const url = 'https://brooksgroves.com/sierra-flow-cobol/';
for (const [name, w] of [['sf', 1280], ['sf-phone', 390]]) {
  const p = await b.newPage({ viewport: { width: w, height: 900 } });
  p.on('pageerror', e => log.push(`${name} pageerror: ${e.message}`));
  p.on('console', m => { if (m.type() === 'error') log.push(`${name} console: ${m.text().slice(0, 160)}`); });
  p.on('response', r => { if (r.status() >= 400) log.push(`${name} ${r.status()} ${r.url().slice(0, 140)}`); });
  try {
    await p.goto(url + '?v=' + Date.now(), { waitUntil: 'networkidle', timeout: 60000 });
    await p.waitForTimeout(4000);
    await p.evaluate(() => document.getElementById('report').scrollIntoView());
    await p.waitForTimeout(4500);
    await p.evaluate(() => scrollTo(0, 0));
    await p.waitForTimeout(800);
    const info = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth,
      status: document.getElementById('status').innerText.replace(/\s+/g, ' '),
      now: [...document.querySelectorAll('.now')].map(e => e.innerText.replace(/\s+/g, ' ')),
      lines: document.querySelectorAll('#report .ln').length, deck: document.getElementById('pos').innerText,
      tiles: [...document.querySelectorAll('.leaflet-tile-loaded')].length }));
    log.push(`${name}: ${JSON.stringify(info)}`);
    await p.screenshot({ path: `tools/shots/${name}.png`, fullPage: true });
    if (name === 'sf') {
      await p.click('#showlog'); await p.waitForTimeout(800);
      await p.screenshot({ path: `tools/shots/sf-log.png`, clip: { x: 0, y: 0, width: 1280, height: 1500 } });
    }
  } catch (e) { log.push(`${name} failed: ${e.message.split('\n')[0]}`); }
}
fs.writeFileSync('tools/shots/errors.txt', log.join('\n'));
await b.close();
