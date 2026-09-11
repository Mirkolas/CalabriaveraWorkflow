const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const MAIN=(process.env.MAIN_BASE_URL||'https://calabriavera.com').replace(/\/$/,'');
const REACT=(process.env.STAGING_BASE_URL||'https://calabriavera.sonotacamirko.workers.dev').replace(/\/$/,'');
const OUT=path.resolve(process.env.PARITY_OUT||'parity-audit-fast');
fs.mkdirSync(OUT,{recursive:true});

function countFrom(text=''){ const m=String(text).match(/(\d+)\s+attivit/i); return m?Number(m[1]):-1; }

async function capture(browser, base, route, label){
  const context=await browser.newContext({viewport:{width:1365,height:900}});
  const page=await context.newPage();
  const errors=[];
  page.on('pageerror',e=>errors.push(`page:${e.message||e}`));
  page.on('console',m=>{ if(m.type()==='error'&&!/favicon|ERR_BLOCKED_BY_CLIENT|tile|net::ERR_ABORTED/i.test(m.text())) errors.push(`console:${m.text()}`); });
  const response=await page.goto(base+route,{waitUntil:'domcontentloaded',timeout:20000}).catch(()=>null);
  if(route==='/catalogo'){
    await page.waitForFunction(()=>/^\d+\s+attivit/i.test(document.querySelector('#result-count')?.textContent?.trim()||'') && document.querySelectorAll('#results>.activity-item').length>0,null,{timeout:12000}).catch(()=>{});
  }else{
    await page.waitForFunction(()=>/^\d+\s+attivit/i.test(document.querySelector('#map-count')?.textContent?.trim()||'') && document.querySelector('.leaflet-container') && document.querySelector('.leaflet-control-zoom'),null,{timeout:14000}).catch(()=>{});
  }
  await page.waitForTimeout(route==='/mappa'?2800:900);
  const data=await page.evaluate(()=>{
    const visible=(el)=>!!el&&getComputedStyle(el).display!=='none'&&getComputedStyle(el).visibility!=='hidden';
    const selectCount=(id)=>document.querySelector(`#${id}`)?.querySelectorAll('option').length||0;
    const text=(id)=>document.querySelector(`#${id}`)?.textContent?.replace(/\s+/g,' ').trim()||'';
    const map=document.querySelector('.leaflet-container');
    const mapLayout=document.querySelector('.map-layout');
    const catalogLayout=document.querySelector('.catalog-layout');
    return {
      resultCount:text('result-count'), mapCount:text('map-count'),
      activityCards:document.querySelectorAll('#results>.activity-item').length,
      categoryOptions:selectCount('category'), provinceOptions:selectCount('province'), cityOptions:selectCount('city'),
      catalogLayout:Boolean(catalogLayout), catalogColumns:catalogLayout?getComputedStyle(catalogLayout).gridTemplateColumns:'',
      mapLayout:Boolean(mapLayout), mapColumns:mapLayout?getComputedStyle(mapLayout).gridTemplateColumns:'',
      leaflet:Boolean(map), zoomControls:document.querySelectorAll('.leaflet-control-zoom').length, scaleControls:document.querySelectorAll('.leaflet-control-scale').length,
      clusters:document.querySelectorAll('.cv-map-cluster-shell').length, pins:document.querySelectorAll('.cv-map-pin-shell').length,
      mapPanel:Boolean(document.querySelector('#map-panel')), fitButton:Boolean(document.querySelector('#map-fit-results')), mobileFilterButton:Boolean(document.querySelector('#map-mobile-filters')),
      serviceVisible:visible(document.querySelector('#service')), verifiedVisible:visible(document.querySelector('#verified')), mapResultsVisible:visible(document.querySelector('#map-results')),
      overflow:Math.max(0,document.documentElement.scrollWidth-document.documentElement.clientWidth),
    };
  });
  await page.screenshot({path:path.join(OUT,`${label}.png`),fullPage:true});
  await context.close();
  return {...data,status:response?.status()||0,errors,count:countFrom(route==='/catalogo'?data.resultCount:data.mapCount)};
}

