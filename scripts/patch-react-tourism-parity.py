from pathlib import Path

interactions = r'''import { currentUser, requireActiveUser } from "./auth";
import type { Review } from "../types";

async function services() {
  const [{ db }, firestore] = await Promise.all([import("./firebase-db"), import("firebase/firestore")]);
  return { db, firestore };
}

function localRateLimit(key: string, windowMs: number) {
  const stamp = Date.now();
  const storageKey = `cv-rate-${key}`;
  const last = Number(localStorage.getItem(storageKey) || 0);
  if (stamp - last < windowMs) throw new Error("RATE_LIMIT");
  localStorage.setItem(storageKey, String(stamp));
}

export async function isTourismFavorite(businessId: string) {
  const user = await currentUser();
  if (!user) return false;
  const { db, firestore: f } = await services();
  return (await f.getDoc(f.doc(db, "favorites", `${user.uid}_${businessId}`))).exists();
}

export async function toggleTourismFavorite(businessId: string) {
  const existingUser = await currentUser();
  if (!existingUser) throw new Error("AUTH_REQUIRED");
  const user = await requireActiveUser(existingUser);
  const { db, firestore: f } = await services();
  const ref = f.doc(db, "favorites", `${user.uid}_${businessId}`);
  const snapshot = await f.getDoc(ref);
  if (snapshot.exists()) {
    await f.deleteDoc(ref);
    return false;
  }
  await f.setDoc(ref, { userId: user.uid, businessId, createdAt: f.serverTimestamp() });
  return true;
}

export async function listTourismReviews(businessId: string) {
  const { db, firestore: f } = await services();
  const snapshot = await f.getDocs(f.query(
    f.collection(db, "reviews"),
    f.where("businessId", "==", businessId),
    f.where("status", "==", "approved"),
    f.orderBy("createdAt", "desc"),
    f.limit(30),
  ));
  return snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() }) as Review);
}

export async function addTourismReview(data: { businessId: string; rating: number; title: string; text: string }) {
  const existingUser = await currentUser();
  if (!existingUser) throw new Error("AUTH_REQUIRED");
  const user = await requireActiveUser(existingUser);
  if (!user.emailVerified) throw new Error("EMAIL_NOT_VERIFIED");
  localRateLimit(`review-${data.businessId}`, 60000);
  const { db, firestore: f } = await services();
  const existing = await f.getDocs(f.query(
    f.collection(db, "reviews"),
    f.where("businessId", "==", data.businessId),
    f.where("userId", "==", user.uid),
    f.limit(1),
  ));
  if (!existing.empty) throw new Error("REVIEW_EXISTS");
  const ref = await f.addDoc(f.collection(db, "reviews"), {
    ...data,
    userId: user.uid,
    rating: Number(data.rating),
    status: "pending",
    createdAt: f.serverTimestamp(),
  });
  try {
    await f.setDoc(f.doc(db, "emailEvents", `review-received_${ref.id}`), {
      type: "review.received",
      sourceCollection: "reviews",
      sourceId: ref.id,
      actorUid: user.uid,
      createdAt: f.serverTimestamp(),
    });
  } catch {
    console.warn("Coda email recensione non disponibile.");
  }
  return ref.id;
}
'''

