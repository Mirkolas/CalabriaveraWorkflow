from pathlib import Path
import json
import re

ROOT = Path('source')
FRONT = ROOT / 'frontend-react'


def read(path):
    return path.read_text(encoding='utf-8')


def write(path, text):
    path.write_text(text, encoding='utf-8')

# 1) Static public datasets + SEO/static files copied into the React build.
copy_script = FRONT / 'scripts/copy-legacy-assets.mjs'
text = read(copy_script)
anchor = 'console.log(`Pagine legacy: ${legalFiles.length}; asset locali copiati: ${assetFiles.length}`);'
if 'legacyDataDir' not in text:
    block = r'''
const staticPublicFiles = [
  "assets/data/public-businesses-v1.json",
  "assets/data/public-blog-v1.json",
  "robots.txt",
  "sitemap.xml",
  "sitemap-pages.xml",
  "google881f83ee84963abe.html",
];
for (const relative of staticPublicFiles) {
  const source = resolve(repoRoot, relative);
  if (!existsSync(source)) continue;
  const target = resolve(reactRoot, "public", relative);
  mkdirSync(dirname(target), { recursive: true });
  copyFileSync(source, target);
}
const legacyDataDir = resolve(reactRoot, "public/legacy-data");
mkdirSync(legacyDataDir, { recursive: true });
for (const name of ["public-businesses-v1.json", "public-blog-v1.json"]) {
  const source = resolve(repoRoot, "assets/data", name);
  if (!existsSync(source)) throw new Error(`Snapshot pubblico mancante: ${source}`);
  copyFileSync(source, resolve(legacyDataDir, name));
}
'''
    if anchor not in text:
        raise SystemExit('copy script anchor missing')
    text = text.replace(anchor, block + '\n' + anchor)
write(copy_script, text)

# 2) Production static pages may be indexed. Worker staging still overwrites this to noindex.
index_path = FRONT / 'index.html'
text = read(index_path)
text = text.replace('<meta name="robots" content="noindex,nofollow" />', '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />')
write(index_path, text)

# 3) R2 upload remains on the Cloudflare Worker when the frontend is hosted by Firebase.
editor = FRONT / 'src/lib/business-editor.ts'
text = read(editor)
if 'R2_UPLOAD_WORKER' not in text:
    marker = 'async function uploadEditorImageToR2('
    insert = '''const R2_UPLOAD_WORKER = "https://calabriavera.sonotacamirko.workers.dev";\n\nfunction r2UploadEndpoint() {\n  if (typeof location !== "undefined" && location.hostname.endsWith(".workers.dev")) return "/api/images/upload";\n  return `${R2_UPLOAD_WORKER}/api/images/upload`;\n}\n\n'''
    if marker not in text:
        raise SystemExit('business editor marker missing')
    text = text.replace(marker, insert + marker, 1)
text = text.replace('fetch("/api/images/upload", {', 'fetch(r2UploadEndpoint(), {')
write(editor, text)

# 4) Allow the production origin to call the authenticated upload endpoint cross-origin.
worker = FRONT / 'worker.ts'
text = read(worker)
if 'UPLOAD_CORS_ORIGINS' not in text:
    marker = 'const IMAGE_CDN_ORIGIN = "https://img.calabriavera.com";'
    cors = '''const IMAGE_CDN_ORIGIN = "https://img.calabriavera.com";\nconst UPLOAD_CORS_ORIGINS = new Set(["https://calabriavera.com", "https://www.calabriavera.com"]);\n\nfunction uploadCorsHeaders(origin: string) {\n  const headers = new Headers();\n  if (UPLOAD_CORS_ORIGINS.has(origin)) {\n    headers.set("Access-Control-Allow-Origin", origin);\n    headers.set("Access-Control-Allow-Methods", "POST,OPTIONS");\n    headers.set("Access-Control-Allow-Headers", "Authorization,Content-Type,X-User-Id,X-Business-Id");\n    headers.set("Access-Control-Max-Age", "86400");\n    headers.set("Vary", "Origin");\n  }\n  return headers;\n}\n\nfunction withUploadCors(response: Response, origin: string) {\n  if (!UPLOAD_CORS_ORIGINS.has(origin)) return response;\n  const headers = new Headers(response.headers);\n  for (const [key, value] of uploadCorsHeaders(origin)) headers.set(key, value);\n  return new Response(response.body, { status: response.status, statusText: response.statusText, headers });\n}\n'''
    if marker not in text:
        raise SystemExit('worker image marker missing')
    text = text.replace(marker, cors, 1)
