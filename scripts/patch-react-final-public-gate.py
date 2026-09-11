from pathlib import Path

root = Path('source/frontend-react')

# 1) Normalize trailing slashes in client routing so prerendered /catalogo/ and /blog/ keep their exact CSS.
p = root / 'src/components/Layout.tsx'
s = p.read_text(encoding='utf-8')
old = '  const cleanPath = location.pathname.replace(/^\\/(?:en|fr|de|es)(?=\\/|$)/, "") || "/";'
new = '  const rawCleanPath = location.pathname.replace(/^\\/(?:en|fr|de|es)(?=\\/|$)/, "") || "/";\n  const cleanPath = rawCleanPath === "/" ? "/" : rawCleanPath.replace(/\\/+$/, "") || "/";'
if old not in s:
    raise SystemExit('Layout cleanPath marker missing')
s = s.replace(old, new, 1)
s = s.replace('className="cv-login-button"', 'className="button button-secondary cv-account-login"')
s = s.replace('className="cv-register-button"', 'className="button button-primary cv-account-register"')
p.write_text(s, encoding='utf-8')

# 2) Normalize Worker route paths and bypass Cloudflare directory redirects for prerendered index routes.
p = root / 'worker.ts'
s = p.read_text(encoding='utf-8')
old = '''function cleanPath(pathname: string) {\n  const stripped = pathname.replace(/^\\/(?:en|fr|de|es)(?=\\/|$)/, "");\n  return stripped || "/";\n}'''
new = '''function cleanPath(pathname: string) {\n  const stripped = pathname.replace(/^\\/(?:en|fr|de|es)(?=\\/|$)/, "");\n  return normalizeRoutePath(stripped || "/");\n}'''
if old not in s:
    raise SystemExit('Worker cleanPath marker missing')
s = s.replace(old, new, 1)
old = '  let asset = await env.ASSETS.fetch(request);\n  if (!asset.ok || !asset.headers.get("content-type")?.includes("text/html")) return asset;'
new = '''  let htmlRequest = request;\n  if (path === "/catalogo" || path === "/blog") {\n    const prerenderUrl = new URL(url.toString());\n    prerenderUrl.pathname = `${url.pathname.replace(/\\/+$/, "")}/index.html`;\n    prerenderUrl.search = "";\n    htmlRequest = new Request(prerenderUrl.toString(), { method: "GET", headers: request.headers });\n  }\n  let asset = await env.ASSETS.fetch(htmlRequest);\n  if (!asset.ok || !asset.headers.get("content-type")?.includes("text/html")) return asset;'''
if old not in s:
    raise SystemExit('Worker asset fetch marker missing')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# 3) Put a final production-parity stylesheet last in every route CSS list.
p = root / 'scripts/copy-legacy-assets.mjs'
s = p.read_text(encoding='utf-8')
needle = 'const languageCss = "/assets/css/language-modern.css";'
if needle not in s:
    raise SystemExit('route css append marker missing')
insert = '''const liveParityCss = "/assets/css/react-live-parity.css";\nfor (const styles of Object.values(routeCss)) if (!styles.includes(liveParityCss)) styles.push(liveParityCss);\n'''
s = s.replace(needle, insert + needle, 1)
p.write_text(s, encoding='utf-8')

