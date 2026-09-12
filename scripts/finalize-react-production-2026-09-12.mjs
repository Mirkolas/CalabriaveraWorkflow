import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.argv[2] || 'source');
const p = (rel) => path.join(root, rel);
const read = (rel) => fs.readFileSync(p(rel), 'utf8');
const write = (rel, text) => fs.writeFileSync(p(rel), text, 'utf8');

function replaceOnce(rel, before, after) {
  const source = read(rel);
  if (source.includes(after)) return;
  const count = source.split(before).length - 1;
  if (count !== 1) throw new Error(`${rel}: attesa una occorrenza, trovate ${count}`);
  write(rel, source.replace(before, after));
}

// 1) Evita il flash di Suspense sulle route pubbliche principali.
{
  const rel = 'frontend-react/src/App.tsx';
  let source = read(rel);
  const imports = `import CatalogPage from "./pages/CatalogPage";\nimport MagazinePage from "./pages/MagazinePage";\nimport MapPage from "./pages/MapPage";\nimport BusinessPage from "./pages/BusinessPage";\nimport TourismPage from "./pages/TourismPage";\nimport BlogPostPage from "./pages/BlogPostPage";\nimport LegalPage from "./pages/LegalPage";\n`;
  if (!source.includes('import CatalogPage from "./pages/CatalogPage";')) {
    source = source.replace('import OriginalHomePage from "./pages/OriginalHomePage";\n', `import OriginalHomePage from "./pages/OriginalHomePage";\n${imports}`);
  }
  source = source.replace('const serverRendering = typeof window === "undefined";\n', '');
  for (const name of ['CatalogPage','MagazinePage','MapPage','BusinessPage','TourismPage','BlogPostPage','LegalPage']) {
    const pattern = new RegExp(`const ${name} = serverRendering \\? \\(await import\\("\\./pages\\/${name}\\"\\)\\)\\.default : lazy\\(\\(\\) => import\\("\\./pages\\/${name}\\"\\)\\);\\n`, 'g');
    source = source.replace(pattern, '');
  }
  write(rel, source);
}

// 2) Le immagini business nuove restano R2; quelle legacy puntano direttamente al vecchio hosting finché migrate.
{
  const rel = 'frontend-react/src/lib/businesses.ts';
  let source = read(rel);
  if (!source.includes('const LEGACY_IMAGE_ORIGIN = "https://calabriavera-e08d4.web.app";')) {
    source = source.replace('const PROD_ORIGIN = "https://calabriavera.com";\n', 'const PROD_ORIGIN = "https://calabriavera.com";\nconst LEGACY_IMAGE_ORIGIN = "https://calabriavera-e08d4.web.app";\n');
  }
  const oldFn = `export function businessImageUrl(item: Pick<Business, "imageKey" | "r2ImageKey" | "imageUrl" | "imageDataUrl">) {\n  const key = String(item.imageKey || item.r2ImageKey || "").replace(/^\\/+/, "");\n  if (key) return \`${'${IMAGE_CDN}'}\/${'${encodeURI(key)}'}\`;\n  const raw = String(item.imageUrl || item.imageDataUrl || "").trim();\n  if (!raw) return "";\n  if (/^(?:https?:|data:|blob:)/i.test(raw)) return raw;\n  return \`${'${PROD_ORIGIN}'}\/${'${raw.replace(/^\\/+/, "")}'}\`;\n}\n\nexport function imageUrlFromGallery(item: BusinessImage) {\n  const key = String(item.imageKey || item.r2ImageKey || "").replace(/^\\/+/, "");\n  if (key) return \`${'${IMAGE_CDN}'}\/${'${encodeURI(key)}'}\`;\n  const raw = String(item.imageUrl || item.imageDataUrl || "").trim();\n  if (!raw) return "";\n  if (/^(?:https?:|data:|blob:)/i.test(raw)) return raw;\n  return \`${'${PROD_ORIGIN}'}\/${'${raw.replace(/^\\/+/, "")}'}\`;\n}`;
  const newFn = `function resolvedLegacyImage(raw: string) {\n  const value = String(raw || "").trim();\n  if (!value) return "";\n  if (/^(?:data:|blob:)/i.test(value)) return value;\n  try {\n    const parsed = new URL(value, PROD_ORIGIN);\n    if (parsed.pathname.startsWith("/assets/images/businesses/") && (parsed.origin === PROD_ORIGIN || !/^https?:/i.test(value))) {\n      return \`${'${LEGACY_IMAGE_ORIGIN}'}${'${parsed.pathname}'}${'${parsed.search}'}\`;\n    }\n  } catch {}\n  if (/^https?:/i.test(value)) return value;\n  return \`${'${PROD_ORIGIN}'}\/${'${value.replace(/^\\/+/, "")}'}\`;\n}\n\nexport function businessImageUrl(item: Pick<Business, "imageKey" | "r2ImageKey" | "imageUrl" | "imageDataUrl">) {\n  const key = String(item.imageKey || item.r2ImageKey || "").replace(/^\\/+/, "");\n  if (key) return \`${'${IMAGE_CDN}'}\/${'${encodeURI(key)}'}\`;\n  return resolvedLegacyImage(String(item.imageUrl || item.imageDataUrl || ""));\n}\n\nexport function imageUrlFromGallery(item: BusinessImage) {\n  const key = String(item.imageKey || item.r2ImageKey || "").replace(/^\\/+/, "");\n  if (key) return \`${'${IMAGE_CDN}'}\/${'${encodeURI(key)}'}\`;\n  return resolvedLegacyImage(String(item.imageUrl || item.imageDataUrl || ""));\n}`;
  if (!source.includes('function resolvedLegacyImage(raw: string)')) {
    if (!source.includes(oldFn)) throw new Error('businesses.ts: blocco immagini atteso non trovato');
    source = source.replace(oldFn, newFn);
  }
  write(rel, source);
}

