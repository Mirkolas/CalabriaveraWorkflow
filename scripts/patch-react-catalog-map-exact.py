from pathlib import Path
import re

root = Path('source/frontend-react')
copy_path = root / 'scripts/copy-legacy-assets.mjs'
map_path = root / 'src/pages/MapPage.tsx'

# --- Generate the same tourism dataset and CSS cascade used by main. ---
s = copy_path.read_text()
s = s.replace('import { fileURLToPath } from "node:url";', 'import { fileURLToPath, pathToFileURL } from "node:url";')

start = s.index('const tourismSource = resolve(repoRoot, "assets/js/tourism-data-core.js");')
end_marker = 'console.log(`Modulo turismo TypeScript generato: ${tourismTarget}`);'
end = s.index(end_marker, start) + len(end_marker)
new_tourism = r'''const tourismCoreSource = resolve(repoRoot, "assets/js/tourism-data-core.js");
const tourismExtraSource = resolve(repoRoot, "assets/js/tourism-data-extra.js");
const tourismImagesSource = resolve(repoRoot, "assets/js/tourism-image-map.js");
const generatedDir = resolve(reactRoot, "src/generated");
const tourismTarget = resolve(generatedDir, "tourism-data-core.ts");
for (const source of [tourismCoreSource, tourismExtraSource, tourismImagesSource]) {
  if (!existsSync(source)) throw new Error(`Asset turismo sorgente non trovato: ${source}`);
}
mkdirSync(generatedDir, { recursive: true });
const [coreTourism, extraTourism, imageMap] = await Promise.all([
  import(pathToFileURL(tourismCoreSource).href),
  import(pathToFileURL(tourismExtraSource).href),
  import(pathToFileURL(tourismImagesSource).href),
]);
const mergedTourism = [
  ...(coreTourism.TOURISM_BUSINESSES || []),
  ...(extraTourism.EXTRA_TOURISM_BUSINESSES || []),
].map((item) => imageMap.curateTourismImage(item));
const tourismIds = new Set();
for (const item of mergedTourism) {
  if (!item?.id || !item?.slug || !item?.name || !item?.comune || !item?.provincia) throw new Error(`Scheda turismo incompleta: ${item?.id || item?.name || "sconosciuta"}`);
  if (tourismIds.has(item.id)) throw new Error(`ID turismo duplicato: ${item.id}`);
  tourismIds.add(item.id);
}
if (mergedTourism.length !== 52) throw new Error(`Parità turismo inattesa: ${mergedTourism.length}, attese 52 schede del main`);
const tourismTs = `import type { Business } from "../types";\nexport const TOURISM_BUSINESSES: Business[] = ${JSON.stringify(mergedTourism, null, 2)};\nexport function tourismBusinessById(id: string) { return TOURISM_BUSINESSES.find((item) => item.id === id) || null; }\nexport function tourismBusinessBySlug(slug: string) { return TOURISM_BUSINESSES.find((item) => item.slug === slug) || null; }\n`;
writeFileSync(tourismTarget, tourismTs, "utf8");
console.log(`Modulo turismo TypeScript generato: ${tourismTarget} (${mergedTourism.length} schede curate)`);'''
s = s[:start] + new_tourism + s[end:]

