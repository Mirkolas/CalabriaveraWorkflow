from pathlib import Path

interactions = r'''import { currentUser } from "./auth";

const METRIC_FIELDS = new Set(["views", "phoneClicks", "websiteClicks", "whatsappClicks", "requestCount"]);

export async function incrementBusinessMetric(businessId: string, field: string) {
  if (!METRIC_FIELDS.has(field) || !businessId) return false;
  const user = await currentUser();
  if (!user?.uid) return false;
  const localKey = `cv-metric-once:${user.uid}:${businessId}:${field}`;
  try { if (localStorage.getItem(localKey) === "1") return false; } catch {}
  const [{ db }, f] = await Promise.all([import("./firebase-db"), import("firebase/firestore")]);
  const eventId = `${user.uid}_${businessId}_${field}`;
  try {
    const created = await f.runTransaction(db, async (tx) => {
      const eventRef = f.doc(db, "businessMetricEvents", eventId);
      const businessRef = f.doc(db, "businesses", businessId);
      const [eventSnap, businessSnap] = await Promise.all([tx.get(eventRef), tx.get(businessRef)]);
      if (eventSnap.exists() || !businessSnap.exists() || businessSnap.data().status !== "approved") return false;
      tx.set(eventRef, { userId: user.uid, businessId, metric: field, createdAt: f.serverTimestamp() });
      tx.update(businessRef, { [field]: f.increment(1) });
      return true;
    });
    if (created) try { localStorage.setItem(localKey, "1"); } catch {}
    return created;
  } catch { return false; }
}
'''

