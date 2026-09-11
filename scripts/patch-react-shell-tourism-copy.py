from pathlib import Path

root = Path('source')

# Build preparation: generate strongly typed full tourism data and publish exact local legacy assets/pages.
p = root / 'frontend-react/scripts/copy-legacy-assets.mjs'
p.write_text(r'''import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(scriptDir, "../..");
const reactRoot = resolve(scriptDir, "..");

const tourismSource = resolve(repoRoot, "assets/js/tourism-data-core.js");
const generatedDir = resolve(reactRoot, "src/generated");
const tourismTarget = resolve(generatedDir, "tourism-data-core.ts");
if (!existsSync(tourismSource)) throw new Error(`Asset turismo sorgente non trovato: ${tourismSource}`);
mkdirSync(generatedDir, { recursive: true });
const tourismJs = readFileSync(tourismSource, "utf8");
const tourismTs = `import type { Business } from "../types";\n${tourismJs.replace("export const TOURISM_BUSINESSES = [", "export const TOURISM_BUSINESSES: Business[] = [")}`;
writeFileSync(tourismTarget, tourismTs, "utf8");
console.log(`Modulo turismo TypeScript generato: ${tourismTarget}`);

const legacyDir = resolve(reactRoot, "public/legacy");
mkdirSync(legacyDir, { recursive: true });
const legalFiles = ["privacy-policy.html", "cookie-policy.html", "termini.html", "note-legali.html", "contatti.html", "chi-siamo.html"];
for (const name of legalFiles) {
  const source = resolve(repoRoot, name);
  if (!existsSync(source)) throw new Error(`Pagina legacy sorgente non trovata: ${source}`);
  copyFileSync(source, resolve(legacyDir, name));
}

const assetFiles = [
  "assets/Logo.webp", "assets/Logo.png", "assets/site.webmanifest", "assets/favicon.ico", "assets/favicon-16x16.png", "assets/favicon-32x32.png", "assets/apple-touch-icon.png", "assets/android-chrome-192x192.png", "assets/android-chrome-512x512.png",
  "assets/images/home/tropea-960.webp", "assets/images/home/tropea-1600.webp", "assets/images/home/sila-720.webp", "assets/images/home/sila-1280.webp", "assets/images/home/scilla-720.webp", "assets/images/home/capo-colonna-720.webp"
];
for (const relative of assetFiles) {
  const source = resolve(repoRoot, relative);
  if (!existsSync(source)) continue;
  const target = resolve(reactRoot, "public", relative);
  mkdirSync(dirname(target), { recursive: true });
  copyFileSync(source, target);
}
console.log(`Pagine legacy: ${legalFiles.length}; asset locali copiati: ${assetFiles.length}`);
''', encoding='utf-8')

# Full tourism data replaces the temporary four-item compatibility layer.
p = root / 'frontend-react/src/lib/tourism-static.ts'
p.write_text(r'''import type { Business } from "../types";
import { TOURISM_BUSINESSES } from "../generated/tourism-data-core";

export const ALL_TOURISM: Business[] = TOURISM_BUSINESSES;
const FEATURED_IDS = new Set(["turismo-centro-storico-tropea", "turismo-foresta-sila", "turismo-scilla-castello", "turismo-capo-colonna"]);
export const FEATURED_TOURISM: Business[] = ALL_TOURISM.filter((item) => FEATURED_IDS.has(item.id));

export function featuredTourismBySlug(slug: string) {
  return ALL_TOURISM.find((item) => item.slug === slug) || null;
}
''', encoding='utf-8')

for relative in ['frontend-react/src/pages/CatalogPage.tsx', 'frontend-react/src/pages/MapPage.tsx']:
    p = root / relative
    s = p.read_text(encoding='utf-8')
    s = s.replace('import { FEATURED_TOURISM } from "../lib/tourism-static";', 'import { ALL_TOURISM } from "../lib/tourism-static";')
    s = s.replace('for (const item of FEATURED_TOURISM)', 'for (const item of ALL_TOURISM)')
    p.write_text(s, encoding='utf-8')

