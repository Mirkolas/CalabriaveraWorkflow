const fs = require('node:fs');
const path = require('node:path');
const { chromium, request: apiRequest } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const MAIN=(process.env.MAIN_BASE_URL||'https://calabriavera.com').replace(/\/$/,'');
const REACT=(process.env.STAGING_BASE_URL||'https://calabriavera.sonotacamirko.workers.dev').replace(/\/$/,'');
const OUT=path.resolve(process.env.PARITY_OUT||'parity-audit-fast');
fs.mkdirSync(OUT,{recursive:true});

const publicRoutes=['/','/catalogo','/mappa','/blog','/attivita?turismo=centro-storico-di-tropea','/login','/registrazione','/chi-siamo','/contatti','/privacy-policy','/cookie-policy','/termini','/note-legali','/en/','/en/catalogo','/en/mappa','/en/blog','/fr/','/de/','/es/'];
const privateRoutes=['/profilo','/preferiti','/dashboard','/messaggi','/aggiungi-attivita'];
const adminRoutes=['/admin','/admin/attivita','/admin/recensioni','/admin/blog','/admin/categorie','/admin/comuni','/admin/utenti','/admin/messaggi','/admin/seo','/admin/impostazioni','/admin/backup'];
const legacyRedirects=new Map([
 ['/index.html','/'],['/catalogo.html','/catalogo'],['/mappa.html','/mappa'],['/blog.html','/blog'],['/login.html','/login'],['/registrazione.html','/registrazione'],['/profilo.html','/profilo'],['/preferiti.html','/preferiti'],['/dashboard.html','/dashboard'],['/messaggi.html','/messaggi'],['/aggiungi-attivita.html','/aggiungi-attivita'],['/chi-siamo.html','/chi-siamo'],['/contatti.html','/contatti'],['/privacy-policy.html','/privacy-policy'],['/cookie-policy.html','/cookie-policy'],['/termini.html','/termini'],['/note-legali.html','/note-legali'],['/pages/admin/index.html','/admin'],['/pages/admin/attivita.html','/admin/attivita']
]);

function cleanRoute(route){ return route.split('?')[0].replace(/^\/(?:en|fr|de|es)(?=\/|$)/,'')||'/'; }
function routeLang(route){ return route.match(/^\/(en|fr|de|es)(?=\/|$)/)?.[1]||'it'; }
function norm(v=''){return String(v).replace(/\u00a0/g,' ').replace(/\s+/g,' ').replace(/©\s*20\d{2}/g,'© YEAR').trim();}
function words(v=''){return new Set(norm(v).toLowerCase().split(/[^a-zà-ÿ0-9]+/i).filter(x=>x.length>2));}
function similarity(a,b){const A=words(a),B=words(b);if(!A.size&&!B.size)return 1;let n=0;for(const x of A)if(B.has(x))n++;return n/Math.max(1,new Set([...A,...B]).size);}
function controlsSignature(a){return a.map(x=>`${x.tag}:${x.type}:${x.name}:${x.required?'1':'0'}`).sort().join('|');}
function decodeHtml(v=''){return String(v).replace(/&nbsp;/gi,' ').replace(/&amp;/gi,'&').replace(/&quot;/gi,'"').replace(/&#39;|&apos;/gi,"'").replace(/&lt;/gi,'<').replace(/&gt;/gi,'>').replace(/&#(\d+);/g,(_,n)=>String.fromCodePoint(Number(n))).replace(/&#x([0-9a-f]+);/gi,(_,n)=>String.fromCodePoint(parseInt(n,16)));}
function htmlText(v=''){return norm(decodeHtml(String(v).replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,' ').replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi,' ').replace(/<[^>]+>/g,' ')));}

async function waitReady(page,route){
  const clean=cleanRoute(route);
  await page.waitForLoadState('domcontentloaded',{timeout:15000}).catch(()=>{});
  await page.evaluate(()=>document.fonts?.ready).catch(()=>{});
  if(clean==='/catalogo') await page.waitForFunction(()=>document.querySelectorAll('.activity-item').length>0 || /nessun risultato|0 attività/i.test(document.querySelector('main')?.innerText||''),null,{timeout:9000}).catch(()=>{});
  else if(clean==='/mappa') await page.waitForFunction(()=>document.querySelector('.leaflet-container') && (document.querySelector('.leaflet-control-zoom') || /impossibile inizializzare/i.test(document.querySelector('main')?.innerText||'')),null,{timeout:9000}).catch(()=>{});
  else if(clean==='/blog') await page.waitForFunction(()=>document.querySelectorAll('.blog-card').length>0 || /nessun|non ci sono|contenuti/i.test(document.querySelector('main')?.innerText||''),null,{timeout:9000}).catch(()=>{});
  else if(['/login','/registrazione','/chi-siamo','/contatti','/privacy-policy','/cookie-policy','/termini','/note-legali'].includes(clean)) await page.waitForSelector('main h1',{timeout:7000}).catch(()=>{});
  else await page.waitForSelector('main h1',{timeout:5000}).catch(()=>{});
  if(routeLang(route)!=='it' && clean==='/') await page.waitForTimeout(1400);
  await page.waitForTimeout(500);
}

