from pathlib import Path

p = Path('frontend-react/src/pages/CatalogPage.tsx')
s = p.read_text()

s = s.replace(
    'import { CATEGORIES, PROVINCES, CATEGORY_GROUPS, categoryGroup, timeValue } from "../lib/businesses";',
    'import { CATEGORIES, PROVINCES, timeValue } from "../lib/businesses";',
    1,
)
s = s.replace(
    'import { languageFromPath, uiText, withLanguage } from "../lib/language";',
    'import { languageFromPath, localizedField, uiText, withLanguage, type Language } from "../lib/language";',
    1,
)
s = s.replace('type Sort = "newest" | "rating" | "oldest" | "name";', 'type Sort = "newest" | "rating" | "oldest";', 1)

old_category = '''function categoryMatches(item: Business, requested: string) {
  if (!requested) return true;
  const requestedGroup = categoryGroup(requested);
  const itemGroup = categoryGroup(item.category || item.subcategory);
  if (CATEGORIES.includes(requested)) return itemGroup === requestedGroup;
  const groupTypes = CATEGORY_GROUPS[requestedGroup] || [];
  if (groupTypes.includes(requested)) return String(item.category || item.subcategory) === requested || String(item.subcategory || "") === requested;
  return itemGroup === requestedGroup;
}

'''
if old_category not in s:
    raise SystemExit('catalog grouped category matcher not found')
s = s.replace(old_category, '', 1)

old_index = '''function indexed(item: Business) {
  const services = (item.services || []).map(normalizeText);
  return {
    name: normalizeText(item.name),
    category: normalizeText(item.category),
    subcategory: normalizeText(item.subcategory),
    comune: normalizeText(item.comune),
    services,
    haystack: normalizeText([item.name, item.description, item.category, item.subcategory, item.comune, item.provincia, ...(item.services || []), ...((item as Record<string, unknown>).keywords as string[] || []), JSON.stringify((item as Record<string, unknown>).translations || {})].join(" ")),
  };
}

function relevanceScore(item: Business, phrase: string, words: string[]) {
  if (!words.length) return 0;
  const index = indexed(item);
'''
new_index = '''function indexed(item: Business, language: Language) {
  const services = (item.services || []).map(normalizeText);
  return {
    name: normalizeText(localizedField<string>(item, "name", language) || item.name),
    category: normalizeText(item.category),
    subcategory: normalizeText(item.subcategory),
    comune: normalizeText(item.comune),
    services,
    haystack: normalizeText([item.name, item.description, item.category, item.subcategory, item.comune, item.provincia, ...(item.services || []), ...((item as Record<string, unknown>).keywords as string[] || [])].join(" ")),
  };
}

function relevanceScore(item: Business, phrase: string, words: string[], language: Language) {
  if (!words.length) return 0;
  const index = indexed(item, language);
'''
if old_index not in s:
    raise SystemExit('catalog search index contract changed')
s = s.replace(old_index, new_index, 1)

s = s.replace(
    'const [sort, setSort] = useState<Sort>((["newest", "rating", "oldest", "name"].includes(initial.get("ordine") || "") ? initial.get("ordine") : "newest") as Sort);',
    'const [sort, setSort] = useState<Sort>((["newest", "rating", "oldest"].includes(initial.get("ordine") || "") ? initial.get("ordine") : "newest") as Sort);',
    1,
)
s = s.replace('      if (!categoryMatches(item, category)) return false;', '      if (category && item.category !== category) return false;', 1)
s = s.replace('      const index = indexed(item);', '      const index = indexed(item, language);', 1)

s = s.replace('relevanceScore(b, keywordNormalized, keywordWords) - relevanceScore(a, keywordNormalized, keywordWords)', 'relevanceScore(b, keywordNormalized, keywordWords, language) - relevanceScore(a, keywordNormalized, keywordWords, language)')
s = s.replace('      if (sort === "name") return String(a.name || "").localeCompare(String(b.name || ""), "it");\n', '', 1)

old_deps = '  }, [items, category, province, city, verified, serviceNormalized, keywordNormalized, keywordWords.join("|"), date, nearby, userLocation, radius, sort]);'
new_deps = '  }, [items, category, province, city, verified, serviceNormalized, keywordNormalized, keywordWords.join("|"), date, nearby, userLocation, radius, sort, language]);'
if old_deps not in s:
    raise SystemExit('catalog filter dependency contract changed')
s = s.replace(old_deps, new_deps, 1)

p.write_text(s)
