from pathlib import Path

p=Path('source/frontend-react/src/pages/AdminPage.tsx')
s=p.read_text(encoding='utf-8')

activities_start=s.index('function ActivitiesPanel(')
activities_end=s.index('\nfunction ReviewsPanel(', activities_start)
activities=r'''function ActivitiesPanel({items,busy,action}:{items:Business[];busy:boolean;action:AdminAction}){
  const [search,setSearch]=useState("");
  const filtered=useMemo(()=>{
    const q=search.toLowerCase().trim();
    return items.filter((item)=>!q||[item.name,item.comune,item.category,item.status].join(" ").toLowerCase().includes(q));
  },[items,search]);
  const cards=filtered.map((item)=><article className="card" key={item.id}>
    <div className="meta-row">
      <span>{item.category||""}</span><span>·</span><span>{item.comune||""}</span>
      <span className={`badge status-${item.status||""}`}>{item.status||""}</span>
      {item.verified?<span className="badge badge-verified">Verificata</span>:null}
    </div>
    <h3>{item.name||""}</h3><p>{item.description||""}</p>
    <div className="form-actions">
      <Link className="button button-secondary" href={`/attivita?id=${encodeURIComponent(item.id)}`}>Apri</Link>
      {item.status!=="approved"?<button disabled={busy} className="button button-primary" type="button" onClick={()=>{void action(()=>setBusinessStatus(item.id,"approved"));}}>Approva</button>:null}
      {item.status!=="rejected"?<button disabled={busy} className="button button-secondary" type="button" onClick={()=>{void action(()=>setBusinessStatus(item.id,"rejected"));}}>Rifiuta</button>:null}
      <button disabled={busy} className="button button-secondary" type="button" onClick={()=>{void action(()=>setBusinessVerified(item.id,!item.verified));}}>{item.verified?"Rimuovi verifica":"Verifica"}</button>
      <button disabled={busy} className="button button-secondary danger" type="button" onClick={()=>{if(window.confirm(`Eliminare “${item.name||"questa attività"}”?`)) void action(()=>deleteBusinessAdmin(item.id));}}>Elimina</button>
    </div>
  </article>);
  return <>
    <div className="section-heading"><div><p className="eyebrow">Moderazione</p><h2>Attività</h2></div><span className="badge">{items.length} totali</span></div>
    <label>Cerca attività<input id="admin-business-search" value={search} onChange={(event)=>setSearch(event.target.value)} placeholder="Nome, comune o categoria"/></label>
    <div id="admin-business-list" className="result-list">{cards.length?cards:<div className="notice">Nessuna attività trovata.</div>}</div>
  </>;
}'''
s=s[:activities_start]+activities+s[activities_end:]

blog_start=s.index('function BlogPanel(')
blog_end=s.index('\nfunction PostEditor(', blog_start)
blog=r'''function BlogPanel({posts,sources,busy,action}:{posts:Row[];sources:Row[];busy:boolean;action:AdminAction}){
  const [tab,setTab]=useState<"posts"|"sources">("posts");
  const [editingPost,setEditingPost]=useState<Row|null|undefined>(undefined);
  const [editingSource,setEditingSource]=useState<Row|null|undefined>(undefined);
  if(editingPost!==undefined) return <PostEditor post={editingPost} busy={busy} action={action} close={()=>setEditingPost(undefined)}/>;
  if(editingSource!==undefined) return <SourceEditor source={editingSource} busy={busy} action={action} close={()=>setEditingSource(undefined)}/>;
  const originals=posts.filter((row)=>row.origin!=="external").length;
  const imported=posts.filter((row)=>row.origin==="external").length;
  const published=posts.filter((row)=>row.status==="published").length;
  const postCards=posts.map((row)=>{
    const external=row.origin==="external" && Boolean(row.externalUrl);
    const viewHref=external?stringValue(row.externalUrl):`/blog/${encodeURIComponent(stringValue(row.slug))}`;
    return <article className="card" key={row.id}>
      <div className="meta-row"><span className="badge">{external?"Importato":"Editoriale"}</span><span>{stringValue(row.category)}</span><span>·</span><span>{stringValue(row.status)}</span>{external?<span>· {stringValue(row.sourceName||"Fonte esterna")}</span>:null}</div>
      <h3>{stringValue(row.title)}</h3><p>{stringValue(row.excerpt)}</p>
      <div className="form-actions">
        <button className="button button-secondary" type="button" onClick={()=>setEditingPost(row)}>Modifica</button>
        <button className="button button-secondary danger" type="button" onClick={()=>{if(window.confirm("Eliminare questo articolo?")) void action(()=>deleteCollectionDoc("blogPosts",row.id));}}>Elimina</button>
        {row.status==="published"?<a className="button button-secondary" href={viewHref} target="_blank" rel="noopener noreferrer">{external?"Apri fonte":"Visualizza"}</a>:null}
      </div>
    </article>;
  });
  return <>
    <div className="section-heading"><div><p className="eyebrow">Contenuti</p><h2>Blog &amp; Magazine</h2></div><button className="button button-primary" type="button" onClick={()=>setEditingPost(null)}>Nuovo articolo</button></div>
    <div className="tabs"><button type="button" className={`tab ${tab==="posts"?"active":""}`} onClick={()=>setTab("posts")}>Articoli</button><button type="button" className={`tab ${tab==="sources"?"active":""}`} onClick={()=>setTab("sources")}>Fonti automatiche</button></div>
    {tab==="posts"?<><div className="stat-grid"><div className="stat"><div>Totale</div><strong>{posts.length}</strong></div><div className="stat"><div>Editoriali</div><strong>{originals}</strong></div><div className="stat"><div>Importati</div><strong>{imported}</strong></div><div className="stat"><div>Pubblicati</div><strong>{published}</strong></div></div><div className="result-list">{postCards}</div></>:<SourcesList sources={sources} action={action} edit={setEditingSource}/>}
  </>;
}'''
s=s[:blog_start]+blog+s[blog_end:]

p.write_text(s,encoding='utf-8')
print('ADMIN_ACTIVITIES_AND_BLOG_JSX_SIMPLIFIED')