async function inspect(page,base,route){
  const errors=[];
  const onPageError=e=>errors.push(`page:${e.message||e}`);
  const onConsole=m=>{if(m.type()==='error'){const t=m.text();if(!/favicon|ERR_BLOCKED_BY_CLIENT|Failed to load resource.*404.*tile|net::ERR_ABORTED/i.test(t))errors.push(`console:${t}`);}};
  page.on('pageerror',onPageError);page.on('console',onConsole);
  const response=await page.goto(base+route,{waitUntil:'domcontentloaded',timeout:18000}).catch(()=>null);
  await waitReady(page,route);
  const data=await page.evaluate(()=>{
    const main=document.querySelector('main')||document.body;
    const hero=document.querySelector('.cv-home-hero');
    const catalog=document.querySelector('.catalog-layout');
    const map=document.querySelector('.map-layout');
    const logo=document.querySelector('.brand-logo');
    const header=document.querySelector('.cv-header');
    const countText=[...main.querySelectorAll('*')].map(x=>x.childElementCount?null:(x.textContent||'').trim()).find(x=>/^\d+\s+attivit/i.test(x||''))||'';
    return {
      url:location.pathname+location.search,title:document.title,lang:document.documentElement.lang,
      h1:[...main.querySelectorAll('h1')].map(x=>x.textContent?.trim()||''),h2:[...main.querySelectorAll('h2')].map(x=>x.textContent?.trim()||''),mainText:main.innerText,bodyText:document.body.innerText,
      controls:[...main.querySelectorAll('input,select,textarea')].map(x=>({tag:x.tagName.toLowerCase(),type:x.getAttribute('type')||'',name:x.getAttribute('name')||x.id||'',required:x.hasAttribute('required')})),
      buttons:[...main.querySelectorAll('button')].map(x=>x.textContent?.trim()||'').filter(Boolean),links:[...main.querySelectorAll('a[href]')].map(x=>x.getAttribute('href')||'').filter(Boolean),
      overflow:Math.max(0,document.documentElement.scrollWidth-document.documentElement.clientWidth),favoriteButtons:document.querySelectorAll('[aria-pressed][aria-label*="preferit" i]').length,
      leaflet:Boolean(document.querySelector('.leaflet-container')),leafletControls:document.querySelectorAll('.leaflet-control-zoom').length,mapError:/impossibile inizializzare la mappa/i.test(main.innerText),
      activityCards:document.querySelectorAll('.activity-item').length,blogCards:document.querySelectorAll('.blog-card').length,catalogCount:countText,
      parityCss:[...document.querySelectorAll('link[data-cv-main-parity]')].map(x=>x.getAttribute('href')||''),
      computed:{heroBackground:hero?getComputedStyle(hero).backgroundImage:'',catalogDisplay:catalog?getComputedStyle(catalog).display:'',catalogColumns:catalog?getComputedStyle(catalog).gridTemplateColumns:'',mapDisplay:map?getComputedStyle(map).display:'',mapColumns:map?getComputedStyle(map).gridTemplateColumns:'',logoWidth:logo?Math.round(logo.getBoundingClientRect().width):0,headerHeight:header?Math.round(header.getBoundingClientRect().height):0},
    };
  }).catch(()=>({url:'',title:'',lang:'',h1:[],h2:[],mainText:'',bodyText:'',controls:[],buttons:[],links:[],overflow:999,favoriteButtons:0,leaflet:false,leafletControls:0,mapError:false,activityCards:0,blogCards:0,catalogCount:'',parityCss:[],computed:{}}));
  page.off('pageerror',onPageError);page.off('console',onConsole);
  return {...data,status:response?.status()||0,errors};
}

async function auditRoute(browser,route,viewport){
 const a=await browser.newContext({viewport}),b=await browser.newContext({viewport});const [pa,pb]=await Promise.all([a.newPage(),b.newPage()]);
 try{const [main,react]=await Promise.all([inspect(pa,MAIN,route),inspect(pb,REACT,route)]);return{route,viewport:`${viewport.width}x${viewport.height}`,main,react,sameH1:norm(main.h1.join('|'))===norm(react.h1.join('|')),sameControls:controlsSignature(main.controls)===controlsSignature(react.controls),textSimilarity:similarity(main.mainText,react.mainText)};}finally{await a.close();await b.close();}
}
async function screenshotPair(browser,route,label){for(const [name,base] of [['main',MAIN],['react',REACT]]){const c=await browser.newContext({viewport:{width:1365,height:900}}),p=await c.newPage();try{await inspect(p,base,route);await p.screenshot({path:path.join(OUT,`${label}-${name}.png`),fullPage:true});}finally{await c.close();}}}

