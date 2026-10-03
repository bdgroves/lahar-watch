// Live check of the PUGET-TIDES post and where it's listed.
import { chromium } from 'playwright';
import fs from 'fs';
const b = await chromium.launch();
const log = [];
const pages = [['post', '/blog/puget-tides-post.html', 1280], ['post-phone', '/blog/puget-tides-post.html', 390],
  ['blog', '/blog/index.html', 1280], ['home', '/', 1280], ['hyd', '/hydrology.html', 1280], ['tides', '/puget-tides/', 390], ['tags', '/tags.html#FORTRAN', 1280]];
for (const [name, path, w] of pages) {
  const p = await b.newPage({ viewport: { width: w, height: 900 } });
  p.on('pageerror', e => log.push(`${name} pageerror: ${e.message}`));
  p.on('response', r => { if (r.status() >= 400 && r.url().includes('brooksgroves.com')) log.push(`${name} ${r.status()} ${r.url().slice(0, 140)}`); });
  await p.goto('https://brooksgroves.com' + path + (path.includes('#') ? '' : '?v=' + Date.now()), { waitUntil: 'networkidle', timeout: 60000 });
  await p.waitForTimeout(1500);
  const info = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth,
    links: document.querySelectorAll('a[href*="puget-tides"]').length,
    imgs: [...document.querySelectorAll('img[src*="puget-tides"]')].map(i => i.naturalWidth),
    text: (document.body.innerText.match(/PUGET-TIDES[^\n]{0,80}/g) || []).slice(0, 3) }));
  log.push(`${name}: ${JSON.stringify(info)}`);
  if (name.startsWith('post')) await p.screenshot({ path: `tools/shots/${name}.png`, fullPage: true });
}
fs.writeFileSync('tools/shots/errors.txt', log.join('\n'));
await b.close();
