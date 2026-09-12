from pathlib import Path

p=Path('frontend-react/src/pages/AdminPage.tsx')
p.write_text(r'''import { useEffect } from "react";
import { setPageSeo } from "../lib/seo";
import { stripLanguagePath } from "../lib/language";

function adminKind() {
  const parts=stripLanguagePath(location.pathname).split("/").filter(Boolean);
  return parts[0]==="admin" && parts[1] ? parts[1] : "index";
}

async function legacyModule(path: string): Promise<Record<string, unknown>> {
  return import(/* @vite-ignore */ path) as Promise<Record<string, unknown>>;
}

export default function AdminPage() {
  const kind=adminKind();
  useEffect(()=>{
    let cancelled=false;
    setPageSeo({title:"Amministrazione | CalabriaVera",description:"Area amministrativa CalabriaVera.",path:location.pathname,robots:"noindex,nofollow"});
    document.body.dataset.page=`admin-${kind}`;
    const boot=async()=>{
      try{
        const base=await legacyModule("/assets/js/admin.js");
        if(cancelled)return;
        const initAdmin=base.initAdmin;
        if(typeof initAdmin!=="function")throw new Error("LEGACY_ADMIN_INIT_MISSING");
        await (initAdmin as (kind:string)=>Promise<void>)(kind);
        if(cancelled)return;

        // Mirror the exact entrypoint order emitted by the final pre-React build.
        if(kind==="attivita" || kind==="messaggi") {
          await legacyModule("/assets/js/admin-critical-upgrades.js");
          if(cancelled)return;
        }
        if(kind==="messaggi") {
          await legacyModule("/assets/js/admin-conversation-delete-ui.js");
          if(cancelled)return;
        }
        if(kind==="utenti") {
          await legacyModule("/assets/js/admin-user-profile-ui.js");
          if(cancelled)return;
        }
        if(kind==="index") {
          await legacyModule("/assets/js/admin-maintenance-toggle.js");
          if(cancelled)return;
          await legacyModule("/assets/js/admin-automation-status.js");
          if(cancelled)return;
        }

        await legacyModule("/assets/js/admin-console.js");
        if(cancelled)return;
        await legacyModule("/assets/js/admin-upgrade.js");
      }catch(error){
        console.error(error);
        if(cancelled)return;
        const root=document.getElementById("admin-root");
        if(root)root.innerHTML='<div class="notice" role="alert"><strong>Errore di caricamento.</strong><p>Ricarica la pagina. Se il problema continua, contatta l’assistenza.</p></div>';
      }
    };
    void boot();
    return()=>{cancelled=true;};
  },[kind]);
  return <section className="section container"><div id="admin-root"><div className="notice" role="status">Caricamento amministrazione…</div></div></section>;
}
''')
print('React AdminPage delegated to exact final built legacy admin runtime with exact page entrypoint order')
