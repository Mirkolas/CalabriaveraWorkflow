from pathlib import Path

root = Path('source')

# Build exact legal/info content from the main-branch HTML files into a TypeScript module.
p = root / 'frontend-react/scripts/copy-legacy-assets.mjs'
s = p.read_text(encoding='utf-8')
if 'legal-content.ts' not in s:
    s += r'''

const legalModuleTarget = resolve(generatedDir, "legal-content.ts");
const legalKindByFile = {
  "privacy-policy.html": "privacy",
  "cookie-policy.html": "cookie",
  "termini.html": "terms",
  "note-legali.html": "legal",
  "chi-siamo.html": "about",
  "contatti.html": "contacts",
};
const legalPayload = {};
for (const [name, kind] of Object.entries(legalKindByFile)) {
  const raw = readFileSync(resolve(repoRoot, name), "utf8");
  const mainMatch = raw.match(/<main\b[^>]*>([\s\S]*?)<\/main>/i);
  const titleMatch = raw.match(/<title>([\s\S]*?)<\/title>/i);
  const descriptionMatch = raw.match(/<meta\s+name=["']description["']\s+content=["']([^"']*)["']/i);
  let html = mainMatch?.[1] || "";
  html = html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, "");
  html = html.replace(/href=(['"])(\/[^'"?#]*?)\.html([?#][^'"]*)?\1/gi, (_m, quote, route, suffix = "") => `href=${quote}${route}${suffix}${quote}`);
  legalPayload[kind] = {
    html,
    title: (titleMatch?.[1] || "").replace(/\s+/g, " ").trim(),
    description: (descriptionMatch?.[1] || "").trim(),
  };
}
writeFileSync(legalModuleTarget, `export const LEGAL_CONTENT = ${JSON.stringify(legalPayload, null, 2)} as const;\n`, "utf8");
console.log(`Contenuti legali TypeScript generati: ${legalModuleTarget}`);
'''
p.write_text(s, encoding='utf-8')

# Render bundled legal content synchronously. No runtime /legacy fetch, no loader, no 404.
p = root / 'frontend-react/src/pages/LegalPage.tsx'
p.write_text(r'''import { useEffect } from "react";
import { LEGAL_CONTENT } from "../generated/legal-content";
import { setPageSeo } from "../lib/seo";

type Kind = keyof typeof LEGAL_CONTENT;

export default function LegalPage({ kind }: { kind: Kind }) {
  const page = LEGAL_CONTENT[kind];
  useEffect(() => {
    setPageSeo({
      title: page.title || "CalabriaVera",
      description: page.description || "CalabriaVera",
      path: location.pathname,
      robots: "index,follow",
    });
  }, [kind, page.title, page.description]);
  return <div className="cv-legacy-content" dangerouslySetInnerHTML={{ __html: page.html }} />;
}
''', encoding='utf-8')

# Public data: retry Firestore briefly before declaring it unavailable, and never emit a 404
# for a JSON API endpoint. A 200/empty response lets the client attempt its direct SDK fallback.
p = root / 'frontend-react/worker.ts'
s = p.read_text(encoding='utf-8')
old = '''    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        structuredQuery: {
          select: { fields: fields.map((fieldPath) => ({ fieldPath })) },
          from: [{ collectionId }],
          where: { fieldFilter: { field: { fieldPath: "status" }, op: "EQUAL", value: { stringValue: status } } },
          limit: 1000,
        },
      }),
    });
    if (!response.ok) return null;
    const wire = await response.json() as Array<{ document?: { name?: string; fields?: Record<string, Record<string, unknown>> } }>;'''
new = '''    const body = JSON.stringify({
      structuredQuery: {
        select: { fields: fields.map((fieldPath) => ({ fieldPath })) },
        from: [{ collectionId }],
        where: { fieldFilter: { field: { fieldPath: "status" }, op: "EQUAL", value: { stringValue: status } } },
        limit: 1000,
      },
    });
    let response: Response | null = null;
    for (let attempt = 0; attempt < 4; attempt += 1) {
      response = await fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body });
      if (response.ok) break;
      if (![429, 500, 502, 503, 504].includes(response.status)) return null;
      if (attempt < 3) await new Promise((resolve) => setTimeout(resolve, 180 * (attempt + 1)));
    }
    if (!response?.ok) return null;
    const wire = await response.json() as Array<{ document?: { name?: string; fields?: Record<string, Record<string, unknown>> } }>;'''
if old not in s:
    if 'for (let attempt = 0; attempt < 4; attempt += 1)' not in s:
        raise SystemExit('Worker Firestore fetch marker missing')
else:
    s = s.replace(old, new, 1)
