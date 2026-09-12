import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.argv[2] || 'source');

function file(rel) { return path.join(root, rel); }
function read(rel) { return fs.readFileSync(file(rel), 'utf8'); }
function write(rel, text) { fs.writeFileSync(file(rel), text, 'utf8'); }
function replaceExact(rel, before, after) {
  const source = read(rel);
  if (!source.includes(before)) throw new Error(`Contratto non trovato in ${rel}: ${before.slice(0, 100)}`);
  const count = source.split(before).length - 1;
  if (count !== 1) throw new Error(`Contratto ambiguo in ${rel}: ${count} occorrenze`);
  write(rel, source.replace(before, after));
}
function replaceRegex(rel, regex, replacement, label) {
  const source = read(rel);
  let count = 0;
  const next = source.replace(regex, (...args) => { count += 1; return typeof replacement === 'function' ? replacement(...args) : replacement; });
  if (count !== 1) throw new Error(`${label || rel}: attesa 1 sostituzione, trovate ${count}`);
  write(rel, next);
}

// 1) Header: usa il logo WebP corretto gia' pubblicato su R2.
replaceExact(
  'frontend-react/src/components/Layout.tsx',
  'const LOGO = "https://img.calabriavera.com/static/assets/Logo.png";',
  'const LOGO = "https://img.calabriavera.com/static/assets/Logo.webp";'
);
replaceExact(
  'frontend-react/src/components/Layout.tsx',
  '    const page = exactMainPage(cleanPath) || (cleanPath.startsWith("/admin/") ? `admin-${cleanPath.split("/").filter(Boolean).at(-1)}` : cleanPath.replace(/^\\//, "") || "app");',
  '    const page = cleanPath.startsWith("/attivita/") ? "business" : (exactMainPage(cleanPath) || (cleanPath.startsWith("/admin/") ? `admin-${cleanPath.split("/").filter(Boolean).at(-1)}` : cleanPath.replace(/^\\//, "") || "app"));'
);
replaceRegex(
  'frontend-react/index.html',
  /href=["']\/assets\/Logo\.webp["']/,
  'href="https://img.calabriavera.com/static/assets/Logo.webp"',
  'preload logo React'
);

// 2) URL canonici delle attivita': elimina eventuale suffisso data legacy.
replaceExact(
  'frontend-react/src/lib/businesses.ts',
`export function businessPath(item: Business) {
  if (String(item.id || "").startsWith("turismo-")) {
    return \`/attivita?turismo=\${encodeURIComponent(String(item.slug || item.id))}\`;
  }
  return \`/attivita/\${slugify(item.provincia || "calabria")}/\${slugify(item.comune || "calabria")}/\${slugify(specificCategory(item))}/\${encodeURIComponent(String(item.slug || slugify(item.name) || item.id))}\`;
}`,
`export function businessPath(item: Business) {
  if (String(item.id || "").startsWith("turismo-")) {
    return \`/attivita?turismo=\${encodeURIComponent(String(item.slug || item.id))}\`;
  }
  const rawSlug = slugify(item.slug || item.name || item.id);
  const cleanSlug = rawSlug.replace(/-?\\d{4}-\\d{2}-\\d{2}$/, "").replace(/-+$/, "") || slugify(item.name || item.id);
  return \`/attivita/\${slugify(item.provincia || "calabria")}/\${slugify(item.comune || "calabria")}/\${slugify(specificCategory(item))}/\${encodeURIComponent(cleanSlug)}\`;
}`
);

// 3) Letture Firestore Messaggi: carica solo le attivita' effettivamente referenziate.
const businessesRel = 'frontend-react/src/lib/businesses.ts';
let businesses = read(businessesRel);
const featuredMarker = '\nexport async function loadFeaturedBusinesses(max = 6) {';
if (!businesses.includes(featuredMarker)) throw new Error('Marker loadFeaturedBusinesses non trovato');
if (!businesses.includes('export async function loadBusinessesByIds(')) {
  businesses = businesses.replace(featuredMarker, `
export async function loadBusinessesByIds(ids: string[], max = 50) {
  const unique = [...new Set(ids.map((value) => String(value || "").trim()).filter(Boolean))].slice(0, Math.max(0, max));
  if (!unique.length) return [] as Business[];
  const { db, firestore: f } = await services();
  const snapshots = await Promise.all(unique.map((id) => f.getDoc(f.doc(db, "businesses", id)).catch(() => null)));
  return snapshots.flatMap((snapshot) => snapshot?.exists() ? [toBusiness(snapshot)] : []);
}
${featuredMarker}`);
  write(businessesRel, businesses);
}

replaceExact(
  'frontend-react/src/pages/MessagesPage.tsx',
  'import { businessPath, loadAllBusinesses, timeValue } from "../lib/businesses";',
  'import { businessPath, loadBusinessesByIds, timeValue } from "../lib/businesses";'
);
replaceExact(
  'frontend-react/src/pages/MessagesPage.tsx',
  '  getConversationPreferences, getPublicProfile, getQuickReplies, hideConversation, listConversations,',
  '  getConversationPreferences, getPublicProfile, getQuickReplies, hideConversation,'
);
replaceRegex(
  'frontend-react/src/pages/MessagesPage.tsx',
  /        const \[rows,allBusinesses\]=await Promise\.all\(\[listConversations\(\),loadAllBusinesses\(\)\.catch\(\(\)=>\[\]\)\]\);[\s\S]*?        const requested=new URLSearchParams\(location\.search\)\.get\("conversation"\)\|\|""; setSelectedId\(requested&&nextRows\.some\(\(row\)=>row\.id===requested\)\?requested:nextRows\[0\]\?\.id\|\|""\);/,
`        const params=new URLSearchParams(location.search); const businessId=params.get("business")||"", ownerId=params.get("owner")||"";
        if(businessId&&ownerId&&ownerId!==user.uid){const started=await startBusinessConversation(businessId,ownerId);if(!active)return;setSelectedId(started.id);history.replaceState({},"",withLanguage(\`/messaggi?conversation=\${encodeURIComponent(started.id)}\`,language));}`,
  'inizializzazione Messaggi quota-safe'
);
replaceExact(
  'frontend-react/src/pages/MessagesPage.tsx',
  '  useEffect(()=>{if(!userId)return;let alive=true,stop:(()=>void)|undefined;void watchConversations((rows)=>{if(!alive)return;setConversations(rows);setSelectedId((current)=>current&&rows.some((row)=>row.id===current)?current:rows[0]?.id||"");},()=>{if(alive)setError(c(copy,"loadError"));}).then((u)=>{if(alive)stop=u;else u();}).catch(()=>{if(alive)setError(c(copy,"loadError"));});return()=>{alive=false;stop?.()};},[userId,language]);',
  '  useEffect(()=>{if(!userId)return;let alive=true,stop:(()=>void)|undefined;void watchConversations((rows)=>{if(!alive)return;setConversations(rows);const requested=new URLSearchParams(location.search).get("conversation")||"";setSelectedId((current)=>{const preferred=current||requested;return preferred&&rows.some((row)=>row.id===preferred)?preferred:rows[0]?.id||"";});},()=>{if(alive)setError(c(copy,"loadError"));}).then((u)=>{if(alive)stop=u;else u();}).catch(()=>{if(alive)setError(c(copy,"loadError"));});return()=>{alive=false;stop?.()};},[userId,language]);'
);
const profileEffect = '  useEffect(()=>{if(!userId||!conversations?.length)return;let active=true;const ids=[...new Set(conversations.map((row)=>peerId(row,userId)).filter(Boolean))];void Promise.all(ids.map(async(id)=>[id,await getPublicProfile(id)] as const)).then((pairs)=>{if(active)setProfiles((current)=>({...current,...Object.fromEntries(pairs)}));});return()=>{active=false};},[conversations,userId]);';
const businessEffect = `  useEffect(()=>{if(!conversations?.length){setBusinesses({});return;}let active=true;const ids=[...new Set(conversations.map((row)=>String(row.businessId||"")).filter(Boolean))].filter((id)=>!businesses[id]);if(!ids.length)return;void loadBusinessesByIds(ids).then((rows)=>{if(!active)return;setBusinesses((current)=>({...current,...Object.fromEntries(rows.map((business)=>[business.id,business]))}));}).catch(()=>undefined);return()=>{active=false};},[conversations,businesses]);\n\n`;
let messages = read('frontend-react/src/pages/MessagesPage.tsx');
if (!messages.includes(businessEffect.trim())) {
  if (!messages.includes(profileEffect)) throw new Error('Marker profili Messaggi non trovato');
  messages = messages.replace(profileEffect, businessEffect + profileEffect);
  write('frontend-react/src/pages/MessagesPage.tsx', messages);
}

// 4) Fallback Magazine: immagini statiche da R2, non dal bundle locale.
replaceExact(
  'frontend-react/src/pages/MagazinePage.tsx',
  'const DEFAULT_IMAGES = { events: "/assets/images/blog-default-events.png", news: "/assets/images/blog-default-news.png" } as const;',
  'const DEFAULT_IMAGES = { events: "https://img.calabriavera.com/static/assets/images/blog-default-events.png", news: "https://img.calabriavera.com/static/assets/images/blog-default-news.png" } as const;'
);
replaceExact(
  'frontend-react/src/lib/magazine.ts',
`export function magazineCover(post: BlogPost) {
  const fallback = \`\${PROD}/assets/images/blog-default-\${magazineLane(post) === "events" ? "events" : "news"}.png\`;
  const external = ["external", "social"].includes(String(post.origin || "")) || Boolean(post.externalUrl);
  if (!external && !revoked(post)) return String(post.coverUrl || fallback);
  return licensedCover(post) ? String(post.coverUrl || fallback) : fallback;
}`,
`export function magazineCover(post: BlogPost) {
  const fallback = \`https://img.calabriavera.com/static/assets/images/blog-default-\${magazineLane(post) === "events" ? "events" : "news"}.png\`;
  const explicit = String(post.coverUrl || "");
  const cover = /\\/assets\\/images\\/blog-default-(?:events|news)\\.png(?:$|[?#])/.test(explicit) ? fallback : explicit;
  const external = ["external", "social"].includes(String(post.origin || "")) || Boolean(post.externalUrl);
  if (!external && !revoked(post)) return cover || fallback;
  return licensedCover(post) ? (cover || fallback) : fallback;
}`
);

// 5) Worker: redirect slug datato, canonical server-side e fallback immagini business legacy.
const workerRel = 'frontend-react/worker.ts';
let worker = read(workerRel);
const canonicalTargetMarker = '  const target = CANONICAL_REDIRECTS.get(path);';
if (!worker.includes('const cleanedBusinessSlug = rawBusinessSlug.replace')) {
  if (!worker.includes(canonicalTargetMarker)) throw new Error('Marker canonicalRedirect Worker non trovato');
  worker = worker.replace(canonicalTargetMarker, `  if (path.startsWith("/attivita/")) {
    const parts = path.split("/");
    const rawBusinessSlug = decodeURIComponent(parts.at(-1) || "");
    const cleanedBusinessSlug = rawBusinessSlug.replace(/-?\\d{4}-\\d{2}-\\d{2}$/, "").replace(/-+$/, "");
    if (cleanedBusinessSlug && cleanedBusinessSlug !== rawBusinessSlug) {
      parts[parts.length - 1] = encodeURIComponent(cleanedBusinessSlug);
      return \`\${prefix}\${parts.join("/")}\${url.search}\`;
    }
  }
  ${canonicalTargetMarker.trim()}`);
}
const robotsMarker = 'function rewriteRobots(html: string, url: URL) {';
if (!worker.includes('function rewriteCanonical(html: string, url: URL)')) {
  if (!worker.includes(robotsMarker)) throw new Error('Marker rewriteRobots non trovato');
  worker = worker.replace(robotsMarker, `function rewriteCanonical(html: string, url: URL) {
  const pathname = normalizeRoutePath(url.pathname);
  const keepTourism = cleanPath(url.pathname) === "/attivita" && url.searchParams.has("turismo");
  const suffix = keepTourism ? \`?turismo=\${encodeURIComponent(url.searchParams.get("turismo") || "")}\` : "";
  const canonical = \`https://calabriavera.com\${pathname === "/" ? "" : pathname}\${suffix}\`;
  let next = html.replace(/<link\\s+rel=["']canonical["'][^>]*>/gi, "");
  next = next.replace("</head>", \`<link rel="canonical" href="\${canonical}" /></head>\`);
  if (/<meta\\s+property=["']og:url["']/i.test(next)) next = next.replace(/<meta\\s+property=["']og:url["']\\s+content=["'][^"']*["']\\s*\\/?\\s*>/i, \`<meta property="og:url" content="\${canonical}" />\`);
  return next;
}

${robotsMarker}`);
}
const localizeMarker = '  rawHtml = localizeFirstPaint(rawHtml, url);\n  const parityLinks = mainParityLinks(path);';
if (!worker.includes('rawHtml = rewriteCanonical(rawHtml, url);')) {
  if (!worker.includes(localizeMarker)) throw new Error('Marker first paint Worker non trovato');
  worker = worker.replace(localizeMarker, '  rawHtml = localizeFirstPaint(rawHtml, url);\n  rawHtml = rewriteCanonical(rawHtml, url);\n  const parityLinks = mainParityLinks(path);');
}
const staticMarker = '      const staticAsset = LEGACY_STATIC.get(url.pathname);';
if (!worker.includes('url.pathname.startsWith("/assets/images/businesses/")')) {
  if (!worker.includes(staticMarker)) throw new Error('Marker asset Worker non trovato');
  worker = worker.replace(staticMarker, '      if (url.pathname.startsWith("/assets/images/businesses/")) return proxy(request, url.pathname, "image/avif,image/webp,image/*,*/*;q=0.8", 86400);\n      const staticAsset = LEGACY_STATIC.get(url.pathname);');
}
write(workerRel, worker);

// Contratti finali essenziali.
const checks = [
  ['frontend-react/src/components/Layout.tsx', 'static/assets/Logo.webp'],
  ['frontend-react/src/components/Layout.tsx', 'cleanPath.startsWith("/attivita/") ? "business"'],
  ['frontend-react/src/lib/businesses.ts', 'loadBusinessesByIds'],
  ['frontend-react/src/pages/MessagesPage.tsx', 'loadBusinessesByIds'],
  ['frontend-react/src/lib/magazine.ts', 'img.calabriavera.com/static/assets/images/blog-default-'],
  ['frontend-react/worker.ts', 'rewriteCanonical'],
  ['frontend-react/worker.ts', '/assets/images/businesses/'],
];
for (const [rel, token] of checks) if (!read(rel).includes(token)) throw new Error(`Check finale fallito: ${rel} -> ${token}`);
console.log('Patch produzione applicata: logo, SEO/canonical, CSS business, immagini R2, legacy image fallback, Messaggi quota-safe.');