(async()=>{
  const browser=await chromium.launch({headless:true});
  let mainCatalog,reactCatalog,mainMap,reactMap;
  try{
    [mainCatalog,reactCatalog]=await Promise.all([
      capture(browser,MAIN,'/catalogo','catalog-exact-main'),
      capture(browser,REACT,'/catalogo','catalog-exact-react'),
    ]);
    [mainMap,reactMap]=await Promise.all([
      capture(browser,MAIN,'/mappa','map-exact-main'),
      capture(browser,REACT,'/mappa','map-exact-react'),
    ]);
  } finally { await browser.close(); }
  const report={generatedAt:new Date().toISOString(),main:MAIN,react:REACT,mainCatalog,reactCatalog,mainMap,reactMap,failures:[]};
  const f=report.failures;
  for(const [name,row] of Object.entries({mainCatalog,reactCatalog,mainMap,reactMap})){
    if(row.status!==200) f.push(`${name}: HTTP ${row.status}`);
    if(row.errors.length) f.push(`${name}: ${row.errors.join(' | ')}`);
    if(row.overflow>4) f.push(`${name}: horizontal overflow ${row.overflow}px`);
  }
  if(mainCatalog.count<52||reactCatalog.count!==mainCatalog.count) f.push(`catalog total mismatch main=${mainCatalog.count} react=${reactCatalog.count}`);
  if(mainCatalog.activityCards!==reactCatalog.activityCards||reactCatalog.activityCards!==Math.min(18,reactCatalog.count)) f.push(`catalog initial cards mismatch main=${mainCatalog.activityCards} react=${reactCatalog.activityCards}`);
  for(const key of ['categoryOptions','provinceOptions','cityOptions']) if(mainCatalog[key]!==reactCatalog[key]) f.push(`catalog ${key} mismatch main=${mainCatalog[key]} react=${reactCatalog[key]}`);
  if(reactCatalog.categoryOptions!==11||reactCatalog.provinceOptions!==6||reactCatalog.cityOptions!==117) f.push(`catalog options unexpected category=${reactCatalog.categoryOptions} province=${reactCatalog.provinceOptions} city=${reactCatalog.cityOptions}`);
  if(!reactCatalog.catalogLayout) f.push('catalog layout missing');
  if(mainMap.count<52||reactMap.count!==mainMap.count) f.push(`map total mismatch main=${mainMap.count} react=${reactMap.count}`);
  for(const key of ['categoryOptions','provinceOptions','cityOptions']) if(mainMap[key]!==reactMap[key]) f.push(`map ${key} mismatch main=${mainMap[key]} react=${reactMap[key]}`);
  if(reactMap.categoryOptions!==11||reactMap.provinceOptions!==6||reactMap.cityOptions!==117) f.push(`map options unexpected category=${reactMap.categoryOptions} province=${reactMap.provinceOptions} city=${reactMap.cityOptions}`);
  if(!reactMap.leaflet||reactMap.zoomControls<1||reactMap.scaleControls<1) f.push(`map controls incomplete leaflet=${reactMap.leaflet} zoom=${reactMap.zoomControls} scale=${reactMap.scaleControls}`);
  if(reactMap.clusters<1||reactMap.pins<1) f.push(`map marker shell incomplete clusters=${reactMap.clusters} pins=${reactMap.pins}`);
  if(!reactMap.mapPanel||!reactMap.fitButton||!reactMap.mobileFilterButton) f.push('map toolbar/sidebar DOM incomplete');
  if(reactMap.serviceVisible||reactMap.verifiedVisible||reactMap.mapResultsVisible) f.push(`map hidden controls differ service=${reactMap.serviceVisible} verified=${reactMap.verifiedVisible} results=${reactMap.mapResultsVisible}`);
  fs.writeFileSync(path.join(OUT,'catalog-map-exact.json'),JSON.stringify(report,null,2));
  console.log(f.length?f.join('\n'):'CATALOG_MAP_EXACT_GREEN');
  process.exitCode=f.length?1:0;
})().catch(e=>{console.error(e);process.exit(1);});
