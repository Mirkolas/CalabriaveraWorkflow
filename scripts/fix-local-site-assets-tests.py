from pathlib import Path
import re
import sys

root = Path(sys.argv[1]).resolve()
path = root / "tests/site-stability.test.mjs"
text = path.read_text(encoding="utf-8")

replacement = r'''test('React usa logo e bandiere canonici dalla cartella assets locale', () => {
  const layout = read('frontend-react/src/components/Layout.tsx');
  assert.match(layout, /const LOGO = "\/assets\/Logo\.webp"/);
  assert.match(layout, /const FLAG_CDN = "\/assets\/flags"/);
  assert.match(layout, /style=\{flagStyle\(language\)\}/);
  assert.match(layout, /style=\{flagStyle\(lang\)\}/);
  assert.doesNotMatch(layout, /img\.calabriavera\.com\/static\/assets\/flags/);
});

test('header pubblico mantiene solo Home nella navigazione primaria', () => {
  const layout = read('frontend-react/src/components/Layout.tsx');
  const block = layout.match(/const nav = \[([\s\S]*?)\] as const;/)?.[1] || '';
  assert.match(block, /uiText\("home", language\)/);
  assert.doesNotMatch(block, /uiText\("explore"|"map"|"magazine"|"about"/);
});

test('favicon e immagini Blog usano gli asset canonici locali', () => {
  const html = read('frontend-react/index.html');
  const blog = read('frontend-react/src/pages/MagazinePage.tsx');
  assert.match(html, /href="\/assets\/favicon\.ico\?v=/);
  assert.match(html, /href="\/assets\/favicon-32x32\.png\?v=/);
  assert.match(html, /href="\/assets\/apple-touch-icon\.png\?v=/);
  assert.match(blog, /\/assets\/images\/blog-default-events\.png/);
  assert.match(blog, /\/assets\/images\/blog-default-news\.png/);
});'''

pattern = re.compile(r"test\('React language selector usa le bandiere dal CDN R2', \(\) => \{[\s\S]*?\n\}\);", re.MULTILINE)
if pattern.search(text):
    text = pattern.sub(lambda _m: replacement, text, count=1)
elif "header pubblico mantiene solo Home" not in text:
    raise SystemExit("language selector regression test not found")

path.write_text(text, encoding="utf-8")
print("updated tests/site-stability.test.mjs")