old = '    if (request.method === "POST" && url.pathname === "/api/images/upload") return uploadBusinessImage(request, env);\n'
new = '''    if (url.pathname === "/api/images/upload") {\n      const origin = request.headers.get("origin") || "";\n      if (request.method === "OPTIONS") {\n        if (!UPLOAD_CORS_ORIGINS.has(origin)) return new Response(null, { status: 403 });\n        return new Response(null, { status: 204, headers: uploadCorsHeaders(origin) });\n      }\n      if (request.method === "POST") return withUploadCors(await uploadBusinessImage(request, env), origin);\n    }\n'''
if old in text:
    text = text.replace(old, new, 1)
elif new.strip() not in text:
    raise SystemExit('worker upload dispatch anchor missing')
write(worker, text)

# 5) Make prerender independent from Firestore quotas and generate production-indexable public routes/details.
prerender = FRONT / 'scripts/prerender-home.mjs'
text = read(prerender)
if 'async function readStaticDataset' not in text:
    marker = 'const FIRESTORE_PROJECT_ID = "calabriavera-e08d4";'
    repl = marker + '''\nconst repoRoot = resolve(root, "..");\n\nasync function readStaticDataset(relativePath) {\n  try {\n    const payload = JSON.parse(await readFile(resolve(repoRoot, relativePath), "utf8"));\n    return Array.isArray(payload?.items) ? payload.items : [];\n  } catch {\n    return [];\n  }\n}\n'''
    text = text.replace(marker, repl, 1)
if 'function routeSlug(value)' not in text:
    marker = 'function safeJson(value) {'
    helper = '''function routeSlug(value) {\n  return String(value || "")\n    .normalize("NFD")\n    .replace(/[\\u0300-\\u036f]/g, "")\n    .toLowerCase()\n    .replace(/&/g, " e ")\n    .replace(/[^a-z0-9]+/g, "-")\n    .replace(/^-+|-+$/g, "");\n}\n\nfunction summaryText(value, fallback = "Scopri CalabriaVera.") {\n  const clean = String(value || "").replace(/<[^>]*>/g, " ").replace(/\\s+/g, " ").trim();\n  return (clean || fallback).slice(0, 180);\n}\n\n'''
    text = text.replace(marker, helper + marker, 1)
if 'function snapshotValueScript' not in text:
    marker = 'function withRoot(template, markup, page, scripts = "") {'
    helper = '''function snapshotValueScript(id, value) {\n  return `<script type="application/json" id="${id}">${safeJson(value)}</script>`;\n}\n\n'''
    text = text.replace(marker, helper + marker, 1)
# Ensure every prerendered public document is indexable even though app-shell remains a safe fallback.
needle = '  let html = template.replace(/<html\\s+lang=["\'][^"\']+["\']>/i, `<html lang="${page.lang}">`);'
if 'max-image-preview:large' not in text[text.find('function withRoot'):text.find('function outputPath')]:
    replacement = needle + '\n  html = html.replace(/<meta\\s+name=["\\\']robots["\\\']\\s+content=["\\\'][^"\\\']*["\\\']\\s*\\/?\\s*>/i, `<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />`);'
    if needle not in text:
        raise SystemExit('withRoot anchor missing')
    text = text.replace(needle, replacement, 1)
# Replace query block with static fallback.
old_query = '''  const [businessRows, blogRows] = await Promise.all([\n    queryCollection("businesses", "approved", BUSINESS_FIELDS),\n    queryCollection("blogPosts", "published", BLOG_FIELDS),\n  ]);\n  if (!businessRows.length) console.warn("Prerender businesses empty: runtime data loader will hydrate the page.");\n  if (!blogRows.length) console.warn("Prerender blog empty: runtime data loader will hydrate the page.");\n'''
new_query = '''  let [businessRows, blogRows] = await Promise.all([\n    queryCollection("businesses", "approved", BUSINESS_FIELDS),\n    queryCollection("blogPosts", "published", BLOG_FIELDS),\n  ]);\n  if (!businessRows.length) businessRows = await readStaticDataset("assets/data/public-businesses-v1.json");\n  if (!blogRows.length) blogRows = await readStaticDataset("assets/data/public-blog-v1.json");\n  if (!businessRows.length) console.warn("Prerender businesses empty: runtime data loader will hydrate the page.");\n  if (!blogRows.length) console.warn("Prerender blog empty: runtime data loader will hydrate the page.");\n'''
if old_query in text:
    text = text.replace(old_query, new_query, 1)
