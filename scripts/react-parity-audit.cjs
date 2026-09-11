const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const MAIN = (process.env.MAIN_BASE_URL || 'https://calabriavera.com').replace(/\/$/, '');
const REACT = (process.env.STAGING_BASE_URL || 'https://calabriavera.sonotacamirko.workers.dev').replace(/\/$/, '');
const OUT = path.resolve(process.env.PARITY_OUT || 'parity-audit-fast');
fs.mkdirSync(OUT, { recursive: true });

const publicRoutes = [
  '/', '/catalogo', '/mappa', '/blog', '/attivita?turismo=centro-storico-di-tropea',
  '/login', '/registrazione', '/chi-siamo', '/contatti', '/privacy-policy', '/cookie-policy', '/termini', '/note-legali',
  '/en/', '/en/catalogo', '/en/mappa', '/en/blog', '/fr/', '/de/', '/es/'
];
const privateRoutes = ['/profilo', '/preferiti', '/dashboard', '/messaggi', '/aggiungi-attivita'];
const adminRoutes = ['/admin', '/admin/attivita', '/admin/recensioni', '/admin/blog', '/admin/categorie', '/admin/comuni', '/admin/utenti', '/admin/messaggi', '/admin/seo', '/admin/impostazioni', '/admin/backup'];
const legacyRedirects = new Map([
  ['/index.html', '/'], ['/catalogo.html', '/catalogo'], ['/mappa.html', '/mappa'], ['/blog.html', '/blog'],
  ['/login.html', '/login'], ['/registrazione.html', '/registrazione'], ['/profilo.html', '/profilo'], ['/preferiti.html', '/preferiti'],
  ['/dashboard.html', '/dashboard'], ['/messaggi.html', '/messaggi'], ['/aggiungi-attivita.html', '/aggiungi-attivita'],
  ['/chi-siamo.html', '/chi-siamo'], ['/contatti.html', '/contatti'], ['/privacy-policy.html', '/privacy-policy'],
  ['/cookie-policy.html', '/cookie-policy'], ['/termini.html', '/termini'], ['/note-legali.html', '/note-legali'],
  ['/pages/admin/index.html', '/admin'], ['/pages/admin/attivita.html', '/admin/attivita']
]);
const exactContentRoutes = new Set(['/chi-siamo','/contatti','/privacy-policy','/cookie-policy','/termini','/note-legali']);

function norm(value='') {
  return String(value).replace(/\u00a0/g,' ').replace(/\s+/g,' ').replace(/©\s*20\d{2}/g,'© YEAR').trim();
}
function words(value='') {
  return new Set(norm(value).toLowerCase().split(/[^a-zà-ÿ0-9]+/i).filter(v => v.length > 2));
}
function similarity(a,b) {
  const A=words(a), B=words(b); if (!A.size && !B.size) return 1;
  let common=0; for (const x of A) if (B.has(x)) common++;
  return common / Math.max(1, new Set([...A,...B]).size);
}
function controlsSignature(controls) {
  return controls.map(x => `${x.tag}:${x.type}:${x.name}:${x.required?'1':'0'}`).sort().join('|');
}

async function settle(page) {
  await page.waitForLoadState('domcontentloaded', { timeout: 12000 }).catch(()=>{});
  await page.evaluate(() => document.fonts?.ready).catch(()=>{});
  await page.waitForTimeout(700);
}