# Local assets on home and shell: never depend on the retired Firebase Hosting origin.
p = root / 'frontend-react/src/pages/OriginalHomePage.tsx'
s = p.read_text(encoding='utf-8')
s = s.replace('const LEGACY = "https://calabriavera-e08d4.web.app";\n\n', '')
s = s.replace('`${LEGACY}/assets/images/home/tropea-960.webp`', '"/assets/images/home/tropea-960.webp"')
s = s.replace('`${LEGACY}/assets/images/home/sila-720.webp`', '"/assets/images/home/sila-720.webp"')
s = s.replace('`${LEGACY}/assets/images/home/scilla-720.webp`', '"/assets/images/home/scilla-720.webp"')
s = s.replace('`${LEGACY}/assets/images/home/capo-colonna-720.webp`', '"/assets/images/home/capo-colonna-720.webp"')
s = s.replace('src={`${LEGACY}/assets/Logo.webp`}', 'src="/assets/Logo.png"')
p.write_text(s, encoding='utf-8')

p = root / 'frontend-react/src/components/Layout.tsx'
s = p.read_text(encoding='utf-8')
s = s.replace('const LOGO = "https://calabriavera-e08d4.web.app/assets/Logo.webp";', 'const LOGO = "/assets/Logo.webp";')
s = s.replace('<img src={LOGO} alt="CalabriaVera" width="160" height="56" decoding="async" />', '<img src={LOGO} alt="CalabriaVera" width="188" height="46" decoding="async" />')
s = s.replace('<img src={LOGO} alt="CalabriaVera" width="180" height="64" loading="lazy" />', '<img src={LOGO} alt="CalabriaVera" width="188" height="46" loading="lazy" />')
# Main footer has no separate React-only copyright/tagline strip.
s = s.replace('\n        <div className="container cv-site-footer__bottom"><span>© {new Date().getFullYear()} CalabriaVera</span><span>{uiText("footerTagline", language)}</span></div>', '')
p.write_text(s, encoding='utf-8')

# Exact public-page headings used by main across the five languages.
p = root / 'frontend-react/src/lib/language.ts'
s = p.read_text(encoding='utf-8')
repls = {
    'mapTitle: "Mappa CalabriaVera"': 'mapTitle: "Mappa delle attività in Calabria"',
    'magazineTitle: "Eventi, territori e notizie"': 'magazineTitle: "Vivi la Calabria"',
    'homeTitle: "Businesses and places in Calabria"': 'homeTitle: "Activities and places in Calabria"',
    'catalogTitle: "Business directory"': 'catalogTitle: "Business catalog"',
    'mapTitle: "CalabriaVera map"': 'mapTitle: "Map of businesses in Calabria"',
    'magazineTitle: "Events, places and news"': 'magazineTitle: "Experience Calabria"',
    'mapTitle: "Carte CalabriaVera"': 'mapTitle: "Carte des activités en Calabre"',
    'magazineTitle: "Événements, territoires et actualités"': 'magazineTitle: "Vivez la Calabre"',
    'mapTitle: "CalabriaVera Karte"': 'mapTitle: "Karte der Betriebe in Kalabrien"',
    'magazineTitle: "Events, Orte und Nachrichten"': 'magazineTitle: "Kalabrien erleben"',
    'catalogTitle: "Catálogo de actividades"': 'catalogTitle: "Catálogo de negocios"',
    'mapTitle: "Mapa CalabriaVera"': 'mapTitle: "Mapa de negocios en Calabria"',
    'magazineTitle: "Eventos, lugares y noticias"': 'magazineTitle: "Vive Calabria"',
}
for old,new in repls.items(): s = s.replace(old,new)
p.write_text(s, encoding='utf-8')

# Keep prerender titles in sync with the exact visible main wording.
p = root / 'frontend-react/scripts/prerender-home.mjs'
s = p.read_text(encoding='utf-8')
for old,new in {
    'CalabriaVera | Businesses and places in Calabria':'CalabriaVera | Activities and places in Calabria',
    'Business directory | CalabriaVera':'Business catalog | CalabriaVera',
    'Events, places and news | CalabriaVera':'Experience Calabria | CalabriaVera',
    'Événements, territoires et actualités | CalabriaVera':'Vivez la Calabre | CalabriaVera',
    'Events, Orte und Nachrichten | CalabriaVera':'Kalabrien erleben | CalabriaVera',
    'Catálogo de actividades | CalabriaVera':'Catálogo de negocios | CalabriaVera',
    'Eventos, lugares y noticias | CalabriaVera':'Vive Calabria | CalabriaVera',
}.items(): s = s.replace(old,new)
p.write_text(s, encoding='utf-8')

