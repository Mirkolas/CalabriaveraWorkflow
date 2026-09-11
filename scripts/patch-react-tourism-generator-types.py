from pathlib import Path
p = Path('source/frontend-react/scripts/copy-legacy-assets.mjs')
s = p.read_text(encoding='utf-8')
old = 'const tourismTs = `import type { Business } from "../types";\\n${tourismJs.replace("export const TOURISM_BUSINESSES = [", "export const TOURISM_BUSINESSES: Business[] = [")}`;'
new = '''const typedTourism = tourismJs\n  .replace("export const TOURISM_BUSINESSES = [", "export const TOURISM_BUSINESSES: Business[] = [")\n  .replace("export function tourismBusinessById(id)", "export function tourismBusinessById(id: string)")\n  .replace("export function tourismBusinessBySlug(slug)", "export function tourismBusinessBySlug(slug: string)");\nconst tourismTs = `import type { Business } from "../types";\\n${typedTourism}`;'''
if old not in s:
    raise SystemExit('tourism generator marker missing')
p.write_text(s.replace(old, new, 1), encoding='utf-8')
print('Tourism generator helper types added')
