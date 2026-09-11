from pathlib import Path

root = Path('source')

# Generate the same final CSS cascade used by main, imported after React styles.
p = root / 'frontend-react/scripts/copy-legacy-assets.mjs'
s = p.read_text(encoding='utf-8')
if 'main-parity.css' not in s:
    s += r'''

const parityCssFiles = [
  "assets/css/variables.css",
  "assets/css/global.css",
  "assets/css/layout.css",
  "assets/css/components.css",
  "assets/css/responsive.css",
  "assets/css/enhancements.css",
  "assets/css/compact-modern.css",
  "assets/css/redesign-final.css",
  "assets/css/home-reference.css",
  "assets/css/catalog-activity-cover.css",
  "assets/css/map-clean.css",
  "assets/css/blog-sections.css",
];
const parityCssTarget = resolve(generatedDir, "main-parity.css");
const parityCss = parityCssFiles.map((relative) => {
  const source = resolve(repoRoot, relative);
  return existsSync(source) ? `\n/* source: ${relative} */\n${readFileSync(source, "utf8")}` : "";
}).join("\n");
writeFileSync(parityCssTarget, parityCss, "utf8");
console.log(`CSS parità main generato: ${parityCssTarget}`);
'''
p.write_text(s, encoding='utf-8')

p = root / 'frontend-react/src/main.tsx'
s = p.read_text(encoding='utf-8')
if 'generated/main-parity.css' not in s:
    s = s.replace('import "./styles.css";', 'import "./styles.css";\nimport "./generated/main-parity.css";', 1)
p.write_text(s, encoding='utf-8')

# Give final main CSS the same body page hooks it expects.
p = root / 'frontend-react/src/components/Layout.tsx'
s = p.read_text(encoding='utf-8')
marker = '  useEffect(() => { setMenuOpen(false); }, [snapshot]);'
body_effect = r'''  useEffect(() => {
    setMenuOpen(false);
    const page = cleanPath === "/" ? "home"
      : cleanPath === "/catalogo" ? "catalog"
      : cleanPath === "/mappa" ? "map"
      : cleanPath === "/blog" || cleanPath.startsWith("/blog/") ? "blog"
      : cleanPath === "/chi-siamo" ? "about"
      : cleanPath === "/contatti" ? "contacts"
      : cleanPath === "/privacy-policy" ? "privacy"
      : cleanPath === "/cookie-policy" ? "cookies"
      : cleanPath === "/termini" ? "terms"
      : cleanPath === "/note-legali" ? "legal"
      : cleanPath === "/attivita" || cleanPath.startsWith("/attivita/") ? "activities"
      : cleanPath === "/login" ? "login"
      : cleanPath === "/registrazione" ? "register"
      : cleanPath.replace(/^\//, "") || "app";
    document.body.dataset.page = page;
    return () => { if (document.body.dataset.page === page) delete document.body.dataset.page; };
  }, [snapshot, cleanPath]);'''
if marker in s:
    s = s.replace(marker, body_effect, 1)
elif 'document.body.dataset.page = page;' not in s:
    raise SystemExit('Layout page marker missing')
p.write_text(s, encoding='utf-8')

