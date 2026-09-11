from pathlib import Path

root = Path('source')

# 1) Build a route CSS manifest that prerender can consume, and include the runtime language stylesheet used by main.
p = root / 'frontend-react/scripts/copy-legacy-assets.mjs'
s = p.read_text(encoding='utf-8')
needle = 'const routeModule = `export const MAIN_ROUTE_CSS: Record<string, readonly string[]> = ${JSON.stringify(routeCss, null, 2)};\\nexport const MAIN_ROUTE_PAGE: Record<string, string> = ${JSON.stringify(routePages, null, 2)};\\n`;\nwriteFileSync(resolve(generatedDir, "main-route-css.ts"), routeModule, "utf8");\nconsole.log(`Parità route generata: ${Object.keys(routeCss).length} route, ${cssFiles.size} CSS main`);'
replacement = '''const languageCss = "/assets/css/language-modern.css";\nconst languageSource = resolve(repoRoot, languageCss.slice(1));\nif (existsSync(languageSource)) {\n  const languageTarget = resolve(reactRoot, "public", languageCss.slice(1));\n  mkdirSync(dirname(languageTarget), { recursive: true });\n  copyFileSync(languageSource, languageTarget);\n  for (const styles of Object.values(routeCss)) if (!styles.includes(languageCss)) styles.push(languageCss);\n}\nconst routeModule = `export const MAIN_ROUTE_CSS: Record<string, readonly string[]> = ${JSON.stringify(routeCss, null, 2)};\\nexport const MAIN_ROUTE_PAGE: Record<string, string> = ${JSON.stringify(routePages, null, 2)};\\n`;\nwriteFileSync(resolve(generatedDir, "main-route-css.ts"), routeModule, "utf8");\nwriteFileSync(resolve(reactRoot, "public/main-route-css.json"), JSON.stringify({ routeCss, routePages }), "utf8");\nconsole.log(`Parità route generata: ${Object.keys(routeCss).length} route, ${cssFiles.size} CSS main`);'''
if needle not in s:
    raise SystemExit('copy route manifest marker missing')
s = s.replace(needle, replacement, 1)
p.write_text(s, encoding='utf-8')

# 2) Put exact legacy route CSS directly in prerendered HTML, not only after hydration.
p = root / 'frontend-react/scripts/prerender-home.mjs'
s = p.read_text(encoding='utf-8')
s = s.replace('const serverEntry = resolve(ssr, "entry-server.js");\n', 'const serverEntry = resolve(ssr, "entry-server.js");\nconst routeCssManifestPath = resolve(root, "public/main-route-css.json");\nlet routeCss = {};\n', 1)
old = 'function withRoot(template, markup, page, scripts = "") {\n  let html = template.replace(/<html\\s+lang=["\'][^"\']+["\']>/i, `<html lang="${page.lang}">`);'
new = '''function withRoot(template, markup, page, scripts = "") {\n  let html = template.replace(/<html\\s+lang=["\'][^"\']+["\']>/i, `<html lang="${page.lang}">`);\n  const cleanRoute = page.path.replace(/^\\/(?:en|fr|de|es)(?=\\/|$)/, "") || "/";\n  const routeKey = cleanRoute === "/" ? "/" : cleanRoute.replace(/\\/$/, "");\n  const parityLinks = (routeCss[routeKey] || []).map((href) => `<link rel="stylesheet" href="${href}" data-cv-main-parity>`).join("");\n  if (parityLinks) html = html.replace("</head>", `${parityLinks}</head>`);'''
if old not in s:
    raise SystemExit('prerender withRoot marker missing')
s = s.replace(old, new, 1)
needle = 'const template = await readFile(templatePath, "utf8");\nawait writeFile(resolve(dist, "app-shell.html"), template, "utf8");'
replacement = 'const template = await readFile(templatePath, "utf8");\nrouteCss = JSON.parse(await readFile(routeCssManifestPath, "utf8")).routeCss || {};\nawait writeFile(resolve(dist, "app-shell.html"), template, "utf8");'
if needle not in s:
    raise SystemExit('prerender template marker missing')
s = s.replace(needle, replacement, 1)
# German SEO first paint copy: exact main wording.
s = s.replace('homeTitle: "CalabriaVera | Betriebe und Orte in Kalabrien", homeDescription: "Meer, Dörfer, Wege, Museen, Genuss und lokale Betriebe: nützliche Informationen für die Planung vor Ort."', 'homeTitle: "CalabriaVera | Aktivitäten und Orte in Kalabrien", homeDescription: "Meer, Dörfer, Wege, Museen, Kulinarik und lokale Betriebe: nützliche Informationen für die Wahl von Ziel und Aktivität."')
p.write_text(s, encoding='utf-8')

