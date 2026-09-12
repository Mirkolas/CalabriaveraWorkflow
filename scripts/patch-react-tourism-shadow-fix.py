from pathlib import Path

root = Path('source/frontend-react')
copy_script = root / 'scripts/copy-legacy-assets.mjs'
text = copy_script.read_text(encoding='utf-8')
old = 'import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";'
new = 'import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";'
if new not in text:
    if old not in text: raise SystemExit('fs import anchor missing')
    text = text.replace(old, new, 1)
anchor = 'const tourismTarget = resolve(generatedDir, "tourism-data-core.ts");\n'
insert = '''const tourismTarget = resolve(generatedDir, "tourism-data-core.ts");
const tourismShadowTargets = [
  resolve(generatedDir, "tourism-data-core.js"),
  resolve(generatedDir, "tourism-data-core.d.ts"),
];
for (const shadow of tourismShadowTargets) {
  if (existsSync(shadow)) rmSync(shadow, { force: true });
}
'''
if 'const tourismShadowTargets = [' not in text:
    if anchor not in text: raise SystemExit('tourism target anchor missing')
    text = text.replace(anchor, insert, 1)
copy_script.write_text(text, encoding='utf-8')

for shadow in [root / 'src/generated/tourism-data-core.js', root / 'src/generated/tourism-data-core.d.ts']:
    if shadow.exists(): shadow.unlink()

map_page = root / 'src/pages/MapPage.tsx'
map_text = map_page.read_text(encoding='utf-8')
map_text = map_text.replace('<label style={{display:"none"}}><span><input id="verified" hidden type="checkbox"', '<label><span><input id="verified" type="checkbox"')
map_text = map_text.replace('<div id="map-results" hidden className="stack" style={{marginTop:12}} />', '<div id="map-results" className="stack" style={{marginTop:12}} />')
map_page.write_text(map_text, encoding='utf-8')

print('Removed stale generated JS/DTS shadow files and restored exact Map control visibility.')
