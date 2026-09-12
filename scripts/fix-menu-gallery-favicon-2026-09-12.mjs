import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.argv[2] || 'source');
const p = (rel) => path.join(root, rel);
const read = (rel) => fs.readFileSync(p(rel), 'utf8');
const write = (rel, text) => fs.writeFileSync(p(rel), text, 'utf8');

function mustReplace(rel, before, after) {
  let source = read(rel);
  if (source.includes(after)) return;
  if (!source.includes(before)) throw new Error(`${rel}: blocco atteso non trovato`);
  source = source.replace(before, after);
  write(rel, source);
}

// 1) Header React con la stessa struttura DOM dell'header originale.
{
  const rel = 'frontend-react/src/components/Layout.tsx';
  let source = read(rel);
  source = source.replace(
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 12a4.25 4.25 0 1 0 0-8.5 4.25 4.25 0 0 0 0 8.5Zm0 2c-4.55 0-8 2.48-8 5.1 0 .77.63 1.4 1.4 1.4h13.2c.77 0 1.4-.63 1.4-1.4C20 16.48 16.55 14 12 14Z" /></svg>',
    '<svg className="cv-account-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 12a4.25 4.25 0 1 0 0-8.5 4.25 4.25 0 0 0 0 8.5Zm0 2c-4.55 0-8 2.48-8 5.1 0 .77.63 1.4 1.4 1.4h13.2c.77 0 1.4-.63 1.4-1.4C20 16.48 16.55 14 12 14Z" /></svg>'
  );
  source = source.replace(
    '{nav.map(([label, href, key]) => <Link key={key} href={href} className={isActive(key) ? "is-active" : ""} aria-current={isActive(key) ? "page" : undefined}>{label}</Link>)}',
    '{nav.map(([label, href, key]) => <Link key={key} href={href} data-cv-nav={key} className={isActive(key) ? "is-active" : ""} aria-current={isActive(key) ? "page" : undefined}>{label}</Link>)}'
  );

  const oldMobile = `{menuOpen ? <nav id="mobile-nav" className="container primary-mobile" aria-label="Navigazione mobile">\n          {nav.map(([label, href, key]) => <Link key={key} href={href} className={isActive(key) ? "is-active" : ""}>{label}</Link>)}\n          {authReady ? user ? <><Link href={withLanguage("/profilo", language)}>{uiText("profile", language)}</Link><Link href={withLanguage("/dashboard", language)}>{uiText("dashboard", language)}</Link><Link href={withLanguage("/messaggi", language)}>{uiText("messages", language)}</Link><Link href={withLanguage("/preferiti", language)}>{uiText("favorites", language)}</Link><Link href={withLanguage("/aggiungi-attivita", language)}>{uiText("addBusiness", language)}</Link>{admin ? <Link href={withLanguage("/admin", language)}>Admin</Link> : null}<button type="button" onClick={() => void signOut()}>{uiText("logout", language)}</button></> : <><Link href={withLanguage("/login", language)}>{uiText("login", language)}</Link><Link href={withLanguage("/registrazione", language)}>{uiText("register", language)}</Link></> : null}\n        </nav> : null}`;
  const newMobile = `<nav id="mobile-nav" className="container primary-mobile" aria-label="Navigazione mobile" hidden={!menuOpen}>\n          {nav.map(([label, href, key]) => <Link key={key} href={href} data-cv-nav={key} className={isActive(key) ? "is-active" : ""} aria-current={isActive(key) ? "page" : undefined}>{label}</Link>)}\n          {!authReady ? <AuthPlaceholder /> : user ? <details className="account-menu"><summary className="cv-account-trigger" aria-label={uiText("account", language)} title={uiText("account", language)}><AccountIcon /><span className="sr-only">Account</span></summary><div className="account-links"><Link href={withLanguage("/profilo", language)}>{uiText("profile", language)}</Link><Link href={withLanguage("/dashboard", language)}>{uiText("dashboard", language)}</Link><Link href={withLanguage("/messaggi", language)}>{uiText("messages", language)}</Link><Link href={withLanguage("/preferiti", language)}>{uiText("favorites", language)}</Link><Link href={withLanguage("/aggiungi-attivita", language)}>{uiText("addBusiness", language)}</Link>{admin ? <Link href={withLanguage("/admin", language)}>Admin</Link> : null}<button type="button" onClick={() => void signOut()}>{uiText("logout", language)}</button></div></details> : <div className="guest-actions"><Link href={withLanguage("/login", language)} className="button button-secondary cv-account-login">{uiText("login", language)}</Link><Link href={withLanguage("/registrazione", language)} className="button button-primary cv-account-register">{uiText("register", language)}</Link></div>}\n        </nav>`;
  if (!source.includes(newMobile)) {
    if (!source.includes(oldMobile)) throw new Error('Layout.tsx: menu mobile atteso non trovato');
    source = source.replace(oldMobile, newMobile);
  }
  write(rel, source);
}