# 3) Leaflet markercluster extends the default Leaflet object, not Vite's module namespace.
p = root / 'frontend-react/src/pages/MapPage.tsx'
s = p.read_text(encoding='utf-8')
s = s.replace('''        const L = await import("leaflet");\n        await import("leaflet.markercluster");\n        if (disposed || !elementRef.current) return;\n        leafletRef.current = L;''', '''        const leafletModule = await import("leaflet");\n        await import("leaflet.markercluster");\n        const L = (leafletModule.default || leafletModule) as typeof import("leaflet");\n        if (disposed || !elementRef.current) return;\n        leafletRef.current = L;''', 1)
old = '''        const layer = L.markerClusterGroup({ chunkedLoading: true, chunkInterval: 120, chunkDelay: 30, showCoverageOnHover: false, spiderfyOnMaxZoom: true, removeOutsideVisibleBounds: true, maxClusterRadius: 48, disableClusteringAtZoom: 15 });\n        layer.addTo(map);'''
new = '''        const clusterFactory = (L as typeof L & { markerClusterGroup?: (options?: Record<string, unknown>) => import("leaflet").LayerGroup }).markerClusterGroup;\n        const layer = typeof clusterFactory === "function"\n          ? clusterFactory({ chunkedLoading: true, chunkInterval: 120, chunkDelay: 30, showCoverageOnHover: false, spiderfyOnMaxZoom: true, removeOutsideVisibleBounds: true, maxClusterRadius: 48, disableClusteringAtZoom: 15 })\n          : L.layerGroup();\n        layer.addTo(map);'''
if old not in s:
    raise SystemExit('Map markercluster marker missing')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# 4) Align multilingual home copy to the actual main rendering.
p = root / 'frontend-react/src/lib/language.ts'
s = p.read_text(encoding='utf-8')
replacements = {
'homeSub: "Sea, villages, trails, museums, flavours and local businesses: useful information to choose where to go and what to do.", exploreActivities: "Explore businesses"': 'homeSub: "Sea, villages, trails, museums, food and local businesses: useful information to choose where to go and what to do.", exploreActivities: "Explore activities"',
'placesTitle: "Places and businesses in Calabria", placesSub: "A selection of destinations across the coast, towns, villages and inland areas."': 'placesTitle: "Places and activities in Calabria", placesSub: "A selection of different destinations across the coast, cities, villages and inland areas."',
'searchWhat: "Que cherchez-vous ?"': 'searchWhat: "Que recherchez-vous ?"',
'villages: "Villages et culture"': 'villages: "Bourgs et culture"',
'placesSub: "Une sélection de destinations entre côte, villes, villages et arrière-pays."': 'placesSub: "Une sélection de destinations entre côte, villes, villages et zones intérieures."',
'homeTitle: "Betriebe und Orte in Kalabrien", homeSub: "Meer, Dörfer, Wege, Museen, Genuss und lokale Betriebe: nützliche Informationen für die Planung vor Ort.", exploreActivities: "Betriebe entdecken"': 'homeTitle: "Aktivitäten und Orte in Kalabrien", homeSub: "Meer, Dörfer, Wege, Museen, Kulinarik und lokale Betriebe: nützliche Informationen für die Wahl von Ziel und Aktivität.", exploreActivities: "Aktivitäten entdecken"',
'eat: "Essen gehen"': 'eat: "Essen & Trinken"',
'discover: "ZU ENTDECKEN", placesTitle: "Orte und Betriebe in Kalabrien", placesSub: "Eine Auswahl an Zielen an der Küste, in Städten, Dörfern und im Landesinneren."': 'discover: "ZUM ENTDECKEN", placesTitle: "Orte und Aktivitäten in Kalabrien", placesSub: "Eine Auswahl verschiedener Ziele an Küste, in Städten, Dörfern und im Landesinneren."',
'homeSub: "Mar, pueblos, senderos, museos, sabores y actividades locales: información útil para elegir dónde ir y qué hacer."': 'homeSub: "Mar, pueblos, senderos, museos, sabores y negocios locales: información útil para elegir adónde ir y qué hacer."',
'searchWhat: "¿Qué buscas?"': 'searchWhat: "¿Qué estás buscando?"',
'eventsBlog: "Events & Blog"': 'eventsBlog: "Eventos y Blog"',
'shopping: "Shopping"': 'shopping: "Compras"',
'discover: "POR EXPLORAR"': 'discover: "PARA EXPLORAR"',
'viewAll: "Ver todo"': 'viewAll: "Ver todas"',
'placesSub: "Una selección de destinos entre costa, ciudades, pueblos y zonas de interior."': 'placesSub: "Una selección de destinos entre costa, ciudades, pueblos y zonas del interior."',
}
for old, new in replacements.items():
    if old in s:
        s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# 5) Localize the four exact featured cards instead of leaving Italian content on non-Italian homes.
