from pathlib import Path

root = Path('source')

# Extend the React build preparation step so the exact legacy information/legal HTML
# already versioned in the source branch is published as local assets.
p = root / 'frontend-react/scripts/copy-legacy-assets.mjs'
s = p.read_text(encoding='utf-8')
if 'legalFiles' not in s:
    s = s.replace(
        'import { copyFileSync, existsSync, mkdirSync } from "node:fs";',
        'import { copyFileSync, existsSync, mkdirSync } from "node:fs";'
    )
    s += '''\n\nconst legalDir = resolve(reactRoot, "public/legacy");\nmkdirSync(legalDir, { recursive: true });\nconst legalFiles = [\n  "privacy-policy.html",\n  "cookie-policy.html",\n  "termini.html",\n  "note-legali.html",\n  "contatti.html",\n  "chi-siamo.html",\n];\nfor (const name of legalFiles) {\n  const from = resolve(repoRoot, name);\n  if (!existsSync(from)) throw new Error(`Pagina legacy sorgente non trovata: ${from}`);\n  copyFileSync(from, resolve(legalDir, name));\n}\nconsole.log(`Pagine informative legacy copiate: ${legalFiles.length}`);\n'''
p.write_text(s, encoding='utf-8')

# Serve /legacy/*.html from the exact files bundled in Cloudflare Assets instead of
# relying on the historical Firebase Hosting origin.
p = root / 'frontend-react/worker.ts'
s = p.read_text(encoding='utf-8')
old = '''      if (url.pathname.startsWith("/legacy/")) {\n        const targetPath = `/${url.pathname.slice("/legacy/".length)}`;\n        if (!LEGACY_HTML.has(targetPath)) return new Response("Not Found", { status: 404 });\n        return proxy(request, targetPath, "text/html,application/xhtml+xml", 3600);\n      }'''
new = '''      if (url.pathname.startsWith("/legacy/")) {\n        const targetPath = `/${url.pathname.slice("/legacy/".length)}`;\n        if (!LEGACY_HTML.has(targetPath)) return new Response("Not Found", { status: 404 });\n        const local = await env.ASSETS.fetch(request);\n        if (!local.ok) return new Response("Not Found", { status: 404 });\n        const headers = new Headers(local.headers);\n        headers.set("Cache-Control", "public, max-age=300, s-maxage=3600, stale-while-revalidate=86400");\n        headers.set("X-Content-Type-Options", "nosniff");\n        return new Response(request.method === "HEAD" ? null : local.body, { status: local.status, headers });\n      }'''
if old not in s:
    if 'const local = await env.ASSETS.fetch(request);' not in s:
        raise SystemExit('legacy Worker marker missing')
else:
    s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

print('Local legal parity patch applied')