old2 = '''async function publicDatasetResponse(request: Request, targetPath: string) {
  const payload = await readDataset(targetPath);
  if (!payload) return proxy(request, targetPath, "application/json", 60);'''
new2 = '''async function publicDatasetResponse(request: Request, targetPath: string) {
  const payload = await readDataset(targetPath) || { version: 2, generatedAt: new Date().toISOString(), items: [] };'''
if old2 in s:
    s = s.replace(old2, new2, 1)
elif 'readDataset(targetPath) || { version: 2' not in s:
    raise SystemExit('publicDatasetResponse marker missing')
p.write_text(s, encoding='utf-8')

# Client public-data loader: an empty worker response is not authoritative; retry the direct
# Firestore SDK with small backoff so transient throttling does not collapse the catalog to tourism only.
p = root / 'frontend-react/src/lib/public-data.ts'
s = p.read_text(encoding='utf-8')
helper = r'''
async function retry<T>(task: () => Promise<T>, attempts = 4) {
  let last: unknown;
  for (let index = 0; index < attempts; index += 1) {
    try { return await task(); }
    catch (error) {
      last = error;
      if (index + 1 < attempts) await new Promise((resolve) => setTimeout(resolve, 220 * (index + 1)));
    }
  }
  throw last;
}
'''
if 'async function retry<T>' not in s:
    s = s.replace('async function fetchDataset<T>(url: string): Promise<T[]> {', helper + '\nasync function fetchDataset<T>(url: string): Promise<T[]> {', 1)
old = '''      try {
        publicRows = await fetchDataset<Business>("/legacy-data/public-businesses-v1.json");
      } catch {
        const { loadAllBusinesses } = await import("./businesses");
        publicRows = await loadAllBusinesses(force);
      }'''
new = '''      try { publicRows = await fetchDataset<Business>("/legacy-data/public-businesses-v1.json"); }
      catch { publicRows = []; }
      if (!publicRows.length) {
        const { loadAllBusinesses } = await import("./businesses");
        try { publicRows = await retry(() => loadAllBusinesses(true)); } catch { publicRows = []; }
      }'''
if old in s:
    s = s.replace(old, new, 1)
elif 'try { publicRows = await retry(() => loadAllBusinesses(true)); }' not in s:
    raise SystemExit('business data fallback marker missing')
old = '''      try { return await fetchDataset<BlogPost>("/legacy-data/public-blog-v1.json"); }
      catch {
        const { loadMagazine } = await import("./magazine");
        return loadMagazine(force);
      }'''
new = '''      let rows: BlogPost[] = [];
      try { rows = await fetchDataset<BlogPost>("/legacy-data/public-blog-v1.json"); } catch { rows = []; }
      if (rows.length) return rows;
      const { loadMagazine } = await import("./magazine");
      try { return await retry(() => loadMagazine(true)); } catch { return []; }'''
if old in s:
    s = s.replace(old, new, 1)
elif 'return await retry(() => loadMagazine(true))' not in s:
    raise SystemExit('blog data fallback marker missing')
p.write_text(s, encoding='utf-8')

# Match the exact main home hero image and reference dimensions.
p = root / 'frontend-react/src/styles.css'
s = p.read_text(encoding='utf-8')
if 'cv-exact-main-home-hero' not in s:
    s += r'''

/* cv-exact-main-home-hero */
.cv-home-hero{min-height:438px!important;background:url('https://images.unsplash.com/photo-1533105079780-92b9be482077?auto=format&fit=crop&w=2000&q=90') center 46%/cover no-repeat!important}
.cv-home-hero__shade{background:linear-gradient(90deg,rgba(3,47,80,.86) 0%,rgba(3,47,80,.48) 43%,rgba(3,47,80,.04) 78%),linear-gradient(180deg,rgba(3,47,80,.08),rgba(3,47,80,.2))!important}
.cv-home-hero__content{padding:35px 0 58px!important}.cv-home-hero__mark{width:355px!important;max-height:126px!important;margin:0 0 6px!important}.cv-home-hero h1{font-size:clamp(2.1rem,3.55vw,3.65rem)!important;line-height:1.02!important;max-width:760px!important}.cv-home-hero p{font-size:1.12rem!important;max-width:610px!important}
@media(max-width:850px){.cv-home-hero{min-height:520px!important;background-position:62% center!important}.cv-home-hero__mark{width:270px!important}}
'''
p.write_text(s, encoding='utf-8')

# Tiny public copy mismatch measured by the parity gate.
p = root / 'frontend-react/src/pages/AuthPage.tsx'
s = p.read_text(encoding='utf-8').replace('loginHero: "Bentornato."', 'loginHero: "Bentornato"', 1)
p.write_text(s, encoding='utf-8')

print('Runtime, legal bundle, public-data retries and hero parity applied')