function sourceLegalChecks(){
  const generatedPath=path.resolve('frontend-react/src/generated/legal-content.ts');
  const raw=fs.readFileSync(generatedPath,'utf8');
  const match=raw.match(/export const LEGAL_CONTENT = ([\s\S]*?) as const;/);
  if(!match)return{ok:false,failures:['generated legal content cannot be parsed']};
  const generated=JSON.parse(match[1]);const map={privacy:'privacy-policy.html',cookie:'cookie-policy.html',terms:'termini.html',legal:'note-legali.html',about:'chi-siamo.html'};const failures=[];
  for(const [kind,file] of Object.entries(map)){const html=fs.readFileSync(path.resolve(file),'utf8');const m=html.match(/<main\b[^>]*>([\s\S]*?)<\/main>/i);if(!m||htmlText(m[1])!==htmlText(generated[kind]?.html||''))failures.push(`${file}: generated source text differs`);}
  const contacts=htmlText(generated.contacts?.html||'');if(!/Contatti/i.test(contacts)||!/info\.calabriavera@gmail\.com/i.test(contacts)||!/347 997 5255/.test(contacts))failures.push('contatti: generated dynamic content incomplete');
  return{ok:!failures.length,failures};
}

(async()=>{
 const expected=process.env.EXPECTED_SHA||'';const browser=await chromium.launch({headless:true});const report={expectedSha:expected,main:MAIN,react:REACT,generatedAt:new Date().toISOString(),routes:[],redirects:[],specific:{}};
 try{
  for(let i=0;i<publicRoutes.length;i+=4){const batch=publicRoutes.slice(i,i+4);report.routes.push(...await Promise.all(batch.map(r=>auditRoute(browser,r,{width:1365,height:900}))));}
  for(const r of ['/','/catalogo','/mappa','/blog','/login','/chi-siamo'])report.routes.push(await auditRoute(browser,r,{width:390,height:844}));
  const ctx=await browser.newContext({viewport:{width:1200,height:800}}),p=await ctx.newPage();for(const r of [...privateRoutes,...adminRoutes]){const result=await inspect(p,REACT,r);report.routes.push({route:r,viewport:'1200x800',react:result,privateGate:true});}await ctx.close();
  const http=await apiRequest.newContext({baseURL:REACT,maxRedirects:0});
  for(const [from,to] of legacyRedirects){const r=await http.get(from,{maxRedirects:0}).catch(()=>null);report.redirects.push({from,to,status:r?.status()||0,location:r?.headers()?.location||''});}
  const unauth=await http.post('/api/images/upload',{headers:{'content-type':'image/webp','x-user-id':'anonymous','x-business-id':'anonymous'},data:Buffer.from('not-image')}).catch(()=>null);report.specific.unauthUploadStatus=unauth?.status()||0;
  for(const [key,url] of [['businesses','/legacy-data/public-businesses-v1.json'],['blog','/legacy-data/public-blog-v1.json']]){const r=await http.get(url);let count=-1;try{count=(await r.json()).items?.length??-1;}catch{}report.specific[`${key}SnapshotStatus`]=r.status();report.specific[`${key}SnapshotCount`]=count;}
  const htmlResponse=await http.get('/catalogo');const html=await htmlResponse.text();report.specific.serverParityCss=/data-cv-main-parity/.test(html)&&/catalog-activity-cover\.css/.test(html);
  await http.dispose();
  const check=await browser.newContext({viewport:{width:1365,height:900}}),cp=await check.newPage();
  const home=await inspect(cp,REACT,'/');const catalog=await inspect(cp,REACT,'/catalogo');const map=await inspect(cp,REACT,'/mappa');const blog=await inspect(cp,REACT,'/blog');const contacts=await inspect(cp,REACT,'/contatti');const register=await inspect(cp,REACT,'/registrazione');const privacy=await inspect(cp,REACT,'/privacy-policy');
  Object.assign(report.specific,{homeFavoriteButtons:home.favoriteButtons,catalogFavoriteButtons:catalog.favoriteButtons,catalogActivityCards:catalog.activityCards,catalogHasTourism:/Tropea|Sila|Scilla|Capo Colonna/i.test(catalog.mainText),mapLeaflet:map.leaflet,mapLeafletControls:map.leafletControls,mapError:map.mapError,mapHasTourism:/Tropea|Sila|Scilla|Capo Colonna/i.test(map.mainText),blogCards:blog.blogCards,contactsComplete:/Contatti/i.test(contacts.mainText)&&/info\.calabriavera@gmail\.com/i.test(contacts.mainText)&&/347 997 5255/.test(contacts.mainText),registerH1:norm(register.h1[0]||''),privacyComplete:/Titolare del trattamento/i.test(privacy.mainText)&&/15\. Aggiornamenti/i.test(privacy.mainText),sourceLegal:sourceLegalChecks()});await check.close();
  await screenshotPair(browser,'/','home');await screenshotPair(browser,'/catalogo','catalogo');await screenshotPair(browser,'/mappa','mappa');await screenshotPair(browser,'/privacy-policy','privacy');
 }finally{await browser.close();}
 const failures=[];
 for(const row of report.routes){const r=row.react;if(!r||!r.status||r.status>=400)failures.push(`${row.route}: React HTTP ${r?.status||0}`);if(r?.errors?.length)failures.push(`${row.route}: ${r.errors.join(' | ')}`);if((r?.overflow||0)>4)failures.push(`${row.route}: horizontal overflow ${r.overflow}px`);if(row.privateGate){const clean=(r.url||'').replace(/^\/(en|fr|de|es)(?=\/|$)/,'');if(!clean.startsWith('/login'))failures.push(`${row.route}: unauthenticated gate did not end at login (${r.url})`);continue;}
  const clean=cleanRoute(row.route),lang=routeLang(row.route);if(lang==='it'&&row.sameH1===false&&row.main.h1.length&&row.react.h1.length)failures.push(`${row.route}: H1 differs (${row.main.h1.join(' / ')} <> ${row.react.h1.join(' / ')})`);
  const min=clean==='/'?0.6:['/chi-siamo','/privacy-policy','/cookie-policy','/termini','/note-legali'].includes(clean)?0.75:0.15;if((row.textSimilarity??1)<min)failures.push(`${row.route}: text similarity ${(row.textSimilarity||0).toFixed(2)} < ${min}`);
 }
 for(const x of report.redirects){if(![301,302,307,308].includes(x.status))failures.push(`${x.from}: redirect status ${x.status}`);const target=new URL(x.location||'/',REACT).pathname;if(target!==x.to)failures.push(`${x.from}: redirect target ${target}, expected ${x.to}`);}
 const s=report.specific;
 if(s.unauthUploadStatus!==401)failures.push(`R2 unauth upload=${s.unauthUploadStatus}, expected 401`);
 if(!s.serverParityCss)failures.push('server HTML missing route parity CSS');
 if(s.homeFavoriteButtons<4)failures.push(`home favorite buttons=${s.homeFavoriteButtons}, expected >=4`);
 if(s.catalogFavoriteButtons<1||s.catalogActivityCards<1||!s.catalogHasTourism)failures.push('catalog functional markers incomplete');
 if(!s.mapLeaflet||s.mapLeafletControls<1||s.mapError||!s.mapHasTourism)failures.push(`map runtime incomplete (leaflet=${s.mapLeaflet}, controls=${s.mapLeafletControls}, error=${s.mapError})`);
 if(s.blogSnapshotStatus!==200||s.blogSnapshotCount<1||s.blogCards<1)failures.push(`blog snapshot/runtime incomplete (status=${s.blogSnapshotStatus}, count=${s.blogSnapshotCount}, cards=${s.blogCards})`);
 if(s.businessesSnapshotStatus!==200||s.businessesSnapshotCount<0)failures.push(`business snapshot endpoint invalid (status=${s.businessesSnapshotStatus}, count=${s.businessesSnapshotCount})`);
 if(!s.contactsComplete)failures.push('contacts page incomplete');if(s.registerH1!=='Crea il tuo account')failures.push(`register H1=${s.registerH1}`);if(!s.privacyComplete)failures.push('privacy page incomplete');if(!s.sourceLegal?.ok)failures.push(...(s.sourceLegal?.failures||['source legal parity failed']));
 report.failures=failures;fs.writeFileSync(path.join(OUT,'report.json'),JSON.stringify(report,null,2));fs.writeFileSync(path.join(OUT,'summary.txt'),failures.length?failures.join('\n'):'PARITY_GATE_GREEN');console.log(fs.readFileSync(path.join(OUT,'summary.txt'),'utf8'));console.log(`Checked ${report.routes.length} route/viewport cases, ${report.redirects.length} redirects.`);process.exitCode=failures.length?1:0;
})().catch(e=>{console.error(e);process.exit(1);});