async function inspect(page, base, route) {
  const errors=[];
  const onPageError=e=>errors.push(`page:${e.message || e}`);
  const onConsole=m=>{ if (m.type()==='error') { const t=m.text(); if (!/favicon|ERR_BLOCKED_BY_CLIENT|Failed to load resource.*404.*tile|net::ERR_ABORTED/i.test(t)) errors.push(`console:${t}`); } };
  page.on('pageerror',onPageError); page.on('console',onConsole);
  const response=await page.goto(base+route,{waitUntil:'domcontentloaded',timeout:15000}).catch(()=>null);
  await settle(page);
  const data=await page.evaluate(()=>{
    const main=document.querySelector('main') || document.body;
    return {
      url: location.pathname + location.search,
      title: document.title,
      lang: document.documentElement.lang,
      h1:[...main.querySelectorAll('h1')].map(x=>x.textContent?.trim()||''),
      h2:[...main.querySelectorAll('h2')].map(x=>x.textContent?.trim()||''),
      mainText: main.innerText,
      bodyText: document.body.innerText,
      controls:[...main.querySelectorAll('input,select,textarea')].map(x=>({tag:x.tagName.toLowerCase(),type:x.getAttribute('type')||'',name:x.getAttribute('name')||x.id||'',required:x.hasAttribute('required')})),
      buttons:[...main.querySelectorAll('button')].map(x=>x.textContent?.trim()||'').filter(Boolean),
      links:[...main.querySelectorAll('a[href]')].map(x=>x.getAttribute('href')||'').filter(Boolean),
      overflow: Math.max(0, document.documentElement.scrollWidth-document.documentElement.clientWidth),
      favoriteButtons: document.querySelectorAll('[aria-pressed][aria-label*="preferit" i]').length,
      leaflet: Boolean(document.querySelector('.leaflet-container')),
      root: Boolean(document.querySelector('#root')),
    };
  }).catch(()=>({url:'',title:'',lang:'',h1:[],h2:[],mainText:'',bodyText:'',controls:[],buttons:[],links:[],overflow:999,favoriteButtons:0,leaflet:false,root:false}));
  page.off('pageerror',onPageError); page.off('console',onConsole);
  return {...data,status:response?.status()||0,errors};
}

async function auditRoute(browser, route, viewport) {
  const mainCtx=await browser.newContext({viewport});
  const reactCtx=await browser.newContext({viewport});
  const [mainPage,reactPage]=await Promise.all([mainCtx.newPage(),reactCtx.newPage()]);
  try {
    const [main,react]=await Promise.all([inspect(mainPage,MAIN,route),inspect(reactPage,REACT,route)]);
    const contentSimilarity=similarity(main.mainText,react.mainText);
    return {
      route,viewport:`${viewport.width}x${viewport.height}`,main,react,
      sameH1:norm(main.h1.join('|'))===norm(react.h1.join('|')),
      sameControls:controlsSignature(main.controls)===controlsSignature(react.controls),
      textSimilarity:contentSimilarity,
      exactMainText: exactContentRoutes.has(route) ? norm(main.mainText)===norm(react.mainText) : undefined,
    };
  } finally { await mainCtx.close(); await reactCtx.close(); }
}

async function screenshotPair(browser, route, label) {
  const viewport={width:1365,height:900};
  for (const [name,base] of [['main',MAIN],['react',REACT]]) {
    const ctx=await browser.newContext({viewport}); const page=await ctx.newPage();
    try { await inspect(page,base,route); await page.screenshot({path:path.join(OUT,`${label}-${name}.png`),fullPage:true}); }
    finally { await ctx.close(); }
  }
}