# Catalog card with the exact main activity-item DOM plus working React favorites.
p = root / 'frontend-react/src/components/LegacyCatalogCard.tsx'
p.write_text(r'''import { useEffect, useState } from "react";
import Link from "./Link";
import { businessImageUrl, businessPath, isFavorite, specificCategory, toggleFavorite } from "../lib/businesses";
import { localizedField, withLanguage, type Language } from "../lib/language";
import type { Business } from "../types";

type Point = { lat: number; lng: number } | null;
function distanceKm(point: Point, item: Business) {
  if (!point || !Number.isFinite(Number(item.lat)) || !Number.isFinite(Number(item.lng))) return Infinity;
  const rad=(v:number)=>v*Math.PI/180,dLat=rad(Number(item.lat)-point.lat),dLon=rad(Number(item.lng)-point.lng);
  const x=Math.sin(dLat/2)**2+Math.cos(rad(point.lat))*Math.cos(rad(Number(item.lat)))*Math.sin(dLon/2)**2;
  return 6371*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x));
}
const READ: Record<Language,string>={it:"Leggi tutto",en:"Read more",fr:"Lire la suite",de:"Mehr lesen",es:"Leer más"};

export default function LegacyCatalogCard({ business, index, language, date, point }: { business: Business; index: number; language: Language; date: string; point: Point }) {
  const [favorite,setFavorite]=useState(false),[busy,setBusy]=useState(false);
  useEffect(()=>{let alive=true;void isFavorite(business.id).then((value)=>{if(alive)setFavorite(value)}).catch(()=>undefined);return()=>{alive=false}},[business.id]);
  const title=localizedField<string>(business,"name",language)||business.name||"CalabriaVera";
  const description=localizedField<string>(business,"description",language)||business.description||"";
  const category=business.subcategory||business.category||specificCategory(business), image=businessImageUrl(business);
  const base=withLanguage(businessPath(business),language), href=date?`${base}${base.includes("?")?"&":"?"}data=${encodeURIComponent(date)}`:base;
  const km=distanceKm(point,business),price=Number(business.priceMin||0);
  const toggle=async(event: React.MouseEvent|React.KeyboardEvent)=>{event.preventDefault();event.stopPropagation();if(busy)return;if("key" in event&&event.key!=="Enter"&&event.key!==" ")return;setBusy(true);try{setFavorite(await toggleFavorite(business.id))}catch(error){if(error instanceof Error&&error.message==="AUTH_REQUIRED")location.assign(withLanguage(`/login?next=${encodeURIComponent(location.pathname+location.search)}`,language));}finally{setBusy(false)}};
  return <article className="activity-item">
    <span className="cv-heart" role="button" tabIndex={0} aria-label={`${favorite?"Rimuovi":"Aggiungi"} ${title} ${favorite?"dai":"ai"} preferiti`} aria-pressed={favorite} aria-busy={busy||undefined} data-favorite-id={business.id} onClick={(event)=>void toggle(event)} onKeyDown={(event)=>void toggle(event)}>{favorite?"♥":"♡"}</span>
    <div className="media-placeholder">{image?<Link href={href} aria-label={title}><img src={image} alt={title} loading={index<2?"eager":"lazy"} fetchPriority={index<2?"high":"low"} decoding="async" /></Link>:category}</div>
    <div><div className="meta-row"><span>{category}</span><span>·</span><span>{business.comune||""}</span>{Number.isFinite(km)?<span className="cv-distance">{km.toFixed(km<10?1:0)} km</span>:null}</div><h3><Link href={href}>{title}</Link></h3><p>{description}</p><div className="meta-row"><span>{business.rating?`${Number(business.rating).toFixed(1)} ★`:""}</span>{price?<span>da €{price.toLocaleString("it")}</span>:null}</div></div>
    <Link className="button button-secondary" href={href}>{READ[language]}</Link>
  </article>;
}
''', encoding='utf-8')

