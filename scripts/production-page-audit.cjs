const assert = require('node:assert/strict');
const { mkdirSync, writeFileSync } = require('node:fs');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const baseUrl = (process.env.AUDIT_BASE_URL || 'https://calabriavera.com').replace(/\/$/, '');
const outDir = process.env.AUDIT_OUTPUT_DIR || 'page-audit';
mkdirSync(outDir, { recursive: true });

const routes = [
  { path: '/', name: 'home', page: 'home', selectors: ['h1'] },
  { path: '/catalogo', name: 'catalogo', page: 'catalog', selectors: ['h1', '#filters', '#results'] },
  { path: '/mappa', name: 'mappa', page: 'map', selectors: ['h1', '#map', '#map-filters'] },
  { path: '/blog', name: 'blog', page: 'blog', selectors: ['h1', '#blog-lane-tabs', '#blog-list'] },
];

function sameOrigin(url) {
  try { return new URL(url).origin === baseUrl; } catch { return false; }
}

async function auditViewport(browser, label, viewport) {
  const context = await browser.newContext({ locale: 'it-IT', viewport, serviceWorkers: 'block' });
  const page = await context.newPage();
  const report = [];

  for (const route of routes) {
    const networkErrors = [];
    const pageErrors = [];
    const consoleErrors = [];
    const onResponse = response => {
      if (sameOrigin(response.url()) && response.status() >= 400) networkErrors.push(`${response.status()} ${new URL(response.url()).pathname}`);
    };
    const onPageError = error => pageErrors.push(error?.message || String(error));
    const onConsole = message => {
      if (message.type() === 'error') consoleErrors.push(message.text());
    };
    page.on('response', onResponse);
    page.on('pageerror', onPageError);
    page.on('console', onConsole);

    const started = Date.now();
    const response = await page.goto(`${baseUrl}${route.path}?cv_audit=${Date.now()}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    assert.ok(response, `${label} ${route.path}: nessuna risposta`);
    assert.ok(response.status() < 400, `${label} ${route.path}: HTTP ${response.status()}`);
    assert.equal(await page.locator('body').getAttribute('data-page'), route.page, `${label} ${route.path}: data-page inatteso`);

    for (const selector of route.selectors) {
      await page.locator(selector).first().waitFor({ state: 'visible', timeout: 15000 });
    }

    let firstCardMs = null;
    let eventCards = null;
    let newsCards = null;
    if (route.name === 'blog') {
      const firstCard = page.locator('#blog-list article').first();
      await firstCard.waitFor({ state: 'visible', timeout: 3000 });
      firstCardMs = Date.now() - started;
      assert.ok(firstCardMs < 3000, `${label} Blog: prima card troppo lenta (${firstCardMs} ms)`);
      assert.equal(await page.getByText('Caricamento contenuti…', { exact: true }).count(), 0, `${label} Blog: loader ancora visibile`);
      eventCards = await page.locator('#blog-list article').count();
      assert.ok(eventCards > 0, `${label} Blog: nessun Evento visibile`);

      const newsTab = page.locator('[data-blog-lane="news"]');
      await newsTab.click();
      await page.locator('#blog-list article').first().waitFor({ state: 'visible', timeout: 3000 });
      newsCards = await page.locator('#blog-list article').count();
      assert.ok(newsCards > 0, `${label} Blog: nessuna Notizia visibile`);
      const selected = await newsTab.getAttribute('aria-selected');
      assert.equal(selected, 'true', `${label} Blog: tab Notizie non selezionata logicamente`);
    }

    if (route.name === 'catalogo') {
      const results = page.locator('#results');
      await page.waitForTimeout(400);
      assert.ok(await results.isVisible(), `${label} Catalogo: risultati non visibili`);
    }

    if (route.name === 'mappa') {
      const box = await page.locator('#map').boundingBox();
      assert.ok(box && box.height >= 260, `${label} Mappa: altezza insufficiente`);
    }

    const metrics = await page.evaluate(() => ({
      innerWidth: window.innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      bodyScrollWidth: document.body.scrollWidth,
      h1: document.querySelector('h1')?.textContent?.trim() || '',
      bodyHeight: document.body.getBoundingClientRect().height,
      headerVisible: Boolean(document.querySelector('header')),
      footerVisible: Boolean(document.querySelector('footer')),
    }));
    const maxWidth = Math.max(metrics.scrollWidth, metrics.bodyScrollWidth);
    assert.ok(maxWidth <= metrics.innerWidth + 3, `${label} ${route.path}: overflow orizzontale ${maxWidth}px > ${metrics.innerWidth}px`);
    assert.ok(metrics.h1.length > 0, `${label} ${route.path}: H1 vuoto`);
    assert.ok(metrics.bodyHeight > 400, `${label} ${route.path}: pagina troppo bassa`);
    assert.ok(metrics.headerVisible, `${label} ${route.path}: header assente`);
    assert.ok(metrics.footerVisible, `${label} ${route.path}: footer assente`);

    await page.screenshot({ path: `${outDir}/${label}-${route.name}.png`, fullPage: true });
    await page.waitForTimeout(250);

    const severeConsole = consoleErrors.filter(text => /(?:Uncaught|TypeError|ReferenceError|SyntaxError|Hydration failed)/i.test(text));
    assert.deepEqual(pageErrors, [], `${label} ${route.path}: page errors: ${pageErrors.join(' | ')}`);
    assert.deepEqual(severeConsole, [], `${label} ${route.path}: console errors: ${severeConsole.join(' | ')}`);
    assert.deepEqual(networkErrors, [], `${label} ${route.path}: risorse locali fallite: ${networkErrors.join(', ')}`);

    report.push({
      viewport: label,
      path: route.path,
      h1: metrics.h1,
      width: metrics.innerWidth,
      scrollWidth: maxWidth,
      bodyHeight: Math.round(metrics.bodyHeight),
      firstBlogCardMs: firstCardMs,
      eventCards,
      newsCards,
      consoleErrorCount: consoleErrors.length,
    });

    page.off('response', onResponse);
    page.off('pageerror', onPageError);
    page.off('console', onConsole);
  }

  await context.close();
  return report;
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const desktop = await auditViewport(browser, 'desktop', { width: 1365, height: 900 });
    const mobile = await auditViewport(browser, 'mobile', { width: 390, height: 844 });
    const report = [...desktop, ...mobile];
    writeFileSync(`${outDir}/report.json`, JSON.stringify(report, null, 2));
    console.log(JSON.stringify({ ok: true, report }, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error?.stack || error);
  process.exitCode = 1;
});
