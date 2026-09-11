from pathlib import Path

root = Path('source/frontend-react')
copy_script = root / 'scripts/copy-legacy-assets.mjs'
language_file = root / 'src/lib/language.ts'
layout_file = root / 'src/components/Layout.tsx'

# 1) Copy the exact flag assets used by main's language-modern.css.
s = copy_script.read_text()
needle = '  "assets/Logo.webp", "assets/Logo.png", "assets/site.webmanifest", "assets/favicon.ico", "assets/favicon-16x16.png", "assets/favicon-32x32.png", "assets/apple-touch-icon.png", "assets/android-chrome-192x192.png", "assets/android-chrome-512x512.png",\n'
replacement = '  "assets/Logo.webp", "assets/Logo.png", "assets/site.webmanifest", "assets/favicon.ico", "assets/favicon-16x16.png", "assets/favicon-32x32.png", "assets/apple-touch-icon.png", "assets/android-chrome-192x192.png", "assets/android-chrome-512x512.png",\n  "assets/flags/it.svg", "assets/flags/en.svg", "assets/flags/fr.svg", "assets/flags/de.svg", "assets/flags/es.svg",\n'
if needle not in s:
    raise SystemExit('assetFiles anchor not found')
s = s.replace(needle, replacement, 1)
copy_script.write_text(s)

# 2) Use a footer-specific activity label, because main says "Attività" while the nav/catalog route says "Catalogo".
s = language_file.read_text()
replacements = [
    ('footerCopy: "Scopri la Calabria, trova attività e vivi il territorio."', 'footerActivities: "Attività", footerCopy: "Scopri la Calabria, trova attività e vivi il territorio."'),
    ('footerCopy: "Discover Calabria, find local businesses and experience the region."', 'footerActivities: "Activities", footerCopy: "Discover Calabria, find local businesses and experience the region."'),
]
for old, new in replacements:
    if old not in s:
        raise SystemExit(f'language anchor not found: {old}')
    s = s.replace(old, new, 1)

# FR/DE/ES inherit EN, so override the footer label explicitly near their language-specific navigation keys.
lang_overrides = [
    ('...EN, home: "Accueil", explore: "Explorer", catalog: "Catalogue",', '...EN, home: "Accueil", explore: "Explorer", catalog: "Catalogue", footerActivities: "Activités",'),
    ('...EN, home: "Startseite", explore: "Entdecken", catalog: "Katalog",', '...EN, home: "Startseite", explore: "Entdecken", catalog: "Katalog", footerActivities: "Aktivitäten",'),
    ('...EN, home: "Inicio", explore: "Explorar", catalog: "Catálogo",', '...EN, home: "Inicio", explore: "Explorar", catalog: "Catálogo", footerActivities: "Actividades",'),
]
for old, new in lang_overrides:
    if old not in s:
        raise SystemExit(f'language override anchor not found: {old}')
    s = s.replace(old, new, 1)
language_file.write_text(s)

# 3) Change only the footer link label, not the page/nav catalog wording.
s = layout_file.read_text()
old = '<Link href={withLanguage("/catalogo", language)}>{uiText("catalog", language)}</Link>'
new = '<Link href={withLanguage("/catalogo", language)}>{uiText("footerActivities", language)}</Link>'
if old not in s:
    raise SystemExit('footer catalog link anchor not found')
s = s.replace(old, new, 1)
layout_file.write_text(s)

print('Final flags/footer parity patch applied.')
