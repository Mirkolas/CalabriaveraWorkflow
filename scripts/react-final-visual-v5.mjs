import { createServer } from 'node:http';
import { readFile, stat, mkdir, writeFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { chromium } from 'playwright';
import pixelmatch from 'pixelmatch';
import { PNG } from 'pngjs';

const [oracleRoot, reactRoot, outputRoot = '/tmp/cv-visual/out-v5'] = process.argv.slice(2);
if (!oracleRoot || !reactRoot) throw new Error('usage: react-final-visual-v5.mjs <oracle-dist> <react-dist> [output]');
await mkdir(outputRoot, { recursive: true });

const mime = {
  '.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8',
  '.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp',
  '.svg':'image/svg+xml','.ico':'image/x-icon','.woff2':'font/woff2'
};
function safe(root, rel) {
  const cleaned = normalize(rel).replace(/^(\.\.(\/|\\|$))+/, '').replace(/^[/\\]+/, '');
  return join(root, cleaned);
}
async function exists(path) { try { return (await stat(path)).isFile(); } catch { return false; } }
function serve(root, mode, port) {
  const server = createServer(async (req, res) => {
    try {
      const url = new URL(req.url || '/', `http://127.0.0.1:${port}`);
      const pathname = decodeURIComponent(url.pathname);
      const rel = pathname.replace(/^\//, '');
      const candidates = pathname === '/' ? ['index.html'] : mode === 'oracle' ? [rel, `${rel}.html`] : [rel, `${rel}/index.html`, 'index.html'];
      let file = null;
      for (const candidateRel of candidates) {
        const candidate = safe(root, candidateRel);
        if (await exists(candidate)) { file = candidate; break; }
      }
      if (!file) { res.writeHead(404); res.end('not found'); return; }
      const body = await readFile(file);
      res.writeHead(200, {'content-type': mime[extname(file).toLowerCase()] || 'application/octet-stream', 'cache-control':'no-store'});
      res.end(body);
    } catch (error) { res.writeHead(500); res.end(String(error)); }
  });
  return new Promise(resolve => server.listen(port, '127.0.0.1', () => resolve(server)));
}

const oracleServer = await serve(oracleRoot, 'oracle', 4173);
const reactServer = await serve(reactRoot, 'react', 4174);
const browser = await chromium.launch({ headless: true });
const routes = ['/', '/catalogo', '/mappa', '/blog', '/chi-siamo', '/contatti', '/privacy-policy', '/cookie-policy', '/termini', '/note-legali', '/login', '/registrazione'];
const dynamic = new Set(['/catalogo','/mappa','/blog']);
const viewports = [{name:'desktop', width:1365, height:900}, {name:'mobile', width:390, height:844}];
const results = [], failures = [];

function normalizeCss(route) {
  const base = '*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}html{scroll-behavior:auto!important}';
  if (route === '/catalogo') return base + '#results,#result-count,#load-more{visibility:hidden!important}';
  if (route === '/blog') return base + '#blog-list,#blog-more{visibility:hidden!important}';
  if (route === '/mappa') return base + '#map,#map-count{visibility:hidden!important}';
  return base;
}
async function shot(port, route, viewport, tag) {
  const context = await browser.newContext({ viewport: {width:viewport.width,height:viewport.height}, locale:'it-IT', serviceWorkers:'block' });
  await context.addInitScript(() => { try { localStorage.setItem('cv-consent','rejected'); } catch {} });
  const page = await context.newPage();
  await page.route('**/*', async r => {
    const u = new URL(r.request().url());
    if (u.hostname === '127.0.0.1' || u.protocol === 'data:' || u.protocol === 'blob:') return r.continue();
    if (tag === 'react' && u.hostname === 'img.calabriavera.com' && u.pathname.startsWith('/static/')) {
      const rel = u.pathname.slice('/static/'.length);
      const file = safe(oracleRoot, rel);
      if (!(await exists(file))) throw new Error(`R2 parity asset non presente nell'oracolo: ${u.pathname}`);
      const body = await readFile(file);
      return r.fulfill({ status: 200, body, contentType: mime[extname(file).toLowerCase()] || 'application/octet-stream' });
    }
    if (tag === 'legacy' && route === '/mappa' && u.hostname === 'unpkg.com') return r.continue();
    return r.abort();
  });
  await page.goto(`http://127.0.0.1:${port}${route}`, { waitUntil:'domcontentloaded', timeout:30000 });
  if (route === '/mappa') await page.waitForSelector('.cv-map-aside-head', { timeout: 8000 }).catch(()=>{});
  await page.addStyleTag({content:normalizeCss(route)}).catch(()=>{});
  await page.evaluate(() => document.fonts?.ready).catch(()=>{});
  await page.waitForTimeout(dynamic.has(route) ? 1800 : 900);
  await page.evaluate(() => scrollTo(0,0)).catch(()=>{});
  const name = route === '/' ? 'home' : route.slice(1).replaceAll('/','-');
  const path = `${outputRoot}/${name}-${viewport.name}-${tag}.png`;
  await page.screenshot({path, fullPage:false, animations:'disabled'});
  await context.close();
  return path;
}

try {
  for (const viewport of viewports) {
    for (const route of routes) {
      const aPath = await shot(4173, route, viewport, 'legacy');
      const bPath = await shot(4174, route, viewport, 'react');
      const a = PNG.sync.read(await readFile(aPath));
      const b = PNG.sync.read(await readFile(bPath));
      if (a.width !== b.width || a.height !== b.height) throw new Error(`dimension mismatch ${route} ${viewport.name}`);
      const diff = new PNG({width:a.width,height:a.height});
      const changed = pixelmatch(a.data,b.data,diff.data,a.width,a.height,{threshold:0.1,includeAA:false});
      const ratio = changed/(a.width*a.height);
      const name = route === '/' ? 'home' : route.slice(1).replaceAll('/','-');
      await writeFile(`${outputRoot}/${name}-${viewport.name}-diff.png`, PNG.sync.write(diff));
      results.push({route, viewport:viewport.name, changed, ratio, mode:dynamic.has(route)?'stable-ui':'full-page'});
      console.log(`VISUAL ${viewport.name.padEnd(7)} ${route.padEnd(18)} ${(ratio*100).toFixed(3)}% ${dynamic.has(route)?'[stable UI]':'[full]'}`);
      if (ratio > 0.010) failures.push(`${viewport.name} ${route}: ${(ratio*100).toFixed(3)}%`);
    }
  }
  await writeFile(`${outputRoot}/results.json`, JSON.stringify(results,null,2));
  if (failures.length) {
    console.error('::error::Visual parity >1%: '+failures.join(' | '));
    process.exitCode = 1;
  } else {
    console.log('Visual parity v5: tutte le route deterministic/stable UI <= 1% pixel diff');
  }
} finally {
  await browser.close();
  oracleServer.close(); reactServer.close();
}
