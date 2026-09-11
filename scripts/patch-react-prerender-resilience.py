from pathlib import Path

p = Path('source/frontend-react/scripts/prerender-home.mjs')
s = p.read_text(encoding='utf-8')
old = '  if (!response.ok) throw new Error(`PRERENDER_FIRESTORE_${collectionId}_${response.status}`);'
new = '''  if (!response.ok) {\n    console.warn(`Prerender Firestore fallback for ${collectionId}: HTTP ${response.status}`);\n    return [];\n  }'''
if old in s:
    s = s.replace(old, new, 1)
elif 'Prerender Firestore fallback for' not in s:
    raise SystemExit('Firestore response marker missing')
s = s.replace('  if (!businessRows.length) throw new Error("PRERENDER_BUSINESSES_EMPTY");', '  if (!businessRows.length) console.warn("Prerender businesses empty: runtime data loader will hydrate the page.");')
s = s.replace('  if (!blogRows.length) throw new Error("PRERENDER_BLOG_EMPTY");', '  if (!blogRows.length) console.warn("Prerender blog empty: runtime data loader will hydrate the page.");')
p.write_text(s, encoding='utf-8')
print('React prerender resilience patch applied')