# Replace the language loop with a full static public route/detail prerender.
start = text.find('  for (const language of languages) {')
end = text.find('\n} finally {', start)
if start < 0 or end < 0:
    raise SystemExit('prerender language loop not found')
new_loop = r'''  let renderedPages = 0;
  const legalLabels = {
    "chi-siamo": "Chi siamo",
    contatti: "Contatti",
    "privacy-policy": "Privacy Policy",
    "cookie-policy": "Cookie Policy",
    termini: "Termini e condizioni",
    "note-legali": "Note legali",
  };
  for (const language of languages) {
    const pages = [
      { path: `${language.prefix}/` || "/", lang: language.lang, title: language.homeTitle, description: language.homeDescription, kind: "home" },
      { path: `${language.prefix}/catalogo` || "/catalogo", lang: language.lang, title: language.catalogTitle, description: language.catalogDescription, kind: "catalog" },
      { path: `${language.prefix}/mappa` || "/mappa", lang: language.lang, title: `Mappa attività | CalabriaVera`, description: language.catalogDescription, kind: "map" },
      { path: `${language.prefix}/blog` || "/blog", lang: language.lang, title: language.blogTitle, description: language.blogDescription, kind: "blog" },
      ...Object.entries(legalLabels).map(([route, label]) => ({ path: `${language.prefix}/${route}`, lang: language.lang, title: `${label} | CalabriaVera`, description: `CalabriaVera - ${label}.`, kind: "static" })),
    ];
    for (const page of pages) {
      const snapshot = page.kind === "catalog" || page.kind === "map" ? { businesses } : page.kind === "blog" ? { magazine } : {};
      const markup = await render(page.path, snapshot);
      const scripts = page.kind === "catalog" || page.kind === "map" ? snapshotScript("cv-react-businesses", businesses) : page.kind === "blog" ? snapshotScript("cv-react-magazine", magazine) : "";
      const html = withRoot(template, markup, page, scripts);
      const target = outputPath(page);
      await mkdir(dirname(target), { recursive: true });
      await writeFile(target, html, "utf8");
      renderedPages += 1;
      console.log(`Prerender ${page.kind}: ${page.path}`);
    }

    const businessPaths = new Set();
    for (const item of businesses) {
      const province = routeSlug(item.provincia || item.province);
      const city = routeSlug(item.comune || item.municipality);
      const category = routeSlug(item.subcategory || item.category || item.categoria || "altro");
      const slug = routeSlug(item.slug || item.name || item.id);
      if (!province || !city || !category || !slug) continue;
      const path = `${language.prefix}/attivita/${province}/${city}/${category}/${slug}`;
      if (businessPaths.has(path)) continue;
      businessPaths.add(path);
      const page = { path, lang: language.lang, title: `${String(item.name || "Attività")} | CalabriaVera`, description: summaryText(item.description, `Scopri ${String(item.name || "questa attività")} su CalabriaVera.`), kind: "business-detail" };
      const markup = await render(path, { businesses });
      const html = withRoot(template, markup, page, snapshotValueScript("cv-react-business", item));
      const target = outputPath(page);
      await mkdir(dirname(target), { recursive: true });
      await writeFile(target, html, "utf8");
      renderedPages += 1;
    }

    const postPaths = new Set();
    for (const post of magazine) {
      const slug = String(post.slug || post.id || "").trim();
      if (!slug) continue;
      const encoded = encodeURIComponent(slug);
      const path = `${language.prefix}/blog/${encoded}`;
      if (postPaths.has(path)) continue;
      postPaths.add(path);
      const page = { path, lang: language.lang, title: `${String(post.title || "Magazine")} | CalabriaVera`, description: summaryText(post.description || post.excerpt, language.blogDescription), kind: "post-detail" };
      const markup = await render(path, { magazine });
      const html = withRoot(template, markup, page, snapshotValueScript("cv-react-post", post));
      const target = outputPath(page);
      await mkdir(dirname(target), { recursive: true });
      await writeFile(target, html, "utf8");
      renderedPages += 1;
    }
  }
  console.log(`Prerender produzione completo: ${renderedPages} pagine pubbliche.`);
'''
text = text[:start] + new_loop + text[end:]
write(prerender, text)

