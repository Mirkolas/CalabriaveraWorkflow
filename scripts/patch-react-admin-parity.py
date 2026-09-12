from pathlib import Path

root=Path('source/frontend-react/src')
admin_page=root/'pages/AdminPage.tsx'
backup_page=root/'pages/BackupPage.tsx'
app=root/'App.tsx'
admin_lib=root/'lib/admin.ts'

admin_page.write_text(r'''import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import Link from "../components/Link";
import {
  deleteBusinessAdmin, deleteCollectionDoc, deleteConversationAdmin, getSiteSettings,
  listBusinessesAdmin, listCollectionAdmin, listConversationsAdmin, listReportsAdmin, listReviewsAdmin,
  requireAdmin, saveCollectionDoc, setBusinessStatus, setBusinessVerified, setReviewStatus,
  updateSiteSettings,
} from "../lib/admin";
import { slugify } from "../lib/businesses";
import { navigate } from "../lib/navigation";
import { setPageSeo } from "../lib/seo";
import type { Business, Review } from "../types";

type Row = Record<string, unknown> & { id: string };
type AdminAction = (task: () => Promise<unknown>) => Promise<void>;

const MENU = [
  ["index", "Panoramica", "/admin"],
  ["attivita", "Attività", "/admin/attivita"],
  ["recensioni", "Recensioni", "/admin/recensioni"],
  ["blog", "Blog", "/admin/blog"],
  ["utenti", "Utenti", "/admin/utenti"],
  ["categorie", "Categorie", "/admin/categorie"],
  ["comuni", "Comuni", "/admin/comuni"],
  ["messaggi", "Messaggi", "/admin/messaggi"],
  ["impostazioni", "Impostazioni", "/admin/impostazioni"],
  ["seo", "SEO", "/admin/seo"],
] as const;

function sectionFromPath() {
  const parts=location.pathname.split("/").filter(Boolean);
  return parts.length <= 1 ? "index" : parts.at(-1) || "index";
}
function stringValue(value: unknown) { return typeof value === "string" ? value : value == null ? "" : String(value); }
function timeText(value: unknown) {
  if (value && typeof value === "object" && "toMillis" in value && typeof (value as {toMillis?:unknown}).toMillis === "function") {
    return new Intl.DateTimeFormat("it-IT",{dateStyle:"medium",timeStyle:"short"}).format((value as {toMillis:()=>number}).toMillis());
  }
  const seconds=value && typeof value === "object" && "seconds" in value ? Number((value as {seconds?:number}).seconds||0) : 0;
  const parsed=seconds?seconds*1000:new Date(String(value||"")).getTime();
  return Number.isFinite(parsed)&&parsed>0 ? new Intl.DateTimeFormat("it-IT",{dateStyle:"medium",timeStyle:"short"}).format(parsed) : "";
}
function dateTimeLocal(value: unknown) {
  let date: Date | null=null;
  if (value && typeof value === "object" && "toDate" in value && typeof (value as {toDate?:unknown}).toDate === "function") date=(value as {toDate:()=>Date}).toDate();
  else if (value) date=new Date(String(value));
  if (!date || Number.isNaN(date.getTime())) return "";
  return new Date(date.getTime()-date.getTimezoneOffset()*60000).toISOString().slice(0,16);
}

export default function AdminPage() {
  const section=sectionFromPath();
  const [authorized,setAuthorized]=useState<boolean|null>(null);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");
  const [businesses,setBusinesses]=useState<Business[]>([]);
  const [reviews,setReviews]=useState<Review[]>([]);
  const [rows,setRows]=useState<Row[]>([]);
  const [secondary,setSecondary]=useState<Row[]>([]);
  const [tertiary,setTertiary]=useState<Row[]>([]);

  const load=async()=>{
    setBusy(true);setError("");
    try{
      await requireAdmin(); setAuthorized(true);
      setBusinesses([]);setReviews([]);setRows([]);setSecondary([]);setTertiary([]);
      if(section==="index"){
        const [allBusinesses,pendingReviews,users,posts,reports]=await Promise.all([
          listBusinessesAdmin(),listReviewsAdmin("pending"),listCollectionAdmin("users",300),listCollectionAdmin("blogPosts",500),listReportsAdmin(),
        ]);
        setBusinesses(allBusinesses);setReviews(pendingReviews);setRows(users);setSecondary(posts);setTertiary(reports);
      } else if(section==="attivita") setBusinesses(await listBusinessesAdmin());
      else if(section==="recensioni") setReviews(await listReviewsAdmin("pending"));
      else if(section==="blog"){
        const [posts,sources]=await Promise.all([listCollectionAdmin("blogPosts",500),listCollectionAdmin("magazineSources",300)]);
        setRows(posts);setSecondary(sources);
      } else if(section==="utenti") setRows(await listCollectionAdmin("users",300));
      else if(section==="categorie") setRows(await listCollectionAdmin("categories",300));
      else if(section==="comuni") setRows(await listCollectionAdmin("municipalities",300));
      else if(section==="messaggi") setRows(await listConversationsAdmin(300));
      else if(section==="impostazioni") setRows([await getSiteSettings()]);
      else if(section==="seo"){
        const [allBusinesses,posts]=await Promise.all([listBusinessesAdmin(),listCollectionAdmin("blogPosts",500)]);
        setBusinesses(allBusinesses);setRows(posts);
      }
    }catch(cause){
      const message=cause instanceof Error?cause.message:"";
      if(message==="AUTH_REQUIRED") navigate(`/login?next=${encodeURIComponent(location.pathname)}`,true);
      else if(message==="ADMIN_REQUIRED"){setAuthorized(false);setError("Questo account non dispone dei permessi necessari.");}
      else {setAuthorized(false);setError("Impossibile caricare il pannello amministratore.");}
    }finally{setBusy(false);}
  };

  useEffect(()=>{setPageSeo({title:"Amministrazione | CalabriaVera",description:"Area amministrativa CalabriaVera.",path:location.pathname,robots:"noindex,nofollow"});void load();},[section]);
  const action:AdminAction=async(task)=>{setBusy(true);setError("");try{await task();await load();}catch(cause){console.error(cause);setError("Operazione non riuscita.");setBusy(false);}};

  if(authorized===null) return <section className="section container"><div id="admin-root"><div className="notice">Caricamento amministrazione…</div></div></section>;
  if(!authorized) return <section className="section container"><div id="admin-root"><div className="notice"><strong>Accesso amministratore richiesto.</strong><p>{error}</p><Link className="button button-secondary" href="/">Torna alla home</Link></div></div></section>;

  return <section className="section container"><div id="admin-root">
    <div className="section-heading"><div><p className="eyebrow">CalabriaVera</p><h1 style={{fontSize:"clamp(3rem,6vw,4.6rem)"}}>Amministrazione</h1></div></div>
    <div className="admin-layout"><aside className="card stack" aria-label="Menu amministrazione">{MENU.map(([key,label,href])=><Link key={key} className={section===key?"button button-primary":"button button-secondary"} href={href}>{label}</Link>)}</aside><section><div id="admin-content" className="stack">
      {error?<div className="notice" role="alert">{error}</div>:null}
      {section==="index"?<Overview businesses={businesses} reviews={reviews} users={rows} posts={secondary} reports={tertiary}/>:null}
      {section==="attivita"?<ActivitiesPanel items={businesses} busy={busy} action={action}/>:null}
      {section==="recensioni"?<ReviewsPanel rows={reviews} action={action}/>:null}
      {section==="blog"?<BlogPanel posts={rows} sources={secondary} busy={busy} action={action}/>:null}
      {section==="utenti"?<UsersPanel rows={rows}/>:null}
      {section==="categorie"?<TaxonomyPanel title="Categorie" collection="categories" rows={rows} busy={busy} action={action}/>:null}
      {section==="comuni"?<TaxonomyPanel title="Comuni" collection="municipalities" rows={rows} busy={busy} action={action} withProvince/>:null}
      {section==="messaggi"?<MessagesAdminPanel rows={rows} busy={busy} action={action}/>:null}
      {section==="impostazioni"?<SettingsPanel settings={rows[0]||null} busy={busy} action={action}/>:null}
      {section==="seo"?<SeoPanel businesses={businesses} posts={rows}/>:null}
      {!MENU.some(([key])=>key===section)?<div className="notice"><strong>Sezione amministrativa non disponibile.</strong><p>Usa il menu per aprire una sezione supportata dal pannello principale.</p></div>:null}
    </div></section></div>
  </div></section>;
}

function Overview({businesses,reviews,users,posts,reports}:{businesses:Business[];reviews:Review[];users:Row[];posts:Row[];reports:Row[]}){
  const openReports=reports.filter((row)=>row.status==="open").length;
  const published=posts.filter((row)=>row.status==="published").length;
  return <><div><p className="eyebrow">Stato del portale</p><h2>Panoramica</h2></div><div className="stat-grid"><div className="stat"><div>Attività</div><strong>{businesses.length}</strong></div><div className="stat"><div>Da approvare</div><strong>{businesses.filter((item)=>item.status==="pending").length}</strong></div><div className="stat"><div>Recensioni in attesa</div><strong>{reviews.length}</strong></div><div className="stat"><div>Utenti</div><strong>{users.length}</strong></div></div><div className="grid-2"><div className="card"><h3>Contenuti</h3><p>{published} articoli pubblicati su {posts.length} totali.</p><Link className="text-link" href="/admin/blog">Gestisci blog</Link></div><div className="card"><h3>Segnalazioni</h3><p>{openReports} segnalazioni aperte.</p><p className="muted small">Le segnalazioni restano disponibili per il controllo amministrativo.</p></div></div></>;
}

function ActivitiesPanel({items,busy,action}:{items:Business[];busy:boolean;action:AdminAction}){
  const [search,setSearch]=useState("");
  const filtered=useMemo(()=>{const q=search.toLowerCase().trim();return items.filter((item)=>!q||[item.name,item.comune,item.category,item.status].join(" ").toLowerCase().includes(q));},[items,search]);
  return <><div className="section-heading"><div><p className="eyebrow">Moderazione</p><h2>Attività</h2></div><span className="badge">{items.length} totali</span></div><label>Cerca attività<input id="admin-business-search" value={search} onChange={(event)=>setSearch(event.target.value)} placeholder="Nome, comune o categoria"/></label><div id="admin-business-list" className="result-list">{filtered.map((item)=><article className="card" key={item.id}><div className="meta-row"><span>{item.category||""}</span><span>·</span><span>{item.comune||""}</span><span className={`badge status-${item.status||""}`}>{item.status||""}</span>{item.verified?<span className="badge badge-verified">Verificata</span>:null}</div><h3>{item.name||""}</h3><p>{item.description||""}</p><div className="form-actions"><Link className="button button-secondary" href={`/attivita?id=${encodeURIComponent(item.id)}`}>Apri</Link>{item.status!=="approved"?<button disabled={busy} className="button button-primary" onClick={()=>void action(()=>setBusinessStatus(item.id,"approved"))}>Approva</button>:null}{item.status!=="rejected"?<button disabled={busy} className="button button-secondary" onClick={()=>void action(()=>setBusinessStatus(item.id,"rejected"))}>Rifiuta</button>:null}<button disabled={busy} className="button button-secondary" onClick={()=>void action(()=>setBusinessVerified(item.id,!item.verified))}>{item.verified?"Rimuovi verifica":"Verifica"}</button><button disabled={busy} className="button button-secondary danger" onClick={()=>window.confirm(`Eliminare “${item.name||"questa attività"}”?`)&&void action(()=>deleteBusinessAdmin(item.id))}>Elimina</button></div></article>):<div className="notice">Nessuna attività trovata.</div>}</div></>;
}

function ReviewsPanel({rows,action}:{rows:Review[];action:AdminAction}){
  return <><div className="section-heading"><div><p className="eyebrow">Moderazione</p><h2>Recensioni</h2></div><span className="badge">{rows.length} in attesa</span></div><div className="result-list">{rows.length?rows.map((row)=><article className="card" key={row.id}><div className="meta-row"><strong>{row.rating}/5</strong><span>{timeText(row.createdAt)}</span></div><h3>{row.title||"Senza titolo"}</h3><p>{row.text||""}</p><div className="form-actions"><button className="button button-primary" onClick={()=>void action(()=>setReviewStatus(row.id,"approved"))}>Approva</button><button className="button button-secondary" onClick={()=>void action(()=>setReviewStatus(row.id,"rejected"))}>Rifiuta</button></div></article>):<div className="notice">Nessuna recensione in attesa.</div>}</div></>;
}

function BlogPanel({posts,sources,busy,action}:{posts:Row[];sources:Row[];busy:boolean;action:AdminAction}){
  const [tab,setTab]=useState<"posts"|"sources">("posts");
  const [editingPost,setEditingPost]=useState<Row|null|undefined>(undefined);
  const [editingSource,setEditingSource]=useState<Row|null|undefined>(undefined);
  if(editingPost!==undefined) return <PostEditor post={editingPost} busy={busy} action={action} close={()=>setEditingPost(undefined)}/>;
  if(editingSource!==undefined) return <SourceEditor source={editingSource} busy={busy} action={action} close={()=>setEditingSource(undefined)}/>;
  const originals=posts.filter((row)=>row.origin!=="external").length, imported=posts.filter((row)=>row.origin==="external").length;
  return <><div className="section-heading"><div><p className="eyebrow">Contenuti</p><h2>Blog & Magazine</h2></div><button className="button button-primary" type="button" onClick={()=>setEditingPost(null)}>Nuovo articolo</button></div><div className="tabs"><button type="button" className={`tab ${tab==="posts"?"active":""}`} onClick={()=>setTab("posts")}>Articoli</button><button type="button" className={`tab ${tab==="sources"?"active":""}`} onClick={()=>setTab("sources")}>Fonti automatiche</button></div>{tab==="posts"?<><div className="stat-grid"><div className="stat"><div>Totale</div><strong>{posts.length}</strong></div><div className="stat"><div>Editoriali</div><strong>{originals}</strong></div><div className="stat"><div>Importati</div><strong>{imported}</strong></div><div className="stat"><div>Pubblicati</div><strong>{posts.filter((row)=>row.status==="published").length}</strong></div></div><div className="result-list">{posts.map((row)=>{const external=row.origin==="external"&&row.externalUrl;const viewHref=external?stringValue(row.externalUrl):`/blog/${encodeURIComponent(stringValue(row.slug))}`;return <article className="card" key={row.id}><div className="meta-row"><span className="badge">{external?"Importato":"Editoriale"}</span><span>{stringValue(row.category)}</span><span>·</span><span>{stringValue(row.status)}</span>{external?<span>· {stringValue(row.sourceName||"Fonte esterna")}</span>:null}</div><h3>{stringValue(row.title)}</h3><p>{stringValue(row.excerpt)}</p><div className="form-actions"><button className="button button-secondary" onClick={()=>setEditingPost(row)}>Modifica</button><button className="button button-secondary danger" onClick={()=>window.confirm("Eliminare questo articolo?")&&void action(()=>deleteCollectionDoc("blogPosts",row.id))}>Elimina</button>{row.status==="published"?<a className="button button-secondary" href={viewHref} target="_blank" rel="noopener noreferrer">{external?"Apri fonte":"Visualizza"}</a>:null}</div></article>})}</div></>:<SourcesList sources={sources} action={action} edit={setEditingSource}/>}</>;
}

function PostEditor({post,busy,action,close}:{post:Row|null;busy:boolean;action:AdminAction;close:()=>void}){
  const external=post?.origin==="external";
  const submit=(event:FormEvent<HTMLFormElement>)=>{event.preventDefault();const form=event.currentTarget,data=new FormData(form);const title=stringValue(data.get("title")).trim(),excerpt=stringValue(data.get("excerpt")).trim(),content=stringValue(data.get("content")).trim();const payload:Record<string,unknown>={title,category:stringValue(data.get("category")).trim(),slug:slugify(stringValue(data.get("slug"))||title),excerpt,content,coverUrl:stringValue(data.get("coverUrl")).trim(),status:data.get("published")==="on"?"published":"draft",publishedAt:stringValue(data.get("publishedAt"))?new Date(stringValue(data.get("publishedAt"))).toISOString():post?.publishedAt||new Date().toISOString(),translations:{...((post?.translations as Record<string,unknown>)||{}),it:{title,excerpt,content}}};void action(()=>saveCollectionDoc("blogPosts",payload,post?.id)).then(close);};
  return <div className="card"><p className="eyebrow">{post?"Modifica articolo":"Nuovo articolo"}</p><h2>{post?stringValue(post.title):"Scrivi un articolo"}</h2>{external?<div className="notice"><strong>Contenuto importato da {stringValue(post?.sourceName||"fonte esterna")}</strong><p>Puoi correggere titolo, categoria, sommario e stato. Il link alla fonte originale e i metadati di importazione vengono mantenuti.</p></div>:null}<form id="post-form" className="form-grid" onSubmit={submit}><label>Titolo<input name="title" required maxLength={180} defaultValue={stringValue(post?.title)}/></label><label>Categoria<input name="category" required maxLength={80} defaultValue={stringValue(post?.category||"Guide")}/></label><label>Slug<input name="slug" defaultValue={stringValue(post?.slug)}/></label><label>Data pubblicazione<input name="publishedAt" type="datetime-local" defaultValue={dateTimeLocal(post?.publishedAt)}/></label><label className="full">Sommario<textarea name="excerpt" maxLength={500} defaultValue={stringValue(post?.excerpt)}/></label><label className="full">Contenuto<textarea name="content" required style={{minHeight:320}} defaultValue={stringValue(post?.content||post?.excerpt)}/></label><label className="full">Immagine di copertina URL<input name="coverUrl" type="url" defaultValue={stringValue(post?.coverUrl)}/></label>{external?<label className="full">Fonte originale<input disabled value={stringValue(post?.externalUrl)}/></label>:null}<label className="full"><span><input type="checkbox" name="published" defaultChecked={post?.status==="published"}/> Pubblica subito</span></label><div className="full form-actions"><button className="button button-primary" disabled={busy}>Salva</button><button type="button" className="button button-secondary" onClick={close}>Annulla</button></div></form></div>;
}

function SourcesList({sources,action,edit}:{sources:Row[];action:AdminAction;edit:(row:Row|null)=>void}){
  const enabled=sources.filter((row)=>row.enabled!==false).length,errors=sources.filter((row)=>row.lastError).length;
  return <><div className="section-heading"><div><p className="eyebrow">Automazione RSS / Atom</p><h3>Fonti del Magazine</h3></div><button className="button button-primary" type="button" onClick={()=>edit(null)}>Aggiungi fonte</button></div><div className="stat-grid"><div className="stat"><div>Fonti</div><strong>{sources.length}</strong></div><div className="stat"><div>Attive</div><strong>{enabled}</strong></div><div className="stat"><div>Errori</div><strong>{errors}</strong></div><div className="stat"><div>Frequenza</div><strong>6h</strong></div></div><div className="notice"><strong>Importazione automatica dentro Blog / Magazine</strong><p>Il portale importa soltanto metadata, breve estratto e link originale; le immagini restano disabilitate salvo diritti espliciti.</p></div><div className="result-list">{sources.map((row)=><article className="card" key={row.id}><div className="meta-row"><span className={`badge ${row.enabled!==false?"success":""}`}>{row.enabled!==false?"Attiva":"Disattivata"}</span><span>{stringValue(row.category||"Magazine")}</span><span>·</span><span>{stringValue(row.province||"Calabria")}</span></div><h3>{stringValue(row.name||"Fonte")}</h3><p className="small"><strong>Feed:</strong> {stringValue(row.feedUrl)}</p>{row.lastError?<div className="notice danger"><strong>Ultimo errore</strong><p className="small">{stringValue(row.lastError)}</p></div>:null}<div className="form-actions"><button className="button button-secondary" onClick={()=>edit(row)}>Modifica</button><button className="button button-secondary danger" onClick={()=>window.confirm("Eliminare questa fonte? Gli articoli già importati resteranno nel Magazine.")&&void action(()=>deleteCollectionDoc("magazineSources",row.id))}>Elimina fonte</button>{row.homepageUrl?<a className="button button-secondary" href={stringValue(row.homepageUrl)} target="_blank" rel="noopener noreferrer">Apri sito</a>:null}</div></article>)}</div></>;
}

function SourceEditor({source,busy,action,close}:{source:Row|null;busy:boolean;action:AdminAction;close:()=>void}){
  const [urlError,setUrlError]=useState("");
  const submit=(event:FormEvent<HTMLFormElement>)=>{event.preventDefault();const form=event.currentTarget,data=new FormData(form);let feed:URL,homepage:URL|null=null;try{feed=new URL(stringValue(data.get("feedUrl")).trim());if(!["http:","https:"].includes(feed.protocol))throw new Error();if(stringValue(data.get("homepageUrl")).trim()){homepage=new URL(stringValue(data.get("homepageUrl")).trim());if(!["http:","https:"].includes(homepage.protocol))throw new Error();}}catch{setUrlError("URL feed o sito fonte non valido.");return;}setUrlError("");const payload={name:stringValue(data.get("name")).trim(),feedUrl:feed.toString(),homepageUrl:homepage?.toString()||"",category:stringValue(data.get("category")).trim(),province:stringValue(data.get("province")).trim()||"Calabria",maxItemsPerRun:Math.min(50,Math.max(1,Number(data.get("maxItemsPerRun")||12))),maxAgeDays:Math.min(60,Math.max(1,Number(data.get("maxAgeDays")||10))),excerptMaxLength:Math.min(500,Math.max(160,Number(data.get("excerptMaxLength")||360))),enabled:data.get("enabled")==="on",autoPublish:data.get("autoPublish")==="on",allowImages:data.get("allowImages")==="on",rightsMode:"metadata-link",notes:stringValue(data.get("notes")).trim()};void action(()=>saveCollectionDoc("magazineSources",payload,source?.id)).then(close);};
  return <div className="card"><p className="eyebrow">Blog & Magazine · Automazione</p><h2>{source?`Modifica ${stringValue(source.name||"fonte")}`:"Aggiungi fonte RSS / Atom"}</h2>{urlError?<div className="notice danger">{urlError}</div>:null}<form id="magazine-source-form" className="form-grid" onSubmit={submit}><label>Nome fonte<input name="name" required maxLength={120} defaultValue={stringValue(source?.name)}/></label><label>Categoria<input name="category" required maxLength={80} defaultValue={stringValue(source?.category||"Magazine")}/></label><label className="full">URL feed RSS / Atom<input name="feedUrl" type="url" required defaultValue={stringValue(source?.feedUrl)}/></label><label className="full">URL sito della fonte<input name="homepageUrl" type="url" defaultValue={stringValue(source?.homepageUrl)}/></label><label>Provincia / area<input name="province" maxLength={80} defaultValue={stringValue(source?.province||"Calabria")}/></label><label>Max nuovi articoli per sincronizzazione<input name="maxItemsPerRun" type="number" min={1} max={50} defaultValue={Number(source?.maxItemsPerRun||12)}/></label><label>Età massima articoli (giorni)<input name="maxAgeDays" type="number" min={1} max={60} defaultValue={Number(source?.maxAgeDays||10)}/></label><label>Lunghezza estratto<input name="excerptMaxLength" type="number" min={160} max={500} defaultValue={Number(source?.excerptMaxLength||360)}/></label><label className="full"><span><input type="checkbox" name="enabled" defaultChecked={source?.enabled!==false}/> Fonte attiva</span></label><label className="full"><span><input type="checkbox" name="autoPublish" defaultChecked={source?.autoPublish!==false}/> Pubblica automaticamente; se disattivato salva come bozza</span></label><label className="full"><span><input type="checkbox" name="allowImages" defaultChecked={source?.allowImages===true}/> Usa le immagini presenti nel feed <strong>solo se disponi dei diritti necessari</strong></span></label><label className="full">Note interne<textarea name="notes" maxLength={800} defaultValue={stringValue(source?.notes)}/></label><div className="full notice"><strong>Modalità protetta metadata-link</strong><p>Il sistema non importa automaticamente il testo completo. Ogni contenuto esterno conserva il link e l’attribuzione alla fonte originale.</p></div><div className="full form-actions"><button className="button button-primary" disabled={busy}>Salva fonte</button><button type="button" className="button button-secondary" onClick={close}>Annulla</button></div></form></div>;
}

function UsersPanel({rows}:{rows:Row[]}){
  return <><div className="section-heading"><div><p className="eyebrow">Community</p><h2>Utenti</h2></div><span className="badge">{rows.length} account</span></div><div className="table-wrap"><table><thead><tr><th>Nome</th><th>Email</th><th>Ruolo</th><th>Marketing</th></tr></thead><tbody>{rows.map((row)=><tr key={row.id}><td>{stringValue(row.displayName||[row.firstName,row.lastName].filter(Boolean).join(" ")||"—")}</td><td>{stringValue(row.email)}</td><td><span className="badge">{stringValue(row.role||"USER")}</span></td><td>{row.marketingConsent?"Sì":"No"}</td></tr>)}</tbody></table></div><div className="notice"><strong>Gestione credenziali</strong><p>Disabilitazione e cancellazione degli accessi si effettuano da Firebase Authentication, così le credenziali non vengono mai esposte al browser.</p></div></>;
}

function TaxonomyPanel({title,collection,rows,busy,action,withProvince=false}:{title:string;collection:string;rows:Row[];busy:boolean;action:AdminAction;withProvince?:boolean}){
  const submit=(event:FormEvent<HTMLFormElement>)=>{event.preventDefault();const form=event.currentTarget,data=new FormData(form),name=stringValue(data.get("name")).trim(),province=stringValue(data.get("province")).trim();if(!name)return;void action(()=>saveCollectionDoc(collection,{name,...(withProvince?{province}:{}),active:true},slugify(name)));form.reset();};
  const sorted=[...rows].sort((a,b)=>stringValue(a.name).localeCompare(stringValue(b.name),"it"));
  return <><div className="section-heading"><div><p className="eyebrow">Tassonomie</p><h2>{title}</h2></div><span className="badge">{rows.length}</span></div><form id="taxonomy-form" className="form-grid card" onSubmit={submit}><label>Nome<input name="name" required/></label>{withProvince?<label>Provincia<input name="province" required/></label>:null}<div className="form-actions"><button className="button button-primary" disabled={busy}>Aggiungi</button></div></form><div className="table-wrap"><table><thead><tr><th>Nome</th>{withProvince?<th>Provincia</th>:null}<th></th></tr></thead><tbody>{sorted.map((row)=><tr key={row.id}><td>{stringValue(row.name)}</td>{withProvince?<td>{stringValue(row.province)}</td>:null}<td><button className="button button-secondary danger" onClick={()=>window.confirm("Eliminare questa voce?")&&void action(()=>deleteCollectionDoc(collection,row.id))}>Elimina</button></td></tr>)}</tbody></table></div></>;
}

function MessagesAdminPanel({rows,busy,action}:{rows:Row[];busy:boolean;action:AdminAction}){
  return <><div className="section-heading"><div><p className="eyebrow">Assistenza</p><h2>Messaggi</h2></div><span className="badge">{rows.length} conversazioni</span></div><div className="table-wrap"><table><thead><tr><th>Attività</th><th>Partecipanti</th><th>Ultimo messaggio</th><th>Aggiornata</th><th>Azioni</th></tr></thead><tbody>{rows.length?rows.map((row)=><tr key={row.id}><td>{stringValue(row.businessId)}</td><td>{Array.isArray(row.participantIds)?row.participantIds.map(String).join(", "):""}</td><td>{stringValue(row.lastMessage)}</td><td>{timeText(row.updatedAt)}</td><td><button disabled={busy} className="button button-secondary danger" onClick={()=>window.confirm(`Eliminare definitivamente questa conversazione?\n\nVerranno eliminati anche tutti i messaggi collegati.\nL’operazione non può essere annullata.`)&&void action(()=>deleteConversationAdmin(row.id))}>Elimina definitivamente</button></td></tr>):<tr><td colSpan={5}>Nessuna conversazione.</td></tr>}</tbody></table></div></>;
}

function SettingsPanel({settings,busy,action}:{settings:Row|null;busy:boolean;action:AdminAction}){
  const key=`${settings?.maintenance===true}-${stringValue(settings?.contactEmail)}-${stringValue(settings?.siteName)}`;
  const submit=(event:FormEvent<HTMLFormElement>)=>{event.preventDefault();const data=new FormData(event.currentTarget);void action(()=>updateSiteSettings({siteName:stringValue(data.get("siteName")).trim()||"CalabriaVera",contactEmail:stringValue(data.get("contactEmail")).trim(),footerText:stringValue(data.get("footerText")).trim(),maintenance:data.get("maintenance")==="on"}));};
  return <><div><p className="eyebrow">Configurazione</p><h2>Impostazioni</h2></div><form key={key} id="settings-form" className="form-grid card" onSubmit={submit}><label>Nome sito<input name="siteName" required defaultValue={stringValue(settings?.siteName||"CalabriaVera")}/></label><label>Email contatti<input name="contactEmail" type="email" defaultValue={stringValue(settings?.contactEmail)}/></label><label className="full">Testo footer<textarea name="footerText" defaultValue={stringValue(settings?.footerText||"Il portale delle attività e dei servizi della Calabria.")}/></label><label className="full"><span><input type="checkbox" name="maintenance" defaultChecked={settings?.maintenance===true}/> Modalità manutenzione</span></label><div className="full form-actions"><button className="button button-primary" disabled={busy}>Salva impostazioni</button></div></form></>;
}

function SeoPanel({businesses,posts}:{businesses:Business[];posts:Row[]}){
  const approved=businesses.filter((item)=>item.status==="approved"),published=posts.filter((row)=>row.status==="published");
  return <><div><p className="eyebrow">Indicizzazione</p><h2>SEO e sitemap</h2></div><div className="stat-grid"><div className="stat"><div>Attività indicizzabili</div><strong>{approved.length}</strong></div><div className="stat"><div>Articoli indicizzabili</div><strong>{published.length}</strong></div><div className="stat"><div>Attività con slug</div><strong>{businesses.filter((item)=>item.slug).length}</strong></div><div className="stat"><div>Attività con descrizione</div><strong>{businesses.filter((item)=>String(item.description||"").length>=80).length}</strong></div></div><div className="notice"><strong>Sitemap automatica</strong><p>La build di deploy genera le pagine statiche e la sitemap. In produzione, la pipeline legge solo attività approvate e articoli pubblicati.</p><a className="text-link" href="/sitemap.xml" target="_blank" rel="noreferrer">Apri sitemap corrente</a></div></>;
}
''',encoding='utf-8')