# 4) Live production visual corrections from the measured main rendering.
css = r'''html,body,#root,.cv-site-shell{max-width:100%;overflow-x:clip}
.cv-header .header-inner{min-height:64px!important}
.cv-header .brand-logo{width:177px!important;height:auto!important}
.footer-logo{width:188px!important;height:auto!important;max-width:188px!important}
body[data-page="home"] .cv-home-hero{background-image:linear-gradient(90deg,rgba(1,39,67,.78),rgba(1,39,67,.2) 58%,rgba(1,39,67,.03)),url('/assets/images/home/tropea-1600.webp')!important;background-position:center 46%!important;background-size:cover!important;background-repeat:no-repeat!important}
body[data-page="home"] .cv-home-hero__shade{background:transparent!important}
@media(max-width:700px){
  .cv-header .header-inner{min-height:60px!important;width:min(calc(100% - 24px),1480px)!important}
  .cv-header .brand-logo{width:96px!important}
  body[data-page="home"] .cv-home-hero{background-image:linear-gradient(90deg,rgba(1,39,67,.78),rgba(1,39,67,.2) 58%,rgba(1,39,67,.03)),url('/assets/images/home/tropea-960.webp')!important;background-position:62% center!important}
  body[data-page="map"] .map-layout{grid-template-columns:minmax(0,1fr)!important;display:grid!important}
  body[data-page="map"] .map-layout>aside{grid-column:1!important;grid-row:1!important;border-right:0!important;border-bottom:1px solid var(--cv-line)!important}
  body[data-page="map"] .map-layout>section{grid-column:1!important;grid-row:2!important;min-width:0!important}
}
'''
parity_css = root / 'public/assets/css/react-live-parity.css'
parity_css.parent.mkdir(parents=True, exist_ok=True)
parity_css.write_text(css, encoding='utf-8')

# 5) Align blog subtitles to main i18n and repair the accidental Italian shopping label.
p = root / 'src/lib/language.ts'
s = p.read_text(encoding='utf-8')
s = s.replace('shopping: "Compras"', 'shopping: "Shopping"', 1)
s = s.replace('magazineSub: "Contenuti dedicati alla Calabria, ordinati per data reale di pubblicazione e con attribuzione delle fonti esterne."', 'magazineSub: "Ispirazioni, curiosità, guide ed eventi per vivere il territorio."', 1)
s = s.replace('magazineSub: "Content about Calabria, ordered by the actual publication date and with attribution for external sources."', 'magazineSub: "Ideas, guides, stories and events to discover the region."', 1)
s = s.replace('magazineSub: "Contenus consacrés à la Calabre, triés par date réelle de publication et avec attribution des sources externes."', 'magazineSub: "Idées, guides, récits et événements pour découvrir le territoire."', 1)
s = s.replace('magazineSub: "Inhalte über Kalabrien, nach tatsächlichem Veröffentlichungsdatum sortiert und mit Quellenangaben."', 'magazineSub: "Ideen, Reiseführer, Geschichten und Veranstaltungen aus der Region."', 1)
s = s.replace('magazineSub: "Contenidos sobre Calabria, ordenados por fecha real de publicación y con atribución de las fuentes externas."', 'magazineSub: "Ideas, guías, historias y eventos para descubrir el territorio."', 1)
p.write_text(s, encoding='utf-8')

# 6) Home search category selector uses the same grouped taxonomy as main Catalog.
p = root / 'src/pages/OriginalHomePage.tsx'
s = p.read_text(encoding='utf-8')
s = s.replace('import { isFavorite, toggleFavorite } from "../lib/businesses";', 'import { CATEGORIES, isFavorite, toggleFavorite } from "../lib/businesses";', 1)
old = '<select name="categoria" aria-label={uiText("categories", language)}><option value="">{uiText("allCategories", language)}</option><option value="Turismo">Turismo</option><option value="Ristoranti">{uiText("eat", language)}</option><option value="Hotel">{uiText("sleep", language)}</option><option value="Servizi turistici">{uiText("do", language)}</option><option value="Stabilimenti balneari">{uiText("sea", language)}</option><option value="Esperienze">Esperienze</option><option value="Prodotti tipici">Prodotti tipici</option></select>'
new = '<select name="categoria" aria-label={uiText("categories", language)}><option value="">{uiText("allCategories", language)}</option>{CATEGORIES.map((category) => <option key={category} value={category}>{category}</option>)}</select>'
if old not in s:
    raise SystemExit('Home category selector marker missing')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

print('Final live public parity patch applied')
