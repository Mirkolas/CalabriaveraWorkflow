from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
magazine = root / 'frontend-react/src/lib/magazine.ts'
publisher = root / 'tools/publish-magazine-batch.mjs'
tests = root / 'tests/site-stability.test.mjs'


def read(path):
    return path.read_text(encoding='utf-8')


def write(path, text):
    path.write_text(text, encoding='utf-8')

# Frontend: "recent" means published on CalabriaVera most recently. The source
# timestamp is metadata/fallback, not the primary feed-order timestamp.
s = read(magazine)
old = '  for (const value of [post.sourcePublishedAt, post.publishedAt, post.importedAt, post.createdAt, post.sitePublishedAt]) {'
new = '  for (const value of [post.sitePublishedAt, post.publishedAt, post.sourcePublishedAt, post.importedAt, post.createdAt]) {'
if old in s:
    s = s.replace(old, new)
elif new not in s:
    raise SystemExit('magazine.ts: publicationMillis timestamp order not found')
write(magazine, s)

# Backend live-feed document: retain source chronology for queue selection, but
# order the public live feed by the actual CalabriaVera publication timestamp.
s = read(publisher)
anchor = '''function safeSourcePublishedAt(row) {
  const maxAllowed = Date.now() + MAX_FUTURE_PUBLICATION_SKEW_MS;
  for (const value of [row.sourcePublishedAt, row.importedAt, row.createdAt, row.publishedAt, row.sitePublishedAt]) {
    const ms = millis(value);
    if (ms > 0 && ms <= maxAllowed) return value;
  }
  return null;
}
'''
helper = anchor + '''function sitePublicationMillis(row) {
  const maxAllowed = Date.now() + MAX_FUTURE_PUBLICATION_SKEW_MS;
  for (const value of [row.sitePublishedAt, row.publishedAt, row.sourcePublishedAt, row.importedAt, row.createdAt]) {
    const ms = millis(value);
    if (ms > 0 && ms <= maxAllowed) return ms;
  }
  return 0;
}
'''
if 'function sitePublicationMillis(row)' not in s:
    if anchor not in s:
        raise SystemExit('publish-magazine-batch: safeSourcePublishedAt anchor not found')
    s = s.replace(anchor, helper)
old_sort = '    .sort((a, b) => millis(safeSourcePublishedAt(b)) - millis(safeSourcePublishedAt(a)) || String(a.id || "").localeCompare(String(b.id || "")))\n    .slice(0, LIVE_FEED_LIMIT);'
new_sort = '    .sort((a, b) => sitePublicationMillis(b) - sitePublicationMillis(a) || String(a.id || "").localeCompare(String(b.id || "")))\n    .slice(0, LIVE_FEED_LIMIT);'
if old_sort in s:
    s = s.replace(old_sort, new_sort)
elif new_sort not in s:
    raise SystemExit('publish-magazine-batch: live-feed source-date sort not found')
write(publisher, s)

s = read(tests)
marker = "Magazine ordina i contenuti per pubblicazione CalabriaVera"
if marker not in s:
    s += r'''

test('Magazine ordina i contenuti per pubblicazione CalabriaVera, non per data fonte', () => {
  const magazine = read('frontend-react/src/lib/magazine.ts');
  const publisher = read('tools/publish-magazine-batch.mjs');
  assert.match(magazine, /\[post\.sitePublishedAt, post\.publishedAt, post\.sourcePublishedAt, post\.importedAt, post\.createdAt\]/);
  assert.match(publisher, /function sitePublicationMillis\(row\)/);
  assert.match(publisher, /\[row\.sitePublishedAt, row\.publishedAt, row\.sourcePublishedAt, row\.importedAt, row\.createdAt\]/);
  assert.match(publisher, /sitePublicationMillis\(b\) - sitePublicationMillis\(a\)/);
});
'''
write(tests, s)

print('Magazine publication order now follows CalabriaVera publication time')
