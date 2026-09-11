from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "source")

# Catalog: include the same static tourism entries that main mixes into discovery.
p = root / "frontend-react/src/pages/CatalogPage.tsx"
s = p.read_text(encoding="utf-8")
if 'import { FEATURED_TOURISM } from "../lib/tourism-static";' not in s:
    s = s.replace('import type { Business } from "../types";', 'import type { Business } from "../types";\nimport { FEATURED_TOURISM } from "../lib/tourism-static";', 1)
marker = 'type LocationPoint = { lat: number; lng: number } | null;\n'
helper = '''type LocationPoint = { lat: number; lng: number } | null;

function includeTourism(rows: Business[]) {
  const byId = new Map(rows.map((item) => [item.id, item]));
  for (const item of FEATURED_TOURISM) if (!byId.has(item.id)) byId.set(item.id, item);
  return [...byId.values()];
}
'''
if 'function includeTourism(rows: Business[])' not in s:
    if marker not in s: raise SystemExit('Catalog location marker not found')
    s = s.replace(marker, helper, 1)
s = s.replace('''  const [items, setItems] = useState<Business[] | null>(() => {
    const inline = readInlineBusinesses();
    return inline.length ? inline : null;
  });''', '''  const [items, setItems] = useState<Business[] | null>(() => includeTourism(readInlineBusinesses()));''', 1)
s = s.replace('loadPublicBusinessesFast(true)\n      .then((rows) => { if (active) setItems(rows); })\n      .catch(() => { if (active && !readInlineBusinesses().length) { setItems([]); setError(true); } });', 'loadPublicBusinessesFast(true)\n      .then((rows) => { if (active) setItems(includeTourism(rows)); })\n      .catch(() => { if (active) { setItems(includeTourism(readInlineBusinesses())); setError(true); } });', 1)
p.write_text(s, encoding="utf-8")

# Map: include the same tourism locations.
p = root / "frontend-react/src/pages/MapPage.tsx"
s = p.read_text(encoding="utf-8")
if 'import { FEATURED_TOURISM } from "../lib/tourism-static";' not in s:
    s = s.replace('import type { Business } from "../types";', 'import type { Business } from "../types";\nimport { FEATURED_TOURISM } from "../lib/tourism-static";', 1)
marker = 'type UserPoint = { lat: number; lng: number } | null;\n'
helper = '''type UserPoint = { lat: number; lng: number } | null;

function includeTourism(rows: Business[]) {
  const byId = new Map(rows.map((item) => [item.id, item]));
  for (const item of FEATURED_TOURISM) if (!byId.has(item.id)) byId.set(item.id, item);
  return [...byId.values()];
}
'''
if 'function includeTourism(rows: Business[])' not in s:
    if marker not in s: raise SystemExit('Map point marker not found')
    s = s.replace(marker, helper, 1)
s = s.replace('''  const [items, setItems] = useState<Business[] | null>(() => {
    const inline = readInlineBusinesses();
    return inline.length ? inline : null;
  });''', '''  const [items, setItems] = useState<Business[] | null>(() => includeTourism(readInlineBusinesses()));''', 1)
s = s.replace('loadPublicBusinessesFast(true).then((rows) => { if (active) setItems(rows); }).catch(() => { if (active && !readInlineBusinesses().length) setItems([]); });', 'loadPublicBusinessesFast(true).then((rows) => { if (active) setItems(includeTourism(rows)); }).catch(() => { if (active) setItems(includeTourism(readInlineBusinesses())); });', 1)
p.write_text(s, encoding="utf-8")

# Business cards: restore the favorite heart used by main catalog cards.
p = root / "frontend-react/src/components/BusinessCard.tsx"
s = p.read_text(encoding="utf-8")
if 'from "react";' not in s.splitlines()[0:3]:
    s = 'import { useEffect, useState } from "react";\n' + s
s = s.replace('import { businessImageUrl, businessPath, categoryGroup, specificCategory } from "../lib/businesses";', 'import { businessImageUrl, businessPath, categoryGroup, specificCategory, isFavorite, toggleFavorite } from "../lib/businesses";', 1)
if 'import { navigate } from "../lib/navigation";' not in s:
    s = s.replace('import Link from "./Link";', 'import Link from "./Link";\nimport { navigate } from "../lib/navigation";', 1)
