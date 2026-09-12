from pathlib import Path

app = Path('frontend-react/src/App.tsx')
s = app.read_text()
old_import = 'import { navigate, useLocationSnapshot } from "./lib/navigation";'
new_import = 'import { navigate, useLocationSnapshot } from "./lib/navigation";\nimport { setPageSeo } from "./lib/seo";'
if old_import not in s:
    raise SystemExit('navigation import contract changed')
if 'import { setPageSeo } from "./lib/seo";' not in s:
    s = s.replace(old_import, new_import, 1)
start = s.index('function NotFoundPage() {')
end = s.index('\nfunction RouteView()', start)
legacy = '''function NotFoundPage() {
  useEffect(() => {
    setPageSeo({
      title: "Pagina non trovata | CalabriaVera",
      description: "CalabriaVera: il portale locale delle attività e dei servizi della Calabria.",
      path: "/404",
      robots: "noindex,follow",
    });
    document.head.querySelector<HTMLMetaElement>('meta[name="robots"]')?.setAttribute("content", "noindex,follow");
  }, []);
  return <section className="section container"><p className="eyebrow">CalabriaVera</p><h1>Pagina non trovata</h1><div className="prose"><p>La pagina richiesta non è disponibile o è stata spostata.</p><div className="form-actions"><Link className="button button-primary" href="/">Torna alla home</Link><Link className="button button-secondary" href="/catalogo">Apri il catalogo</Link></div></div></section>;
}
'''
s = s[:start] + legacy + s[end:]
app.write_text(s)

copy = Path('frontend-react/scripts/copy-legacy-assets.mjs')
c = copy.read_text()
route_anchor = '''const routeSources = {
  "/": "index.html",
'''
route_replacement = '''const routeSources = {
  "/": "index.html",
  "/404": "404.html",
'''
if '  "/404": "404.html",' not in c:
    if route_anchor not in c:
        raise SystemExit('route source contract changed')
    c = c.replace(route_anchor, route_replacement, 1)
copy.write_text(c)

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
    raise SystemExit('main route key contract changed')
l = l.replace(old_key, new_key, 1)
layout.write_text(l)