p = root / 'frontend-react/src/pages/OriginalHomePage.tsx'
s = p.read_text(encoding='utf-8')
s = s.replace('import { languageFromPath, uiText, withLanguage } from "../lib/language";', 'import { languageFromPath, uiText, withLanguage, type Language } from "../lib/language";', 1)
marker = 'const featured: readonly FeaturedItem[] = [\n'
if marker not in s:
    raise SystemExit('featured marker missing')
insert_after = '];\n\nfunction FeaturedHeart'
pos = s.find(insert_after, s.find(marker))
if pos < 0:
    raise SystemExit('featured end marker missing')
localized = r'''

const FEATURED_COPY: Partial<Record<Language, Record<string, { title: string; kind: string }>>> = {
  en: {
    "turismo-centro-storico-tropea": { title: "Tropea Historic Center", kind: "Villages and culture" },
    "turismo-foresta-sila": { title: "Sila Forest", kind: "Nature and trails" },
    "turismo-scilla-castello": { title: "Scilla and its Castle", kind: "Villages and culture" },
    "turismo-capo-colonna": { title: "Capo Colonna Archaeological Park", kind: "Archaeology and landscape" },
  },
  fr: {
    "turismo-centro-storico-tropea": { title: "Centre historique de Tropea", kind: "Bourgs et culture" },
    "turismo-foresta-sila": { title: "Forêt de la Sila", kind: "Nature et sentiers" },
    "turismo-scilla-castello": { title: "Scilla et son château", kind: "Bourgs et culture" },
    "turismo-capo-colonna": { title: "Parc archéologique de Capo Colonna", kind: "Archéologie et territoire" },
  },
  de: {
    "turismo-centro-storico-tropea": { title: "Historisches Zentrum von Tropea", kind: "Dörfer und Kultur" },
    "turismo-foresta-sila": { title: "Sila-Wald", kind: "Natur und Wege" },
    "turismo-scilla-castello": { title: "Scilla und seine Burg", kind: "Dörfer und Kultur" },
    "turismo-capo-colonna": { title: "Archäologischer Park Capo Colonna", kind: "Archäologie und Landschaft" },
  },
  es: {
    "turismo-centro-storico-tropea": { title: "Centro histórico de Tropea", kind: "Pueblos y cultura" },
    "turismo-foresta-sila": { title: "Bosque de la Sila", kind: "Naturaleza y senderos" },
    "turismo-scilla-castello": { title: "Scilla y su castillo", kind: "Pueblos y cultura" },
    "turismo-capo-colonna": { title: "Parque Arqueológico de Capo Colonna", kind: "Arqueología y territorio" },
  },
};

function featuredCopy(item: FeaturedItem, language: Language) {
  return FEATURED_COPY[language]?.[item.id] || { title: item.title, kind: item.kind };
}
'''
s = s[:pos+2] + localized + s[pos+2:]
old_map = '{featured.map((item, index) => <Link key={item.title} className="cv-experience-card" href={withLanguage(item.href, language)} style={{ backgroundImage: `linear-gradient(180deg,transparent 22%,rgba(0,0,0,.72)),url(\'${item.image}\')` }}>{item.badge ? <i>{item.badge}</i> : null}<FeaturedHeart id={item.id} title={item.title} /><div><span>{item.province}</span><h3>{item.title}</h3><p>{item.kind}</p></div>{index === 0 ? <img src={item.image} alt="" aria-hidden="true" fetchPriority="high" decoding="async" className="cv-card-preload" /> : null}</Link>)}'
new_map = '{featured.map((item, index) => { const copy = featuredCopy(item, language); return <Link key={item.title} className="cv-experience-card" href={withLanguage(item.href, language)} style={{ backgroundImage: `linear-gradient(180deg,transparent 22%,rgba(0,0,0,.72)),url(\'${item.image}\')` }}>{item.badge ? <i>{item.badge}</i> : null}<FeaturedHeart id={item.id} title={copy.title} /><div><span>{item.province}</span><h3>{copy.title}</h3><p>{copy.kind}</p></div>{index === 0 ? <img src={item.image} alt="" aria-hidden="true" fetchPriority="high" decoding="async" className="cv-card-preload" /> : null}</Link>; })}'
if old_map not in s:
    raise SystemExit('featured render marker missing')
s = s.replace(old_map, new_map, 1)
p.write_text(s, encoding='utf-8')