backup_page.write_text(r'''import { useEffect } from "react";
import { setPageSeo } from "../lib/seo";

export default function BackupPage(){
  useEffect(()=>{setPageSeo({title:"Backup e ripristino | CalabriaVera",description:"Backup e ripristino CalabriaVera.",path:"/backup",robots:"noindex,nofollow"});},[]);
  return <section className="section container"><p className="eyebrow">Admin</p><h1>Backup e ripristino</h1><div id="backup-root"><div className="notice"><h2>Backup cifrati</h2><p>Le copie complete vengono conservate nelle Releases del repository GitHub privato. Ogni quinto backup riuscito resta soltanto il più recente, dopo la verifica del download.</p><p><a className="button button-primary" rel="noopener noreferrer" target="_blank" href="https://github.com/Mirkolas/calabriavera/actions/workflows/daily-backup.yml">Controlla o avvia backup</a></p><p>Se il job risulta saltato, l’automazione non è attiva: controlla gli accessi Firebase e le variabili GitHub.</p></div><div className="notice"><h2>Ripristino protetto</h2><p>Il ripristino parte in simulazione e richiede una conferma prima di modificare dati o account. Conserva una copia offline della chiave.</p><a className="button button-secondary" rel="noopener noreferrer" target="_blank" href="https://github.com/Mirkolas/calabriavera/blob/main/docs/GITHUB_BACKUP_RIPRISTINO.md">Apri la guida</a></div></div></section>;
}
''',encoding='utf-8')

