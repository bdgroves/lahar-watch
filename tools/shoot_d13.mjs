// Day 13 check: does the raindrop page trace from Groveland in a real browser (CORS, NLDI, tiles)?
import { chromium } from 'playwright';
import fs from 'fs';
const b = await chromium.launch();
const log = [];
const p = await b.newPage({ viewport: { width: 1600, height: 1000 } });
p.on('pageerror', e => log.push(`pageerror: ${e.message}`));
p.on('console', m => { if (m.type() === 'error') log.push(`console: ${m.text().slice(0, 200)}`); });
p.on('response', r => { if (r.status() >= 400) log.push(`${r.status()} ${r.url().slice(0, 160)}`); });
await p.goto('https://brooksgroves.com/30DayMapChallenge/2026/day-13-interactions/?v=' + Date.now(), { waitUntil: 'networkidle', timeout: 90000 });
await p.waitForTimeout(22000);
log.push('out: ' + await p.evaluate(() => document.getElementById('out').innerText.replace(/\s+/g, ' ')));
await p.screenshot({ path: 'tools/shots/d13.png' });
// a second click, in Nevada (should end in a basin, not the sea)
await p.mouse.click(900, 430);
await p.waitForTimeout(12000);
log.push('click2: ' + await p.evaluate(() => document.getElementById('out').innerText.replace(/\s+/g, ' ')));
await p.screenshot({ path: 'tools/shots/d13b.png' });
fs.writeFileSync('tools/shots/errors.txt', log.join('\n'));
await b.close();
