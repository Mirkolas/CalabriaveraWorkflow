from pathlib import Path
p=Path('source/frontend-react/src/pages/AdminPage.tsx')
s=p.read_text(encoding='utf-8')
start=s.index('function BlogPanel(')
end=s.index('\nfunction PostEditor(', start)
replacement=r'''function BlogPanel({posts,sources,busy,action}:{posts:Row[];sources:Row[];busy:boolean;action:AdminAction}){
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
s=s[:start]+replacement+s[end:]
p.write_text(s,encoding='utf-8')
print('ADMIN_BLOG_JSX_SIMPLIFIED')
