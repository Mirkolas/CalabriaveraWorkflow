const assert = require('node:assert/strict');
const { mkdirSync, writeFileSync } = require('node:fs');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const baseUrl = (process.env.AUDIT_BASE_URL || 'https://calabriavera.com').replace(/\/$/, '');
const baseOrigin = new URL(baseUrl).origin;
const criticalOrigins = new Set([baseOrigin, 'https://img.calabriavera.com']);
const outDir = process.env.AUDIT_OUTPUT_DIR || 'page-audit';
mkdirSync(outDir, { recursive: true });

const routes = [
  { path: '/', name: 'home', page: 'home', selectors: ['h1'] },
  { path: '/catalogo', name: 'catalogo', page: 'catalog', selectors: ['h1', '#filters', '#results'] },
  { path: '/mappa', name: 'mappa', page: 'map', selectors: ['#map', '#map-filters'] },
  { path: '/blog', name: 'blog', page: 'blog', selectors: ['h1', '#blog-lane-tabs', '#blog-list'] },
];

function criticalAsset(url) {
  try { return criticalOrigins.has(new URL(url).origin); } catch { return false; }
}

async function auditCanonicalAssets(page, label, routeFailures) {
  const check = (condition, message) => { if (!condition) routeFailures.push(message); };
  const assetState = await page.evaluate(() => {
    const primary = [...document.querySelectorAll('.primary-nav a')]
      .filter(node => getComputedStyle(node).display !== 'none')
      .map(node => ({ text: (node.textContent || '').trim(), href: node.getAttribute('href') || '' }));
    const logo = document.querySelector('.brand-logo');
    const icons = [...document.querySelectorAll('link[rel~="icon"], link[rel="apple-touch-icon"]')].map(node => node.getAttribute('href') || '');
    return {
      primary,
      logoSrc: logo?.getAttribute('src') || '',
      logoNaturalWidth: logo instanceof HTMLImageElement ? logo.naturalWidth : 0,
      icons,
    };
  });
  check(assetState.primary.length === 1, `${label} Home: navigazione primaria deve contenere solo Home, trovate ${assetState.primary.length} voci`);
  check(assetState.primary[0]?.text.trim().toLowerCase() === 'home', `${label} Home: unica voce primaria non è Home`);
  check(assetState.logoSrc === '/assets/Logo.webp', `${label} Home: logo header non usa /assets/Logo.webp (${assetState.logoSrc})`);
  check(assetState.logoNaturalWidth > 0, `${label} Home: logo header non caricato`);
  check(assetState.icons.some(href => href.startsWith('/assets/favicon.ico?v=')), `${label} Home: favicon.ico canonico assente`);
  check(assetState.icons.some(href => href.startsWith('/assets/favicon-32x32.png?v=')), `${label} Home: favicon 32x32 canonico assente`);
  check(assetState.icons.some(href => href.startsWith('/assets/apple-touch-icon.png?v=')), `${label} Home: apple-touch-icon canonico assente`);

  const language = page.locator('details.header-language');
  try {
    await language.locator('summary').click();
    const flags = page.locator('.cv-language-list .cv-language-flag');
    check(await flags.count() === 5, `${label} Home: attese 5 bandiere lingua`);
    for (let i = 0; i < await flags.count(); i += 1) {
      const background = await flags.nth(i).evaluate(node => getComputedStyle(node).backgroundImage);
      check(background.includes('/assets/flags/'), `${label} Home: bandiera ${i + 1} non usa /assets/flags (${background})`);
      check(background !== 'none', `${label} Home: bandiera ${i + 1} senza background`);
    }
    await language.locator('summary').click().catch(() => undefined);
  } catch (error) {
    routeFailures.push(`${label} Home: selettore lingue non verificabile (${error?.message || error})`);
  }

  for (const asset of [
    '/assets/Logo.webp',
    '/assets/favicon.ico',
    '/assets/favicon-32x32.png',
    '/assets/apple-touch-icon.png',
    '/assets/flags/it.svg',
    '/assets/flags/en.svg',
    '/assets/flags/fr.svg',
    '/assets/flags/de.svg',
    '/assets/flags/es.svg',
    '/assets/Story-Promo_instagram-facebook.png',
    '/assets/images/blog-default-events.png',
    '/assets/images/blog-default-news.png',
  ]) {
    try {
      const response = await page.request.get(`${baseUrl}${asset}?cv_asset_audit=${Date.now()}`);
      check(response.ok(), `${label} asset ${asset}: HTTP ${response.status()}`);
    } catch (error) {
      routeFailures.push(`${label} asset ${asset}: ${error?.message || error}`);
    }
  }
}

