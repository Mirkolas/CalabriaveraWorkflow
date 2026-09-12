import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { chromium } from 'playwright';

const [root] = process.argv.slice(2);
if (!root) throw new Error('usage: react-route-css-no-flash.mjs <react-dist>');

const mime = {
  '.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8',
  '.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp',
  '.svg':'image/svg+xml','.ico':'image/x-icon','.woff2':'font/woff2'
};
function safe(rel) {
  const cleaned = normalize(rel).replace(/^(\.\.(\/|\\|$))+/, '').replace(/^[/\\]+/, '');
  return join(root, cleaned);
}
async function exists(path) { try { return (await stat(path)).isFile(); } catch { return false; } }
const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url || '/', 'http://127.0.0.1:4181');
    const pathname = decodeURIComponent(url.pathname);
    const rel = pathname.replace(/^\//, '');
    const candidates = pathname === '/' ? ['index.html'] : [rel, `${rel}/index.html`, 'index.html'];
    let file = null;
    for (const candidateRel of candidates) {
      const candidate = safe(candidateRel);
      if (await exists(candidate)) { file = candidate; break; }
    }
    if (!file) { res.writeHead(404); res.end('not found'); return; }
    const body = await readFile(file);
    res.writeHead(200, {'content-type': mime[extname(file).toLowerCase()] || 'application/octet-stream', 'cache-control':'no-store'});
    res.end(body);
  } catch (error) { res.writeHead(500); res.end(String(error)); }
});
await new Promise(resolve => server.listen(4181, '127.0.0.1', resolve));

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1365, height: 900 }, serviceWorkers: 'block' });
const page = await context.newPage();
let delayRouteCss = false;

await page.route('**/*', async route => {
  const url = new URL(route.request().url());
  if (url.hostname !== '127.0.0.1') {
    await route.abort();
    return;
  }
  if (delayRouteCss && url.pathname.startsWith('/assets/css/cv-bundle-') && url.pathname.endsWith('.css')) {
    await new Promise(resolve => setTimeout(resolve, 450));
  }
  await route.continue();
});

try {
  await page.goto('http://127.0.0.1:4181/', { waitUntil: 'domcontentloaded', timeout: 15000 });
  await page.waitForSelector('.brand-logo', { timeout: 5000 });
  await page.waitForFunction(() => [...document.querySelectorAll('link[data-cv-main-parity]')].some((node) => Boolean(node.sheet)), null, { timeout: 5000 });

  const initialWidth = await page.evaluate(() => Number.parseFloat(getComputedStyle(document.querySelector('.brand-logo')).width || '0'));
  if (initialWidth < 150 || initialWidth > 240) throw new Error(`Logo iniziale fuori scala: ${initialWidth.toFixed(1)}px`);
  delayRouteCss = true;

  const targets = ['/catalogo', '/mappa', '/blog', '/chi-siamo'];
  for (const target of targets) {
    await page.evaluate((pathname) => {
      const anchor = [...document.querySelectorAll('a[href]')].find((node) => new URL(node.href).pathname === pathname);
      if (!anchor) throw new Error(`link ${pathname} non trovato`);
      anchor.click();
    }, target);

    const started = Date.now();
    let maxLogo = 0;
    let minLogo = Number.POSITIVE_INFINITY;
    let styleGap = false;
    while (Date.now() - started < 700) {
      const state = await page.evaluate(() => {
        const logo = document.querySelector('.brand-logo');
        const width = logo ? Number.parseFloat(getComputedStyle(logo).width || '0') : 0;
        const loadedParity = [...document.querySelectorAll('link[data-cv-main-parity]:not([data-cv-main-parity-stage])')]
          .some((node) => Boolean(node.sheet));
        return { width, loadedParity };
      });
      maxLogo = Math.max(maxLogo, state.width);
      minLogo = Math.min(minLogo, state.width);
      if (!state.loadedParity) styleGap = true;
      await page.waitForTimeout(10);
    }

    await page.waitForFunction((pathname) => location.pathname === pathname && !document.querySelector('link[data-cv-main-parity-stage]'), target, { timeout: 5000 });
    const finalState = await page.evaluate(() => ({
      path: location.pathname,
      width: Number.parseFloat(getComputedStyle(document.querySelector('.brand-logo')).width || '0'),
      active: [...document.querySelectorAll('link[data-cv-main-parity]:not([data-cv-main-parity-stage])')].filter((node) => Boolean(node.sheet)).length,
    }));

    console.log(`NO-FLASH ${target}: logo ${minLogo.toFixed(1)}-${maxLogo.toFixed(1)}px; final ${finalState.width.toFixed(1)}px; active css ${finalState.active}`);
    if (styleGap) throw new Error(`FOUC rilevato verso ${target}: nessun foglio parity attivo durante lo swap`);
    if (minLogo < 150 || maxLogo > 240) throw new Error(`Logo instabile verso ${target}: ${minLogo.toFixed(1)}-${maxLogo.toFixed(1)}px`);
    if (finalState.width < 150 || finalState.width > 240) throw new Error(`Logo finale fuori scala su ${target}: ${finalState.width.toFixed(1)}px`);
    if (finalState.active < 1) throw new Error(`CSS parity finale assente su ${target}`);
  }

  console.log('Route CSS transition: nessun flash senza stile e nessun logo gigante');
} finally {
  await context.close();
  await browser.close();
  server.close();
}
