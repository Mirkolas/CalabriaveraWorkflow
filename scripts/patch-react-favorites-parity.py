from pathlib import Path

root = Path('source/frontend-react')

account = root / 'src/lib/account.ts'
text = account.read_text(encoding='utf-8')
old = '''  const [{ loadAllBusinesses }, { FEATURED_TOURISM }] = await Promise.all([
    import("./businesses"),
    import("./tourism-static"),
  ]);
  const byId = new Map((await loadAllBusinesses()).concat(FEATURED_TOURISM).map((business) => [business.id, business]));
'''
new = '''  const [{ loadAllBusinesses }, { ALL_TOURISM }] = await Promise.all([
    import("./businesses"),
    import("./tourism-static"),
  ]);
  const byId = new Map((await loadAllBusinesses()).concat(ALL_TOURISM).map((business) => [business.id, business]));
'''
if old not in text:
    raise SystemExit('favorites data anchor missing')
account.write_text(text.replace(old, new, 1), encoding='utf-8')

favorites = root / 'src/pages/FavoritesPage.tsx'
favorites.write_text(r'''import { useEffect, useState } from "react";
import Link from "../components/Link";
import { loadFavoriteBusinesses } from "../lib/account";
import { businessImageUrl, businessPath, toggleFavorite } from "../lib/businesses";
import { languageFromPath, withLanguage, type Language } from "../lib/language";
import { navigate } from "../lib/navigation";
import { setPageSeo } from "../lib/seo";
import type { Business } from "../types";

const COPY: Record<Language, { title: string; error: string; none: string; noneText: string; explore: string; savedOne: string; savedMany: string; add: string; open: string; remove: string }> = {
  it: { title: "Preferiti", error: "Impossibile caricare i preferiti.", none: "Nessun preferito", noneText: "Salva le attività che vuoi ritrovare facilmente: appariranno tutte qui.", explore: "Esplora il catalogo", savedOne: "attività salvata", savedMany: "attività salvate", add: "Aggiungi altri preferiti", open: "Apri scheda", remove: "Rimuovi" },
  en: { title: "Favorites", error: "Unable to load favorites.", none: "No favorites", noneText: "Save the businesses you want to find easily: they will all appear here.", explore: "Explore the directory", savedOne: "saved business", savedMany: "saved businesses", add: "Add more favorites", open: "Open profile", remove: "Remove" },
  fr: { title: "Favoris", error: "Impossible de charger les favoris.", none: "Aucun favori", noneText: "Enregistrez les activités que vous souhaitez retrouver facilement : elles apparaîtront toutes ici.", explore: "Explorer le catalogue", savedOne: "activité enregistrée", savedMany: "activités enregistrées", add: "Ajouter des favoris", open: "Ouvrir la fiche", remove: "Retirer" },
  de: { title: "Favoriten", error: "Favoriten konnten nicht geladen werden.", none: "Keine Favoriten", noneText: "Speichere Betriebe, die du leicht wiederfinden möchtest: Sie erscheinen alle hier.", explore: "Katalog entdecken", savedOne: "gespeicherter Betrieb", savedMany: "gespeicherte Betriebe", add: "Weitere Favoriten", open: "Eintrag öffnen", remove: "Entfernen" },
  es: { title: "Favoritos", error: "No se pudieron cargar los favoritos.", none: "Sin favoritos", noneText: "Guarda las actividades que quieras encontrar fácilmente: aparecerán todas aquí.", explore: "Explorar el catálogo", savedOne: "actividad guardada", savedMany: "actividades guardadas", add: "Añadir más favoritos", open: "Abrir ficha", remove: "Quitar" },
};

function routeFor(business: Business, language: Language) {
  const base = String(business.id || "").startsWith("turismo-")
    ? `/attivita?turismo=${encodeURIComponent(String(business.slug || business.id))}`
    : businessPath(business);
  return withLanguage(base, language);
}

export default function FavoritesPage() {
  const language = languageFromPath();
  const copy = COPY[language];
  const [items, setItems] = useState<Business[] | null>(null);
  const [error, setError] = useState("");
  const [removing, setRemoving] = useState("");
  const [leaving, setLeaving] = useState("");

  useEffect(() => {
    setPageSeo({ title: `${copy.title} | CalabriaVera`, description: copy.title, path: location.pathname, robots: "noindex,nofollow" });
    let active = true;
    loadFavoriteBusinesses().then((rows) => { if (active) setItems(rows); }).catch((cause) => {
      if (!active) return;
      if (cause instanceof Error && cause.message === "AUTH_REQUIRED") navigate(withLanguage("/login?next=/preferiti", language), true);
      else if (cause instanceof Error && cause.message === "ACCOUNT_SUSPENDED") navigate(withLanguage("/login?suspended=1", language), true);
      else { setItems([]); setError(copy.error); }
    });
    return () => { active = false; };
  }, [language, copy.title, copy.error]);

  const remove = async (business: Business) => {
    if (removing) return;
    setRemoving(business.id);
    setError("");
    try {
      let active = await toggleFavorite(business.id);
      if (active) active = await toggleFavorite(business.id);
      if (active) throw new Error("FAVORITE_REMOVE_NOT_CONFIRMED");
      setLeaving(business.id);
      if (!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
        await new Promise((resolve) => window.setTimeout(resolve, 260));
      }
      setItems((current) => current ? current.filter((item) => item.id !== business.id) : current);
    } catch (cause) {
      console.error("Rimozione preferito non riuscita", cause);
      setError(copy.error);
    } finally {
      setLeaving("");
      setRemoving("");
    }
  };

  return (
    <section className="section container">
      <p className="eyebrow">CalabriaVera</p>
      <h1>{copy.title}</h1>
      <div id="favorites-root">
        {error ? <div className="notice">{error}</div> : null}
        {items === null ? <div className="notice">Caricamento preferiti…</div> : items.length ? <>
          <div className="cv-favorites-toolbar">
            <div><strong>{items.length}</strong><span>{items.length === 1 ? copy.savedOne : copy.savedMany}</span></div>
            <Link href={withLanguage("/catalogo", language)} className="text-link">{copy.add}</Link>
          </div>
          <div className="cv-favorites-grid">
            {items.map((business) => {
              const url = routeFor(business, language);
              const image = businessImageUrl(business);
              const place = [business.comune, business.provincia].filter(Boolean).join(" · ");
              const subtype = String(business.subcategory || business.category || "Attività");
              return <article key={business.id} className={`cv-favorite-card${leaving === business.id ? " cv-favorite-leave" : ""}`} data-favorite-card={business.id}>
                {image ? <Link className="cv-favorite-media" href={url}><img loading="lazy" decoding="async" src={image} alt={business.name || ""} /></Link> : <Link className="cv-favorite-media cv-favorite-media--placeholder" href={url}><span>{subtype}</span></Link>}
                <div className="cv-favorite-body">
                  <div className="cv-favorite-meta"><span>{subtype}</span>{place ? <span>{place}</span> : null}</div>
                  <h2><Link href={url}>{business.name || "Attività"}</Link></h2>
                  <div className="cv-favorite-actions">
                    <Link className="button button-primary" href={url}>{copy.open}</Link>
                    <button className="button cv-remove-favorite" type="button" data-favorite-remove={business.id} disabled={removing === business.id} aria-busy={removing === business.id ? "true" : undefined} aria-label={`${copy.remove} ${business.name || "attività"} dai preferiti`} onClick={() => void remove(business)}><span aria-hidden="true">♥</span> {copy.remove}</button>
                  </div>
                </div>
              </article>;
            })}
          </div>
        </> : <div className="empty-state cv-favorites-empty">
          <div className="cv-empty-icon" aria-hidden="true">♡</div>
          <h2>{copy.none}</h2>
          <p>{copy.noneText}</p>
          <Link className="button button-primary" href={withLanguage("/catalogo", language)}>{copy.explore}</Link>
        </div>}
      </div>
    </section>
  );
}
''', encoding='utf-8')

print('Applied exact main Favorites DOM and full tourism favorites parity.')
