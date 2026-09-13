from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
styles = root / 'frontend-react/src/styles.css'
tests = root / 'tests/site-stability.test.mjs'


def read(path):
    return path.read_text(encoding='utf-8')


def write(path, text):
    path.write_text(text, encoding='utf-8')

s = read(styles)
marker = '/* cv-mobile-readable-content-cards */'
block = '''

/* cv-mobile-readable-content-cards
   On phone widths the legacy two-column card grids make titles, metadata and
   actions too small. Keep tablet/desktop parity, but use a readable single
   column on phones. */
@media (max-width: 560px) {
  body[data-page="catalog"] #results.result-list,
  body[data-page="blog"] #blog-list.card-grid {
    grid-template-columns: minmax(0, 1fr) !important;
  }
  body[data-page="catalog"] #results.result-list > *,
  body[data-page="blog"] #blog-list.card-grid > * {
    min-width: 0;
    width: 100%;
  }
}
'''
if marker not in s:
    s += block
write(styles, s)

s = read(tests)
test_marker = "Catalogo e Blog sono a una colonna sui telefoni"
if test_marker not in s:
    s += r'''

test('Catalogo e Blog sono a una colonna sui telefoni', () => {
  const styles = read('frontend-react/src/styles.css');
  assert.match(styles, /cv-mobile-readable-content-cards/);
  assert.match(styles, /body\[data-page="catalog"\] #results\.result-list/);
  assert.match(styles, /body\[data-page="blog"\] #blog-list\.card-grid/);
  assert.match(styles, /grid-template-columns:\s*minmax\(0,\s*1fr\)\s*!important/);
});
'''
write(tests, s)

print('Mobile Catalog and Blog card grids are now single-column')