# 6) Dedicated Firebase Hosting config for the React dist.
config = {
    "hosting": {
        "public": "dist",
        "cleanUrls": True,
        "trailingSlash": False,
        "ignore": ["firebase.react.json", "**/.*", "**/node_modules/**"],
        "redirects": [
            {"source": "/index.html", "destination": "/", "type": 301},
            {"source": "/catalogo.html", "destination": "/catalogo", "type": 301},
            {"source": "/mappa.html", "destination": "/mappa", "type": 301},
            {"source": "/blog.html", "destination": "/blog", "type": 301},
            {"source": "/login.html", "destination": "/login", "type": 301},
            {"source": "/registrazione.html", "destination": "/registrazione", "type": 301},
            {"source": "/profilo.html", "destination": "/profilo", "type": 301},
            {"source": "/preferiti.html", "destination": "/preferiti", "type": 301},
            {"source": "/dashboard.html", "destination": "/dashboard", "type": 301},
            {"source": "/messaggi.html", "destination": "/messaggi", "type": 301},
            {"source": "/aggiungi-attivita.html", "destination": "/aggiungi-attivita", "type": 301},
            {"source": "/privacy-policy.html", "destination": "/privacy-policy", "type": 301},
            {"source": "/cookie-policy.html", "destination": "/cookie-policy", "type": 301},
            {"source": "/termini.html", "destination": "/termini", "type": 301},
            {"source": "/note-legali.html", "destination": "/note-legali", "type": 301},
            {"source": "/contatti.html", "destination": "/contatti", "type": 301},
            {"source": "/chi-siamo.html", "destination": "/chi-siamo", "type": 301},
            {"source": "/cerca", "destination": "/catalogo", "type": 301},
        ],
        "rewrites": [{"source": "**", "destination": "/app-shell.html"}],
        "headers": [
            {"source": "/build-version.txt", "headers": [{"key": "Cache-Control", "value": "public,max-age=0,must-revalidate"}]},
            {"source": "**/*.html", "headers": [{"key": "Cache-Control", "value": "public,max-age=0,must-revalidate"}]},
            {"source": "/assets/**", "headers": [{"key": "Cache-Control", "value": "public,max-age=3600,stale-while-revalidate=86400"}]},
            {"source": "**", "headers": [
                {"key": "X-Content-Type-Options", "value": "nosniff"},
                {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"},
                {"key": "X-Frame-Options", "value": "SAMEORIGIN"},
                {"key": "Permissions-Policy", "value": "geolocation=(self),camera=(),microphone=()"},
                {"key": "Cross-Origin-Opener-Policy", "value": "same-origin-allow-popups"},
                {"key": "Strict-Transport-Security", "value": "max-age=31536000; includeSubDomains"},
                {"key": "Content-Security-Policy", "value": "base-uri 'self'; object-src 'none'; frame-ancestors 'self'; upgrade-insecure-requests"},
                {"key": "X-Permitted-Cross-Domain-Policies", "value": "none"},
            ]},
        ],
    }
}
write(FRONT / 'firebase.react.json', json.dumps(config, ensure_ascii=False, indent=2) + '\n')

# 7) Smoke script for Firebase Hosting emulator.
smoke = r'''const base = process.env.FIREBASE_HOSTING_EMULATOR_URL || "http://127.0.0.1:5000";
const expected = process.env.EXPECTED_SHA || "";
const paths = ["/", "/catalogo", "/mappa", "/blog", "/privacy-policy", "/login", "/legacy-data/public-businesses-v1.json", "/legacy-data/public-blog-v1.json", "/build-version.txt"];
for (const path of paths) {
  const response = await fetch(base + path, { redirect: "manual" });
  if (response.status !== 200) throw new Error(`${path}: HTTP ${response.status}`);
  const body = await response.text();
  if (!body.trim()) throw new Error(`${path}: empty response`);
  if (path === "/build-version.txt" && expected && body.trim() !== expected) throw new Error(`build version ${body.trim()} != ${expected}`);
  if (path === "/catalogo" && !body.includes("53 attività trovate")) throw new Error("catalog prerender total missing");
  if (path === "/mappa" && !body.includes("attività sulla mappa")) throw new Error("map prerender missing");
  if (path.endsWith("public-businesses-v1.json")) JSON.parse(body);
  if (path.endsWith("public-blog-v1.json")) JSON.parse(body);
}
console.log("FIREBASE_REACT_HOSTING_SMOKE_GREEN");
'''
write(FRONT / 'scripts/smoke-firebase-static.mjs', smoke)

# 8) Production workflow now deploys the React build to the already-connected Firebase Hosting domain.
workflow = ROOT / '.github/workflows/firebase-deploy.yml'
text = read(workflow)
admin_idx = text.find('\n  admin-maintenance:')
if admin_idx < 0:
    raise SystemExit('firebase deploy admin job anchor missing')
head = text[:text.find('jobs:')]
admin = text[admin_idx:]
deploy_job = r'''jobs:
  deploy:
    if: github.ref == 'refs/heads/main' && github.event_name != 'schedule' && (vars.FIREBASE_AUTO_DEPLOY_ENABLED == 'true' || github.event_name == 'workflow_dispatch')
    concurrency:
      group: firebase-production
      cancel-in-progress: false
    runs-on: ubuntu-latest
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-node@v7
        with:
          node-version: '24'
          cache: npm
          cache-dependency-path: frontend-react/package-lock.json
      - name: Build React production hosting
        working-directory: frontend-react
        env:
          GITHUB_SHA: ${{ github.sha }}
        run: |
          set -euo pipefail
          npm ci
          npm run build
          test "$(cat dist/build-version.txt)" = "$GITHUB_SHA"
          test -s dist/catalogo/index.html
          test -s dist/mappa/index.html
          test -s dist/blog/index.html
          test -s dist/legacy-data/public-businesses-v1.json
          test -s dist/legacy-data/public-blog-v1.json
          grep -q 'turismo-isola-dino' dist/catalogo/index.html
          grep -q 'index,follow,max-image-preview:large' dist/catalogo/index.html
      - uses: google-github-actions/auth@v3
        with:
          workload_identity_provider: ${{ vars.FIREBASE_WIF_PROVIDER }}
          service_account: ${{ vars.FIREBASE_DEPLOY_SERVICE_ACCOUNT }}
      - name: Deploy React Firebase Hosting
        working-directory: frontend-react
        run: npx --yes firebase-tools@15.22.1 deploy --project calabriavera-e08d4 --only hosting --config firebase.react.json --non-interactive
      - name: Verify exact production revision
        env:
          EXPECTED_SHA: ${{ github.sha }}
        shell: bash
        run: |
          set -euo pipefail
          for i in $(seq 1 30); do
            live="$(curl -fsS --max-time 15 https://calabriavera.com/build-version.txt 2>/dev/null || true)"
            if [ "$live" = "$EXPECTED_SHA" ]; then break; fi
            sleep 10
          done
          test "$(curl -fsS --max-time 20 https://calabriavera.com/build-version.txt)" = "$EXPECTED_SHA"
          curl -fsS --max-time 20 https://calabriavera.com/catalogo | grep -q '53 attività trovate'
          curl -fsS --max-time 20 https://calabriavera.com/mappa | grep -q 'attività sulla mappa'
          curl -fsSI --max-time 20 https://calabriavera.com/ | grep -qi 'x-content-type-options: nosniff'
          echo "FIREBASE_REACT_PRODUCTION_GREEN=$EXPECTED_SHA"
'''
write(workflow, head + deploy_job + admin)

# Sanity checks
for relative in [
    'frontend-react/firebase.react.json',
    'frontend-react/scripts/smoke-firebase-static.mjs',
    'frontend-react/src/lib/business-editor.ts',
    'frontend-react/worker.ts',
    '.github/workflows/firebase-deploy.yml',
]:
    if not (ROOT / relative).exists():
        raise SystemExit(f'missing {relative}')

print('PATCH_REACT_FIREBASE_PRODUCTION_OK')
