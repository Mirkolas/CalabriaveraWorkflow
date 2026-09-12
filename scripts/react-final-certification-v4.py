#!/usr/bin/env python3
import json
from pathlib import Path

root = Path('source/frontend-react')
oracle = Path('oracle/dist')
route_map = json.loads((root / 'public/main-route-css.json').read_text())
css = route_map['routeCss']
pages = route_map['routePages']

expected_top = {
    '/404','/','/catalogo','/mappa','/blog','/blog/:detail','/attivita/:detail',
    '/login','/registrazione','/profilo','/preferiti','/dashboard','/messaggi',
    '/aggiungi-attivita','/chi-siamo','/contatti','/privacy-policy','/cookie-policy',
    '/termini','/note-legali','/backup','/admin','/admin/attivita','/admin/recensioni',
    '/admin/segnalazioni','/admin/blog','/admin/categorie','/admin/comuni','/admin/utenti',
    '/admin/messaggi','/admin/comunicazioni','/admin/seo','/admin/sistema','/admin/impostazioni'
}
missing = expected_top - set(css)
assert not missing, f'Route mancanti: {sorted(missing)}'
assert '/admin/backup' not in css and '/admin/backup' not in pages

unique_bundles = sorted({item for values in css.values() for item in values})
assert len(unique_bundles) == 9, unique_bundles
for url in unique_bundles:
    name = Path(url).name
    expected = oracle / 'assets/css' / name
    public = root / 'public/assets/css' / name
    built = root / 'dist/assets/css' / name
    assert expected.is_file(), f'Bundle oracle mancante: {name}'
    assert public.read_bytes() == expected.read_bytes(), f'CSS public diverso: {name}'
    assert built.read_bytes() == expected.read_bytes(), f'CSS dist diverso: {name}'
print(f'CSS route: {len(css)} route, {len(unique_bundles)} bundle byte-per-byte OK')

oracle_js = oracle / 'assets/js'
public_js = root / 'public/assets/js'
dist_js = root / 'dist/assets/js'
oracle_files = sorted(p.relative_to(oracle_js) for p in oracle_js.rglob('*') if p.is_file())
assert oracle_files
for rel in oracle_files:
    data = (oracle_js / rel).read_bytes()
    assert (public_js / rel).read_bytes() == data, f'Runtime public diverso: {rel}'
    assert (dist_js / rel).read_bytes() == data, f'Runtime dist diverso: {rel}'
assert sorted(p.relative_to(public_js) for p in public_js.rglob('*') if p.is_file()) == oracle_files
assert sorted(p.relative_to(dist_js) for p in dist_js.rglob('*') if p.is_file()) == oracle_files
print(f'Runtime legacy: {len(oracle_files)} file byte-per-byte OK')

app = (root / 'src/App.tsx').read_text()
layout = (root / 'src/components/Layout.tsx').read_text()
styles = (root / 'src/styles.css').read_text()
backup = (root / 'src/pages/BackupPage.tsx').read_text()
catalog = (root / 'src/pages/CatalogPage.tsx').read_text()
map_page = (root / 'src/pages/MapPage.tsx').read_text()
magazine = (root / 'src/pages/MagazinePage.tsx').read_text()
legal = (root / 'src/pages/LegalPage.tsx').read_text()

assert '<div id="site-footer">' in layout
assert 'id="toast-root"' in layout and 'aria-live="polite"' in layout
assert 'path === "/backup"' in app
assert 'ADMIN_ROUTES.has(path)' in app and 'path.startsWith("/admin/")' not in app
assert '.cv-legacy-content{display:contents}' in styles
assert '.cv-legacy-content h1' not in styles and '.cv-legacy-content p' not in styles

for fragment in ('Backup cifrati','Ripristino protetto','Controlla o avvia backup','Apri la guida'):
    assert fragment in backup, fragment
assert 'id="backup-root"' in backup
assert 'rel="noopener"' in backup and 'noopener noreferrer' not in backup

for value in ('id="filters"','id="keyword"','id="category"','id="province"','id="city"','id="verified"','id="sort"','id="result-count"','id="results"','id="load-more"'):
    assert value in catalog, f'Catalogo senza {value}'
assert 'LEGACY_CATALOG_SEARCH' in catalog and 'LEGACY_CATALOG_ALL' in catalog

for value in ('id="map"','id="map-count"','id="map-zoom"','id="map-filters"','id="category"','id="province"','id="city"','id="verified"','id="use-location"','id="map-fit-results"','id="map-near-radius"','cv-map-aside-head'):
    assert value in map_page, f'Mappa senza {value}'
for value in ('id="blog-lane-tabs"','id="blog-list"','id="blog-more"','data-blog-lane'):
    assert value in magazine, f'Blog senza {value}'
assert 'cv-blog-tabs-legacy-parity' in styles
assert 'LEGAL_IDENTITY' in legal and 'Titolare del sito e del trattamento' in legal

langs = ['', 'en', 'fr', 'de', 'es']
stable = ['catalogo','mappa','blog','chi-siamo','contatti','privacy-policy','cookie-policy','termini','note-legali']
for lang in langs:
    for route in stable:
        path = root / 'dist' / lang / route / 'index.html' if lang else root / 'dist' / route / 'index.html'
        assert path.is_file(), f'Prerender mancante: {path}'
assert (root / 'dist/index.html').is_file()
print('Route, shell, controlli, fix finali e prerender multilingua: OK')
