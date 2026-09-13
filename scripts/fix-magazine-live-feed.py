from pathlib import Path
import re
import sys

root = Path(sys.argv[1]).resolve()
page = root / 'frontend-react/src/pages/MagazinePage.tsx'
public_data = root / 'frontend-react/src/lib/public-data.ts'
magazine = root / 'frontend-react/src/lib/magazine.ts'
tests = root / 'tests/site-stability.test.mjs'


def read(path):
    return path.read_text(encoding='utf-8')


def write(path, text):
    path.write_text(text, encoding='utf-8')


# 1) Magazine page: niente refresh ritardato di 4,5 s. Lo snapshot inline resta
# immediato e il live feed viene richiesto subito in parallelo.
s = read(page)
old = '''    loadPublicMagazineFast(true).then((items) => { if (active) setPosts(items); }).catch(() => { if (active && !readInlineMagazine().length) setPosts([]); });
    const refresh = () => void import("../lib/magazine").then(({ loadMagazine }) => loadMagazine(true)).then((fresh) => { if (active && fresh.length) setPosts(fresh); }).catch(() => undefined);
    const timer = window.setTimeout(refresh, 4500);
    return () => { active = false; window.clearTimeout(timer); };
'''
new = '''    loadPublicMagazineFast(true)
      .then((items) => {
        if (!active) return;
        if (items.length) setPosts(items);
        else if (!readInlineMagazine().length) setPosts([]);
      })
      .catch(() => { if (active && !readInlineMagazine().length) setPosts([]); });
    return () => { active = false; };
'''
if old not in s:
    raise SystemExit('MagazinePage: blocco refresh 4500 ms non trovato')
s = s.replace(old, new)
write(page, s)

# 2) magazine.ts: usa il documento compatto settings/blogLiveFeed e rende la
# query completa di fallback deterministicamente recente tramite publishedAt.
s = read(magazine)
services_anchor = '''async function services() {
  const [{ db }, firestore] = await Promise.all([import("./firebase-db"), import("firebase/firestore")]);
  return { db, firestore };
}
'''
if services_anchor not in s:
    raise SystemExit('magazine.ts: services() non trovato')
insert = services_anchor + '''
export async function loadMagazineLiveFeed() {
  const { db, firestore: f } = await services();
  const snapshot = await f.getDoc(f.doc(db, "settings", "blogLiveFeed"));
  if (!snapshot.exists()) return [];
  const data = snapshot.data() as { items?: BlogPost[] };
  const items = Array.isArray(data?.items) ? data.items : [];
  return items
    .filter((post) => post && !revoked(post))
    .sort((a, b) => publicationMillis(b) - publicationMillis(a) || String(a.id || "").localeCompare(String(b.id || "")));
}
'''
s = s.replace(services_anchor, insert)
old_query = '    const snapshot = await f.getDocs(f.query(f.collection(db, "blogPosts"), f.where("status", "==", "published"), f.limit(500)));'
new_query = '    const snapshot = await f.getDocs(f.query(f.collection(db, "blogPosts"), f.where("status", "==", "published"), f.orderBy("publishedAt", "desc"), f.limit(250)));'
if old_query not in s:
    raise SystemExit('magazine.ts: query limit(500) non trovata')
s = s.replace(old_query, new_query)
write(magazine, s)

# 3) public-data.ts: snapshot statico + live feed Firestore in parallelo, unione
# per id/slug e fallback alla query completa soltanto se entrambe le fonti mancano.
s = read(public_data)
anchor = '''export async function loadPublicMagazineFast(force = false): Promise<BlogPost[]> {
  if (force) magazinePromise = null;
  if (!magazinePromise) {
    magazinePromise = (async () => {
      let rows: BlogPost[] = [];
      try { rows = await fetchDataset<BlogPost>("/assets/data/public-blog-v1.json"); } catch { rows = []; }
      if (rows.length) return rows;
      const { loadMagazine } = await import("./magazine");
      try { return await retry(() => loadMagazine(true)); } catch { return []; }
    })();
  }
  try { return await magazinePromise; }
  catch (error) { magazinePromise = null; throw error; }
}
'''
replacement = '''function mergeMagazineDatasets(live: BlogPost[], snapshot: BlogPost[]) {
  const byKey = new Map<string, BlogPost>();
  for (const item of snapshot) {
    const key = String(item.id || item.slug || "");
    if (key) byKey.set(key, item);
  }
  const liveKeys: string[] = [];
  for (const item of live) {
    const key = String(item.id || item.slug || "");
    if (!key) continue;
    const previous = byKey.get(key) || ({} as BlogPost);
    byKey.set(key, { ...previous, ...item });
    liveKeys.push(key);
  }
  const liveSet = new Set(liveKeys);
  return [
    ...liveKeys.map((key) => byKey.get(key)).filter(Boolean),
    ...snapshot.filter((item) => !liveSet.has(String(item.id || item.slug || ""))),
  ] as BlogPost[];
}

export async function loadPublicMagazineFast(force = false): Promise<BlogPost[]> {
  if (force) magazinePromise = null;
  if (!magazinePromise) {
    magazinePromise = (async () => {
      const snapshotPromise = fetchDataset<BlogPost>("/assets/data/public-blog-v1.json").catch(() => [] as BlogPost[]);
      const livePromise = import("./magazine")
        .then(({ loadMagazineLiveFeed }) => retry(() => loadMagazineLiveFeed(), 2))
        .catch(() => [] as BlogPost[]);
      const [snapshot, live] = await Promise.all([snapshotPromise, livePromise]);
      const merged = mergeMagazineDatasets(live, snapshot);
      if (merged.length) return merged;
      const { loadMagazine } = await import("./magazine");
      try { return await retry(() => loadMagazine(true), 2); } catch { return []; }
    })();
  }
  try { return await magazinePromise; }
  catch (error) { magazinePromise = null; throw error; }
}
'''
if anchor not in s:
    raise SystemExit('public-data.ts: loadPublicMagazineFast originale non trovato')
s = s.replace(anchor, replacement)
write(public_data, s)

# 4) Regressione: impedisce di reintrodurre il timer e la scansione non ordinata.
s = read(tests)
marker = "React Blog usa il live feed Firestore senza attesa artificiale"
if marker not in s:
    s += r'''

test('React Blog usa il live feed Firestore senza attesa artificiale', () => {
  const page = read('frontend-react/src/pages/MagazinePage.tsx');
  const data = read('frontend-react/src/lib/public-data.ts');
  const magazine = read('frontend-react/src/lib/magazine.ts');
  assert.doesNotMatch(page, /setTimeout\(refresh,\s*4500\)/);
  assert.match(data, /loadMagazineLiveFeed/);
  assert.match(data, /Promise\.all\(\[snapshotPromise, livePromise\]\)/);
  assert.match(magazine, /doc\(db,\s*"settings",\s*"blogLiveFeed"\)/);
  assert.match(magazine, /orderBy\("publishedAt",\s*"desc"\)/);
  assert.match(magazine, /limit\(250\)/);
  assert.doesNotMatch(magazine, /limit\(500\)/);
});
'''
write(tests, s)

print('Magazine live-feed patch applied')