async function auditViewport(browser, label, viewport) {
  const context = await browser.newContext({ locale: 'it-IT', viewport, serviceWorkers: 'block' });
  const page = await context.newPage();
  const report = [];
  const failures = [];

  for (const route of routes) {
    const networkErrors = [];
    const pageErrors = [];
    const consoleErrors = [];
    const routeFailures = [];
    const onResponse = response => {
      if (criticalAsset(response.url()) && response.status() >= 400) {
        const url = new URL(response.url());
        networkErrors.push(`${response.status()} ${url.origin}${url.pathname}`);
      }
    };
    const onPageError = error => pageErrors.push(error?.message || String(error));
    const onConsole = message => { if (message.type() === 'error') consoleErrors.push(message.text()); };
    page.on('response', onResponse);
    page.on('pageerror', onPageError);
    page.on('console', onConsole);

    const started = Date.now();
    let firstCardMs = null;
    let eventCards = null;
    let newsCards = null;
    let firstEvent = null;
    let firstNews = null;
    let metrics = null;

    const check = (condition, message) => { if (!condition) routeFailures.push(message); };

    try {
      const response = await page.goto(`${baseUrl}${route.path}?cv_audit=${Date.now()}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
      check(Boolean(response), `${label} ${route.path}: nessuna risposta`);
      if (response) check(response.status() < 400, `${label} ${route.path}: HTTP ${response.status()}`);

      try {
        await page.waitForFunction(expected => document.body.dataset.page === expected, route.page, { timeout: 10000 });
      } catch {
        routeFailures.push(`${label} ${route.path}: data-page atteso ${route.page}, trovato ${await page.locator('body').getAttribute('data-page')}`);
      }

      for (const selector of route.selectors) {
        try { await page.locator(selector).first().waitFor({ state: 'visible', timeout: 12000 }); }
        catch { routeFailures.push(`${label} ${route.path}: elemento non visibile ${selector}`); }
      }

      if (route.name === 'home') {
        await page.locator('.brand-logo').waitFor({ state: 'visible', timeout: 5000 }).catch(() => undefined);
        await auditCanonicalAssets(page, label, routeFailures);
      }

      if (route.name === 'blog') {
        const firstCard = page.locator('#blog-list article').first();
        try {
          await firstCard.waitFor({ state: 'visible', timeout: 4000 });
          firstCardMs = Date.now() - started;
          check(firstCardMs < 4000, `${label} Blog: prima card troppo lenta (${firstCardMs} ms)`);
          eventCards = await page.locator('#blog-list article').count();
          check(eventCards > 0, `${label} Blog: nessun Evento visibile`);
          firstEvent = {
            title: (await firstCard.locator('h3').textContent().catch(() => ''))?.trim() || '',
            meta: (await firstCard.locator('.eyebrow').textContent().catch(() => ''))?.trim() || '',
          };
        } catch {
          routeFailures.push(`${label} Blog: nessuna card Evento entro 4 secondi`);
        }
        check(await page.getByText('Caricamento contenuti…', { exact: true }).count() === 0, `${label} Blog: loader ancora visibile`);

        const newsTab = page.locator('[data-blog-lane="news"]');
        try {
          await newsTab.click();
          const firstNewsCard = page.locator('#blog-list article').first();
          await firstNewsCard.waitFor({ state: 'visible', timeout: 4000 });
          newsCards = await page.locator('#blog-list article').count();
          check(newsCards > 0, `${label} Blog: nessuna Notizia visibile`);
          check(await newsTab.getAttribute('aria-selected') === 'true', `${label} Blog: tab Notizie non selezionata logicamente`);
          firstNews = {
            title: (await firstNewsCard.locator('h3').textContent().catch(() => ''))?.trim() || '',
            meta: (await firstNewsCard.locator('.eyebrow').textContent().catch(() => ''))?.trim() || '',
          };
        } catch {
          routeFailures.push(`${label} Blog: tab Notizie o relative card non funzionanti`);
        }
      }

      if (route.name === 'catalogo') {
        await page.waitForTimeout(350);
        check(await page.locator('#results').isVisible().catch(() => false), `${label} Catalogo: risultati non visibili`);
        const countText = (await page.locator('#result-count').textContent().catch(() => ''))?.trim() || '';
        check(!/caricamento/i.test(countText), `${label} Catalogo: caricamento ancora visibile`);
      }

      if (route.name === 'mappa') {
        const box = await page.locator('#map').boundingBox().catch(() => null);
        check(Boolean(box && box.height >= 260), `${label} Mappa: altezza insufficiente`);
      }

      metrics = await page.evaluate(() => ({
        innerWidth: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        bodyScrollWidth: document.body.scrollWidth,
        h1: document.querySelector('h1')?.textContent?.trim() || '',
        bodyHeight: document.body.getBoundingClientRect().height,
        headerVisible: Boolean(document.querySelector('header')),
        footerVisible: Boolean(document.querySelector('footer')),
      }));
      const maxWidth = Math.max(metrics.scrollWidth, metrics.bodyScrollWidth);
      check(maxWidth <= metrics.innerWidth + 3, `${label} ${route.path}: overflow orizzontale ${maxWidth}px > ${metrics.innerWidth}px`);
      check(metrics.h1.length > 0, `${label} ${route.path}: H1 semantico assente o vuoto`);
      check(metrics.bodyHeight > 400, `${label} ${route.path}: pagina troppo bassa`);
      check(metrics.headerVisible, `${label} ${route.path}: header assente`);
      check(metrics.footerVisible, `${label} ${route.path}: footer assente`);

      await page.waitForTimeout(250);
      const severeConsole = consoleErrors.filter(text => /(?:Uncaught|TypeError|ReferenceError|SyntaxError|Hydration failed)/i.test(text));
      if (pageErrors.length) routeFailures.push(`${label} ${route.path}: page errors: ${pageErrors.join(' | ')}`);
      if (severeConsole.length) routeFailures.push(`${label} ${route.path}: console errors: ${severeConsole.join(' | ')}`);
      if (networkErrors.length) routeFailures.push(`${label} ${route.path}: asset critici falliti: ${networkErrors.join(', ')}`);
    } catch (error) {
      routeFailures.push(`${label} ${route.path}: ${error?.message || error}`);
    } finally {
      try { await page.screenshot({ path: `${outDir}/${label}-${route.name}.png`, fullPage: true }); } catch {}
      page.off('response', onResponse);
      page.off('pageerror', onPageError);
      page.off('console', onConsole);
    }

    const maxWidth = metrics ? Math.max(metrics.scrollWidth, metrics.bodyScrollWidth) : null;
    report.push({
      viewport: label,
      path: route.path,
      ok: routeFailures.length === 0,
      failures: routeFailures,
      h1: metrics?.h1 || '',
      width: metrics?.innerWidth || viewport.width,
      scrollWidth: maxWidth,
      bodyHeight: metrics ? Math.round(metrics.bodyHeight) : null,
      firstBlogCardMs: firstCardMs,
      eventCards,
      newsCards,
      firstEvent,
      firstNews,
      consoleErrorCount: consoleErrors.length,
      networkErrors,
    });
    failures.push(...routeFailures);
  }

  await context.close();
  return { report, failures };
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const desktop = await auditViewport(browser, 'desktop', { width: 1365, height: 900 });
    const mobile = await auditViewport(browser, 'mobile', { width: 390, height: 844 });
    const report = [...desktop.report, ...mobile.report];
    const failures = [...desktop.failures, ...mobile.failures];
    const result = { ok: failures.length === 0, failures, report };
    writeFileSync(`${outDir}/report.json`, JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result, null, 2));
    if (failures.length) throw new Error(`Audit produzione fallito (${failures.length} problemi):\n- ${failures.join('\n- ')}`);
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error?.stack || error);
  process.exitCode = 1;
});
