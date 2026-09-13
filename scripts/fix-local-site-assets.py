from pathlib import Path
import re
import sys

root = Path(sys.argv[1]).resolve()


def read(rel):
    return (root / rel).read_text(encoding="utf-8")


def write(rel, text):
    path = root / rel
    path.write_text(text, encoding="utf-8")
    print(f"updated {rel}")


def replace_required(text, old, new, label):
    if old not in text:
        if new in text:
            return text
        raise SystemExit(f"marker missing for {label}")
    return text.replace(old, new)

# 1) Shared header: local canonical assets + only Home in primary navigation.
layout_rel = "frontend-react/src/components/Layout.tsx"
layout = read(layout_rel)
layout = replace_required(layout,
    'const LOGO = "https://img.calabriavera.com/static/assets/Logo.webp";',
    'const LOGO = "/assets/Logo.webp";',
    "local header logo")
layout = replace_required(layout,
    'const FLAG_CDN = "https://img.calabriavera.com/static/assets/flags";',
    'const FLAG_CDN = "/assets/flags";',
    "local flags")
nav_pattern = re.compile(r'  const nav = \[\n(?:.*\n)*?  \] as const;', re.MULTILINE)
nav_new = '  const nav = [\n    [uiText("home", language), withLanguage("/", language), "home"],\n  ] as const;'
if not nav_pattern.search(layout):
    if nav_new not in layout:
        raise SystemExit("primary nav block not found")
else:
    layout = nav_pattern.sub(nav_new, layout, count=1)
write(layout_rel, layout)

# 2) All site-facing React/CSS static references use the repository /assets tree.
# User/business R2 URLs do not use /static/assets and therefore are left untouched.
site_paths = [root / "frontend-react" / "index.html", root / "assets" / "site.webmanifest"]
site_paths += list((root / "frontend-react" / "src").rglob("*.ts"))
site_paths += list((root / "frontend-react" / "src").rglob("*.tsx"))
site_paths += list((root / "frontend-react" / "src").rglob("*.css"))
site_paths += list((root / "assets" / "css").rglob("*.css"))
for path in dict.fromkeys(site_paths):
    text = path.read_text(encoding="utf-8")
    updated = text.replace("https://img.calabriavera.com/static/assets/", "/assets/")
    if updated != text:
        path.write_text(updated, encoding="utf-8")
        print(f"updated {path.relative_to(root)}")

# OriginalHomePage used a CDN prefix variable; make it local explicitly.
home_rel = "frontend-react/src/pages/OriginalHomePage.tsx"
home = read(home_rel)
home = replace_required(home,
    'const STATIC_IMAGE_CDN = "https://img.calabriavera.com/static";',
    'const STATIC_IMAGE_CDN = "";',
    "local home asset base")
write(home_rel, home)

# 3) Canonical favicon set from repository assets. Cache-bust the HTML references.
index_rel = "frontend-react/index.html"
index = read(index_rel)
index = re.sub(
    r'    <link rel="manifest"[^\n]*\n(?:    <link rel="(?:icon|shortcut icon|apple-touch-icon)"[^\n]*\n)+',
    '    <link rel="manifest" href="/assets/site.webmanifest?v=20260913-local" />\n'
    '    <link rel="icon" href="/assets/favicon.ico?v=20260913-local" sizes="any" />\n'
    '    <link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32x32.png?v=20260913-local" />\n'
    '    <link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16x16.png?v=20260913-local" />\n'
    '    <link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png?v=20260913-local" />\n',
    index,
    count=1,
)
index = index.replace('href="https://img.calabriavera.com/static/assets/Logo.webp"', 'href="/assets/Logo.webp"')
index = index.replace('href="https://img.calabriavera.com/static/assets/images/home/tropea-1600.webp"', 'href="/assets/images/home/tropea-1600.webp"')
write(index_rel, index)

# 4) Manifest PWA uses the repository icons served by calabriavera.com.
manifest_rel = "assets/site.webmanifest"
manifest = read(manifest_rel)
manifest = manifest.replace('"/assets/android-chrome-192x192.png"', '"/assets/android-chrome-192x192.png?v=20260913-local"')
manifest = manifest.replace('"/assets/android-chrome-512x512.png"', '"/assets/android-chrome-512x512.png?v=20260913-local"')
write(manifest_rel, manifest)

