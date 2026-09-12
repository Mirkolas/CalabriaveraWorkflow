from pathlib import Path

page = r'''import { useEffect, useMemo, useState } from "react";
import Link from "../components/Link";
import { languageFromPath, localizedField, uiText, withLanguage, type Language } from "../lib/language";
import { magazineCover, magazineLane, publicationMillis, type BlogPost } from "../lib/magazine";
import { loadPublicMagazineFast, readInlineMagazine } from "../lib/public-data";
import { setPageSeo } from "../lib/seo";

const LOCALES: Record<Language, string> = { it: "it-IT", en: "en-GB", fr: "fr-FR", de: "de-DE", es: "es-ES" };
const DEFAULT_IMAGES = { events: "/assets/images/blog-default-events.png", news: "/assets/images/blog-default-news.png" } as const;
const VISIBLE_PAGE_SIZE = 12;

function formatDate(post: BlogPost, language: Language) {
  const stamp = publicationMillis(post);
  return stamp ? new Intl.DateTimeFormat(LOCALES[language], { dateStyle: "medium", timeZone: "Europe/Rome" }).format(stamp) : "";
}

function safeHttpUrl(value: unknown) {
  try {
    const url = new URL(String(value || ""));
    return /^https?:$/.test(url.protocol) ? url.href : "";
  } catch { return ""; }
}

function laneLabel(lane: "events" | "news") {
  return lane === "events" ? "Eventi, turismo e borghi" : "Notizie";
}

export default function MagazinePage() {
  const language = languageFromPath();
  const [posts, setPosts] = useState<BlogPost[] | null>(() => {
    const inline = readInlineMagazine();
    return inline.length ? inline : null;
  });
  const [lane, setLane] = useState<"events" | "news">("events");
  const [visible, setVisible] = useState(VISIBLE_PAGE_SIZE);

  useEffect(() => {
    setPageSeo({ title: `${uiText("magazineTitle", language)} | CalabriaVera`, description: uiText("magazineSub", language), path: location.pathname });
    let active = true;
    loadPublicMagazineFast(true).then((items) => { if (active) setPosts(items); }).catch(() => { if (active && !readInlineMagazine().length) setPosts([]); });
    const refresh = () => void import("../lib/magazine").then(({ loadMagazine }) => loadMagazine(true)).then((fresh) => { if (active && fresh.length) setPosts(fresh); }).catch(() => undefined);
    const timer = window.setTimeout(refresh, 4500);
    return () => { active = false; window.clearTimeout(timer); };
  }, [language]);

  useEffect(() => {
    if (document.querySelector('link[data-cv-blog-sections]')) return;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/assets/css/blog-sections.css?v=20260905-2";
    link.dataset.cvBlogSections = "";
    document.head.appendChild(link);
  }, []);

  const filtered = useMemo(() => (posts || []).filter((post) => magazineLane(post) === lane).sort((a, b) => publicationMillis(b) - publicationMillis(a) || String(a.id || "").localeCompare(String(b.id || ""))), [posts, lane]);

  return (<>
    <section className="article-hero container">
      <p className="eyebrow">CalabriaVera · Blog &amp; Magazine</p>
      <h1>{uiText("magazineTitle",language)}</h1>
      <p className="prose">{uiText("magazineSub",language)}</p>
    </section>
    <section className="section container">
      <div id="blog-lane-tabs" className="cv-blog-tabs" role="tablist" aria-label="Sezioni Eventi e Blog">
        {(["events","news"] as const).map((value) => <button key={value} type="button" className={`cv-blog-tab${lane===value?" is-active":""}`} role="tab" data-blog-lane={value} aria-selected={lane===value} onClick={()=>{setLane(value);setVisible(VISIBLE_PAGE_SIZE)}}>{laneLabel(value)}</button>)}
      </div>
      {posts===null?<div className="notice">Caricamento contenuti…</div>:<>
        <div id="blog-list" className="card-grid" aria-live="polite">
          {filtered.length ? filtered.slice(0,visible).map((post,index)=>{
            const externalUrl=safeHttpUrl(post.externalUrl), isExternal=Boolean(externalUrl&&["external","social"].includes(String(post.origin||"")));
            const title=localizedField<string>(post,"title",language)||post.title||"";
            const excerpt=localizedField<string>(post,"excerpt",language)||post.excerpt||"";
            const href=isExternal?externalUrl:withLanguage(`/blog/${encodeURIComponent(String(post.slug||post.id))}`,language);
            const fallback=DEFAULT_IMAGES[magazineLane(post)];
            const licenseUrl=safeHttpUrl(post.licenseUrl), license=String(post.license||"").trim();
            const credit=externalUrl ? <p className="small muted">Fonte: {String(post.attribution||post.sourceName||"fonte esterna")}{license ? <> · {licenseUrl?<a href={licenseUrl} target="_blank" rel="noopener noreferrer">{license}</a>:license}</> : null}. Testo abbreviato.</p> : null;
            const textLink=isExternal?<a className="text-link" href={href} target="_blank" rel="noopener noreferrer nofollow">{uiText("readSource",language)}</a>:<Link className="text-link" href={href}>{uiText("readArticle",language)}</Link>;
            return <article key={post.id} className="blog-card"><div className="media-placeholder blog-media" style={{aspectRatio:"16/9"}}><img data-blog-cover data-blog-fallback={fallback} loading={index<2?"eager":"lazy"} decoding="async" fetchPriority={index<2?"high":"low"} referrerPolicy="no-referrer" src={magazineCover(post)} alt={title} onError={(event)=>{const img=event.currentTarget; if(img.src.endsWith(fallback)) return; img.removeAttribute("srcset"); img.src=fallback;}}/></div><div className="body"><p className="eyebrow">{post.category||"Blog"} · {formatDate(post,language)}</p><h3>{title}</h3><p>{excerpt}</p>{credit}{textLink}</div></article>;
          }) : <div className="notice">Nessun contenuto {laneLabel(lane)} disponibile.</div>}
        </div>
        <button id="blog-more" type="button" className="button button-secondary" style={{display:"block",margin:"2rem auto"}} hidden={visible>=filtered.length} onClick={()=>setVisible((value)=>value+VISIBLE_PAGE_SIZE)}>{uiText("loadMagazine",language)}</button>
      </>}
    </section>
  </>);
}
'''

Path('frontend-react/src/pages/MagazinePage.tsx').write_text(page)