route_start = s.index('const routeSources = {')
route_end_marker = 'console.log(`Parità route generata: ${Object.keys(routeCss).length} route, ${cssFiles.size} CSS main`);'
route_end = s.index(route_end_marker, route_start) + len(route_end_marker)
new_routes = r'''const routeSources = {
  "/": "index.html",
  "/catalogo": "catalogo.html",
  "/mappa": "mappa.html",
  "/blog": "blog.html",
  "/blog/:detail": "blog-articolo.html",
  "/attivita/:detail": "attivita.html",
  "/login": "login.html",
  "/registrazione": "registrazione.html",
  "/profilo": "profilo.html",
  "/preferiti": "preferiti.html",
  "/dashboard": "dashboard.html",
  "/messaggi": "messaggi.html",
  "/aggiungi-attivita": "aggiungi-attivita.html",
  "/chi-siamo": "chi-siamo.html",
  "/contatti": "contatti.html",
  "/privacy-policy": "privacy-policy.html",
  "/cookie-policy": "cookie-policy.html",
  "/termini": "termini.html",
  "/note-legali": "note-legali.html",
  "/backup": "backup.html",
  "/admin": "pages/admin/index.html",
  "/admin/attivita": "pages/admin/attivita.html",
  "/admin/recensioni": "pages/admin/recensioni.html",
  "/admin/segnalazioni": "pages/admin/segnalazioni.html",
  "/admin/blog": "pages/admin/blog.html",
  "/admin/categorie": "pages/admin/categorie.html",
  "/admin/comuni": "pages/admin/comuni.html",
  "/admin/utenti": "pages/admin/utenti.html",
  "/admin/messaggi": "pages/admin/messaggi.html",
  "/admin/comunicazioni": "pages/admin/comunicazioni.html",
  "/admin/seo": "pages/admin/seo.html",
  "/admin/sistema": "pages/admin/sistema.html",
  "/admin/impostazioni": "pages/admin/impostazioni.html",
  "/admin/backup": "pages/admin/backup.html",
};
const CORE_STYLES = [
  "/assets/css/figma-modern.css",
  "/assets/css/enhancements.css",
  "/assets/css/compact-modern.css",
  "/assets/css/ux-refine.css",
  "/assets/css/reference-replica.css",
  "/assets/css/redesign-runtime.css",
  "/assets/css/redesign-functional.css",
  "/assets/css/redesign-final.css",
  "/assets/css/responsive-polish.css",
  "/assets/css/authentic-local.css",
  "/assets/css/site-audit.css",
  "/assets/css/responsive-final.css",
  "/assets/css/device-polish.css",
  "/assets/css/language-modern.css",
  "/assets/css/platform-features.css",
  "/assets/css/responsive-hardening.css",
  "/assets/css/critical-shell.css",
  "/assets/css/growth-enhancements.css?v=20260903-growth-v1",
  "/assets/css/ui-final-overrides.css?v=20260905-activity-shell-v4",
  "/assets/css/header-unified.css?v=20260905-header-v2",
];
const PAGE_STYLES = {
  catalog: ["/assets/css/catalog-activity-cover.css?v=20260905-cover-v5"],
  business: ["/assets/css/business-detail.css?v=20260905-business-scope-v1"],
  messages: ["/assets/css/messages-v2.css"],
};
const liveParityCss = "/assets/css/react-live-parity.css";
const assetPath = (href) => String(href || "").split(/[?#]/, 1)[0];
const routeCss = {};
const routePages = {};
const cssFiles = new Set();
for (const [route, relative] of Object.entries(routeSources)) {
  const source = resolve(repoRoot, relative);
  if (!existsSync(source)) continue;
  const raw = readFileSync(source, "utf8");
  let styles = [...raw.matchAll(/<link\b[^>]*rel=["']stylesheet["'][^>]*href=["']([^"']+)["'][^>]*>/gi)]
    .map((match) => match[1])
    .filter((href) => href.startsWith("/assets/css/"));
  const page = raw.match(/<body\b[^>]*\bdata-page=["']([^"']+)["']/i)?.[1] || "";
  if (page) routePages[route] = page;
  for (const href of [...CORE_STYLES, ...(PAGE_STYLES[page] || []), liveParityCss]) {
    const pathOnly = assetPath(href);
    styles = styles.filter((current) => assetPath(current) !== pathOnly);
    styles.push(href);
  }
  routeCss[route] = styles;
  for (const href of styles) cssFiles.add(assetPath(href).slice(1));
}
for (const relative of cssFiles) {
  const source = resolve(repoRoot, relative);
  if (!existsSync(source)) {
    if (relative === "assets/css/react-live-parity.css") continue;
    throw new Error(`CSS main non trovato: ${source}`);
  }
  const target = resolve(reactRoot, "public", relative);
  mkdirSync(dirname(target), { recursive: true });
  copyFileSync(source, target);
}
const routeModule = `export const MAIN_ROUTE_CSS: Record<string, readonly string[]> = ${JSON.stringify(routeCss, null, 2)};\nexport const MAIN_ROUTE_PAGE: Record<string, string> = ${JSON.stringify(routePages, null, 2)};\n`;
writeFileSync(resolve(generatedDir, "main-route-css.ts"), routeModule, "utf8");
writeFileSync(resolve(reactRoot, "public/main-route-css.json"), JSON.stringify({ routeCss, routePages }), "utf8");
console.log(`Parità route generata: ${Object.keys(routeCss).length} route, ${cssFiles.size} CSS main con cascata finale produzione`);'''
s = s[:route_start] + new_routes + s[route_end:]
copy_path.write_text(s)