s=app.read_text(encoding='utf-8')
anchor='const AdminPage = lazy(() => import("./pages/AdminPage"));'
if anchor not in s: raise SystemExit('AdminPage import marker missing')
s=s.replace(anchor,anchor+'\nconst BackupPage = lazy(() => import("./pages/BackupPage"));',1)
old='  if (path === "/backup" || path === "/admin" || path.startsWith("/admin/")) return <AdminPage />;'
new='  if (path === "/backup") return <BackupPage />;\n  if (path === "/admin" || path.startsWith("/admin/")) return <AdminPage />;'
if old not in s: raise SystemExit('admin route marker missing')
s=s.replace(old,new,1)
app.write_text(s,encoding='utf-8')

s=admin_lib.read_text(encoding='utf-8')
old='import { currentUser } from "./auth";'
new='import { auditEvent, currentUser } from "./auth";'
if old not in s: raise SystemExit('admin auth import marker missing')
s=s.replace(old,new,1)
old='  deletedMessages += await deleteConversationMessages(conversationId);\n  return { deletedMessages };'
new='  deletedMessages += await deleteConversationMessages(conversationId);\n  void auditEvent("admin_conversation_deleted", conversationId);\n  return { deletedMessages };'
if old not in s: raise SystemExit('conversation delete marker missing')
s=s.replace(old,new,1)
admin_lib.write_text(s,encoding='utf-8')
print('ADMIN_PARITY_PATCHED')
