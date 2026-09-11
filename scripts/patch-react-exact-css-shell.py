from pathlib import Path

root = Path('source')

# Stop bundling all legacy CSS into one stylesheet. Copy the exact source files instead.
p = root / 'frontend-react/scripts/copy-legacy-assets.mjs'
s = p.read_text(encoding='utf-8')
marker = '\n\nconst parityCssFiles = ['
if marker in s:
    s = s.split(marker, 1)[0].rstrip() + '\n'
css_copy = r'''

const parityCssFiles = [
  "assets/css/reset.css",
  "assets/css/variables.css",
  "assets/css/global.css",
  "assets/css/layout.css",
  "assets/css/components.css",
  "assets/css/responsive.css",
  "assets/css/portal-refresh.css",
  "assets/css/home-reference.css",
  "assets/css/reference-replica.css",
  "assets/css/redesign-runtime.css",
  "assets/css/redesign-functional.css",
  "assets/css/redesign-final.css",
  "assets/css/catalog-activity-cover.css",
  "assets/css/map-clean.css",
  "assets/css/language-modern.css",
];
for (const relative of parityCssFiles) {
  const source = resolve(repoRoot, relative);
  if (!existsSync(source)) throw new Error(`CSS main non trovato: ${source}`);
  const target = resolve(reactRoot, "public", relative);
  mkdirSync(dirname(target), { recursive: true });
  copyFileSync(source, target);
}
console.log(`CSS main copiati separatamente: ${parityCssFiles.length}`);
'''
if 'CSS main copiati separatamente' not in s:
    s += css_copy
p.write_text(s, encoding='utf-8')

# Remove the approximate concatenated stylesheet import.
p = root / 'frontend-react/src/main.tsx'
s = p.read_text(encoding='utf-8').replace('import "./generated/main-parity.css";\n', '')
p.write_text(s, encoding='utf-8')

p = root / 'frontend-react/src/components/Layout.tsx'
s = p.read_text(encoding='utf-8')

helper = r'''
const MAIN_COMMON_CSS = [
  "/assets/css/reset.css",
  "/assets/css/variables.css",
  "/assets/css/global.css",
  "/assets/css/layout.css",
  "/assets/css/components.css",
  "/assets/css/responsive.css",
] as const;

function exactMainCss(path: string) {
  if (path === "/") return [...MAIN_COMMON_CSS, "/assets/css/home-reference.css", "/assets/css/reference-replica.css", "/assets/css/redesign-runtime.css", "/assets/css/redesign-functional.css", "/assets/css/redesign-final.css"];
  if (path === "/catalogo") return [...MAIN_COMMON_CSS, "/assets/css/reference-replica.css", "/assets/css/redesign-runtime.css", "/assets/css/redesign-functional.css", "/assets/css/catalog-activity-cover.css"];
  if (path === "/mappa") return [...MAIN_COMMON_CSS, "/assets/css/reference-replica.css", "/assets/css/redesign-runtime.css", "/assets/css/redesign-functional.css", "/assets/css/map-clean.css"];
  if (path === "/blog" || path.startsWith("/blog/")) return [...MAIN_COMMON_CSS, "/assets/css/reference-replica.css", "/assets/css/redesign-runtime.css", "/assets/css/redesign-functional.css"];
  return [];
}
'''
if 'const MAIN_COMMON_CSS' not in s:
    s = s.replace('const langs = ["it", "en", "fr", "de", "es"] as const;\n', 'const langs = ["it", "en", "fr", "de", "es"] as const;\n' + helper + '\n', 1)

# Add route-exact styles after body[data-page] is set. Files remain separate, preserving @import semantics and cascade order.
body_effect_end = '  }, [snapshot, cleanPath]);\n\n  useEffect(() => {\n    if (!user) { setFavoriteCount(0); return; }'
style_effect = r'''  }, [snapshot, cleanPath]);

  useEffect(() => {
    const expected = exactMainCss(cleanPath);
    document.querySelectorAll<HTMLLinkElement>('link[data-cv-main-parity]').forEach((node) => node.remove());
    for (const href of expected) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      link.dataset.cvMainParity = "";
      document.head.appendChild(link);
    }
    return () => document.querySelectorAll<HTMLLinkElement>('link[data-cv-main-parity]').forEach((node) => node.remove());
  }, [snapshot, cleanPath]);

  useEffect(() => {
    if (!user) { setFavoriteCount(0); return; }'''
if 'link[data-cv-main-parity]' not in s:
    if body_effect_end not in s:
        raise SystemExit('Layout style insertion marker missing')
    s = s.replace(body_effect_end, style_effect, 1)

# Add the exact legacy class hooks used by main CSS, without removing React classes/behavior.
replacements = {
  '<header className="cv-site-header">': '<header className="cv-site-header site-header cv-header">',
  '<div className="container cv-site-header__inner">': '<div className="container cv-site-header__inner header-inner">',
  'className="cv-brand" aria-label="CalabriaVera home"': 'className="cv-brand brand" aria-label="CalabriaVera home"',
  '<img src={LOGO} alt="CalabriaVera" width="188" height="46" decoding="async" />': '<img className="brand-logo" src={LOGO} alt="CalabriaVera" width="188" height="46" decoding="async" />',
  '<nav className="cv-desktop-nav" aria-label="Navigazione principale">': '<nav className="cv-desktop-nav primary-nav" aria-label="Navigazione principale">',
  '<div className="cv-header-actions">': '<div className="cv-header-actions header-actions">',
  '<label className="cv-language-select" aria-label="Lingua">': '<label className="cv-language-select header-language" aria-label="Lingua">',
  '<details className="cv-account-menu">': '<details className="cv-account-menu account-menu">',
  '<div className="cv-account-popover">': '<div className="cv-account-popover account-links">',
  'className="cv-menu-button" onClick=': 'className="cv-menu-button menu-button" onClick=',
  'className="cv-mobile-menu" aria-label="Navigazione mobile"': 'className="cv-mobile-menu primary-mobile" aria-label="Navigazione mobile"',
  '<main className="cv-site-main">': '<main id="main-content" className="cv-site-main">',
  '<footer className="cv-site-footer">': '<footer className="cv-site-footer footer">',
  '<div className="container cv-site-footer__grid">': '<div className="container cv-site-footer__grid footer-grid">',
  '<div className="cv-footer-brand-copy">': '<div className="cv-footer-brand-copy footer-brand-copy">',
  '<img src={LOGO} alt="CalabriaVera" width="188" height="46" loading="lazy" />': '<img className="footer-logo" src={LOGO} alt="CalabriaVera" width="188" height="46" loading="lazy" />',
  '<div className="cv-footer-contact">': '<div className="cv-footer-contact footer-contact">',
  'className="cv-whatsapp-float"': 'className="cv-whatsapp-float whatsapp-float"',
}
for old, new in replacements.items():
    if old in s:
        s = s.replace(old, new)

# Guest action aliases occur in both placeholder and logged-out markup.
s = s.replace('className="cv-guest-actions cv-auth-placeholder"', 'className="cv-guest-actions guest-actions cv-auth-placeholder"')
s = s.replace('className="cv-guest-actions"><Link', 'className="cv-guest-actions guest-actions"><Link')

p.write_text(s, encoding='utf-8')
print('Exact per-route main CSS and legacy shell hooks applied')
