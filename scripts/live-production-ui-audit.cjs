const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const base = 'https://calabriavera.com';
const email = (process.env.SMOKE_TEST_EMAIL || '').trim();
const password = process.env.SMOKE_TEST_PASSWORD || '';
const out = path.resolve(process.env.AUDIT_OUT || 'live-audit');
fs.mkdirSync(out, { recursive: true });

async function main() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: 'it-IT', serviceWorkers: 'allow' });
  const page = await context.newPage();
  const failed = [];
  const pageErrors = [];
  page.on('response', (r) => {
    if (r.status() < 400) return;
    try {
      const u = new URL(r.url());
      if (u.hostname === 'calabriavera.com' || u.hostname === 'img.calabriavera.com' || u.hostname.endsWith('.web.app')) failed.push(`${r.status()} ${r.url()}`);
    } catch {}
  });
  page.on('pageerror', (e) => pageErrors.push(e.stack || e.message || String(e)));

  async function shot(name, fullPage = false) {
    await page.screenshot({ path: path.join(out, `${name}.png`), fullPage });
  }
  async function goto(route, selector) {
    const response = await page.goto(`${base}${route}`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    assert.ok(response && response.status() < 400, `${route}: HTTP ${response?.status()}`);
    if (selector) await page.locator(selector).first().waitFor({ state: 'visible', timeout: 20000 });
    await page.waitForTimeout(600);
  }
  async function monitorTransition(linkSelector, expectedPath, expectedPage) {
    await page.evaluate(() => {
      window.__cvTransitionSamples = [];
      window.__cvTransitionTimer = setInterval(() => {
        const logo = document.querySelector('.brand-logo');
        const r = logo?.getBoundingClientRect();
        window.__cvTransitionSamples.push({ w: r?.width || 0, h: r?.height || 0, loader: Boolean(document.querySelector('.cv-route-loader')) });
      }, 16);
    });
    await page.locator(linkSelector).first().click();
    await page.waitForURL((u) => u.pathname === expectedPath, { timeout: 15000 });
    if (expectedPage) await page.waitForFunction((p) => document.body.dataset.page === p, expectedPage, { timeout: 15000 });
    await page.waitForTimeout(650);
    const samples = await page.evaluate(() => { clearInterval(window.__cvTransitionTimer); return window.__cvTransitionSamples || []; });
    assert.ok(samples.length > 5, `${expectedPath}: campioni transizione insufficienti`);
    assert.ok(Math.max(...samples.map((s) => s.w)) <= 180, `${expectedPath}: flash logo gigante (${Math.max(...samples.map((s) => s.w))}px)`);
    assert.ok(Math.max(...samples.map((s) => s.h)) <= 90, `${expectedPath}: flash logo alto`);
    assert.equal(samples.some((s) => s.loader), false, `${expectedPath}: loader Suspense visibile durante la navigazione pubblica`);
  }

  try {
    const version = (await (await context.request.get(`${base}/build-version.txt?audit=${Date.now()}`)).text()).trim();
    assert.equal(version, '614900d278cdec25daafcda95a64f430e3548836', `build .com inattesa: ${version}`);

    await goto('/', '#cv-home-search');
    assert.equal(await page.locator('body').getAttribute('data-page'), 'home');
    const robots = await page.locator('meta[name="robots"]').getAttribute('content');
    assert.match(robots || '', /^index,follow/i, `Home robots inatteso: ${robots}`);
    const backgrounds = await page.locator('.cv-experience-card').evaluateAll((nodes) => nodes.slice(0, 4).map((n) => getComputedStyle(n).backgroundImage));
    assert.equal(backgrounds.length, 4, 'Home: card in evidenza mancanti');
    for (const bg of backgrounds) assert.ok(bg && bg !== 'none' && bg.includes('img.calabriavera.com'), `Home: background R2 non applicato: ${bg}`);
    await shot('01-home', true);

    const lang = page.locator('details[data-language-menu]');
    await lang.locator('summary').click();
    assert.equal(await lang.getAttribute('open'), '', 'Menu lingue non si apre');
    await lang.locator('.cv-language-list').waitFor({ state: 'visible', timeout: 5000 });
    await shot('02-language-menu');
    await lang.locator('summary').click();

    await monitorTransition('.primary-nav a[href="/catalogo"]', '/catalogo', 'catalog');
    await shot('03-catalogo');
    await monitorTransition('.primary-nav a[href="/mappa"]', '/mappa', 'map');
    await shot('04-mappa');
    await monitorTransition('.primary-nav a[href="/blog"]', '/blog', 'blog');
    await shot('05-blog');
    await monitorTransition('.primary-nav a[href="/chi-siamo"]', '/chi-siamo', 'about');
    await shot('06-chi-siamo');

    const clean = '/attivita/reggio-calabria/marina-di-gioiosa-ionica/b-e-b/le-ninfee-b-e-b';
    const dated = `${clean}2026-09-05`;
    const old = await context.request.get(`${base}${dated}`, { maxRedirects: 0 });
    assert.equal(old.status(), 301, `Slug con data: atteso 301, ottenuto ${old.status()}`);
    assert.ok((old.headers().location || '').endsWith(clean), `Redirect Le Ninfee errato: ${old.headers().location || ''}`);
    await goto(clean, '#business-root');
    const cover = page.locator('#business-cover img');
    await cover.waitFor({ state: 'visible', timeout: 15000 });
    await page.waitForFunction(() => { const i = document.querySelector('#business-cover img'); return i && i.complete && i.naturalWidth > 0; }, null, { timeout: 15000 });
    const coverInfo = await cover.evaluate((i) => ({ src: i.currentSrc || i.src, w: i.naturalWidth, h: i.naturalHeight }));
    assert.ok(coverInfo.w > 0 && coverInfo.src.includes('calabriavera-e08d4.web.app'), `Le Ninfee: cover legacy non risolta correttamente: ${JSON.stringify(coverInfo)}`);
    await shot('07-le-ninfee', true);

    if (email && password) {
      await goto('/login', '#auth-form');
      await page.locator('#auth-form input[name="email"]').fill(email);
      await page.locator('#auth-form input[name="password"]').fill(password);
      await page.locator('#auth-form button[type="submit"]').click();
      await page.waitForTimeout(1600);

      await goto('/messaggi', 'body');
      await page.waitForFunction(() => location.pathname === '/messaggi' || location.pathname === '/login', null, { timeout: 15000 });
      if (new URL(page.url()).pathname === '/messaggi') {
        await page.locator('#messages-root').waitFor({ state: 'visible', timeout: 20000 });
        await shot('08-messaggi', true);
      }

      await goto('/admin', 'body');
      await page.waitForTimeout(2200);
      if (new URL(page.url()).pathname.startsWith('/admin')) {
        const text = await page.locator('#admin-root').innerText().catch(() => '');
        assert.ok(text && !/Caricamento area amministrativa aggiornata/i.test(text), `Admin ancora fermo sul loader: ${text.slice(0, 200)}`);
        await shot('09-admin', true);
        const adminLink = page.locator('a[href="/admin/messaggi"], a[href$="/admin/messaggi"]');
        if (await adminLink.count()) {
          await page.goto(`${base}/admin/messaggi`, { waitUntil: 'domcontentloaded', timeout: 30000 });
          await page.waitForTimeout(3000);
          const crmText = await page.locator('#admin-root').innerText().catch(() => '');
          assert.ok(!/Caricamento centro messaggi e CRM/i.test(crmText), 'Admin Messaggi/CRM ancora bloccato sul caricamento');
          await shot('10-admin-messaggi', true);
        }
      }
    }

    const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, locale: 'it-IT', serviceWorkers: 'block' });
    const mp = await mobile.newPage();
    await mp.goto(`${base}/`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await mp.locator('#cv-home-search').waitFor({ state: 'visible', timeout: 20000 });
    await mp.locator('#menu-toggle').click();
    await mp.locator('#mobile-nav').waitFor({ state: 'visible', timeout: 5000 });
    await mp.screenshot({ path: path.join(out, '11-mobile-menu.png'), fullPage: false });
    await mobile.close();

    assert.deepEqual(failed, [], `Risorse produzione fallite:\n${failed.join('\n')}`);
    const relevantErrors = pageErrors.filter((x) => /calabriavera|firebase|TypeError|ReferenceError/i.test(x));
    assert.deepEqual(relevantErrors, [], `Errori JS produzione:\n${relevantErrors.join('\n---\n')}`);
    fs.writeFileSync(path.join(out, 'result.txt'), `PASS\nbuild=${version}\ncover=${JSON.stringify(coverInfo)}\n`, 'utf8');
    console.log('LIVE UI AUDIT PASS');
  } finally {
    await context.close();
    await browser.close();
  }
}
main().catch((e) => { console.error(e.stack || e); process.exitCode = 1; });
