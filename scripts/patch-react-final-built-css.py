from pathlib import Path

# 1) Remove the React visual cascade. Exact legacy final bundles are loaded per route instead.
main = Path('frontend-react/src/main.tsx')
s = main.read_text()
for line in ['import "./styles.css";\n', 'import "./shell-parity.css";\n', 'import "./consent.css";\n']:
    if line not in s:
        raise SystemExit(f'main.tsx visual CSS import contract changed: {line.strip()}')
    s = s.replace(line, '', 1)
main.write_text(s)

# Leaflet base CSS was previously inherited from styles.css; keep it scoped to the map chunk.
map_page = Path('frontend-react/src/pages/MapPage.tsx')
m = map_page.read_text()
leaflet_import = 'import "leaflet/dist/leaflet.css";\n'
if leaflet_import not in m:
    marker = 'import "leaflet.markercluster/dist/MarkerCluster.css";\n'
    if marker not in m:
        raise SystemExit('MapPage markercluster CSS contract changed')
    m = m.replace(marker, leaflet_import + marker, 1)
map_page.write_text(m)

# 2) Generate route CSS from the exact final *built* legacy bundles, not source CSS lists.
copy = Path('frontend-react/scripts/copy-legacy-assets.mjs')
c = copy.read_text()
if '  "/404": "404.html",' not in c:
    anchor = 'const routeSources = {\n  "/": "index.html",\n'
    if anchor not in c:
        raise SystemExit('routeSources anchor changed')
    c = c.replace(anchor, 'const routeSources = {\n  "/404": "404.html",\n  "/": "index.html",\n', 1)
start = c.index('const CORE_STYLES = [')
end_marker = 'console.log(`Parità route generata: ${Object.keys(routeCss).length} route, ${cssFiles.size} CSS main con cascata finale produzione`);'
end = c.index(end_marker, start) + len(end_marker)
replacement = r'''const EXACT_BUNDLES = {
  generic: "/assets/css/cv-bundle-1dae388af7394278.css",
  business: "/assets/css/cv-bundle-603cc2ff50d0e016.css",
  catalog: "/assets/css/cv-bundle-d6726897b303029e.css",
  home: "/assets/css/cv-bundle-89794cb4f569c254.css",
  map: "/assets/css/cv-bundle-5605509f9b6e4dee.css",
  messages: "/assets/css/cv-bundle-05735d3b1a3300b8.css",
  adminActivity: "/assets/css/cv-bundle-b23bf9fdf406ca6d.css",
  adminGeneric: "/assets/css/cv-bundle-28783d3e87e06008.css",
  adminUsers: "/assets/css/cv-bundle-fe11938d8fd5afe9.css",
};
const EXACT_BUNDLE_BY_ROUTE = {
  "/": EXACT_BUNDLES.home,
  "/catalogo": EXACT_BUNDLES.catalog,
  "/mappa": EXACT_BUNDLES.map,
  "/attivita/:detail": EXACT_BUNDLES.business,
  "/messaggi": EXACT_BUNDLES.messages,
  "/admin": EXACT_BUNDLES.adminGeneric,
  "/admin/attivita": EXACT_BUNDLES.adminActivity,
  "/admin/messaggi": EXACT_BUNDLES.adminActivity,
  "/admin/utenti": EXACT_BUNDLES.adminUsers,
  "/admin/recensioni": EXACT_BUNDLES.adminGeneric,
  "/admin/blog": EXACT_BUNDLES.adminGeneric,
  "/admin/categorie": EXACT_BUNDLES.adminGeneric,
  "/admin/comuni": EXACT_BUNDLES.adminGeneric,
  "/admin/seo": EXACT_BUNDLES.adminGeneric,
  "/admin/impostazioni": EXACT_BUNDLES.adminGeneric,
};
const routeCss = {};
const routePages = {};
for (const [route, relative] of Object.entries(routeSources)) {
  const source = resolve(repoRoot, relative);
  if (!existsSync(source)) continue;
  const raw = readFileSync(source, "utf8");
  const page = raw.match(/<body\b[^>]*\bdata-page=["']([^"']+)["']/i)?.[1] || "";
  if (page) routePages[route] = page;
  const href = EXACT_BUNDLE_BY_ROUTE[route] || (route.startsWith("/admin/") ? EXACT_BUNDLES.adminGeneric : EXACT_BUNDLES.generic);
  const builtTarget = resolve(reactRoot, "public", href.slice(1));
  if (!existsSync(builtTarget)) throw new Error(`Bundle CSS finale esatto mancante: ${builtTarget}`);
  routeCss[route] = [href];
}
const routeModule = `export const MAIN_ROUTE_CSS: Record<string, readonly string[]> = ${JSON.stringify(routeCss, null, 2)};\nexport const MAIN_ROUTE_PAGE: Record<string, string> = ${JSON.stringify(routePages, null, 2)};\n`;
writeFileSync(resolve(generatedDir, "main-route-css.ts"), routeModule, "utf8");
writeFileSync(resolve(reactRoot, "public/main-route-css.json"), JSON.stringify({ routeCss, routePages }), "utf8");
console.log(`Parità route generata da bundle finali backup: ${Object.keys(routeCss).length} route, ${new Set(Object.values(routeCss).flat()).size} bundle esatti`);'''
c = c[:start] + replacement + c[end:]
copy.write_text(c)