// 2) Catalogo: se la scheda non ha cover top-level, usa la prima foto della galleria Firestore.
{
  const rel = 'frontend-react/src/components/LegacyCatalogCard.tsx';
  let source = read(rel);
  source = source.replace(
    'import { businessImageUrl, businessPath, isFavorite, specificCategory, toggleFavorite } from "../lib/businesses";',
    'import { businessImageUrl, businessPath, imageUrlFromGallery, isFavorite, loadBusinessImages, specificCategory, toggleFavorite } from "../lib/businesses";'
  );
  source = source.replace(
    '  const [favorite,setFavorite]=useState(false),[busy,setBusy]=useState(false);\n  useEffect(()=>{let alive=true;void isFavorite(business.id).then((value)=>{if(alive)setFavorite(value)}).catch(()=>undefined);return()=>{alive=false}},[business.id]);\n',
    '  const [favorite,setFavorite]=useState(false),[busy,setBusy]=useState(false),[galleryCover,setGalleryCover]=useState("");\n  useEffect(()=>{let alive=true;void isFavorite(business.id).then((value)=>{if(alive)setFavorite(value)}).catch(()=>undefined);return()=>{alive=false}},[business.id]);\n  const directImage=businessImageUrl(business);\n  useEffect(()=>{if(directImage){setGalleryCover("");return}let alive=true;void loadBusinessImages(business.id).then((rows)=>{if(!alive)return;setGalleryCover(rows.map(imageUrlFromGallery).find(Boolean)||"")}).catch(()=>{if(alive)setGalleryCover("")});return()=>{alive=false}},[business.id,directImage]);\n'
  );
  source = source.replace(
    '  const category=business.subcategory||business.category||specificCategory(business), image=businessImageUrl(business);',
    '  const category=business.subcategory||business.category||specificCategory(business), image=directImage||galleryCover;'
  );
  write(rel, source);
}

// 3) Anche le card React moderne usano lo stesso fallback, senza leggere la galleria se una cover esiste già.
{
  const rel = 'frontend-react/src/components/BusinessCard.tsx';
  let source = read(rel);
  source = source.replace(
    'import { businessImageUrl, businessPath, categoryGroup, specificCategory, isFavorite, toggleFavorite } from "../lib/businesses";',
    'import { businessImageUrl, businessPath, categoryGroup, imageUrlFromGallery, specificCategory, isFavorite, loadBusinessImages, toggleFavorite } from "../lib/businesses";'
  );
  source = source.replace(
    '  const image = businessImageUrl(business);\n  const name = localizedField<string>(business, "name", language) || business.name || labels.fallback;\n  const [favorite, setFavorite] = useState(false);\n',
    '  const directImage = businessImageUrl(business);\n  const [galleryCover, setGalleryCover] = useState("");\n  const image = directImage || galleryCover;\n  const name = localizedField<string>(business, "name", language) || business.name || labels.fallback;\n  const [favorite, setFavorite] = useState(false);\n'
  );
  const marker = '  useEffect(() => {\n    if (!showFavorite) return;\n';
  const galleryEffect = '  useEffect(() => {\n    if (directImage) { setGalleryCover(""); return; }\n    let active = true;\n    void loadBusinessImages(business.id).then((rows) => {\n      if (!active) return;\n      setGalleryCover(rows.map(imageUrlFromGallery).find(Boolean) || "");\n    }).catch(() => { if (active) setGalleryCover(""); });\n    return () => { active = false; };\n  }, [business.id, directImage]);\n\n';
  if (!source.includes(galleryEffect)) {
    if (!source.includes(marker)) throw new Error('BusinessCard.tsx: punto inserimento fallback non trovato');
    source = source.replace(marker, galleryEffect + marker);
  }
  write(rel, source);
}