(async()=>{
  const expected=process.env.EXPECTED_SHA||'';
  const browser=await chromium.launch({headless:true});
  const report={expectedSha:expected,main:MAIN,react:REACT,generatedAt:new Date().toISOString(),routes:[],redirects:[],specific:{}};
  try {
    // Four workers keeps the audit fast while avoiding excessive load on production.
    for (let i=0;i<publicRoutes.length;i+=4) {
      const batch=publicRoutes.slice(i,i+4);
      report.routes.push(...await Promise.all(batch.map(route=>auditRoute(browser,route,{width:1365,height:900}))));
    }
    for (const route of ['/', '/catalogo','/mappa','/blog','/login','/chi-siamo']) {
      report.routes.push(await auditRoute(browser,route,{width:390,height:844}));
    }

    const ctx=await browser.newContext({viewport:{width:1200,height:800}}); const page=await ctx.newPage();
    for (const route of [...privateRoutes,...adminRoutes]) {
      const result=await inspect(page,REACT,route);
      report.routes.push({route,viewport:'1200x800',react:result,privateGate:true});
    }
    await ctx.close();

    const request=await browser.request.newContext({baseURL:REACT,maxRedirects:0});
    for (const [from,to] of legacyRedirects) {
      const r=await request.get(from,{maxRedirects:0}).catch(()=>null);
      report.redirects.push({from,to,status:r?.status()||0,location:r?.headers()?.location||''});
    }
    const unauth=await request.post('/api/images/upload',{headers:{'content-type':'image/webp','x-user-id':'anonymous','x-business-id':'anonymous'},data:Buffer.from('not-image')}).catch(()=>null);
    report.specific.unauthUploadStatus=unauth?.status()||0;
    await request.dispose();

    // Functional markers in the current React deployment.
    const checkCtx=await browser.newContext({viewport:{width:1365,height:900}}); const p=await checkCtx.newPage();
    const home=await inspect(p,REACT,'/');
    report.specific.homeFavoriteButtons=home.favoriteButtons;
    const catalog=await inspect(p,REACT,'/catalogo');
    report.specific.catalogFavoriteButtons=catalog.favoriteButtons;
    report.specific.catalogHasTourism=/Tropea|Sila|Scilla|Capo Colonna/i.test(catalog.mainText);
    const map=await inspect(p,REACT,'/mappa');
    report.specific.mapLeaflet=map.leaflet;
    report.specific.mapHasTourism=/Tropea|Sila|Scilla|Capo Colonna/i.test(map.mainText);
    const privacy=await inspect(p,REACT,'/privacy-policy');
    report.specific.privacyComplete=/Titolare del trattamento/i.test(privacy.mainText) && /15\. Aggiornamenti/i.test(privacy.mainText);
    await checkCtx.close();

    await screenshotPair(browser,'/','home');
    await screenshotPair(browser,'/catalogo','catalogo');
    await screenshotPair(browser,'/privacy-policy','privacy');
  } finally { await browser.close(); }

  const failures=[];
  for (const row of report.routes) {
    const r=row.react;
    if (!r || !r.status || r.status>=400) failures.push(`${row.route}: React HTTP ${r?.status||0}`);
    if (r?.errors?.length) failures.push(`${row.route}: ${r.errors.join(' | ')}`);
    if ((r?.overflow||0)>4) failures.push(`${row.route}: horizontal overflow ${r.overflow}px`);
    if (!row.privateGate) {
      if (row.sameH1===false) failures.push(`${row.route}: H1 differs (${row.main.h1.join(' / ')} <> ${row.react.h1.join(' / ')})`);
      if ((row.textSimilarity??1)<0.45) failures.push(`${row.route}: text similarity ${(row.textSimilarity||0).toFixed(2)}`);
      if (row.exactMainText===false) failures.push(`${row.route}: exact main content differs`);
    } else {
      const clean=(r.url||'').replace(/^\/(en|fr|de|es)(?=\/|$)/,'');
      if (!clean.startsWith('/login')) failures.push(`${row.route}: unauthenticated gate did not end at login (${r.url})`);
    }
  }
  for (const item of report.redirects) {
    if (![301,302,307,308].includes(item.status)) failures.push(`${item.from}: redirect status ${item.status}`);
    const target=new URL(item.location||'/',REACT).pathname;
    if (target!==item.to) failures.push(`${item.from}: redirect target ${target}, expected ${item.to}`);
  }
  if (report.specific.unauthUploadStatus!==401) failures.push(`R2 unauth upload=${report.specific.unauthUploadStatus}, expected 401`);
  if (report.specific.homeFavoriteButtons<4) failures.push(`home favorite buttons=${report.specific.homeFavoriteButtons}, expected >=4`);
  if (report.specific.catalogFavoriteButtons<1) failures.push(`catalog favorite buttons=${report.specific.catalogFavoriteButtons}, expected >=1`);
  if (!report.specific.catalogHasTourism) failures.push('catalog missing static tourism entries');
  if (!report.specific.mapLeaflet) failures.push('map missing Leaflet');
  if (!report.specific.mapHasTourism) failures.push('map missing static tourism entries');
  if (!report.specific.privacyComplete) failures.push('privacy page is not the complete main version');

  report.failures=failures;
  fs.writeFileSync(path.join(OUT,'report.json'),JSON.stringify(report,null,2));
  fs.writeFileSync(path.join(OUT,'summary.txt'),failures.length?failures.join('\n'):'PARITY_GATE_GREEN');
  console.log(fs.readFileSync(path.join(OUT,'summary.txt'),'utf8'));
  console.log(`Checked ${report.routes.length} route/viewport cases, ${report.redirects.length} legacy redirects.`);
  process.exitCode=failures.length?1:0;
})().catch(error=>{console.error(error);process.exit(1);});