page = r'''import { useEffect, useMemo, useState, type FormEvent } from "react";
import type { User } from "firebase/auth";
import Link from "../components/Link";
import { currentUser } from "../lib/auth";
import { businessImageUrl, businessPath, getBusinessFromLocation, imageUrlFromGallery, isFavorite, loadBusinessImages, loadReviews, specificCategory, submitReview, timeValue, toggleFavorite } from "../lib/businesses";
import { incrementBusinessMetric } from "../lib/business-detail-interactions";
import { startBusinessConversation } from "../lib/conversation-start";
import { languageFromPath, localizedField, withLanguage, type Language } from "../lib/language";
import { sendConversationMessage, getPublicProfile, publicProfileName, type PublicProfile } from "../lib/messages";
import { navigate } from "../lib/navigation";
import { findPublicBusiness, readInlineBusiness } from "../lib/public-data";
import { submitBusinessReport, type ReportCategory } from "../lib/reporting";
import { setPageSeo, setStructuredData } from "../lib/seo";
import type { Business, BusinessImage, Review } from "../types";

const COPY: Record<Language, Record<string, string>> = {
  it: { verified:"Verificata", reviews:"recensioni", about:"Informazioni", community:"Esperienze della community", writeReview:"Scrivi una recensione", noReviews:"Nessun risultato", send:"Invia", contact:"Contatta l’attività", call:"Chiama", website:"Sito web", whatsapp:"WhatsApp", save:"Salva nei preferiti", saved:"Salvato", message:"Invia messaggio", notFound:"Attività non trovata", notFoundText:"La scheda non esiste o non è ancora pubblica.", back:"Torna al catalogo" },
  en: { verified:"Verified", reviews:"reviews", about:"Information", community:"Community experiences", writeReview:"Write a review", noReviews:"No results", send:"Send", contact:"Contact the business", call:"Call", website:"Website", whatsapp:"WhatsApp", save:"Save to favorites", saved:"Saved", message:"Send message", notFound:"Business not found", notFoundText:"This listing does not exist or is not public yet.", back:"Back to directory" },
  fr: { verified:"Vérifiée", reviews:"avis", about:"Informations", community:"Expériences de la communauté", writeReview:"Écrire un avis", noReviews:"Aucun résultat", send:"Envoyer", contact:"Contacter l’activité", call:"Appeler", website:"Site web", whatsapp:"WhatsApp", save:"Ajouter aux favoris", saved:"Enregistrée", message:"Envoyer un message", notFound:"Activité introuvable", notFoundText:"Cette fiche n’existe pas ou n’est pas encore publique.", back:"Retour au catalogue" },
  de: { verified:"Verifiziert", reviews:"Bewertungen", about:"Informationen", community:"Erfahrungen der Community", writeReview:"Bewertung schreiben", noReviews:"Keine Ergebnisse", send:"Senden", contact:"Betrieb kontaktieren", call:"Anrufen", website:"Website", whatsapp:"WhatsApp", save:"Zu Favoriten", saved:"Gespeichert", message:"Nachricht senden", notFound:"Betrieb nicht gefunden", notFoundText:"Dieser Eintrag existiert nicht oder ist noch nicht öffentlich.", back:"Zurück zum Katalog" },
  es: { verified:"Verificada", reviews:"reseñas", about:"Información", community:"Experiencias de la comunidad", writeReview:"Escribir una reseña", noReviews:"Sin resultados", send:"Enviar", contact:"Contactar con la actividad", call:"Llamar", website:"Sitio web", whatsapp:"WhatsApp", save:"Guardar en favoritos", saved:"Guardada", message:"Enviar mensaje", notFound:"Actividad no encontrada", notFoundText:"Esta ficha no existe o aún no es pública.", back:"Volver al catálogo" },
};
const LOCALES: Record<Language,string>={it:"it-IT",en:"en-GB",fr:"fr-FR",de:"de-DE",es:"es-ES"};
const REPORT_LABELS: Record<ReportCategory,string>={wrong_phone:"Numero di telefono errato",closed:"Attività chiusa",changed_hours:"Orari cambiati",wrong_address:"Indirizzo errato",wrong_website:"Sito web errato",other:"Altro"};

function toast(message:string){const root=document.getElementById("toast-root");if(!root)return;root.innerHTML="";const node=document.createElement("div");node.className="toast";node.textContent=message;root.appendChild(node);window.setTimeout(()=>{if(root.contains(node))root.innerHTML=""},3800)}
function Stars({value}:{value:number}){const rating=Math.max(0,Math.min(5,Math.round(Number(value)||0)));return <span className="cv-stars" aria-label={`${rating} stelle su 5`}>{[1,2,3,4,5].map(v=><span key={v} className={v<=rating?undefined:"is-empty"}>★</span>)}</span>}
function formatDate(value:unknown,language:Language){const stamp=timeValue(value);return stamp?new Intl.DateTimeFormat(LOCALES[language],{dateStyle:"medium"}).format(stamp):""}
function safeHttp(value:unknown){try{const u=new URL(String(value||""));return /^https?:$/.test(u.protocol)?u.href:""}catch{return ""}}
function initials(name:string){return String(name||"").split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join("").toUpperCase()||"CV"}

export default function BusinessPage(){
  const language=languageFromPath(),copy=COPY[language],routeKey=`${location.pathname}${location.search}`;
  const [business,setBusiness]=useState<Business|null|undefined>(()=>readInlineBusiness()||undefined);
  const [gallery,setGallery]=useState<BusinessImage[]>([]),[reviews,setReviews]=useState<Review[]|null>(null),[favorite,setFavorite]=useState(false);
  const [selectedImage,setSelectedImage]=useState(0),[user,setUser]=useState<User|null>(null),[ownerProfile,setOwnerProfile]=useState<PublicProfile|null>(null);
  const [reviewRating,setReviewRating]=useState(5),[reviewBusy,setReviewBusy]=useState(false),[messageOpen,setMessageOpen]=useState(false),[messageBusy,setMessageBusy]=useState(false),[reportOpen,setReportOpen]=useState(false),[reportBusy,setReportBusy]=useState(false);

  useEffect(()=>{let active=true,previewSeen=false,hydratedId="";setBusiness(undefined);setGallery([]);setReviews(null);setSelectedImage(0);setOwnerProfile(null);
    const seo=(item:Business)=>{const name=String(localizedField(item as Record<string,unknown>,"name",language)||item.name||"Attività locale"),description=String(localizedField(item as Record<string,unknown>,"description",language)||item.description||"");const image=businessImageUrl(item);setPageSeo({title:`${name} | CalabriaVera`,description:description.slice(0,155),path:withLanguage(businessPath(item),language),image:image||undefined});const rating=Number(item.rating||0),reviewCount=Number(item.reviewCount||0),lat=Number(item.lat),lng=Number(item.lng);setStructuredData("business",{"@context":"https://schema.org","@type":"LocalBusiness",name,description,url:`https://calabriavera.com${withLanguage(businessPath(item),language)}`,...(image?{image:[image]}:{}),...(item.phone?{telephone:String(item.phone)}:{}),...(item.website?{sameAs:[String(item.website)]}:{}),address:{"@type":"PostalAddress",streetAddress:item.address||"",postalCode:item.cap||"",addressLocality:item.comune||"",addressRegion:item.provincia||"Calabria",addressCountry:"IT"},...(Number.isFinite(lat)&&Number.isFinite(lng)?{geo:{"@type":"GeoCoordinates",latitude:lat,longitude:lng}}:{}),...(rating>0&&reviewCount>0?{aggregateRating:{"@type":"AggregateRating",ratingValue:rating,reviewCount,bestRating:5,worstRating:1}}:{})});};
    const hydrate=async(item:Business)=>{if(hydratedId===item.id)return;hydratedId=item.id;const [images,rows,authUser,fav]=await Promise.all([loadBusinessImages(item.id).catch(()=>[]),loadReviews(item.id).catch(()=>[]),currentUser().catch(()=>null),isFavorite(item.id).catch(()=>false)]);const owner=item.ownerId?await getPublicProfile(String(item.ownerId)).catch(()=>null):null;if(!active)return;setGallery(images);setReviews(rows);setUser(authUser);setFavorite(fav);setOwnerProfile(owner);void incrementBusinessMetric(item.id,"views");};
    void findPublicBusiness(location.pathname,location.search).then(preview=>{if(!active||!preview)return;previewSeen=true;setBusiness(preview);seo(preview);void hydrate(preview)}).catch(()=>{});
    void getBusinessFromLocation(location.pathname,location.search).then(item=>{if(!active)return;if(!item){if(!previewSeen)setBusiness(null);return}setBusiness(item);seo(item);void hydrate(item)}).catch(()=>{if(active&&!previewSeen)setBusiness(null)});
    return()=>{active=false;setStructuredData("business",null)};
  },[routeKey,language]);

  const images=useMemo(()=>{if(!business)return[];const values=gallery.map(imageUrlFromGallery).filter(Boolean);const cover=businessImageUrl(business);if(cover&&!values.includes(cover))values.unshift(cover);return values},[business,gallery]);
  if(business===undefined)return <section className="section container"><div className="notice"><strong>CalabriaVera</strong><p>Caricamento della pagina…</p></div></section>;
  if(!business)return <section className="section container"><div className="empty-state"><h1 style={{fontSize:"3rem"}}>{copy.notFound}</h1><p>{copy.notFoundText}</p><Link className="button button-primary" href="/catalogo">{copy.back}</Link></div></section>;

  const title=String(localizedField(business as Record<string,unknown>,"name",language)||business.name||""),description=String(localizedField(business as Record<string,unknown>,"description",language)||business.description||"");
  const services=business.services||[],cover=images[selectedImage]||businessImageUrl(business),website=safeHttp(business.website),mapQuery=Number.isFinite(Number(business.lat))&&Number.isFinite(Number(business.lng))?`${Number(business.lat)},${Number(business.lng)}`:[business.address,business.cap,business.comune,business.provincia,"Italia"].filter(Boolean).join(", ");
  const mapEmbed=mapQuery?`https://www.google.com/maps?q=${encodeURIComponent(mapQuery)}&z=17&output=embed`:"",openMap=mapQuery?`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(mapQuery)}`:"";
  const canonical=`https://calabriavera.com${withLanguage(businessPath(business),language)}`;
  const ownerName=ownerProfile?publicProfileName(ownerProfile,String(business.ownerDisplayName||business.ownerName||"Proprietario dell’attività")):String(business.ownerDisplayName||business.ownerName||"");

  const favoriteClick=async()=>{if(!user){location.href=`/login?next=${encodeURIComponent(location.href)}`;return}try{setFavorite(await toggleFavorite(business.id))}catch{toast("Impossibile aggiornare i preferiti.")}};
  const reviewSubmit=async(e:FormEvent<HTMLFormElement>)=>{e.preventDefault();if(!user){location.href=`/login?next=${encodeURIComponent(location.href)}`;return}const form=e.currentTarget,data=new FormData(form);setReviewBusy(true);try{await submitReview(business.id,String(data.get("title")||"").trim(),String(data.get("text")||"").trim(),Number(data.get("rating")||5));toast("Recensione inviata per moderazione.");form.reset();setReviewRating(5)}catch(error){toast(error instanceof Error&&error.message==="REVIEW_EXISTS"?"Hai già lasciato una recensione.":"Impossibile inviare la recensione.")}finally{setReviewBusy(false)}};
  const messageSubmit=async(e:FormEvent<HTMLFormElement>)=>{e.preventDefault();if(!user){location.href=`/login?next=${encodeURIComponent(location.href)}`;return}const text=String(new FormData(e.currentTarget).get("message")||"").trim();if(!text||!business.ownerId)return;setMessageBusy(true);try{const conversation=await startBusinessConversation(business.id,String(business.ownerId));await sendConversationMessage(conversation,text);void incrementBusinessMetric(business.id,"requestCount");toast("Messaggio inviato.");e.currentTarget.reset();setMessageOpen(false)}catch{toast("Impossibile inviare il messaggio.")}finally{setMessageBusy(false)}};
  const reportSubmit=async(e:FormEvent<HTMLFormElement>)=>{e.preventDefault();if(!user){location.href=`/login?next=${encodeURIComponent(location.href)}`;return}const data=new FormData(e.currentTarget),category=String(data.get("category")||"other") as ReportCategory,details=String(data.get("details")||"");setReportBusy(true);try{await submitBusinessReport(business.id,category,details,REPORT_LABELS[category]||REPORT_LABELS.other);toast("Segnalazione inviata.");e.currentTarget.reset();setReportOpen(false)}catch{toast("Impossibile inviare la segnalazione.")}finally{setReportBusy(false)}};
  const shareNative=async()=>{try{if(navigator.share)await navigator.share({title,text:`${title} · CalabriaVera`,url:canonical});else{await navigator.clipboard.writeText(canonical);toast("Link copiato.")}}catch{}};
  const copyShare=async()=>{try{await navigator.clipboard.writeText(canonical);toast("Link copiato.")}catch{toast("Impossibile copiare il link.")}};

  return <section className="section container" id="business-root"><article>
    <div className="article-hero"><p className="eyebrow">{specificCategory(business)} · {business.comune||""}, {business.provincia||""}</p><h1>{title}</h1><div className="meta-row">{business.verified?<span className="badge badge-verified">{copy.verified}</span>:null}{business.rating?<span><Stars value={Number(business.rating)}/> {Number(business.rating).toFixed(1)}</span>:null}<span>{business.reviewCount||0} {copy.reviews}</span></div></div>
    <div className="cv-share-block cv-share-block--top cv-share-bar" data-cv-share="business"><strong>Condividi</strong><div className="cv-share-actions"><button type="button" className="button button-secondary" id="share-native" onClick={shareNative}>Condividi</button><a className="button button-secondary" target="_blank" rel="noopener" href={`https://wa.me/?text=${encodeURIComponent(`${title} · CalabriaVera ${canonical}`)}`}>WhatsApp</a><a className="button button-secondary" target="_blank" rel="noopener" href={`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(canonical)}`}>Facebook</a><button type="button" className="button button-secondary" id="share-copy" onClick={copyShare}>Copia link</button></div></div>
    <div className="split"><div>
      <div className="business-cover" id="business-cover">{cover?<img src={cover} loading="eager" fetchPriority="high" decoding="async" alt={title}/>:specificCategory(business)}</div>
      {images.length>1?<div className="business-gallery">{images.map((src,index)=><button type="button" key={`${src}-${index}`} data-gallery-index={index} className={selectedImage===index?"is-active":undefined} onClick={()=>setSelectedImage(index)}><img loading="lazy" decoding="async" fetchPriority="low" src={src} alt={`Foto ${index+1} di ${title}`}/></button>)}</div>:null}
      <section className="section" style={{paddingTop:"2rem"}}><p className="eyebrow">{copy.about}</p><h2>{title}</h2><p>{description}</p><div className="chip-row">{services.map(service=><span className="chip" key={service}>{service}</span>)}</div></section>
      {mapEmbed?<section className="business-google-map"><div className="business-map-heading"><div><p className="eyebrow">Posizione</p><h2>Dove si trova</h2></div><a className="button button-secondary" href={openMap} target="_blank" rel="noopener">Apri in Google Maps</a></div><div className="google-map-frame"><iframe src={mapEmbed} title={`Mappa di ${title}`} loading="lazy" allowFullScreen/></div><div className="business-map-actions"><Link className="text-link" href={`/mappa?attivita=${encodeURIComponent(business.id)}`}>Vedi nella mappa CalabriaVera</Link></div></section>:null}
      <section><p className="eyebrow">{copy.reviews}</p><h2>{copy.community}</h2><div id="reviews-list">{reviews===null?null:reviews.length?reviews.map(review=><div className="card cv-review-card" key={review.id}><div className="meta-row"><strong><Stars value={Number(review.rating||0)}/></strong><span>{formatDate(review.createdAt,language)}</span></div><h3>{review.title||""}</h3><p>{review.text||""}</p></div>):<div className="notice">{copy.noReviews}</div>}</div><div className="card" style={{marginTop:14}}><h3>{copy.writeReview}</h3>{user?<form id="review-form" className="form-grid" onSubmit={reviewSubmit}><label>Valutazione<div className="cv-star-picker" data-star-picker role="radiogroup" aria-label="Valutazione da 1 a 5 stelle"><input type="hidden" name="rating" value={reviewRating} readOnly/>{[1,2,3,4,5].map(value=><button key={value} type="button" data-star-value={value} className={value<=reviewRating?"is-active":undefined} aria-pressed={value<=reviewRating} aria-label={`${value} stella${value===1?"":"e"}`} onClick={()=>setReviewRating(value)}>★</button>)}</div></label><label>Titolo<input name="title" maxLength={160} required/></label><label className="full">Recensione<textarea name="text" maxLength={4000} required/></label><div className="full form-actions"><button className="button button-primary" disabled={reviewBusy}>{copy.send}</button></div></form>:<><p>Accedi per lasciare una recensione.</p><Link className="button button-secondary" href={`/login?next=${encodeURIComponent(location.href)}`}>Accedi</Link></>}</div></section>
    </div><aside className="card stack"><h3>{copy.contact}</h3>{ownerName?<div className="cv-business-owner" data-business-owner><span className="cv-business-owner__avatar">{ownerProfile?.avatarDataUrl?<img src={String(ownerProfile.avatarDataUrl)} alt={`Foto profilo di ${ownerName}`}/>:initials(ownerName)}</span><span className="cv-business-owner__copy"><small>Proprietario</small><strong>{ownerName}</strong></span></div>:null}{business.address?<div><strong>Indirizzo</strong><p>{business.address}{business.cap?`, ${business.cap}`:""}<br/>{business.comune}</p></div>:null}{business.phone?<a id="phone" className="button button-secondary" href={`tel:${String(business.phone).replace(/[^+\d]/g,"")}`} onClick={()=>void incrementBusinessMetric(business.id,"phoneClicks")}>{copy.call}</a>:null}{website?<a id="site" className="button button-secondary" target="_blank" rel="noopener" href={website} onClick={()=>void incrementBusinessMetric(business.id,"websiteClicks")}>{copy.website}</a>:null}{business.whatsapp?<a id="wa" className="button button-secondary" target="_blank" rel="noopener" href={`https://wa.me/${String(business.whatsapp).replace(/\D/g,"")}`} onClick={()=>void incrementBusinessMetric(business.id,"whatsappClicks")}>{copy.whatsapp}</a>:null}<button id="favorite" className="button button-primary" type="button" onClick={favoriteClick}>{favorite?copy.saved:copy.save}</button>{user?.uid!==business.ownerId?<button id="message-owner" className="button button-secondary" type="button" onClick={()=>{if(!user)location.href=`/login?next=${encodeURIComponent(location.href)}`;else setMessageOpen(true)}}>{copy.message}</button>:null}<button id="report" className="button button-secondary" type="button" onClick={()=>{if(!user)location.href=`/login?next=${encodeURIComponent(location.href)}`;else setReportOpen(true)}}>Segnala una modifica</button>
      {messageOpen?<div id="message-panel" className="card"><form id="message-form" className="stack" onSubmit={messageSubmit}><label>Messaggio<textarea name="message" maxLength={2000} required/></label><div className="form-actions"><button className="button button-primary" disabled={messageBusy}>Invia messaggio</button><button type="button" id="cancel-message" className="button button-secondary" onClick={()=>setMessageOpen(false)}>Annulla</button></div></form></div>:null}
      {reportOpen?<div id="report-panel" className="card"><form id="report-form" className="stack" onSubmit={reportSubmit}><label>Che cosa va corretto?<select name="category" required>{Object.entries(REPORT_LABELS).map(([value,label])=><option value={value} key={value}>{label}</option>)}</select></label><label>Dettagli<textarea name="details" maxLength={500}/></label><div className="form-actions"><button className="button button-primary" disabled={reportBusy}>Invia segnalazione</button><button type="button" id="cancel-report" className="button button-secondary" onClick={()=>setReportOpen(false)}>Annulla</button></div></form></div>:null}
    </aside></div>
  </article></section>;
}
'''

Path('frontend-react/src/lib/business-detail-interactions.ts').write_text(interactions)
Path('frontend-react/src/pages/BusinessPage.tsx').write_text(page)