page = r'''import { useEffect, useMemo, useState, type FormEvent } from "react";
import Link from "../components/Link";
import { businessPath } from "../lib/businesses";
import { currentUser } from "../lib/auth";
import { languageFromPath, withLanguage } from "../lib/language";
import { setPageSeo, setStructuredData } from "../lib/seo";
import { ALL_TOURISM } from "../lib/tourism-static";
import { addTourismReview, isTourismFavorite, listTourismReviews, toggleTourismFavorite } from "../lib/tourism-interactions";
import type { Business, Review } from "../types";

function toast(message: string) {
  const root = document.getElementById("toast-root");
  if (!root) return;
  root.innerHTML = "";
  const node = document.createElement("div");
  node.className = "toast";
  node.textContent = String(message || "");
  root.appendChild(node);
  window.setTimeout(() => { if (root.contains(node)) root.innerHTML = ""; }, 3800);
}

function Stars({ value }: { value: number }) {
  const rating = Math.max(0, Math.min(5, Math.round(Number(value) || 0)));
  return <span className="cv-stars" aria-label={`${rating} stelle su 5`}>{[1,2,3,4,5].map((star) => <span key={star} className={star<=rating?undefined:"is-empty"}>★</span>)}</span>;
}

function imageCredit(item: Business) {
  const label = String(item.imageCredit || "");
  if (!label) return null;
  const source = String(item.imageSourceUrl || "");
  return <p className="cv-tourism-credit">Foto: {source ? <a href={source} target="_blank" rel="noopener noreferrer">{label}</a> : label}</p>;
}

export default function TourismPage() {
  const language = languageFromPath();
  const slug = new URLSearchParams(location.search).get("turismo") || "";
  const item = useMemo(() => ALL_TOURISM.find((entry) => entry.slug === slug || entry.id === slug) || null, [slug]);
  const [reviews, setReviews] = useState<Review[] | null>(null);
  const [reviewsFailed, setReviewsFailed] = useState(false);
  const [favorite, setFavorite] = useState(false);
  const [favoriteBusy, setFavoriteBusy] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewBusy, setReviewBusy] = useState(false);

  useEffect(() => {
    if (!item) return;
    const path = withLanguage(businessPath(item), language);
    setPageSeo({
      title: `${item.name || "CalabriaVera"} | Turismo CalabriaVera`,
      description: String(item.description || "").slice(0,155),
      path,
      image: String(item.imageUrl || "") || undefined,
    });
    setStructuredData("tourism-place", null);
  }, [item, language]);

  useEffect(() => {
    if (!item) return;
    let active = true;
    setReviews(null);
    setReviewsFailed(false);
    void listTourismReviews(item.id).then((rows) => { if (active) setReviews(rows); }).catch(() => { if (active) { setReviews([]); setReviewsFailed(true); } });
    void currentUser().then((user) => user ? isTourismFavorite(item.id) : false).then((value) => { if (active) setFavorite(value); }).catch(() => undefined);
    return () => { active = false; };
  }, [item]);

  if (!item) return <section className="section container"><div className="empty-state"><h1>Esperienza non trovata</h1><Link className="button button-primary" href="/catalogo?categoria=Turismo">Torna alle attività Turismo</Link></div></section>;

  const services = item.services || [];
  const image = String(item.imageUrl || "");
  const mapQuery = `${item.lat},${item.lng}`;

  const toggleFavorite = async () => {
    const user = await currentUser();
    if (!user) {
      location.href = `/login?next=${encodeURIComponent(location.href)}`;
      return;
    }
    setFavoriteBusy(true);
    try { setFavorite(await toggleTourismFavorite(item.id)); }
    catch { toast("Impossibile aggiornare i preferiti."); }
    finally { setFavoriteBusy(false); }
  };

  const submitReview = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const user = await currentUser();
    if (!user) {
      location.href = `/login?next=${encodeURIComponent(location.href)}`;
      return;
    }
    const form = event.currentTarget;
    const data = new FormData(form);
    const rating = Number(data.get("rating"));
    if (!Number.isInteger(rating) || rating < 1 || rating > 5) {
      toast("Seleziona da 1 a 5 stelle.");
      return;
    }
    setReviewBusy(true);
    try {
      await addTourismReview({ businessId: item.id, rating, title: String(data.get("title") || "").trim(), text: String(data.get("text") || "").trim() });
      toast("Recensione inviata per moderazione.");
      form.reset();
      setReviewRating(5);
    } catch (error) {
      toast(error instanceof Error && error.message === "REVIEW_EXISTS" ? "Hai già lasciato una recensione." : "Impossibile inviare la recensione.");
    } finally { setReviewBusy(false); }
  };

  return <section className="container cv-tourism-detail">
    <div className="cv-tourism-hero" style={{backgroundImage:`url('${image.replace(/'/g,"%27")}')`}}>
      <div className="cv-tourism-hero__body">
        <div className="cv-tourism-hero__eyebrow">Turismo · {item.subcategory || "Esperienza"}</div>
        <h1>{item.name}</h1>
        <p>{item.description}</p>
        <div className="cv-tourism-meta"><span>{item.comune}, {item.provincia}</span><span><Stars value={Number(item.rating || 0)} /> {Number(item.rating || 0).toFixed(1)}</span><span>{item.reviewCount || 0} recensioni</span></div>
      </div>
      {imageCredit(item)}
    </div>
    <div className="cv-tourism-grid">
      <div>
        <article className="cv-tourism-card">
          <h2>Scopri l’esperienza</h2>
          <p>{item.description}</p>
          <h3>Servizi disponibili</h3>
          <div className="cv-tourism-services">{services.map((service) => <span key={service}>{service}</span>)}</div>
          <div className="cv-tourism-map"><iframe loading="lazy" title={`Mappa ${item.name || ""}`} src={`https://www.google.com/maps?q=${encodeURIComponent(mapQuery)}&z=13&output=embed`} referrerPolicy="no-referrer-when-downgrade" /></div>
        </article>
        <section style={{marginTop:22}}>
          <div className="section-heading"><h2>Recensioni</h2></div>
          <div id="tourism-reviews">{reviews === null ? null : reviewsFailed ? <div className="notice">Le recensioni saranno disponibili a breve.</div> : reviews.length ? reviews.map((review) => <article key={review.id} className="cv-tourism-card cv-review-card"><div className="meta-row"><strong><Stars value={Number(review.rating || 0)} /></strong></div><h3>{review.title || ""}</h3><p>{review.text || ""}</p></article>) : <div className="notice">Nessuna recensione ancora.</div>}</div>
          <article className="cv-tourism-card" style={{marginTop:14}}>
            <h3>Lascia una recensione</h3>
            <form id="tourism-review-form" className="stack" onSubmit={submitReview}>
              <label>Valutazione<div className="cv-star-picker" data-star-picker role="radiogroup" aria-label="Valutazione da 1 a 5 stelle"><input type="hidden" name="rating" value={reviewRating} readOnly />{[1,2,3,4,5].map((value) => <button key={value} type="button" data-star-value={value} aria-label={`${value} stella${value===1?"":"e"}`} aria-pressed={value<=reviewRating} className={value<=reviewRating?"is-active":undefined} onClick={()=>setReviewRating(value)}>★</button>)}</div></label>
              <label>Titolo<input name="title" maxLength={160} required /></label>
              <label>Recensione<textarea name="text" maxLength={4000} required /></label>
              <button type="submit" className="button button-primary" disabled={reviewBusy}>Invia recensione</button>
            </form>
          </article>
        </section>
      </div>
      <aside className="cv-tourism-card">
        <h2>{item.name}</h2>
        <p><strong>Categoria</strong><br />Turismo · {item.subcategory || ""}</p>
        <p><strong>Località</strong><br />{item.comune}, {item.provincia}</p>
        <div className="cv-tourism-actions"><button id="tourism-favorite" className="button button-primary" type="button" disabled={favoriteBusy} onClick={toggleFavorite}>{favorite ? "♥ Salvato" : "♡ Salva nei preferiti"}</button><Link className="button button-secondary" href={`/mappa?attivita=${encodeURIComponent(item.id)}`}>Vedi sulla mappa</Link><Link className="button button-secondary" href="/catalogo?categoria=Turismo">Altre attività Turismo</Link></div>
      </aside>
    </div>
  </section>;
}
'''

Path('frontend-react/src/lib/tourism-interactions.ts').write_text(interactions)
Path('frontend-react/src/pages/TourismPage.tsx').write_text(page)
