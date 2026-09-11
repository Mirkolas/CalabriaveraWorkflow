from pathlib import Path

p = Path('source/frontend-react/worker.ts')
s = p.read_text(encoding='utf-8')

s = s.replace('async function readDataset(targetPath: string): Promise<Dataset | null> {', 'async function readDataset(targetPath: string, env?: Env): Promise<Dataset | null> {', 1)
needle = '''  const cached = datasetMemory.get(targetPath);\n  if (cached && cached.expiresAt > Date.now()) return cached.value;\n  try {\n    const response = await fetch(`${LEGACY_ORIGIN}${targetPath}`, {'''
replacement = '''  const cached = datasetMemory.get(targetPath);\n  if (cached && cached.expiresAt > Date.now()) return cached.value;\n  if (env) {\n    try {\n      const localUrl = new URL(targetPath, "https://assets.calabriavera.local");\n      const local = await env.ASSETS.fetch(new Request(localUrl, { headers: { Accept: "application/json" } }));\n      if (local.ok) {\n        const payload = await local.json() as Dataset;\n        if (Array.isArray(payload.items)) {\n          datasetMemory.set(targetPath, { expiresAt: Date.now() + DATASET_TTL_MS, value: payload });\n          return payload;\n        }\n      }\n    } catch { /* try legacy snapshot and Firestore below */ }\n  }\n  try {\n    const response = await fetch(`${LEGACY_ORIGIN}${targetPath}`, {'''
if needle not in s:
    raise SystemExit('readDataset local insertion marker missing')
s = s.replace(needle, replacement, 1)

s = s.replace('async function publicDatasetResponse(request: Request, targetPath: string) {\n  const payload = await readDataset(targetPath)', 'async function publicDatasetResponse(request: Request, targetPath: string, env: Env) {\n  const payload = await readDataset(targetPath, env)', 1)
s = s.replace('needsBusinesses ? readDataset("/assets/data/public-businesses-v1.json") : Promise.resolve(null)', 'needsBusinesses ? readDataset("/assets/data/public-businesses-v1.json", env) : Promise.resolve(null)', 1)
s = s.replace('needsMagazine ? readDataset("/assets/data/public-blog-v1.json") : Promise.resolve(null)', 'needsMagazine ? readDataset("/assets/data/public-blog-v1.json", env) : Promise.resolve(null)', 1)
s = s.replace('if (dataPath) return publicDatasetResponse(request, dataPath);', 'if (dataPath) return publicDatasetResponse(request, dataPath, env);', 1)

p.write_text(s, encoding='utf-8')
print('Worker local public snapshot fallback applied')
