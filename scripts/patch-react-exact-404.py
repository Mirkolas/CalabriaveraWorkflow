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
    document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]')?.remove();
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

css_path = Path('frontend-react/public/assets/css/react-live-parity.css')
css = css_path.read_text()
marker = '/* exact built 404 parity */'
block = r'''
/* exact built 404 parity */
body[data-page="notFound"] .site-header .header-inner{min-height:72px}
body[data-page="notFound"] #main-content>section.section.container{width:min(1200px,calc(100% - 18px));max-width:1440px;margin-inline:auto;padding:57.33px 0}
body[data-page="notFound"] #main-content h1{font-family:Georgia,"Times New Roman",serif;font-size:75.075px;font-weight:700;line-height:73.5735px;letter-spacing:-2.1021px;color:#172033;max-width:920px;margin:2.4px 0 12.8px}
body[data-page="notFound"] #main-content .form-actions{gap:8px}
body[data-page="notFound"] #main-content .form-actions .button{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:16.48px;line-height:27.192px;padding:10.24px 14.72px;letter-spacing:normal;max-width:100%}
@media(max-width:700px){body[data-page="notFound"] #main-content>section.section.container{width:calc(100% - 18px);max-width:1200px;padding:28px 0}body[data-page="notFound"] #main-content h1{font-size:31.2px;line-height:32.76px;letter-spacing:-.8736px}}
'''.strip()
if marker in css:
    css = css[:css.index(marker)].rstrip() + '\n' + block + '\n'
else:
    css = css.rstrip() + '\n' + block + '\n'
css_path.write_text(css)