// 3) Protezione grafica anti-flash dell'header anche mentre cambia il CSS route-specifico.
{
  const rel = 'frontend-react/src/styles.css';
  let source = read(rel);
  const rule = `\n/* Shell invariants: impediscono logo/header non stilizzati durante i cambi route. */\n.site-header .brand-logo,.cv-header .brand-logo{display:block;width:132px!important;max-width:132px!important;height:48px!important;object-fit:contain!important;object-position:left center}\n@media(max-width:820px){.site-header .brand-logo,.cv-header .brand-logo{width:118px!important;max-width:118px!important;height:44px!important}}\n`;
  if (!source.includes('Shell invariants: impediscono logo/header')) source += rule;
  write(rel, source);
}

// 4) Firebase Hosting deve essere indicizzabile sulle pagine pubbliche; le pagine private impostano noindex via React.
replaceOnce(
  'frontend-react/index.html',
  '<meta name="robots" content="noindex,nofollow" />',
  '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />'
);

// 5) Redirect SEO esplicito per lo slug storico segnalato da Search Console.
{
  const rel = 'frontend-react/firebase.react.json';
  const json = JSON.parse(read(rel));
  const source = '/attivita/reggio-calabria/marina-di-gioiosa-ionica/b-e-b/le-ninfee-b-e-b2026-09-05';
  const destination = '/attivita/reggio-calabria/marina-di-gioiosa-ionica/b-e-b/le-ninfee-b-e-b';
  json.hosting.redirects ||= [];
  if (!json.hosting.redirects.some((r) => r.source === source)) {
    json.hosting.redirects.unshift({ source, destination, type: 301 });
  }
  write(rel, JSON.stringify(json, null, 2) + '\n');
}

const checks = [
  ['frontend-react/src/App.tsx', 'import CatalogPage from "./pages/CatalogPage";'],
  ['frontend-react/src/lib/businesses.ts', 'LEGACY_IMAGE_ORIGIN'],
  ['frontend-react/src/styles.css', 'Shell invariants: impediscono logo/header'],
  ['frontend-react/index.html', 'index,follow,max-image-preview:large'],
  ['frontend-react/firebase.react.json', 'le-ninfee-b-e-b2026-09-05'],
];
for (const [rel, token] of checks) if (!read(rel).includes(token)) throw new Error(`Check finale fallito: ${rel} -> ${token}`);
console.log('Fix finali applicati: route pubbliche senza Suspense, immagini business legacy, anti-flash header, SEO Firebase e redirect Le Ninfee.');