# 3) Route switching must load one and only one exact final bundle. Restore the exact #site-header wrapper.
layout = Path('frontend-react/src/components/Layout.tsx')
l = layout.read_text()
old_key = '''function mainRouteKey(path: string) {
  if (MAIN_ROUTE_CSS[path]) return path;
  if (path.startsWith("/blog/")) return "/blog/:detail";
  if (path === "/attivita" || path.startsWith("/attivita/")) return "/attivita/:detail";
  return path;
}
'''
new_key = '''function mainRouteKey(path: string) {
  if (MAIN_ROUTE_CSS[path]) return path;
  if (path.startsWith("/catalogo/")) return "/catalogo";
  if (path.startsWith("/mappa/")) return "/mappa";
  if (path.startsWith("/blog/")) return "/blog/:detail";
  if (path === "/attivita" || path.startsWith("/attivita/")) return "/attivita/:detail";
  if (path.startsWith("/admin/")) return MAIN_ROUTE_CSS[path] ? path : "/admin";
  return MAIN_ROUTE_CSS["/404"] ? "/404" : path;
}
'''
if old_key not in l:
    raise SystemExit('Layout mainRouteKey contract changed')
l = l.replace(old_key, new_key, 1)
old_expected = '    const expected = [...exactMainCss(cleanPath), "/assets/css/privacy-consent.css"];'
if old_expected not in l:
    raise SystemExit('Layout CSS expected contract changed')
l = l.replace(old_expected, '    const expected = exactMainCss(cleanPath);', 1)
open_shell = '    <div className="cv-site-shell">\n      <header className="site-header cv-header">'
if open_shell not in l:
    raise SystemExit('Layout header opening contract changed')
l = l.replace(open_shell, '    <div className="cv-site-shell">\n      <div id="site-header">\n      <header className="site-header cv-header">', 1)
close_header = '      </header>\n\n      <main id="main-content" className="cv-site-main">'
if close_header not in l:
    raise SystemExit('Layout header closing contract changed')
l = l.replace(close_header, '      </header>\n      </div>\n\n      <main id="main-content" className="cv-site-main">', 1)
layout.write_text(l)

# 4) Restore the exact 404 content/SEO and use the generic built bundle via /404.
app = Path('frontend-react/src/App.tsx')
a = app.read_text()
nav_import = 'import { navigate, useLocationSnapshot } from "./lib/navigation";'
seo_import = 'import { setPageSeo } from "./lib/seo";'
if seo_import not in a:
    if nav_import not in a:
        raise SystemExit('App navigation import contract changed')
    a = a.replace(nav_import, nav_import + '\n' + seo_import, 1)