# Catalog: keep all React state/logic, replace only the final markup with main DOM/classes.
p = root / 'frontend-react/src/pages/CatalogPage.tsx'
s = p.read_text(encoding='utf-8')
s = s.replace('import BusinessCard from "../components/BusinessCard";', 'import LegacyCatalogCard from "../components/LegacyCatalogCard";')
start = s.index('  return (\n    <section className="mx-auto max-w-7xl')
end = s.rindex('\n  );\n}')
render = r'''  return (
    <section className="section container">
      <p className="eyebrow">CalabriaVera</p>
      <h1>{uiText("catalogTitle", language)}</h1>
      <div className="catalog-layout">
        <aside className="filter-panel">
          <form className="stack" onSubmit={(event)=>event.preventDefault()} onReset={(event)=>{event.preventDefault();reset();}}>
            <label>{uiText("what",language)}<input value={keyword} onChange={(event)=>setKeyword(event.target.value)} list="cv-catalog-suggestions" autoComplete="off" placeholder={uiText("searchWhatHint",language)} /></label>
            <datalist id="cv-catalog-suggestions">{suggestions.map((value)=><option key={value} value={value}/>)}</datalist>
            <span className="cv-smart-hint">Suggerimenti per nome, città e categoria; i risultati più pertinenti vengono mostrati prima.</span>
            <label>{uiText("category",language)}<select value={category} onChange={(event)=>setCategory(event.target.value)}><option value="">{uiText("all",language)}</option>{categoryOptions.map((value)=><option key={value}>{value}</option>)}</select></label>
            <label>{uiText("province",language)}<select value={province} onChange={(event)=>{setProvince(event.target.value);setCity("")}}><option value="">{uiText("all",language)}</option>{PROVINCES.map((value)=><option key={value}>{value}</option>)}</select></label>
            <label>{uiText("city",language)}<select value={city} onChange={(event)=>setCity(event.target.value)}><option value="">{uiText("allCities",language)}</option>{cities.map((value)=><option key={value}>{value}</option>)}</select></label>
            <label className="cv-catalog-extra">{uiText("date",language)} <span className="muted">({uiText("optional",language)})</span><input type="date" value={date} onChange={(event)=>setDate(event.target.value)}/></label>
            <label className="cv-catalog-extra">{uiText("service",language)}<input value={service} onChange={(event)=>setService(event.target.value)} /></label>
            <label className="cv-catalog-extra"><span><input type="checkbox" checked={verified} onChange={(event)=>setVerified(event.target.checked)} /> {uiText("verifiedOnly",language)}</span></label>
            <label>{uiText("sort",language)}<select value={sort} onChange={(event)=>setSort(event.target.value as Sort)}><option value="newest">{uiText("newest",language)}</option><option value="rating">{uiText("rating",language)}</option><option value="oldest">{uiText("oldest",language)}</option></select></label>
            <div className="cv-near-controls"><button type="button" className="button button-secondary" onClick={locate}>{nearby?uiText("disableNearby",language):uiText("nearby",language)}</button><label>{uiText("radius",language)}<select value={radius} onChange={(event)=>setRadius(Number(event.target.value))}><option value="10">10 km</option><option value="25">25 km</option><option value="50">50 km</option><option value="100">100 km</option></select></label></div>
            {locationStatus?<span className="cv-near-active" aria-live="polite">{locationStatus}</span>:null}
            <div className="filter-actions"><button className="button button-primary" type="submit">{language==="it"?"Applica":"Apply"}</button><button type="reset" className="button button-secondary">{uiText("reset",language)}</button></div>
          </form>
        </aside>
        <section>
          <div className="result-toolbar"><p aria-live="polite">{items===null?uiText("loadingBusinesses",language):`${filtered.length} ${language==="it"?"attività trovate":uiText("catalog",language)}`}</p><Link className="button button-secondary" href={withLanguage(`/mappa${mapParams.size?`?${mapParams}`:""}`,language)}>{language==="it"?"Mappa":uiText("map",language)}</Link></div>
          {items===null?<div className="notice">{uiText("loadingBusinesses",language)}</div>:filtered.length?<><div className="result-list" aria-live="polite">{filtered.slice(0,visible).map((business,index)=><LegacyCatalogCard key={business.id} business={business} index={index} language={language} date={date} point={nearby?userLocation:null}/>)}</div>{visible<filtered.length?<button type="button" onClick={()=>setVisible((value)=>value+PAGE_SIZE)} className="button button-secondary" style={{display:"flex",margin:"24px auto 0"}}>{uiText("loadMore",language)}</button>:null}</>:<div className="empty-state"><strong>{uiText("noResults",language)}</strong><p className="muted">{error?"Dati temporaneamente non disponibili.":uiText("tryFilters",language)}</p></div>}
        </section>
      </div>
    </section>
  );'''
