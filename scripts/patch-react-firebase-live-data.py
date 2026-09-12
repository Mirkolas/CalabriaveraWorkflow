from pathlib import Path

ROOT = Path('source/frontend-react')


def read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding='utf-8')

# Firebase production must use the Worker as the live public-data origin, with local static snapshots as fallback.
public_data = ROOT / 'src/lib/public-data.ts'
text = read(public_data)
if 'PUBLIC_DATA_WORKER_ORIGIN' not in text:
    anchor = 'async function fetchDataset<T>(url: string): Promise<T[]> {'
    start = text.find(anchor)
    end = text.find('\n}\n\nexport async function loadTourismBusinesses', start)
    if start < 0 or end < 0:
        raise SystemExit('public-data fetchDataset anchor missing')
    replacement = '''const PUBLIC_DATA_WORKER_ORIGIN = "https://calabriavera.sonotacamirko.workers.dev";\n\nasync function fetchDataset<T>(url: string): Promise<T[]> {\n  const remoteFirst = typeof location !== "undefined" && !location.hostname.endsWith(".workers.dev") && location.hostname !== "localhost" && location.hostname !== "127.0.0.1";\n  const candidates = remoteFirst ? [`${PUBLIC_DATA_WORKER_ORIGIN}${url}`, url] : [url];\n  let lastStatus = 0;\n  for (const candidate of candidates) {\n    try {\n      const response = await fetch(candidate, { cache: "default", headers: { Accept: "application/json" } });\n      lastStatus = response.status;\n      if (!response.ok) continue;\n      const payload = await response.json() as Dataset<T>;\n      if (Array.isArray(payload.items)) return payload.items;\n    } catch { /* try the static Firebase fallback */ }\n  }\n  throw new Error(`PUBLIC_DATA_${lastStatus || "NETWORK"}`);\n}\n'''
    text = text[:start] + replacement + text[end + 2:]
write(public_data, text)

# Worker public datasets should prefer live Firestore and expose safe public CORS; bundled snapshots remain resilience fallback.
worker = ROOT / 'worker.ts'
text = read(worker)
marker = 'async function readDataset(targetPath: string, env?: Env): Promise<Dataset | null> {\n  const cached = datasetMemory.get(targetPath);\n  if (cached && cached.expiresAt > Date.now()) return cached.value;\n'
if 'const live = await firestoreDataset(targetPath);' not in text:
    if marker not in text:
        raise SystemExit('worker readDataset anchor missing')
    text = text.replace(marker, marker + '  const live = await firestoreDataset(targetPath);\n  if (live) return live;\n', 1)
old_headers = '''    "X-Content-Type-Options": "nosniff",\n    "X-CalabriaVera-Data-Source": "snapshot-or-firestore",\n'''
new_headers = '''    "X-Content-Type-Options": "nosniff",\n    "Access-Control-Allow-Origin": "*",\n    "X-CalabriaVera-Data-Source": "firestore-or-snapshot",\n'''
if old_headers in text:
    text = text.replace(old_headers, new_headers, 1)
elif '"Access-Control-Allow-Origin": "*"' not in text:
    raise SystemExit('worker public dataset headers anchor missing')
write(worker, text)

# Pre-render every frozen public blog detail so Firebase production keeps SEO parity for the complete snapshot.
prerender = ROOT / 'scripts/prerender-home.mjs'
text = read(prerender)
if 'const magazine = blogRows.slice(0, 48);' in text:
    text = text.replace('const magazine = blogRows.slice(0, 48);', 'const magazine = blogRows;', 1)
elif 'const magazine = blogRows;' not in text:
    raise SystemExit('prerender magazine slice anchor missing')
write(prerender, text)

print('PATCH_REACT_FIREBASE_LIVE_DATA_OK')