# 5) Copy canonical static assets, explicitly keeping both Blog fallbacks and Story artwork.
copy_rel = "frontend-react/scripts/copy-legacy-assets.mjs"
copy = read(copy_rel)
anchor = '  "assets/css/privacy-consent.css",\n'
extra = (
    '  "assets/Story-Promo_instagram-facebook.png",\n'
    '  "assets/images/blog-default-events.png", "assets/images/blog-default-news.png",\n'
    '  "assets/images/og-calabriavera.png", "assets/images/social-calabriavera.jpg",\n'
    '  "assets/images/story-promo-attivita.jpg", "assets/images/story-promo-attivita.svg",\n'
)
if "assets/Story-Promo_instagram-facebook.png" not in copy:
    if anchor not in copy:
        raise SystemExit("copy asset list anchor missing")
    copy = copy.replace(anchor, anchor + extra, 1)
write(copy_rel, copy)

# 6) Static site assets are intentionally local. R2 remains for user/business images only.
prune_rel = "frontend-react/scripts/prune-local-image-assets.mjs"
prune = '''import { existsSync } from "node:fs";\nimport { resolve } from "node:path";\nimport { fileURLToPath } from "node:url";\n\nconst reactRoot = resolve(fileURLToPath(new URL("..", import.meta.url)));\nconst publicRoot = resolve(reactRoot, "public");\n\nconst REQUIRED_LOCAL_SITE_ASSETS = [\n  "assets/Logo.webp",\n  "assets/Logo.png",\n  "assets/favicon.ico",\n  "assets/favicon-16x16.png",\n  "assets/favicon-32x32.png",\n  "assets/apple-touch-icon.png",\n  "assets/android-chrome-192x192.png",\n  "assets/android-chrome-512x512.png",\n  "assets/flags/it.svg",\n  "assets/flags/en.svg",\n  "assets/flags/fr.svg",\n  "assets/flags/de.svg",\n  "assets/flags/es.svg",\n  "assets/Story-Promo_instagram-facebook.png",\n  "assets/images/blog-default-events.png",\n  "assets/images/blog-default-news.png",\n  "assets/images/home/tropea-960.webp",\n  "assets/images/home/tropea-1600.webp",\n  "assets/images/home/sila-720.webp",\n  "assets/images/home/sila-1280.webp",\n  "assets/images/home/scilla-720.webp",\n  "assets/images/home/capo-colonna-720.webp",\n];\n\nconst missing = REQUIRED_LOCAL_SITE_ASSETS.filter((relative) => !existsSync(resolve(publicRoot, relative)));\nif (missing.length) throw new Error(`Asset statici locali mancanti dal bundle React: ${missing.join(", ")}`);\nconsole.log(`Asset statici del sito mantenuti localmente: ${REQUIRED_LOCAL_SITE_ASSETS.length}. R2 resta dedicato alle immagini business/utente.`);\n'''
write(prune_rel, prune)

# 7) Architecture contract: local site assets + R2 only for uploaded business images.
arch_rel = "frontend-react/scripts/verify-runtime-architecture.mjs"
arch = read(arch_rel)
if 'const magazinePage = readFileSync(resolve(root, "src/pages/MagazinePage.tsx"), "utf8");' not in arch:
    arch = arch.replace(
        'const home = readFileSync(resolve(root, "src/pages/OriginalHomePage.tsx"), "utf8");\n',
        'const home = readFileSync(resolve(root, "src/pages/OriginalHomePage.tsx"), "utf8");\nconst magazinePage = readFileSync(resolve(root, "src/pages/MagazinePage.tsx"), "utf8");\n',
        1,
    )
start = arch.find('const staticImageSources = ')
end = arch.find('\nif (failures.length)', start)
if start < 0 or end < 0:
    raise SystemExit("architecture static block not found")
