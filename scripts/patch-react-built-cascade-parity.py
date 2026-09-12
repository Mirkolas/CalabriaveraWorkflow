from pathlib import Path

copy = Path('frontend-react/scripts/copy-legacy-assets.mjs')
c = copy.read_text()

# Unknown routes must use the real legacy 404 cascade.
route_anchor = '''const routeSources = {
  "/": "index.html",
'''
if '  "/404": "404.html",' not in c:
    if route_anchor not in c:
        raise SystemExit('routeSources anchor changed')
    c = c.replace(route_anchor, '''const routeSources = {
  "/": "index.html",
  "/404": "404.html",
''', 1)

old_helpers = '''const liveParityCss = "/assets/css/react-live-parity.css";
const assetPath = (href) => String(href || "").split(/[?#]/, 1)[0];
const routeCss = {};
'''
new_helpers = '''const liveParityCss = "/assets/css/react-live-parity.css";
const assetPath = (href) => String(href || "").split(/[?#]/, 1)[0];
const PAGE_ONLY_STYLE_PATHS = [
  "/assets/css/catalog-activity-cover.css",
  "/assets/css/business-detail.css",
  "/assets/css/messages-v2.css",
];
const LEGACY_BUSINESS_STYLES = [
  "/assets/css/business-detail.css",
  "/assets/css/business-detail-polish.css",
  "/assets/css/business-owner-tourism-stars.css",
];
const SHARED_EXPERIENCE_STYLE = "/assets/css/activity-experience.css";
const RENDER_PERFORMANCE_STYLE = "/assets/css/render-performance.css";
const BUSINESS_STYLE = "/assets/css/business-detail-v2.css";
const REVIEW_STYLE = "/assets/css/review-stars.css";
const removeStylePath = (styles, path) => styles.filter((href) => assetPath(href) !== assetPath(path));
const ensureStyle = (styles, href) => [...removeStylePath(styles, href), href];
const routeCss = {};
'''
if old_helpers not in c:
    raise SystemExit('route helper contract changed')
c = c.replace(old_helpers, new_helpers, 1)

old_parity = '''  const parityStyles = ["/assets/css/language-modern.css", liveParityCss];
  for (const href of parityStyles) {
    const pathOnly = assetPath(href);
    styles = styles.filter((current) => assetPath(current) !== pathOnly);
    styles.push(href);
  }
  routeCss[route] = styles;
'''
new_parity = '''  // Reproduce the authoritative production build, not only the source HTML.
  // scripts/stabilize-shell.mjs removes page-only CSS, appends CORE_STYLES in
  // this exact order and finally appends the page-specific stylesheet.
  for (const path of PAGE_ONLY_STYLE_PATHS) styles = removeStylePath(styles, path);
  for (const href of CORE_STYLES) styles = ensureStyle(styles, href);
  for (const href of PAGE_STYLES[page] || []) styles = ensureStyle(styles, href);

  // scripts/unify-css.mjs then removes legacy business detail CSS and appends
  // the shared experience/render/review styles before concatenating the bundle.
  for (const path of LEGACY_BUSINESS_STYLES) styles = removeStylePath(styles, path);
  styles = ensureStyle(styles, SHARED_EXPERIENCE_STYLE);
  styles = ensureStyle(styles, RENDER_PERFORMANCE_STYLE);
  if (page === "business" || page === "activities") styles = ensureStyle(styles, BUSINESS_STYLE);
  styles = ensureStyle(styles, REVIEW_STYLE);

  // React-only DOM bridge comes after the exact legacy cascade.
  styles = ensureStyle(styles, liveParityCss);
  routeCss[route] = styles;
'''
if old_parity not in c:
    raise SystemExit('route parity contract changed')
c = c.replace(old_parity, new_parity, 1)
copy.write_text(c)

# Unknown routes share /404 CSS.
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
  if (path.startsWith("/blog/")) return "/blog/:detail";
  if (path === "/attivita" || path.startsWith("/attivita/")) return "/attivita/:detail";
  if (["/cerca", "/magazine", "/register", "/privacy"].includes(path) || path.endsWith(".html") || path.startsWith("/pages/admin/")) return path;
  return MAIN_ROUTE_CSS["/404"] ? "/404" : path;
}
'''
if old_key not in l:
    raise SystemExit('Layout route key contract changed')
l = l.replace(old_key, new_key, 1)
layout.write_text(l)

# Exact legacy 404 markup and SEO. Do not hard-code visual metrics: the exact
# built cascade above must produce them.
app = Path('frontend-react/src/App.tsx')
s = app.read_text()
nav_import = 'import { navigate, useLocationSnapshot } from "./lib/navigation";'
if 'import { setPageSeo } from "./lib/seo";' not in s:
    if nav_import not in s:
        raise SystemExit('App navigation import contract changed')
    s = s.replace(nav_import, nav_import + '\nimport { setPageSeo } from "./lib/seo";', 1)
start = s.index('function NotFoundPage() {')
end = s.index('\nfunction RouteView()', start)
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
s = s[:start] + not_found + s[end:]
app.write_text(s)