s = s.replace('export default function BusinessCard({ business, eager = false }: { business: Business; eager?: boolean }) {', 'export default function BusinessCard({ business, eager = false, showFavorite = true }: { business: Business; eager?: boolean; showFavorite?: boolean }) {', 1)
needle = '  const name = localizedField<string>(business, "name", language) || business.name || labels.fallback;\n'
insert = '''  const name = localizedField<string>(business, "name", language) || business.name || labels.fallback;
  const [favorite, setFavorite] = useState(false);
  const [favoriteBusy, setFavoriteBusy] = useState(false);

  useEffect(() => {
    if (!showFavorite) return;
    let active = true;
    void isFavorite(business.id).then((value) => { if (active) setFavorite(value); }).catch(() => undefined);
    return () => { active = false; };
  }, [business.id, showFavorite]);

  const toggle = async () => {
    if (favoriteBusy) return;
    setFavoriteBusy(true);
    try {
      setFavorite(await toggleFavorite(business.id));
    } catch (error) {
      if (error instanceof Error && error.message === "AUTH_REQUIRED") {
        navigate(withLanguage(`/login?next=${encodeURIComponent(location.pathname + location.search)}`, language));
      }
    } finally {
      setFavoriteBusy(false);
    }
  };
'''
if 'const [favorite, setFavorite]' not in s:
    if needle not in s: raise SystemExit('BusinessCard name marker not found')
    s = s.replace(needle, insert, 1)
s = s.replace('<article className="group overflow-hidden rounded-[1.6rem]', '<article className="group relative overflow-hidden rounded-[1.6rem]', 1)
link_marker = '      <Link href={withLanguage(businessPath(business), language)} className="block">\n'
button = '''      {showFavorite ? <button type="button" disabled={favoriteBusy} onClick={() => void toggle()} className="absolute right-3 top-3 z-10 flex h-10 w-10 items-center justify-center rounded-full border border-white/80 bg-white/95 text-xl font-black text-red-700 shadow-md disabled:opacity-60" aria-label={`${favorite ? "Rimuovi" : "Aggiungi"} ${name} ${favorite ? "dai" : "ai"} preferiti`} aria-pressed={favorite} title={labels.verified}>{favorite ? "♥" : "♡"}</button> : null}
      <Link href={withLanguage(businessPath(business), language)} className="block">
'''
if 'aria-pressed={favorite}' not in s:
    if link_marker not in s: raise SystemExit('BusinessCard link marker not found')
    s = s.replace(link_marker, button, 1)
p.write_text(s, encoding="utf-8")

# Favorites page already has a dedicated remove button, so avoid a second overlay heart there.
p = root / "frontend-react/src/pages/FavoritesPage.tsx"
s = p.read_text(encoding="utf-8")
s = s.replace('<BusinessCard business={business} eager={index < 2} />', '<BusinessCard business={business} eager={index < 2} showFavorite={false} />')
p.write_text(s, encoding="utf-8")

# Header: restore the live favorites count badge from main.
p = root / "frontend-react/src/components/Layout.tsx"
s = p.read_text(encoding="utf-8")
s = s.replace('  const [admin, setAdmin] = useState(false);', '  const [admin, setAdmin] = useState(false);\n  const [favoriteCount, setFavoriteCount] = useState(0);', 1)
marker = '  useEffect(() => { setMenuOpen(false); }, [snapshot]);\n'
effect = '''  useEffect(() => { setMenuOpen(false); }, [snapshot]);

  useEffect(() => {
    if (!user) { setFavoriteCount(0); return; }
    let active = true;
    let stop = () => {};
    void Promise.all([import("../lib/firebase-db"), import("firebase/firestore")]).then(([{ db }, f]) => {
      if (!active) return;
      const query = f.query(f.collection(db, "favorites"), f.where("userId", "==", user.uid), f.limit(150));
      stop = f.onSnapshot(query, (snapshot) => { if (active) setFavoriteCount(snapshot.size); }, () => { if (active) setFavoriteCount(0); });
    }).catch(() => { if (active) setFavoriteCount(0); });
    return () => { active = false; stop(); };
  }, [user]);
'''
if 'setFavoriteCount(snapshot.size)' not in s:
    if marker not in s: raise SystemExit('Layout menu effect marker not found')
    s = s.replace(marker, effect, 1)
old = '<Link className="cv-icon-action" href={withLanguage("/preferiti", language)} aria-label={uiText("favorites", language)} title={uiText("favorites", language)}><HeartIcon /></Link>'
new = '<Link className="cv-icon-action relative" href={withLanguage("/preferiti", language)} aria-label={uiText("favorites", language)} title={uiText("favorites", language)}><HeartIcon />{favoriteCount > 0 ? <span className="absolute -right-1.5 -top-1.5 flex min-h-5 min-w-5 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-black leading-none text-white shadow" aria-label={`${favoriteCount} preferiti`}>{favoriteCount > 99 ? "99+" : favoriteCount}</span> : null}</Link>'
if old in s:
    s = s.replace(old, new, 1)
elif 'aria-label={`${favoriteCount} preferiti`}' not in s:
    raise SystemExit('Layout favorites link marker not found')
p.write_text(s, encoding="utf-8")