# Exact local legacy pages from Assets, not the historical web.app proxy.
p = root / 'frontend-react/worker.ts'
s = p.read_text(encoding='utf-8')
old = '''      if (url.pathname.startsWith("/legacy/")) {\n        const targetPath = `/${url.pathname.slice("/legacy/".length)}`;\n        if (!LEGACY_HTML.has(targetPath)) return new Response("Not Found", { status: 404 });\n        return proxy(request, targetPath, "text/html,application/xhtml+xml", 3600);\n      }'''
new = '''      if (url.pathname.startsWith("/legacy/")) {\n        const targetPath = `/${url.pathname.slice("/legacy/".length)}`;\n        if (!LEGACY_HTML.has(targetPath)) return new Response("Not Found", { status: 404 });\n        const local = await env.ASSETS.fetch(request);\n        if (!local.ok) return new Response("Not Found", { status: 404 });\n        const headers = new Headers(local.headers);\n        headers.set("Cache-Control", "public, max-age=300, s-maxage=3600, stale-while-revalidate=86400");\n        headers.set("X-Content-Type-Options", "nosniff");\n        return new Response(request.method === "HEAD" ? null : local.body, { status: local.status, headers });\n      }'''
if old in s: s = s.replace(old,new,1)
elif 'url.pathname.startsWith("/legacy/")' in s and 'const local = await env.ASSETS.fetch(request);' not in s: raise SystemExit('legacy worker block changed unexpectedly')
p.write_text(s, encoding='utf-8')

# Final shell override mirrors the stable dimensions/colors loaded last on main.
p = root / 'frontend-react/src/styles.css'
s = p.read_text(encoding='utf-8')
marker = '/* cv-main-shell-parity */'
if marker not in s:
    s += r'''

/* cv-main-shell-parity */
:root{--cv-navy:#002f55;--cv-navy2:#002642;--cv-gold:#ffb000;--cv-ink:#101c2b;--cv-muted:#697586;--cv-line:#e4e9ee}
.container{width:min(calc(100% - 48px),1400px);max-width:none;margin-inline:auto}
.cv-site-header{position:relative!important;background:linear-gradient(90deg,#002642,#00365d)!important;box-shadow:none!important}
.cv-site-header__inner{width:min(calc(100% - 48px),1480px)!important;min-height:58px!important;gap:22px!important}
.cv-brand{flex:0 0 auto}.cv-brand img{width:188px!important;height:46px!important;object-fit:contain!important}
.cv-desktop-nav{display:flex!important;align-items:center!important;justify-content:center!important;gap:22px!important;flex:1!important;min-width:0!important;height:58px!important;margin-left:0!important}
.cv-desktop-nav a{position:relative!important;font-size:12px!important;font-weight:760!important;white-space:nowrap!important;height:58px!important;padding:0!important;border-bottom:0!important}
.cv-desktop-nav a.is-active:after{content:"";position:absolute;left:0;right:0;bottom:5px;height:3px;border-radius:3px;background:var(--cv-gold)}
.cv-header-actions{gap:8px!important}.cv-login-button,.cv-register-button{border:0!important;border-radius:9px!important;min-height:38px!important;padding:8px 16px!important;font-weight:850!important}.cv-register-button{background:var(--cv-gold)!important;color:#0a2941!important}.cv-login-button{background:rgba(255,255,255,.08)!important;color:#fff!important}
.cv-site-footer{margin-top:0!important;background:#002f55!important}.cv-site-footer__grid{grid-template-columns:1.45fr 1fr 1fr!important;gap:54px!important;padding:38px 0 34px!important}.cv-footer-brand img{width:188px!important;height:46px!important;object-fit:contain!important}.cv-footer-brand-copy{max-width:430px}
@media(max-width:900px){.container{width:min(calc(100% - 32px),1400px)}.cv-site-header__inner{width:min(calc(100% - 32px),1480px)!important}.cv-brand img{width:150px!important}.cv-site-footer__grid{grid-template-columns:1fr 1fr!important}.cv-desktop-nav{display:none!important}.cv-menu-button{display:block!important}}
@media(max-width:620px){.cv-site-footer__grid{grid-template-columns:1fr!important}.cv-brand img{width:132px!important}.cv-guest-actions{display:none!important}}
'''
p.write_text(s, encoding='utf-8')

print('React shell, local assets, full tourism and copy parity patch applied')
