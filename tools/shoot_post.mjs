// Live check of the blog post and the listings that link to it.
import { chromium } from 'playwright';
import fs from 'fs';
const b = await chromium.launch();
const log = [];
for (const [name, url, w] of [['post', 'https://brooksgroves.com/blog/sierra-flow-revisited-post.html', 1280], ['post-phone', 'https://brooksgroves.com/blog/sierra-flow-revisited-post.html', 390], ['home', 'https://brooksgroves.com/', 1280], ['blogindex', 'https://brooksgroves.com/blog/index.html', 1280]]) {
  const p = await b.newPage({ viewport: { width: w, height: 900 } });
  p.on('pageerror', e => log.push(`${name} pageerror: ${e.message}`));
  p.on('response', r => { if (r.status() >= 400 && r.url().includes('brooksgroves.com')) log.push(`${name} ${r.status()} ${r.url()}`); });
  try {
    await p.goto(url + '?v=' + Date.now(), { waitUntil: 'networkidle', timeout: 60000 });
    await p.evaluate(() => document.querySelectorAll('img').forEach(i => i.loading = 'eager'));
    await p.waitForTimeout(3000);
    const info = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth, title: document.title,
      broken: [...document.images].filter(i => i.complete && i.naturalWidth === 0).map(i => i.src),
      lahar: [...document.querySelectorAll('a[href*="sierra-flow-revisited"]')].length }));
    log.push(`${name}: ${JSON.stringify(info)}`);
    if (name.startsWith('post')) await p.screenshot({ path: `tools/shots/${name}.png`, fullPage: true });
  } catch (e) { log.push(`${name} failed: ${e.message.split('\n')[0]}`); }
}
fs.writeFileSync('tools/shots/errors.txt', log.join('\n'));
await b.close();