// 4) Ripristina le dimensioni originali dell'header e impedisce al menu mobile di diventare un overlay gigante.
{
  const rel = 'frontend-react/src/styles.css';
  let source = read(rel);
  source = source.replace(/\n\/\* Shell invariants: impediscono logo\/header non stilizzati durante i cambi route\. \*\/[\s\S]*$/m, '');
  const css = `\n/* React shell: parità esatta con header-unified.css originale. */\n#site-header .cv-header .brand-logo{display:block!important;width:clamp(158px,13vw,188px)!important;max-width:188px!important;height:48px!important;object-fit:contain!important;object-position:left center!important}\n@media(min-width:1181px){#site-header .cv-header .primary-nav{display:flex!important}#site-header .cv-header .desktop-account{display:block!important}#site-header .cv-header .menu-button,#site-header .primary-mobile{display:none!important}}\n@media(max-width:1180px){#site-header .cv-header .brand-logo{width:168px!important;max-width:168px!important;height:44px!important}#site-header .cv-header .primary-nav,#site-header .cv-header .desktop-account{display:none!important}#site-header .cv-header .menu-button{display:inline-flex!important}#site-header .primary-mobile[hidden]{display:none!important}#site-header .primary-mobile:not([hidden]){position:static!important;inset:auto!important;transform:none!important;width:min(calc(100% - 32px),1480px)!important;max-width:1480px!important;height:auto!important;min-height:0!important;margin:0 auto!important;padding:10px 0 14px!important;display:grid!important;grid-template-columns:repeat(5,minmax(0,1fr))!important;gap:6px!important;max-height:calc(100dvh - 62px)!important;overflow-y:auto!important;border-top:1px solid rgba(255,255,255,.12)!important;background:#00345b!important;box-shadow:none!important}#site-header .primary-mobile>a{min-height:46px!important;display:flex!important;align-items:center!important;justify-content:center!important;padding:9px 10px!important;border-radius:10px!important;color:#fff!important;background:rgba(255,255,255,.055)!important;text-align:center!important;font-size:13px!important;font-weight:750!important}#site-header .primary-mobile>.guest-actions,#site-header .primary-mobile>.account-menu{grid-column:1/-1!important;width:100%!important}#site-header .primary-mobile>.guest-actions{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:8px!important}#site-header .primary-mobile>.account-menu>.cv-account-trigger{width:100%!important;min-height:46px!important;height:auto!important;display:flex!important;gap:8px!important;border-radius:10px!important}#site-header .primary-mobile .account-links{position:static!important;inset:auto!important;width:100%!important;margin-top:6px!important;padding:6px!important;display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:6px!important;background:#073f69!important;border:1px solid rgba(255,255,255,.12)!important;border-radius:12px!important;box-shadow:none!important}#site-header .primary-mobile .account-links>a,#site-header .primary-mobile .account-links>button{min-height:44px!important;display:flex!important;align-items:center!important;justify-content:center!important;padding:8px!important;color:#fff!important;background:rgba(255,255,255,.055)!important;border:0!important;border-radius:9px!important;text-align:center!important}}\n@media(max-width:760px){#site-header .cv-header .brand-logo{width:145px!important;max-width:145px!important;height:42px!important}#site-header .primary-mobile:not([hidden]){grid-template-columns:repeat(2,minmax(0,1fr))!important;width:calc(100% - 24px)!important}#site-header .primary-mobile .account-links{grid-template-columns:repeat(2,minmax(0,1fr))!important}}\n@media(max-width:520px){#site-header .cv-header .brand-logo{width:132px!important;max-width:132px!important}#site-header .primary-mobile:not([hidden]){grid-template-columns:1fr!important;width:calc(100% - 18px)!important}#site-header .primary-mobile>.guest-actions,#site-header .primary-mobile .account-links{grid-template-columns:1fr!important}}\n@media(max-width:390px){#site-header .cv-header .brand-logo{width:124px!important;max-width:124px!important}}\n@media(max-width:330px){#site-header .cv-header .brand-logo{width:110px!important;max-width:110px!important}}\n`;
  if (!source.includes('React shell: parità esatta con header-unified.css originale.')) source += css;
  write(rel, source);
}

// 5) Favicon: usa il logo corrente e cambia URL per invalidare la cache aggressiva dei browser.
{
  const rel = 'frontend-react/index.html';
  let source = read(rel);
  source = source.replace(
    '<link rel="icon" type="image/png" sizes="96x96" href="https://img.calabriavera.com/static/assets/images/favicon-96.png" />',
    '<link rel="icon" type="image/png" href="/assets/Logo.png?v=20260912b" />\n    <link rel="shortcut icon" type="image/png" href="/assets/Logo.png?v=20260912b" />'
  );
  write(rel, source);
}

for (const [rel, token] of [
  ['frontend-react/src/components/Layout.tsx', 'hidden={!menuOpen}'],
  ['frontend-react/src/components/LegacyCatalogCard.tsx', 'galleryCover'],
  ['frontend-react/src/components/BusinessCard.tsx', 'loadBusinessImages'],
  ['frontend-react/src/styles.css', 'React shell: parità esatta con header-unified.css originale.'],
  ['frontend-react/index.html', 'Logo.png?v=20260912b'],
]) {
  if (!read(rel).includes(token)) throw new Error(`Check finale fallito: ${rel} -> ${token}`);
}
console.log('Patch pronta: menu originale, fallback foto galleria e favicon aggiornato.');