s = s[:start] + render + s[end+len('\n  );'):]
p.write_text(s, encoding='utf-8')

# Map: exact main structural classes, same Leaflet React logic.
p = root / 'frontend-react/src/pages/MapPage.tsx'
s = p.read_text(encoding='utf-8')
start = s.index('  return (\n    <section className="mx-auto max-w-7xl')
end = s.rindex('\n  );\n}')
render = r'''  return (
    <section className="section container">
      <p className="eyebrow">CalabriaVera</p><h1>{uiText("mapTitle",language)}</h1>
      <div className="map-layout">
        <section><div className="result-toolbar"><span aria-live="polite">{items===null?uiText("loadingBusinesses",language):`${filtered.length} ${copy.visible}`}</span><span>{copy.zoom} {zoom}</span></div><div style={{position:"relative"}}><div id="map" ref={elementRef} className="leaflet-container" aria-label={uiText("mapTitle",language)} />{!mapReady&&!mapError?<div className="notice" style={{position:"absolute",left:"50%",top:20,transform:"translateX(-50%)",zIndex:500}}>{uiText("prepMap",language)}</div>:null}{mapError?<div className="notice" style={{position:"absolute",inset:20,zIndex:500}}>{copy.mapError}</div>:null}{mapReady&&filtered.length>0?<button type="button" onClick={fitFiltered} className="button button-secondary" style={{position:"absolute",left:16,bottom:16,zIndex:500}}>{copy.fit}</button>:null}</div></section>
        <aside><form className="filter-panel" onSubmit={(event)=>event.preventDefault()}><div className="stack"><label>{uiText("category",language)}<select value={category} onChange={(event)=>setCategory(event.target.value)}><option value="">{uiText("all",language)}</option>{categoryOptions.map((value)=><option key={value}>{value}</option>)}</select></label><label>{uiText("province",language)}<select value={province} onChange={(event)=>{setProvince(event.target.value);setCity("")}}><option value="">{uiText("all",language)}</option>{PROVINCES.map((value)=><option key={value}>{value}</option>)}</select></label><label>{uiText("city",language)}<select value={city} onChange={(event)=>setCity(event.target.value)}><option value="">{uiText("allCities",language)}</option>{cities.map((value)=><option key={value}>{value}</option>)}</select></label><label>{uiText("service",language)}<input value={service} onChange={(event)=>setService(event.target.value)} /></label><label><span><input type="checkbox" checked={verified} onChange={(event)=>setVerified(event.target.checked)} /> {uiText("verifiedOnly",language)}</span></label><button type="submit" className="button button-primary">{language==="it"?"Applica":"Apply"}</button><button type="button" onClick={locate} className="button button-secondary">{nearby?uiText("disableNearby",language):uiText("nearby",language)}</button><label>{uiText("radius",language)}<select value={radius} onChange={(event)=>setRadius(Number(event.target.value))}><option value="10">10 km</option><option value="25">25 km</option><option value="50">50 km</option><option value="100">100 km</option></select></label><button type="button" onClick={reset} className="button button-secondary">{uiText("reset",language)}</button>{locationStatus?<span aria-live="polite" className="muted small">{locationStatus}</span>:null}</div></form><div id="map-results">{filtered.slice(0,8).map((item)=><Link key={item.id} href={withLanguage(routeFor(item),language)} className="card"><h3>{localizedField<string>(item,"name",language)||item.name}</h3><p className="muted">{[item.comune,nearby&&userPoint?`${distanceKm(userPoint,item).toFixed(1)} km`:""].filter(Boolean).join(" · ")}</p></Link>)}</div></aside>
      </div>
    </section>
  );'''
