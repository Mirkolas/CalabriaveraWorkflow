import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)(process.env.PLAYWRIGHT_MODULE);

const DATA={
  businesses:[
    {id:'b1',name:'Borgo Test',comune:'Scilla',provincia:'Reggio Calabria',category:'Ristoranti',status:'pending',email:'borgo@example.test',ownerId:'u1',description:'Descrizione attività completa per il test amministrativo CalabriaVera.',verified:false,views:12,phoneClicks:2,whatsappClicks:1,websiteClicks:3,favoriteCount:4,requestCount:2,slug:'borgo-test',updatedAt:'2026-09-10T10:00:00Z'},
    {id:'b2',name:'Mare Test',comune:'Tropea',provincia:'Vibo Valentia',category:'B&B',status:'approved',email:'mare@example.test',ownerId:'u2',description:'Seconda descrizione sufficientemente lunga per i controlli SEO amministrativi del portale.',verified:true,views:20,phoneClicks:5,whatsappClicks:2,websiteClicks:7,favoriteCount:8,requestCount:3,slug:'mare-test',updatedAt:'2026-09-11T11:00:00Z'}
  ],
  users:[
    {id:'admin-1',displayName:'Admin CalabriaVera',email:'admin@example.test',role:'ADMIN',status:'active',marketingConsent:false},
    {id:'u1',displayName:'Mario Rossi',email:'mario@example.test',role:'USER',status:'active',marketingConsent:true}
  ],
  reviews:[{id:'r1',businessId:'b1',rating:5,title:'Ottimo',text:'Recensione di prova',status:'pending',reviewerName:'Mario Rossi',createdAt:'2026-09-09T09:00:00Z'}],
  reports:[{id:'rep1',status:'open',reason:'Dati errati',businessId:'b1',createdAt:'2026-09-08T08:00:00Z'}],
  blogPosts:[{id:'p1',title:'Articolo prova',slug:'articolo-prova',category:'Territorio',status:'published',origin:'editorial',excerpt:'Estratto prova',publishedAt:'2026-09-07T07:00:00Z'}],
  magazineSources:[{id:'s1',name:'Fonte prova',feedUrl:'https://example.test/feed.xml',homepageUrl:'https://example.test',category:'Magazine',province:'Calabria',enabled:true,lastItemsCreated:1,lastItemsDuplicates:0,lastSuccessAt:'2026-09-11T06:00:00Z'}],
  categories:[{id:'ristoranti',name:'Ristoranti',active:true}],
  municipalities:[{id:'scilla',name:'Scilla',province:'Reggio Calabria',active:true}],
  conversations:[{id:'c1',businessId:'b1',participantIds:['u1','admin-1'],lastMessage:'Buongiorno',updatedAt:'2026-09-11T12:00:00Z'}],
  messages:[{id:'m1',conversationId:'c1',senderId:'u1',text:'Buongiorno',status:'sent',createdAt:'2026-09-11T12:00:00Z'}],
  campaigns:[{id:'crm_b1',kind:'crm_state',businessId:'b1',stage:'contacted',privateNotes:'Richiamare',followUpAt:'2026-09-20T10:00:00Z'}],
  adminOutreach:[{id:'o1',kind:'service_offer',businessId:'b1',businessName:'Borgo Test',recipientEmail:'borgo@example.test',status:'sent',requestedAt:'2026-09-10T10:00:00Z',sentAt:'2026-09-10T10:01:00Z'}],
  adminActions:[],_mailDeliveries:[],emailEvents:[],auditLogs:[],adminAudit:[],magazineSyncRuns:[],socialPublishRuns:[],adminSystemAlerts:[],
  settings:[{id:'site',siteName:'CalabriaVera',contactEmail:'info@example.test',footerText:'Il portale delle attività e dei servizi della Calabria.',maintenance:false}]
};
const json=JSON.stringify(DATA).replace(/</g,'\\u003c');
const authStub=`const user={uid:'admin-1',email:'admin@example.test',getIdTokenResult:async()=>({claims:{admin:true}})};export async function getCurrentUser(){return user}export async function currentUser(){return user}export function watchAuth(cb){let live=true;queueMicrotask(()=>{if(live)cb(user)});return()=>{live=false}}export async function requireUser(){return user}export {user as __testUser};`;
const utilsStub=`export const CATEGORIES=[];export const COMMON_CITIES=[];export const categoryGroup=v=>v;export const escapeHtml=v=>String(v??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;');export const slugify=v=>String(v??'').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase().replace(/&/g,' e ').replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');export const fmtDate=v=>{const d=new Date(v?.seconds?Number(v.seconds)*1000:v||0);return Number.isNaN(d.getTime())?'—':new Intl.DateTimeFormat('it-IT',{dateStyle:'medium',timeStyle:'short'}).format(d)};export const businessPath=x=>'/attivita?id='+encodeURIComponent(x?.id||'');`;
const firestoreStub=`const D=${json};const rows=n=>(D[n]||[]).map(x=>({...x}));export async function listPendingBusinesses(){return rows('businesses').filter(x=>x.status==='pending')}export async function listBusinessesAdmin(){return rows('businesses')}export async function setBusinessStatus(){}export async function setBusinessVerified(){}export async function deleteBusiness(){}export async function listReviewsAdmin(status='pending'){return rows('reviews').filter(x=>!status||x.status===status)}export async function setReviewStatus(){}export async function listBlogAdmin(){return rows('blogPosts')}export async function listDocs(name){return rows(name)}export async function saveDoc(_n,_d,id){return id||'new'}export async function deleteDocById(){};`;
const componentsStub=`export function shell(){}export function toast(){}export function icon(){return ''}`;
const i18nStub=`export function applyStatic(){}export function currentLang(){return 'it'}export function t(k){return k}`;
const conversationDeleteStub=`export async function deleteConversationPermanently(){return {deletedMessages:1}}`;
const remoteFirestore=`const D=${json};const rows=n=>(D[n]||[]).map(x=>({...x}));const nameOf=r=>r?.name||String(r?.path||'').split('/')[0]||'';export const collection=(_db,...p)=>({kind:'collection',path:p.join('/'),name:p[0]||''});export const doc=(a,...p)=>p.length?({kind:'doc',path:p.join('/'),name:p[0]||a?.name||'',id:p[p.length-1]}):({kind:'doc',path:(a?.path||'')+'/new',name:a?.name||'',id:'new'});export const where=(field,op,value)=>({type:'where',field,op,value});export const orderBy=(field,dir='asc')=>({type:'orderBy',field,dir});export const limit=n=>({type:'limit',n});export const query=(ref,...constraints)=>({...ref,constraints});export async function getDocs(ref){let a=rows(nameOf(ref));for(const c of ref?.constraints||[]){if(c.type==='where'&&c.op==='==')a=a.filter(x=>x[c.field]===c.value);if(c.type==='limit')a=a.slice(0,c.n)}const docs=a.map(x=>({id:x.id,ref:{name:nameOf(ref),id:x.id,path:nameOf(ref)+'/'+x.id},data:()=>({...x})}));return{docs,empty:!docs.length,size:docs.length}}export async function getDoc(ref){const x=rows(nameOf(ref)).find(v=>v.id===ref?.id);return{exists:()=>!!x,data:()=>x?({...x}):undefined,id:ref?.id,ref}}export async function setDoc(){}export async function updateDoc(){}export async function deleteDoc(){}export async function addDoc(){return{id:'new'}}export const serverTimestamp=()=> '2026-09-12T12:00:00Z';export const deleteField=()=>null;export const increment=n=>n;export const arrayUnion=(...v)=>v;export const arrayRemove=(...v)=>v;export const writeBatch=()=>({delete(){},set(){},update(){},commit:async()=>{}});export const onSnapshot=(_r,cb)=>{queueMicrotask(async()=>cb(await getDocs(_r)));return()=>{}};`;