new_static = '''const staticImageSources = `${layout}\\n${home}\\n${magazinePage}\\n${indexHtml}\\n${languageCss}\\n${referenceCss}\\n${manifest}`;\nif (/https:\\/\\/img[.]calabriavera[.]com\\/static\\//.test(staticImageSources)) failures.push("Gli asset grafici del sito devono essere serviti da /assets della produzione, non dal CDN statico R2.");\nconst requiredLocalSiteAssets = [\n  "assets/Logo.webp", "assets/Logo.png", "assets/favicon.ico", "assets/favicon-16x16.png", "assets/favicon-32x32.png",\n  "assets/apple-touch-icon.png", "assets/android-chrome-192x192.png", "assets/android-chrome-512x512.png",\n  "assets/flags/it.svg", "assets/flags/en.svg", "assets/flags/fr.svg", "assets/flags/de.svg", "assets/flags/es.svg",\n  "assets/Story-Promo_instagram-facebook.png", "assets/images/blog-default-events.png", "assets/images/blog-default-news.png",\n];\nfor (const relative of requiredLocalSiteAssets) {\n  if (!existsSync(resolve(repoRoot, relative))) failures.push(`Asset canonico mancante nel repository: ${relative}`);\n  if (!existsSync(resolve(root, "public", relative))) failures.push(`Asset canonico non copiato nel bundle React: ${relative}`);\n}\nif (!/const LOGO = "\\/assets\\/Logo[.]webp"/.test(layout)) failures.push("L'header deve usare /assets/Logo.webp.");\nif (!/const FLAG_CDN = "\\/assets\\/flags"/.test(layout)) failures.push("Il selettore lingua deve usare /assets/flags.");\nif (!/blog-default-events[.]png/.test(magazinePage) || !/blog-default-news[.]png/.test(magazinePage)) failures.push("Le due immagini fallback Blog devono restare disponibili.");\n'''
arch = arch[:start] + new_static + arch[end:]
arch = arch.replace(
    'console.log("Architettura runtime verificata: Firebase Auth/Firestore + R2 + Worker, D1 assente, nessun fallback immagini business su Firestore e asset statici immagine serviti da R2.");',
    'console.log("Architettura runtime verificata: Firebase Auth/Firestore + R2 per immagini business/utente + asset grafici del sito serviti da /assets, D1 assente.");'
)
write(arch_rel, arch)

# 8) Regression tests for local assets and Home-only primary nav.
test_rel = "tests/site-stability.test.mjs"
test = read(test_rel)
old_test = '''test('React language selector usa le bandiere dal CDN R2', () => {\n  const layout = read('frontend-react/src/components/Layout.tsx');\n  assert.match(layout, /https:\\\/\\\/img\\.calabriavera\\.com\\/static\\/assets\\/flags/);\n  assert.match(layout, /style=\\{flagStyle\\(language\\)\\}/);\n  assert.match(layout, /style=\\{flagStyle\\(lang\\)\\}/);\n  assert.doesNotMatch(layout, /["'`]\\/assets\\/flags\\//);\n});'''
new_test = '''test('React usa logo e bandiere canonici dalla cartella assets locale', () => {\n  const layout = read('frontend-react/src/components/Layout.tsx');\n  assert.match(layout, /const LOGO = "\\/assets\\/Logo\\.webp"/);\n  assert.match(layout, /const FLAG_CDN = "\\/assets\\/flags"/);\n  assert.match(layout, /style=\\{flagStyle\\(language\\)\\}/);\n  assert.match(layout, /style=\\{flagStyle\\(lang\\)\\}/);\n  assert.doesNotMatch(layout, /img\\.calabriavera\\.com\\/static\\/assets\\/flags/);\n});\n\ntest('header pubblico mantiene solo Home nella navigazione primaria', () => {\n  const layout = read('frontend-react/src/components/Layout.tsx');\n  const block = layout.match(/const nav = \\[([\\s\\S]*?)\\] as const;/)?.[1] || '';\n  assert.match(block, /uiText\\("home", language\\)/);\n  assert.doesNotMatch(block, /uiText\\("explore"|"map"|"magazine"|"about"/);\n});\n\ntest('favicon e immagini Blog usano gli asset canonici locali', () => {\n  const html = read('frontend-react/index.html');\n  const blog = read('frontend-react/src/pages/MagazinePage.tsx');\n  assert.match(html, /href="\\/assets\\/favicon\\.ico\\?v=/);\n  assert.match(html, /href="\\/assets\\/favicon-32x32\\.png\\?v=/);\n  assert.match(html, /href="\\/assets\\/apple-touch-icon\\.png\\?v=/);\n  assert.match(blog, /\\/assets\\/images\\/blog-default-events\\.png/);\n  assert.match(blog, /\\/assets\\/images\\/blog-default-news\\.png/);\n});'''
if old_test in test:
    test = test.replace(old_test, new_test, 1)
elif "header pubblico mantiene solo Home" not in test:
    raise SystemExit("language selector regression test not found")
write(test_rel, test)

print("Local site assets repair prepared successfully")