# --- Bring the React Map DOM and Leaflet controls in line with the live main. ---
m = map_path.read_text()

m = m.replace('  const [locationStatus, setLocationStatus] = useState("");', '  const [locationStatus, setLocationStatus] = useState("");\n  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);')

old_map_init = '''        const map = L.map(elementRef.current, { preferCanvas: true, zoomControl: true, attributionControl: true, fadeAnimation: false, zoomAnimation: true, markerZoomAnimation: false }).setView(CALABRIA_CENTER, 8);\n        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, minZoom: 6, attribution: "&copy; OpenStreetMap contributors", updateWhenIdle: true, updateWhenZooming: false, keepBuffer: 2, crossOrigin: true }).addTo(map);\n        const clusterFactory = (L as typeof L & { markerClusterGroup?: (options?: Record<string, unknown>) => import("leaflet").LayerGroup }).markerClusterGroup;\n        const layer = typeof clusterFactory === "function"\n          ? clusterFactory({ chunkedLoading: true, chunkInterval: 120, chunkDelay: 30, showCoverageOnHover: false, spiderfyOnMaxZoom: true, removeOutsideVisibleBounds: true, maxClusterRadius: 48, disableClusteringAtZoom: 15 })\n          : L.layerGroup();'''
new_map_init = '''        const map = L.map(elementRef.current, { preferCanvas: true, zoomControl: false, attributionControl: true, fadeAnimation: false, zoomAnimation: true, markerZoomAnimation: false }).setView(CALABRIA_CENTER, 8);\n        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, minZoom: 6, attribution: "&copy; OpenStreetMap contributors", updateWhenIdle: true, updateWhenZooming: false, keepBuffer: 2, crossOrigin: true }).addTo(map);\n        L.control.zoom({ position: "topright" }).addTo(map);\n        L.control.scale({ imperial: false, position: "bottomleft" }).addTo(map);\n        const clusterFactory = (L as typeof L & { markerClusterGroup?: (options?: Record<string, unknown>) => import("leaflet").LayerGroup }).markerClusterGroup;\n        const layer = typeof clusterFactory === "function"\n          ? clusterFactory({ chunkedLoading: true, chunkInterval: 120, chunkDelay: 30, showCoverageOnHover: false, spiderfyOnMaxZoom: true, removeOutsideVisibleBounds: true, maxClusterRadius: 48, disableClusteringAtZoom: 15, iconCreateFunction: (cluster: { getChildCount(): number }) => L.divIcon({ className: "cv-map-cluster-shell", html: `<span class="cv-map-cluster">${cluster.getChildCount()}</span>`, iconSize: [42, 42] }) })\n          : L.layerGroup();'''
if old_map_init not in m:
    raise SystemExit('Map init anchor not found')
m = m.replace(old_map_init, new_map_init, 1)

old_icon = '      const icon = L.divIcon({ className: "", html: `<span aria-hidden="true" style="display:block;width:16px;height:16px;border-radius:999px;background:${fill};border:3px solid #fff;box-shadow:0 2px 8px rgba(15,23,42,.28)"></span>`, iconSize: [16, 16], iconAnchor: [8, 8], popupAnchor: [0, -8] });'
new_icon = '      const icon = L.divIcon({ className: "cv-map-pin-shell", html: `<span aria-hidden="true" class="cv-map-pin${isTourism(business) ? " is-tourism" : business.verified ? " is-verified" : ""}" style="background:${fill};--cv-map-pin-color:${fill}"></span>`, iconSize: [30, 38], iconAnchor: [15, 36], popupAnchor: [0, -34] });'
if old_icon not in m:
    raise SystemExit('Map icon anchor not found')
m = m.replace(old_icon, new_icon, 1)

