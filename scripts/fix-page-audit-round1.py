from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
copy_script = root / 'frontend-react/scripts/copy-static-assets.mjs'
home = root / 'frontend-react/src/pages/HomePage.tsx'
tests = root / 'tests/site-stability.test.mjs'


def read(path):
    return path.read_text(encoding='utf-8')


def write(path, text):
    path.write_text(text, encoding='utf-8')

# Copy the flag assets that the shared language selector references at runtime.
s = read(copy_script)
anchor = '  "assets/site.webmanifest",\n'
flags = ''.join(f'  "assets/flags/{lang}.svg",\n' for lang in ('it', 'en', 'fr', 'de', 'es'))
if '"assets/flags/it.svg"' not in s:
    if anchor not in s:
        raise SystemExit('copy-static-assets: manifest anchor not found')
    s = s.replace(anchor, anchor + flags)
write(copy_script, s)

# Home: render featured cards from the prerendered public snapshot immediately,
# then refresh them in the background with the narrow Firestore featured query.
s = read(home)
old_import = 'import { CATEGORIES, loadFeaturedBusinesses } from "../lib/businesses";\n'
new_import = old_import + 'import { readInlineBusinesses } from "../lib/public-data";\n'
if 'readInlineBusinesses' not in s:
    if old_import not in s:
        raise SystemExit('HomePage: businesses import not found')
    s = s.replace(old_import, new_import)

state_old = '  const [featured, setFeatured] = useState<Business[] | null>(null);\n'
state_new = '''  const [featured, setFeatured] = useState<Business[] | null>(() => {\n    const inline = readInlineBusinesses();\n    if (!inline.length) return null;\n    return [...inline]\n      .sort((a, b) => Number(b.rating || 0) - Number(a.rating || 0) || String(a.name || \"\").localeCompare(String(b.name || \"\"), \"it\"))\n      .slice(0, 6);\n  });\n'''
if state_old in s:
    s = s.replace(state_old, state_new)
elif 'const inline = readInlineBusinesses();' not in s:
    raise SystemExit('HomePage: featured state not found')
write(home, s)

# Regression contract.
s = read(tests)
marker = "React Home parte dallo snapshot e il build copia le bandiere lingua"
if marker not in s:
    s += r'''

test('React Home parte dallo snapshot e il build copia le bandiere lingua', () => {
  const home = read('frontend-react/src/pages/HomePage.tsx');
  const copy = read('frontend-react/scripts/copy-static-assets.mjs');
  assert.match(home, /readInlineBusinesses/);
  assert.match(home, /const inline = readInlineBusinesses\(\)/);
  assert.doesNotMatch(home, /useState<Business\[\] \| null>\(null\)/);
  for (const lang of ['it', 'en', 'fr', 'de', 'es']) {
    assert.ok(copy.includes(`assets/flags/${lang}.svg`), `bandiera ${lang} non copiata nel build React`);
  }
});
'''
write(tests, s)

print('Page audit round 1 patch applied')