start = a.index('function NotFoundPage() {')
end = a.index('\nfunction RouteView()', start)
not_found = '''function NotFoundPage() {
  useEffect(() => {
    setPageSeo({
      title: "Pagina non trovata | CalabriaVera",
      description: "CalabriaVera: il portale locale delle attività e dei servizi della Calabria.",
      path: "/404",
      robots: "noindex,follow",
    });
    document.head.querySelector<HTMLMetaElement>('meta[name="robots"]')?.setAttribute("content", "noindex,follow");
    document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]')?.remove();
  }, []);
  return <section className="section container"><p className="eyebrow">CalabriaVera</p><h1>Pagina non trovata</h1><div className="prose"><p>La pagina richiesta non è disponibile o è stata spostata.</p><div className="form-actions"><Link className="button button-primary" href="/">Torna alla home</Link><Link className="button button-secondary" href="/catalogo">Apri il catalogo</Link></div></div></section>;
}
'''
a = a[:start] + not_found + a[end:]
app.write_text(a)

# 5) Load the exact bundle immediately on non-prerendered routes too, before React mounts.
index = Path('frontend-react/index.html')
i = index.read_text()
bootstrap_marker = 'data-cv-exact-built-bootstrap'
if bootstrap_marker not in i:
    needle = '    <title>CalabriaVera | Attività e luoghi della Calabria</title>\n'
    if needle not in i:
        raise SystemExit('index title anchor changed')
    bootstrap = r'''    <script data-cv-exact-built-bootstrap>
      (function(){
        var p=(location.pathname||"/").replace(/^\/(?:en|fr|de|es)(?=\/|$)/,"")||"/";
        p=p==="/"?"/":(p.replace(/\/+$/,"")||"/");
        var generic="/assets/css/cv-bundle-1dae388af7394278.css";
        var href=generic;
        if(p==="/")href="/assets/css/cv-bundle-89794cb4f569c254.css";
        else if(p==="/catalogo"||p.indexOf("/catalogo/")===0)href="/assets/css/cv-bundle-d6726897b303029e.css";
        else if(p==="/mappa"||p.indexOf("/mappa/")===0)href="/assets/css/cv-bundle-5605509f9b6e4dee.css";
        else if(p==="/attivita"||p.indexOf("/attivita/")===0)href="/assets/css/cv-bundle-603cc2ff50d0e016.css";
        else if(p==="/messaggi")href="/assets/css/cv-bundle-05735d3b1a3300b8.css";
        else if(p==="/admin/attivita"||p==="/admin/messaggi")href="/assets/css/cv-bundle-b23bf9fdf406ca6d.css";
        else if(p==="/admin/utenti")href="/assets/css/cv-bundle-fe11938d8fd5afe9.css";
        else if(p==="/admin"||p.indexOf("/admin/")===0)href="/assets/css/cv-bundle-28783d3e87e06008.css";
        document.write('<link rel="stylesheet" href="'+href+'" data-cv-main-parity>');
      })();
    </script>
'''
    i = i.replace(needle, needle + bootstrap, 1)
index.write_text(i)

# Prerendered pages already execute the early bootstrap; avoid a duplicate route stylesheet.
pre = Path('frontend-react/scripts/prerender-home.mjs')
p = pre.read_text()
old = '''  const cleanRoute = page.path.replace(/^\\/(?:en|fr|de|es)(?=\\/|$)/, "") || "/";
  const routeKey = cleanRoute === "/" ? "/" : cleanRoute.replace(/\\/$/, "");
  const parityLinks = (routeCss[routeKey] || []).map((href) => `<link rel="stylesheet" href="${href}" data-cv-main-parity>`).join("");
  if (parityLinks) html = html.replace("</head>", `${parityLinks}</head>`);
'''
if old not in p:
    raise SystemExit('prerender parity-link contract changed')
p = p.replace(old, '', 1)
pre.write_text(p)
