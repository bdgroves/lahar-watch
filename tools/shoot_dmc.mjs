// 30DMC 2026: live check of the gallery's share buttons and preview tags, and stills of the two interactive days.
import { chromium } from 'playwright';
import fs from 'fs';
const BASE = 'https://brooksgroves.com/30DayMapChallenge/2026/';
const b = await chromium.launch();
const log = [];
const page = async (w, h) => { const p = await b.newPage({ viewport: { width: w, height: h } });
  p.on('pageerror', e => log.push(`pageerror: ${e.message}`));
  p.on('response', r => { if (r.status() >= 400) log.push(`${r.status()} ${r.url().slice(0, 140)}`); }); return p; };

let p = await page(1280, 900);
await p.goto(BASE + '?v=' + Date.now(), { waitUntil: 'networkidle' });
log.push('gallery: ' + JSON.stringify(await p.evaluate(() => ({
  share: [...document.querySelectorAll('#share-all a, #share-all button')].map(a => a.textContent.trim() + ' ' + (a.href || '')),
  og: document.querySelector('meta[property="og:image"]')?.content, cells: document.querySelectorAll('.cell[data-d]').length }))));
await p.screenshot({ path: 'tools/shots/dmc-gallery.png' });
await p.click('.cell[data-d="6"]'); await p.waitForTimeout(1500);
log.push('dialog: ' + JSON.stringify(await p.evaluate(() => [...document.querySelectorAll('.dlg .share a')].map(a => a.href))));
await p.screenshot({ path: 'tools/shots/dmc-dialog.png' });
for (const u of [BASE + 'share/day-06.html', BASE + 'card.jpg', BASE + 'day-06-vintage/out/card.jpg']) {
  const r = await p.request.get(u); const t = r.headers()['content-type'];
  log.push(`${r.status()} ${t} ${u}` + (t?.includes('html') ? ' og:image=' + ((await r.text()).match(/og:image" content="([^"]+)/) || [])[1] : ''));
}
p = await page(1600, 1000);
await p.goto(BASE + 'day-13-interactions/', { waitUntil: 'networkidle' });
await p.waitForTimeout(9000);
log.push('day13: ' + (await p.textContent('#out')).replace(/\s+/g, ' ').slice(0, 300));
await p.screenshot({ path: 'tools/shots/dmc-day13.png' });
p = await page(1600, 1000);
await p.goto(BASE + 'day-14-borgesian-map/', { waitUntil: 'networkidle' });
await p.waitForTimeout(4000);
log.push('day14: ' + (await p.textContent('#where')) + ' | ' + (await p.textContent('#hint')));
await p.screenshot({ path: 'tools/shots/dmc-day14.png' });
await p.mouse.move(900, 500); await p.mouse.wheel(0, -2500); await p.waitForTimeout(500);
log.push('day14 after scroll: ' + (await p.textContent('#dist')) + ' | ' + (await p.textContent('#hint')));
await p.screenshot({ path: 'tools/shots/dmc-day14b.png' });
fs.writeFileSync('tools/shots/errors.txt', log.join('\n'));
await b.close();
