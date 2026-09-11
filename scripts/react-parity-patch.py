from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "source")

# businesses.ts: preserve tourism URLs and favoriteCount semantics from main.
p = root / "frontend-react/src/lib/businesses.ts"
s = p.read_text(encoding="utf-8")
old = '''export function businessPath(item: Business) {
  return `/attivita/${slugify(item.provincia || "calabria")}/${slugify(item.comune || "calabria")}/${slugify(specificCategory(item))}/${encodeURIComponent(String(item.slug || slugify(item.name) || item.id))}`;
}
'''
new = '''export function businessPath(item: Business) {
  if (String(item.id || "").startsWith("turismo-")) {
    return `/attivita?turismo=${encodeURIComponent(String(item.slug || item.id))}`;
  }
  return `/attivita/${slugify(item.provincia || "calabria")}/${slugify(item.comune || "calabria")}/${slugify(specificCategory(item))}/${encodeURIComponent(String(item.slug || slugify(item.name) || item.id))}`;
}
'''
if old not in s:
    raise SystemExit("businessPath marker not found")
s = s.replace(old, new, 1)

start = s.index("export async function toggleFavorite(businessId: string) {")
replacement = '''export async function toggleFavorite(businessId: string) {
  const [{ currentUser }, { db, firestore: f }] = await Promise.all([import("./auth"), services()]);
  const user = await currentUser();
  if (!user) throw new Error("AUTH_REQUIRED");
  const favoriteRef = f.doc(db, "favorites", `${user.uid}_${businessId}`);

  if (String(businessId).startsWith("turismo-")) {
    return f.runTransaction(db, async (transaction) => {
      const favorite = await transaction.get(favoriteRef);
      if (favorite.exists()) {
        transaction.delete(favoriteRef);
        return false;
      }
      transaction.set(favoriteRef, { userId: user.uid, businessId, createdAt: f.serverTimestamp() });
      return true;
    });
  }

  const businessRef = f.doc(db, "businesses", businessId);
  return f.runTransaction(db, async (transaction) => {
    const [favorite, business] = await Promise.all([
      transaction.get(favoriteRef),
      transaction.get(businessRef),
    ]);
    if (!business.exists()) throw new Error("BUSINESS_NOT_FOUND");
    if (favorite.exists()) {
      transaction.delete(favoriteRef);
      if (Number(business.data().favoriteCount || 0) > 0) {
        transaction.update(businessRef, { favoriteCount: f.increment(-1) });
      }
      return false;
    }
    transaction.set(favoriteRef, { userId: user.uid, businessId, createdAt: f.serverTimestamp() });
    transaction.update(businessRef, { favoriteCount: f.increment(1) });
    return true;
  });
}
'''
s = s[:start] + replacement
p.write_text(s, encoding="utf-8")

# account.ts: resolve both Firestore and static tourism favorites.
p = root / "frontend-react/src/lib/account.ts"
s = p.read_text(encoding="utf-8")
start = s.index("export async function loadFavoriteBusinesses() {")
end = s.index("\nexport async function loadOwnBusinesses()", start)
replacement = '''export async function loadFavoriteBusinesses() {
  const user = await requireUser();
  const { db, firestore: f } = await services();
  const snapshot = await f.getDocs(f.query(f.collection(db, "favorites"), f.where("userId", "==", user.uid), f.limit(150)));
  const ids = snapshot.docs.map((doc) => String(doc.data().businessId || "")).filter(Boolean);
  if (!ids.length) return [];
  const [{ loadAllBusinesses }, { FEATURED_TOURISM }] = await Promise.all([
    import("./businesses"),
    import("./tourism-static"),
  ]);
  const byId = new Map((await loadAllBusinesses()).concat(FEATURED_TOURISM).map((business) => [business.id, business]));
  return ids.map((id) => byId.get(id)).filter((business): business is Business => Boolean(business));
}
'''
s = s[:start] + replacement + s[end:]
p.write_text(s, encoding="utf-8")

# OriginalHomePage.tsx: make featured hearts functional like main.
p = root / "frontend-react/src/pages/OriginalHomePage.tsx"
s = p.read_text(encoding="utf-8")
s = s.replace(
    'import { useEffect } from "react";',
    'import { useEffect, useState, type KeyboardEvent, type MouseEvent } from "react";',
    1,
)
s = s.replace(
    'import { loadPublicBusinessesFast, loadPublicMagazineFast } from "../lib/public-data";',
    'import { loadPublicBusinessesFast, loadPublicMagazineFast } from "../lib/public-data";\nimport { isFavorite, toggleFavorite } from "../lib/businesses";',
    1,
)
s = s.replace(
    'type FeaturedItem = { href: string; image: string; province: string; title: string; kind: string; badge?: string };',
    'type FeaturedItem = { id: string; href: string; image: string; province: string; title: string; kind: string; badge?: string };',
    1,
)
repls = {
    '{ href: "/attivita?turismo=centro-storico-di-tropea"': '{ id: "turismo-centro-storico-tropea", href: "/attivita?turismo=centro-storico-di-tropea"',
    '{ href: "/attivita?turismo=foresta-della-sila"': '{ id: "turismo-foresta-sila", href: "/attivita?turismo=foresta-della-sila"',
    '{ href: "/attivita?turismo=scilla-e-il-suo-castello"': '{ id: "turismo-scilla-castello", href: "/attivita?turismo=scilla-e-il-suo-castello"',
    '{ href: "/attivita?turismo=parco-archeologico-capo-colonna"': '{ id: "turismo-capo-colonna", href: "/attivita?turismo=parco-archeologico-capo-colonna"',
}
for a, b in repls.items():
    if a not in s:
        raise SystemExit(f"home marker not found: {a}")
    s = s.replace(a, b, 1)

