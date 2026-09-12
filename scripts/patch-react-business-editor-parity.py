from pathlib import Path
p=Path('source/frontend-react/src/pages/BusinessEditorPage.tsx')
s=p.read_text(encoding='utf-8')
# canonical city list and main form id
needle='import { CATEGORIES, PROVINCES, categoryGroup } from "../lib/businesses";'
if needle not in s: raise SystemExit('business import marker missing')
s=s.replace(needle, needle+'\nimport { MAIN_COMMON_CITIES } from "../generated/main-static-options";',1)
s=s.replace('document.getElementById("react-business-form")','document.getElementById("business-form")')
# truthful authorization contract
needle='    const data = new FormData(event.currentTarget);\n    const name = field(data.get("name")).trim();'
repl='    const data = new FormData(event.currentTarget);\n    if (data.get("truthful") !== "on") { setError("Dichiara che i dati sono corretti e che sei autorizzato a rappresentare questa attività."); return; }\n    const name = field(data.get("name")).trim();'
if needle not in s: raise SystemExit('submit marker missing')
s=s.replace(needle,repl,1)
start=s.index('  if (authorized === null || (editId && existing === undefined))')
end=s.rindex('\n}')
block=r'''  if (authorized === null || (editId && existing === undefined)) return <section className="section container"><div id="add-business-root"><div className="notice"><strong>CalabriaVera</strong><p>Verifica accesso…</p></div></div></section>;
  if (!authorized) return null;
  if (!emailVerified) return <section className="section container"><div id="add-business-root"><div className="notice"><h1>Verifica la tua email</h1><p>Prima di inserire o modificare un’attività, completa la verifica.</p><Link className="button button-primary" href="/profilo?next=%2Faggiungi-attivita">Verifica dal profilo</Link></div></div></section>;
  if (editId && existing === null) return <section className="section container"><div id="add-business-root"><div className="notice"><strong>Attività non disponibile.</strong><p>La scheda non esiste o non appartiene al tuo account.</p><Link className="button button-secondary" href="/dashboard">Torna alla dashboard</Link></div></div></section>;

  const needsType = types.length > 1 || (types.length === 1 && types[0] !== group);
  return <section className="section container"><div id="add-business-root">
    <div className="section-heading form-intro"><div><p className="eyebrow">Per le imprese locali</p><h1>{editId?"Modifica attività":"Aggiungi la tua attività"}</h1><p className="prose muted">{editId?"Aggiorna informazioni, servizi e immagini.":"Scegli prima la categoria generale e poi il tipo preciso di attività."}</p></div><div className="form-progress"><span>1 · Identità</span><span>2 · Posizione</span><span>3 · Servizi</span><span>4 · Contatti e foto</span></div></div>
    {error?<div className="notice" role="alert"><strong>{error}</strong></div>:null}
    <form id="business-form" className="business-form" onSubmit={submit} noValidate>
      <section className="card form-section"><div className="form-section-title"><span>1</span><div><h2>Informazioni principali</h2><p>La categoria serve a raggruppare; il tipo identifica esattamente l’attività.</p></div></div><div className="form-grid">
        <label>Nome attività <b>*</b><input name="name" required maxLength={160} autoComplete="organization" defaultValue={field(existing?.name)}/></label>
        <label>Categoria <b>*</b><select value={group} onChange={(event)=>onGroupChange(event.target.value)} required>{CATEGORIES.map((value)=><option key={value} value={value}>{value}</option>)}</select></label>
        <label id="business-type-wrap" hidden={!needsType}>Tipo di attività <b>*</b><select value={selectedType} onChange={(event)=>{setType(event.target.value);setServices([]);}} required={needsType}>{types.map((value)=><option key={value} value={value}>{value}</option>)}</select></label>
        <label className="full">Descrizione <b>*</b><textarea name="description" required minLength={40} maxLength={8000} defaultValue={field(existing?.description)}/></label>
      </div></section>

      <section className="card form-section"><div className="form-section-title"><span>2</span><div><h2>Indirizzo e posizione</h2><p>Cerca l’indirizzo e correggi il pin se necessario.</p></div></div><div className="address-map-layout"><div className="form-grid address-fields">
        <label>Provincia <b>*</b><select name="provincia" required defaultValue={field(existing?.provincia||PROVINCES[0])}>{PROVINCES.map((value)=><option key={value} value={value}>{value}</option>)}</select></label>
        <label>Comune <b>*</b><input name="comune" list="city-options" required autoComplete="address-level2" defaultValue={field(existing?.comune)}/><datalist id="city-options">{MAIN_COMMON_CITIES.map((value)=><option key={value} value={value}/>)}</datalist></label>
        <label>Via / Piazza <b>*</b><input name="street" required maxLength={200} autoComplete="street-address" defaultValue={field(existing?.street)||parsedAddress.street}/></label>
        <label>Numero civico <b>*</b><input name="streetNumber" required maxLength={20} defaultValue={field(existing?.streetNumber)||parsedAddress.streetNumber}/></label>
        <label>CAP <b>*</b><input name="cap" required inputMode="numeric" pattern="[0-9]{5}" maxLength={5} autoComplete="postal-code" defaultValue={field(existing?.cap)}/></label>
        <div className="address-check"><button type="button" className="button button-primary" onClick={()=>void geocode()}>Trova sulla mappa</button><p id="address-status" className="small muted" aria-live="polite">{coords?"Posizione salvata: controlla il pin.":"Completa l’indirizzo e premi “Trova sulla mappa”."}</p></div>
      </div><div className="address-map-panel"><BusinessLocationPicker value={coords} onChange={(next)=>{setCoords(next);setStatus("Posizione aggiornata manualmente.");}}/></div></div></section>

      <section className="card form-section"><div className="form-section-title"><span>3</span><div><h2>Servizi disponibili</h2><p>Le opzioni cambiano automaticamente in base al tipo selezionato.</p></div></div><div id="service-options" className="service-options">{availableServices.map((value)=><label key={value} className="service-option"><input type="checkbox" checked={services.includes(value)} onChange={(event)=>setServices((current)=>event.target.checked?[...new Set([...current,value])]:current.filter((item)=>item!==value))}/><span>{value}</span></label>)}</div></section>

      <section className="card form-section"><div className="form-section-title"><span>4</span><div><h2>Contatti e immagini</h2><p>Seleziona più foto insieme. La prima è la copertina; puoi riordinarle.</p></div></div><div className="form-grid">
        <label>Telefono <b>*</b><input name="phone" type="tel" required maxLength={40} autoComplete="tel" defaultValue={field(existing?.phone)}/></label>
        <label>WhatsApp<input name="whatsapp" type="tel" maxLength={40} defaultValue={field(existing?.whatsapp)}/></label>
        <label>Email pubblica<input name="email" type="email" maxLength={160} defaultValue={field(existing?.email)}/></label>
        <label>Sito web<input name="website" type="url" placeholder="https://" defaultValue={field(existing?.website)}/></label>
        <label>Prezzo indicativo da (€)<input type="number" min="0" step="0.01" name="priceMin" defaultValue={field(existing?.priceMin)}/></label>
        <label>Prezzo indicativo fino a (€)<input type="number" min="0" step="0.01" name="priceMax" defaultValue={field(existing?.priceMax)}/></label>
        <label className="full">Foto attività <span className="muted small business-image-help">JPG, PNG o WebP · massimo 10 · selezione multipla.</span><input id="business-images" type="file" accept="image/jpeg,image/png,image/webp" multiple disabled={imageBusy||images.length>=10} onChange={addImages}/></label>
        <div className="full"><div id="business-image-editor" className="business-image-editor" aria-live="polite">{images.length?images.map((image,index)=><div key={image.id||`${imageSource(image).slice(0,40)}-${index}`} className="business-image-card">{index===0?<span className="business-image-card__cover">Copertina</span>:null}{imageSource(image)?<img src={imageSource(image)} alt={`Foto ${index+1}`} loading={index?"lazy":"eager"}/>:null}<div className="business-image-card__actions">{index>0?<button type="button" className="button button-secondary" onClick={()=>makeCover(index)}>Usa come copertina</button>:null}<button type="button" className="button button-secondary" onClick={()=>moveImage(index,-1)} disabled={index===0}>←</button><button type="button" className="button button-secondary" onClick={()=>moveImage(index,1)} disabled={index===images.length-1}>→</button><button type="button" className="button button-secondary" onClick={()=>removeImage(index)}>Rimuovi</button></div></div>):<p className="muted">Nessuna foto caricata.</p>}</div></div>
      </div></section>

      <section className="card form-section form-confirm"><div className="cv-consent-row cv-business-consent"><input id="business-truthful" type="checkbox" name="truthful" required defaultChecked={Boolean(editId)}/><label htmlFor="business-truthful">Dichiaro che i dati sono corretti e che sono autorizzato a rappresentare questa attività. <b>*</b></label></div></section>
      <p className="form-status muted" id="business-status" role="status">{status}</p><div className="form-actions sticky-form-actions"><button id="business-submit" className="button button-primary" type="submit" disabled={busy||imageBusy}>{busy?"Salvataggio…":editId?"Salva modifiche":"Invia per approvazione"}</button>{editId?<Link className="button button-secondary" href="/dashboard">Annulla</Link>:null}</div>
    </form>
  </div></section>;'''
s=s[:start]+block+s[end:]
for marker in ['id="add-business-root"','id="business-form"','form-progress','business-truthful','required maxLength={20}','pattern="[0-9]{5}"','name="phone" type="tel" required','MAIN_COMMON_CITIES','card form-section','business-image-editor']:
    if marker not in s: raise SystemExit(f'missing {marker}')
if 'react-business-form' in s: raise SystemExit('old form id remains')
p.write_text(s,encoding='utf-8')
print('BUSINESS_EDITOR_PARITY_PATCHED')