async function installMocks(context){
  const js=(route,body)=>route.fulfill({status:200,contentType:'text/javascript; charset=utf-8',body});
  await context.route('**/assets/js/auth.js*',r=>js(r,authStub));
  await context.route('**/assets/js/firestore.js*',r=>js(r,firestoreStub));
  await context.route('**/assets/js/utils.js*',r=>js(r,utilsStub));
  await context.route('**/assets/js/components.js*',r=>js(r,componentsStub));
  await context.route('**/assets/js/i18n.js*',r=>js(r,i18nStub));
  await context.route('**/assets/js/firebase-init.js*',r=>js(r,'export const db={}; export const auth={};'));
  await context.route('**/assets/js/admin-conversation-delete.js*',r=>js(r,conversationDeleteStub));
  for(const f of ['maintenance.js','city-counts.js','full-i18n.js','runtime-idle.js','redesign-interactions.js']) await context.route(`**/assets/js/${f}*`,r=>js(r,f==='maintenance.js'?"document.documentElement.classList.remove('cv-maintenance-pending');export{}":"export{}"));
  await context.route('https://www.gstatic.com/firebasejs/12.4.0/firebase-firestore.js*',r=>js(r,remoteFirestore));
}
function clean(html){return String(html||'').replace(/\s+/g,' ').replace(/>\s+</g,'><').trim()}
async function open(browser,origin,path){
  const c=await browser.newContext({viewport:{width:1365,height:900},serviceWorkers:'block'});await installMocks(c);const p=await c.newPage();const errors=[];p.on('pageerror',e=>errors.push(String(e.message||e)));await p.goto(origin+path,{waitUntil:'domcontentloaded',timeout:30000});await p.locator('#admin-root').waitFor({state:'attached',timeout:15000});await p.waitForFunction(()=>{const r=document.querySelector('#admin-root');if(!r)return false;const t=r.textContent||'';return r.querySelector('.admin-layout')&&!/Caricamento (?:area amministrativa aggiornata|amministrazione|centro di controllo|Attività & CRM|comunicazioni|messaggi)/i.test(t)},null,{timeout:15000}).catch(()=>{});await p.waitForTimeout(700);return{c,p,errors};
}
const routes=[
 ['index','/pages/admin/index.html','/admin'],['attivita','/pages/admin/attivita.html','/admin/attivita'],['recensioni','/pages/admin/recensioni.html','/admin/recensioni'],['segnalazioni','/pages/admin/segnalazioni.html','/admin/segnalazioni'],['utenti','/pages/admin/utenti.html','/admin/utenti'],['comunicazioni','/pages/admin/comunicazioni.html','/admin/comunicazioni'],['messaggi','/pages/admin/messaggi.html','/admin/messaggi'],['blog','/pages/admin/blog.html','/admin/blog'],['categorie','/pages/admin/categorie.html','/admin/categorie'],['impostazioni','/pages/admin/impostazioni.html','/admin/impostazioni'],['seo','/pages/admin/seo.html','/admin/seo'],['sistema','/pages/admin/sistema.html','/admin/sistema']
];
const browser=await chromium.launch({headless:true});const failures=[];
for(const [name,legacyPath,reactPath] of routes){
 const L=await open(browser,'http://127.0.0.1:4190',legacyPath),R=await open(browser,'http://127.0.0.1:4191',reactPath);
 const a=await L.p.locator('#admin-root').evaluate(e=>e.innerHTML),b=await R.p.locator('#admin-root').evaluate(e=>e.innerHTML);
 const at=await L.p.locator('#admin-root').innerText(),bt=await R.p.locator('#admin-root').innerText();
 const menu=await R.p.locator('#admin-root aside a').allTextContents();
 const bad=[];if(clean(a)!==clean(b))bad.push('admin-root DOM mismatch');if(clean(at)!==clean(bt))bad.push('admin-root text mismatch');if(menu.join('|')!=='Centro controllo|Attività & CRM|Recensioni|Segnalazioni|Utenti|Comunicazioni|Messaggi|Blog|Categorie & Comuni')bad.push('final menu mismatch');if(R.errors.length)bad.push('react errors: '+R.errors.join('; '));console.log(`${name}: ${bad.length?bad.join(' | '):'OK'}`);if(bad.length)failures.push({name,bad,legacy:clean(a).slice(0,1500),react:clean(b).slice(0,1500)});await L.c.close();await R.c.close();
}
await browser.close();if(failures.length){console.error(JSON.stringify(failures,null,2));process.exit(1)}console.log('EXACT_FINAL_ADMIN_DOM_GREEN');