render_start = m.index('  return (\n    <section className="section container">')
render_end = m.rindex('\n  );\n}')
new_render = r'''  return (
    <section className="section container">
      <p className="eyebrow">CalabriaVera</p><h1>{uiText("mapTitle",language)}</h1>
      <div className="map-layout">
        <section>
          <div className="result-toolbar cv-map-toolbar">
            <span id="map-count" className="muted" aria-live="polite">{items===null?uiText("loadingBusinesses",language):`${filtered.length} ${language === "it" ? "attività sulla mappa" : copy.visible}`}</span>
            <span id="map-zoom" className="muted">{copy.zoom} {zoom}</span>
            <button id="map-fit-results" type="button" onClick={fitFiltered} className="button button-secondary" disabled={!mapReady || !filtered.length}>{language === "it" ? "Adatta risultati" : copy.fit}</button>
            <button id="map-mobile-filters" type="button" className="button button-primary cv-map-mobile-filter" aria-controls="map-panel" aria-expanded={mobileFiltersOpen} onClick={()=>setMobileFiltersOpen((value)=>!value)}>{language === "it" ? "Filtri" : uiText("filters",language)}</button>
          </div>
          <div id="map" ref={elementRef} className="leaflet-container" role="region" tabIndex={0} aria-busy={!mapReady} aria-label={language === "it" ? "Mappa interattiva delle attività in Calabria" : uiText("mapTitle",language)} />
          {mapError?<div className="notice">{copy.mapError}</div>:null}
        </section>
        <aside id="map-panel" className={mobileFiltersOpen?"is-open":undefined}>
          <div className="cv-map-aside-head"><div><strong>{language === "it" ? "Esplora sulla mappa" : uiText("mapTitle",language)}</strong><small>{language === "it" ? "Filtra le attività visualizzate" : uiText("mapFilterSub",language)}</small></div><button id="map-reset" type="button" className="button button-secondary" onClick={reset}>{language === "it" ? "Azzera" : uiText("reset",language)}</button></div>
          <form id="map-filters" className="filter-panel" onSubmit={(event)=>event.preventDefault()}><div className="stack">
            <label>{uiText("category",language)}<select id="category" value={category} onChange={(event)=>setCategory(event.target.value)}><option value="">{language === "it" ? "Tutte" : uiText("all",language)}</option>{categoryOptions.map((value)=><option key={value}>{value}</option>)}</select></label>
            <label>{uiText("province",language)}<select id="province" value={province} onChange={(event)=>{setProvince(event.target.value);setCity("")}}><option value="">{language === "it" ? "Tutte" : uiText("all",language)}</option>{PROVINCES.map((value)=><option key={value}>{value}</option>)}</select></label>
            <label>{uiText("city",language)}<select id="city" value={city} onChange={(event)=>setCity(event.target.value)}><option value="">{language === "it" ? "Tutte" : uiText("allCities",language)}</option>{cities.map((value)=><option key={value}>{value}</option>)}</select></label>
            <label>{uiText("service",language)}<input id="service" value={service} onChange={(event)=>setService(event.target.value)} /></label>
            <label><span><input id="verified" type="checkbox" checked={verified} onChange={(event)=>setVerified(event.target.checked)} /> <span>{uiText("verifiedOnly",language)}</span></span></label>
            <button type="submit" className="button button-primary">{language==="it"?"Applica":"Apply"}</button>
            <button id="use-location" type="button" onClick={locate} className="button button-secondary">{nearby?uiText("disableNearby",language):(language === "it" ? "Vicino a me" : uiText("nearby",language))}</button>
            <label>{language === "it" ? "Raggio vicino a me" : uiText("radius",language)}<select id="map-near-radius" value={radius} onChange={(event)=>setRadius(Number(event.target.value))}><option value="10">10 km</option><option value="25">25 km</option><option value="50">50 km</option><option value="100">100 km</option></select></label>
            {locationStatus?<span aria-live="polite" className="muted small">{locationStatus}</span>:null}
          </div></form>
          <div id="map-results" className="stack" style={{marginTop:12}} />
        </aside>
      </div>
    </section>
  );'''
m = m[:render_start] + new_render + m[render_end + len('\n  );'):]
map_path.write_text(m)

print('Applied exact main tourism/CSS cascade and Map DOM parity patch.')