s = s[:start] + render + s[end+len('\n  );'):]
p.write_text(s, encoding='utf-8')

# Blog: use article-hero/card-grid/blog-card DOM from main while preserving React lane filtering.
p = root / 'frontend-react/src/pages/MagazinePage.tsx'
s = p.read_text(encoding='utf-8')
start = s.index('  return (\n    <section className="mx-auto max-w-7xl')
end = s.rindex('\n  );\n}')
render = r'''  return (<>
    <section className="article-hero container"><p className="eyebrow">{uiText("magazineEyebrow",language)}</p><h1>{uiText("magazineTitle",language)}</h1><p className="prose">{uiText("magazineSub",language)}</p><div className="tabs" role="tablist" aria-label="Magazine"><button type="button" className={`tab ${lane==="events"?"active":""}`} onClick={()=>{setLane("events");setVisible(12)}}>{uiText("eventsLane",language)}</button><button type="button" className={`tab ${lane==="news"?"active":""}`} onClick={()=>{setLane("news");setVisible(12)}}>{uiText("news",language)}</button></div></section>
    <section className="section container">{posts===null?<div className="notice">{uiText("loadingBusinesses",language)}</div>:filtered.length?<><div id="blog-list" className="card-grid" aria-live="polite">{filtered.slice(0,visible).map((post,index)=>{const external=Boolean(post.externalUrl&&["external","social"].includes(String(post.origin||""))),title=localizedField<string>(post,"title",language)||post.title||"CalabriaVera",excerpt=localizedField<string>(post,"excerpt",language)||localizedField<string>(post,"description",language)||post.excerpt||post.description||"",href=external?String(post.externalUrl):withLanguage(`/blog/${encodeURIComponent(String(post.slug||post.id))}`,language);const card=<article className="blog-card"><div className="blog-media"><img src={magazineCover(post)} alt={title} loading={index<2?"eager":"lazy"} decoding="async" referrerPolicy="no-referrer"/></div><div className="body"><p className="eyebrow">{post.category||"Magazine"} · {formatDate(post,language)}</p><h3>{title}</h3><p>{excerpt}</p><span className="text-link">{external?uiText("readSource",language):uiText("readArticle",language)}</span></div></article>;return external?<a key={post.id} href={href} target="_blank" rel="noreferrer nofollow">{card}</a>:<Link key={post.id} href={href}>{card}</Link>})}</div>{visible<filtered.length?<button type="button" onClick={()=>setVisible((value)=>value+12)} className="button button-secondary" style={{display:"flex",margin:"24px auto 0"}}>{uiText("loadMagazine",language)}</button>:null}</>:<div className="notice">{uiText("noMagazine",language)}</div>}</section>
  </>);'''
s = s[:start] + render + s[end+len('\n  );'):]
p.write_text(s, encoding='utf-8')

# Keep React-only advanced catalog fields available without changing the main screenshot density.
p = root / 'frontend-react/src/styles.css'
s = p.read_text(encoding='utf-8')
if 'cv-main-dom-parity' not in s:
    s += r'''

/* cv-main-dom-parity */
body[data-page="catalog"] .cv-catalog-extra{display:none!important}
body[data-page="catalog"] .cv-smart-hint{font-size:10px;line-height:1.45;color:#607080;margin-top:-5px}
body[data-page="catalog"] .cv-near-controls{display:grid;grid-template-columns:1fr;gap:7px}
body[data-page="catalog"] .cv-near-controls label{display:grid;gap:5px}
body[data-page="blog"] .article-hero .tabs{margin-top:22px;border-bottom:0}
body[data-page="blog"] .article-hero .tab{color:#fff;border-color:transparent}.article-hero .tab.active{border-bottom-color:#ffb000}
'''
p.write_text(s, encoding='utf-8')

print('Exact main CSS cascade and Catalog/Map/Blog DOM parity applied')