marker = "export default function OriginalHomePage() {"
component = '''function FeaturedHeart({ id, title }: { id: string; title: string }) {
  const language = languageFromPath();
  const [active, setActive] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    void isFavorite(id).then((value) => { if (alive) setActive(value); }).catch(() => undefined);
    return () => { alive = false; };
  }, [id]);

  const activate = async (event: MouseEvent | KeyboardEvent) => {
    event.preventDefault();
    event.stopPropagation();
    if (busy) return;
    if ("key" in event && event.key !== "Enter" && event.key !== " ") return;
    setBusy(true);
    try {
      setActive(await toggleFavorite(id));
    } catch (error) {
      if (error instanceof Error && error.message === "AUTH_REQUIRED") {
        navigate(withLanguage(`/login?next=${encodeURIComponent(location.pathname + location.search)}`, language));
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <span
      className="cv-heart"
      role="button"
      tabIndex={0}
      aria-label={`${active ? "Rimuovi" : "Aggiungi"} ${title} ${active ? "dai" : "ai"} preferiti`}
      aria-pressed={active}
      aria-busy={busy || undefined}
      onClick={(event) => void activate(event)}
      onKeyDown={(event) => void activate(event)}
    >
      {active ? "♥" : "♡"}
    </span>
  );
}

'''
if "function FeaturedHeart(" not in s:
    if marker not in s:
        raise SystemExit("OriginalHomePage marker not found")
    s = s.replace(marker, component + marker, 1)
old_heart = '<span className="cv-heart" aria-hidden="true">♡</span>'
if old_heart not in s:
    raise SystemExit("decorative home heart not found")
s = s.replace(old_heart, '<FeaturedHeart id={item.id} title={item.title} />', 1)
p.write_text(s, encoding="utf-8")

# FavoritesPage.tsx: expose count and direct removal, as in main.
p = root / "frontend-react/src/pages/FavoritesPage.tsx"
s = p.read_text(encoding="utf-8")
s = s.replace(
    'import { loadFavoriteBusinesses } from "../lib/account";',
    'import { loadFavoriteBusinesses } from "../lib/account";\nimport { toggleFavorite } from "../lib/businesses";',
    1,
)
s = s.replace(
    '  const [error, setError] = useState("");',
    '  const [error, setError] = useState("");\n  const [removing, setRemoving] = useState("");',
    1,
)
anchor = "  return (\n"
removal = '''  const remove = async (business: Business) => {
    if (removing) return;
    setRemoving(business.id);
    setError("");
    try {
      let active = await toggleFavorite(business.id);
      if (active) active = await toggleFavorite(business.id);
      if (active) throw new Error("FAVORITE_REMOVE_NOT_CONFIRMED");
      setItems((current) => current ? current.filter((item) => item.id !== business.id) : current);
    } catch {
      setError(copy.error);
    } finally {
      setRemoving("");
    }
  };

'''
if "const remove = async (business: Business)" not in s:
    idx = s.index(anchor, s.index("export default function FavoritesPage()"))
    s = s[:idx] + removal + s[idx:]

old = '''      {items === null ? <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3"><div className="h-80 animate-pulse rounded-[1.6rem] bg-stone-100" /><div className="h-80 animate-pulse rounded-[1.6rem] bg-stone-100" /></div> : items.length ? <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{items.map((business, index) => <BusinessCard key={business.id} business={business} eager={index < 2} />)}</div> : <div className="mt-8 rounded-[1.5rem] border border-stone-200 bg-white p-8 text-center"><h2 className="text-xl font-black">{copy.none}</h2><p className="mt-2 text-stone-500">{copy.noneText}</p><Link href={withLanguage("/catalogo", language)} className="mt-5 inline-block rounded-full bg-stone-950 px-5 py-3 text-sm font-black text-white">{copy.explore}</Link></div>}
'''
new = '''      {items === null ? <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3"><div className="h-80 animate-pulse rounded-[1.6rem] bg-stone-100" /><div className="h-80 animate-pulse rounded-[1.6rem] bg-stone-100" /></div> : items.length ? <><div className="mt-6 flex items-center justify-between gap-4 rounded-2xl bg-stone-50 px-5 py-4"><div><strong className="text-xl">{items.length}</strong> <span className="text-stone-500">{items.length === 1 ? "attività salvata" : "attività salvate"}</span></div><Link href={withLanguage("/catalogo", language)} className="font-bold text-emerald-800">Aggiungi altri preferiti</Link></div><div className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{items.map((business, index) => <div key={business.id} className="relative"><BusinessCard business={business} eager={index < 2} /><button type="button" disabled={removing === business.id} onClick={() => void remove(business)} className="mt-2 w-full rounded-xl border border-stone-300 bg-white px-4 py-2.5 text-sm font-black text-red-700 disabled:opacity-50">♥ Rimuovi</button></div>)}</div></> : <div className="mt-8 rounded-[1.5rem] border border-stone-200 bg-white p-8 text-center"><h2 className="text-xl font-black">{copy.none}</h2><p className="mt-2 text-stone-500">{copy.noneText}</p><Link href={withLanguage("/catalogo", language)} className="mt-5 inline-block rounded-full bg-stone-950 px-5 py-3 text-sm font-black text-white">{copy.explore}</Link></div>}
'''
if old not in s:
    raise SystemExit("FavoritesPage render marker not found")
s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
