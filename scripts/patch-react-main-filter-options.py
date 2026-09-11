from pathlib import Path

root = Path('source/frontend-react')
copy_path = root / 'scripts/copy-legacy-assets.mjs'
catalog_path = root / 'src/pages/CatalogPage.tsx'
map_path = root / 'src/pages/MapPage.tsx'

# Generate the exact COMMON_CITIES list from main's canonical utils module during every React build.
s = copy_path.read_text()
anchor = 'console.log(`Modulo turismo TypeScript generato: ${tourismTarget} (${mergedTourism.length} schede curate)`);'
if anchor not in s:
    raise SystemExit('tourism generation anchor not found')
insert = anchor + r'''

const mainUtilsSource = resolve(repoRoot, "assets/js/utils.js");
if (!existsSync(mainUtilsSource)) throw new Error(`Utils main non trovato: ${mainUtilsSource}`);
const mainUtils = await import(pathToFileURL(mainUtilsSource).href);
const mainCities = [...(mainUtils.COMMON_CITIES || [])];
if (mainCities.length !== 116) throw new Error(`Parità comuni inattesa: ${mainCities.length}, attesi 116 dal main`);
if (new Set(mainCities).size !== mainCities.length) throw new Error('Comuni duplicati nel dataset main');
writeFileSync(resolve(generatedDir, "main-static-options.ts"), `export const MAIN_COMMON_CITIES = ${JSON.stringify(mainCities, null, 2)} as const;\n`, "utf8");
console.log(`Opzioni filtri main generate: ${mainCities.length} comuni`);'''
s = s.replace(anchor, insert, 1)
copy_path.write_text(s)

# Catalog: use the same 116 city options and the same dynamic counts shown by main.
c = catalog_path.read_text()
import_anchor = 'import { ALL_TOURISM } from "../lib/tourism-static";'
if import_anchor not in c:
    raise SystemExit('Catalog import anchor not found')
c = c.replace(import_anchor, import_anchor + '\nimport { MAIN_COMMON_CITIES } from "../generated/main-static-options";', 1)
old_cities = '  const cities = useMemo(() => [...new Set((items || []).filter((item) => !province || item.provincia === province).map((item) => String(item.comune || "")).filter(Boolean))].sort((a, b) => a.localeCompare(b, "it")), [items, province]);'
new_cities = '''  const cityCounts = useMemo(() => {\n    const counts = new Map<string, number>();\n    for (const item of items || []) {\n      const value = String(item.comune || "").trim();\n      if (value) counts.set(value, (counts.get(value) || 0) + 1);\n    }\n    return counts;\n  }, [items]);\n  const cities = MAIN_COMMON_CITIES;'''
if old_cities not in c:
    raise SystemExit('Catalog cities anchor not found')
c = c.replace(old_cities, new_cities, 1)

repls = {
    '<form className="stack" onSubmit=': '<form id="filters" className="stack" onSubmit=',
    '<input value={keyword} onChange=': '<input id="keyword" name="keyword" value={keyword} onChange=',
    '<select value={category} onChange=': '<select id="category" name="category" value={category} onChange=',
    '<select value={province} onChange=': '<select id="province" name="province" value={province} onChange=',
    '<select value={city} onChange=': '<select id="city" name="city" value={city} onChange=',
    '<input type="date" value={date} onChange=': '<input id="date" name="data" type="date" value={date} onChange=',
    '<input value={service} onChange=': '<input id="service" name="service" value={service} onChange=',
    '<input type="checkbox" checked={verified} onChange=': '<input id="verified" type="checkbox" checked={verified} onChange=',
    '<select value={sort} onChange=': '<select id="sort" value={sort} onChange=',
    '<button type="button" className="button button-secondary" onClick={locate}>': '<button id="near-me" type="button" className="button button-secondary" onClick={locate}>',
    '<select value={radius} onChange=': '<select id="near-radius" aria-label="Raggio ricerca vicino a me" value={radius} onChange=',
    '<span className="cv-near-active" aria-live="polite">': '<span id="near-status" className="cv-near-active" aria-live="polite">',
    '<button type="reset" className="button button-secondary">': '<button id="reset" type="reset" className="button button-secondary">',
    '<div className="result-toolbar"><p aria-live="polite">': '<div className="result-toolbar"><span id="result-count" className="muted" aria-live="polite">',
    '</p><Link className="button button-secondary"': '</span><Link className="button button-secondary"',
    '<div className="result-list" aria-live="polite">': '<div id="results" className="result-list" aria-live="polite">',
    '<button type="button" onClick={()=>setVisible': '<button id="load-more" type="button" onClick={()=>setVisible',
}
for old, new in repls.items():
    if old not in c:
        raise SystemExit(f'Catalog DOM anchor not found: {old}')
    c = c.replace(old, new, 1)
old_options = '{cities.map((value)=><option key={value}>{value}</option>)}'
new_options = '{cities.map((value)=><option key={value} value={value}>{`${value} (${cityCounts.get(value) || 0})`}</option>)}'
if old_options not in c:
    raise SystemExit('Catalog city option anchor not found')
c = c.replace(old_options, new_options, 1)
catalog_path.write_text(c)

# Map: main always exposes the same canonical 116 city options (without count labels).
m = map_path.read_text()
if import_anchor not in m:
    raise SystemExit('Map import anchor not found')
m = m.replace(import_anchor, import_anchor + '\nimport { MAIN_COMMON_CITIES } from "../generated/main-static-options";', 1)
old_map_cities = '  const cities = useMemo(() => [...new Set((items || []).filter((item) => !province || item.provincia === province).map((item) => String(item.comune || "")).filter(Boolean))].sort((a, b) => a.localeCompare(b, "it")), [items, province]);'
if old_map_cities not in m:
    raise SystemExit('Map cities anchor not found')
m = m.replace(old_map_cities, '  const cities = MAIN_COMMON_CITIES;', 1)
map_path.write_text(m)

print('Applied canonical main city/filter parity to Catalog and Map.')
