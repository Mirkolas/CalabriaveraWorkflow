from pathlib import Path

p=Path('source/frontend-react/scripts/prerender-home.mjs')
s=p.read_text(encoding='utf-8')
old='''  let tourismRows = [];
  try {
    const modulePath = resolve(root, "src/generated/tourism-data-core.js");
    const tourismModule = await import(`${pathToFileURL(modulePath).href}?v=${Date.now()}`);
    tourismRows = Array.isArray(tourismModule.TOURISM_BUSINESSES) ? tourismModule.TOURISM_BUSINESSES : [];
  } catch (error) {
    console.warn("Tourism prerender fallback:", error instanceof Error ? error.message : error);
  }
'''
new='''  let tourismRows = [];
  try {
    const generatedPath = resolve(root, "src/generated/tourism-data-core.ts");
    const source = await readFile(generatedPath, "utf8");
    const marker = 'export const TOURISM_BUSINESSES: Business[] = ';
    const start = source.indexOf(marker);
    const endMarker = ';\\nexport function tourismBusinessById';
    const end = source.indexOf(endMarker, start + marker.length);
    if (start < 0 || end < 0) throw new Error("TOURISM_GENERATED_PAYLOAD_NOT_FOUND");
    const parsed = JSON.parse(source.slice(start + marker.length, end));
    if (!Array.isArray(parsed) || parsed.length !== 52) throw new Error(`TOURISM_GENERATED_COUNT_${Array.isArray(parsed) ? parsed.length : "INVALID"}`);
    tourismRows = parsed;
  } catch (error) {
    console.warn("Tourism prerender fallback:", error instanceof Error ? error.message : error);
  }
'''
if old not in s:
    raise SystemExit('prerender tourism import marker missing')
s=s.replace(old,new,1)
if 'tourism-data-core.js' in s:
    raise SystemExit('stale generated js reference remains')
p.write_text(s,encoding='utf-8')
print('PRERENDER_TOURISM_CANONICAL_PATCHED')