# 6) Main-like anonymous shortcuts and flag language menu in the React shell.
p = root / 'frontend-react/src/components/Layout.tsx'
s = p.read_text(encoding='utf-8')
s = s.replace('''function MessageIcon() {\n  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h16a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H8l-5 3V6a2 2 0 0 1 2-2Zm1.2 3.2 6.8 5 6.8-5" /></svg>;\n}\n''', '''function BellIcon() {\n  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></svg>;\n}\n''', 1)
s = s.replace('const langs = ["it", "en", "fr", "de", "es"] as const;', 'const langs = ["it", "en", "fr", "de", "es"] as const;\nconst languageNames = { it: "Italiano", en: "English", fr: "Français", de: "Deutsch", es: "Español" } as const;', 1)
old_shortcuts = '''            {authReady && user ? <div className="cv-header-shortcuts">\n              <Suspense fallback={<span className="cv-icon-action cv-icon-placeholder" aria-hidden="true" />}><NotificationsMenu uid={user.uid} /></Suspense>\n              <Link className="cv-icon-action relative" href={withLanguage("/preferiti", language)} aria-label={uiText("favorites", language)} title={uiText("favorites", language)}><HeartIcon />{favoriteCount > 0 ? <span className="absolute -right-1.5 -top-1.5 flex min-h-5 min-w-5 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-black leading-none text-white shadow" aria-label={`${favoriteCount} preferiti`}>{favoriteCount > 99 ? "99+" : favoriteCount}</span> : null}</Link>\n              <Link className="cv-icon-action" href={withLanguage("/messaggi", language)} aria-label={uiText("messages", language)} title={uiText("messages", language)}><MessageIcon /></Link>\n            </div> : null}\n\n            <label className="cv-language-select header-language" aria-label="Lingua">\n              <span>{language.toUpperCase()}</span>\n              <select value={language} onChange={(event) => setLanguage(event.target.value as typeof language)}>\n                {langs.map((lang) => <option key={lang} value={lang}>{lang.toUpperCase()}</option>)}\n              </select>\n            </label>'''
new_shortcuts = '''            <div className="cv-header-shortcuts">\n              <Link className="cv-icon-action relative" href={user ? withLanguage("/preferiti", language) : withLanguage(`/login?next=${encodeURIComponent("/preferiti")}`, language)} aria-label={uiText("favorites", language)} title={uiText("favorites", language)}><HeartIcon />{favoriteCount > 0 ? <span className="cv-counter-badge cv-favorite-badge" aria-label={`${favoriteCount} preferiti`}>{favoriteCount > 99 ? "99+" : favoriteCount}</span> : null}</Link>\n              {user ? <Suspense fallback={<span className="cv-icon-action cv-icon-placeholder" aria-hidden="true" />}><NotificationsMenu uid={user.uid} /></Suspense> : <button type="button" className="cv-icon-action" aria-label="Notifiche" title="Notifiche" onClick={() => navigate(withLanguage(`/login?next=${encodeURIComponent(location.pathname + location.search)}`, language))}><BellIcon /></button>}\n            </div>\n\n            <details className="header-language" data-language-menu>\n              <summary className="cv-language-trigger" aria-label="Lingua" title="Lingua"><span className={`cv-language-flag cv-language-flag--${language}`} aria-hidden="true" /><span className="cv-language-code">{language.toUpperCase()}</span><svg className="cv-language-chevron" viewBox="0 0 16 16" aria-hidden="true"><path d="m3 6 5 5 5-5" /></svg></summary>\n              <div className="cv-language-list" role="menu" aria-label="Lingua">{langs.map((lang) => <button key={lang} type="button" className="cv-language-option" role="menuitem" aria-current={lang === language ? "true" : undefined} onClick={() => setLanguage(lang)}><span className={`cv-language-flag cv-language-flag--${lang}`} aria-hidden="true" /><span className="cv-language-code">{lang.toUpperCase()}</span><span className="cv-language-name">{languageNames[lang]}</span><span className="cv-language-check" aria-hidden="true">{lang === language ? "✓" : ""}</span></button>)}</div>\n            </details>'''
if old_shortcuts not in s:
    raise SystemExit('Layout shortcuts/language marker missing')
s = s.replace(old_shortcuts, new_shortcuts, 1)
p.write_text(s, encoding='utf-8')

# 7) Exact first-paint translation in the Worker too.
p = root / 'frontend-react/worker.ts'
s = p.read_text(encoding='utf-8')
s = s.replace('title: "Betriebe und Orte in Kalabrien", subtitle: "Meer, Dörfer, Wege, Museen, Genuss und lokale Betriebe: nützliche Informationen für die Planung vor Ort."', 'title: "Aktivitäten und Orte in Kalabrien", subtitle: "Meer, Dörfer, Wege, Museen, Kulinarik und lokale Betriebe: nützliche Informationen für die Wahl von Ziel und Aktivität."')
s = s.replace('title: "Businesses and places in Calabria", subtitle: "Sea, villages, trails, museums, flavours and local businesses: useful information to choose where to go and what to do."', 'title: "Activities and places in Calabria", subtitle: "Sea, villages, trails, museums, food and local businesses: useful information to choose where to go and what to do."')
p.write_text(s, encoding='utf-8')

print('Final public parity patch applied')
