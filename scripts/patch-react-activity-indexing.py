from pathlib import Path

# Runtime public dataset: merge the deploy snapshot with current approved Firestore rows.
p = Path('frontend-react/src/lib/public-data.ts')
s = p.read_text()
old = '''      let publicRows: Business[] = [];
      try { publicRows = await fetchDataset<Business>("/assets/data/public-businesses-v1.json"); }
      catch { publicRows = []; }
      if (!publicRows.length) {
        const { loadAllBusinesses } = await import("./businesses");
        try { publicRows = await retry(() => loadAllBusinesses(true)); } catch { publicRows = []; }
      }

      let tourism: Business[] = [];
'''
new = '''      let publicRows: Business[] = [];
      try { publicRows = await fetchDataset<Business>("/assets/data/public-businesses-v1.json"); }
      catch { publicRows = []; }
      const { loadAllBusinesses } = await import("./businesses");
      try {
        const liveRows = await retry(() => loadAllBusinesses(true));
        publicRows = [...publicRows, ...liveRows];
      } catch {
        // The deploy snapshot remains a valid offline fallback when Firestore is temporarily unavailable.
      }

      let tourism: Business[] = [];
'''
if old not in s:
    raise SystemExit('public-data snapshot/live merge contract changed')
s = s.replace(old, new, 1)
old2 = '''  const candidates = rows.filter((item) => businessMatches(item, route, "", ""));
  return candidates.sort((a, b) => routeScore(b, route) - routeScore(a, route))[0] || null;
}
'''
new2 = '''  const candidates = rows.filter((item) => businessMatches(item, route, "", ""));
  const localMatch = candidates.sort((a, b) => routeScore(b, route) - routeScore(a, route))[0] || null;
  if (localMatch) return localMatch;

  // Exact legacy behavior: a public detail must still resolve from Firestore even when a deploy snapshot is stale.
  try {
    const { getBusinessFromLocation } = await import("./businesses");
    return await retry(() => getBusinessFromLocation(pathname, search));
  } catch {
    return null;
  }
}
'''
if old2 not in s:
    raise SystemExit('findPublicBusiness fallback contract changed')
s = s.replace(old2, new2, 1)
p.write_text(s)

# Match the legacy public resolver ceiling: query up to 1000 approved businesses.
p = Path('frontend-react/src/lib/businesses.ts')
s = p.read_text()
old_limit = 'f.query(f.collection(db, "businesses"), f.where("status", "==", "approved"), f.limit(500)),'
new_limit = 'f.query(f.collection(db, "businesses"), f.where("status", "==", "approved"), f.limit(1000)),'
if old_limit not in s:
    raise SystemExit('approved business query limit contract changed')
s = s.replace(old_limit, new_limit, 1)
p.write_text(s)

# Prerender every approved business returned by the 1000-row Firestore query, not an arbitrary 96-row subset.
p = Path('frontend-react/scripts/prerender-home.mjs')
s = p.read_text()
old3 = '''  const businesses = [...tourismRows, ...businessRows].filter((item) => {
    const key = String(item.id || `${item.name || ""}-${item.comune || ""}`);
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  }).slice(0, 96);
'''
new3 = '''  const businesses = [...tourismRows, ...businessRows].filter((item) => {
    const key = String(item.id || `${item.name || ""}-${item.comune || ""}`);
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
'''
if old3 not in s:
    raise SystemExit('prerender business cap contract changed')
s = s.replace(old3, new3, 1)

# Public pages must carry canonical + hreflang in the HTML response itself, before client hydration.
# The exact-built CSS patch intentionally removes the old cleanRoute/parity-link block, so anchor on
# the title replacement line that remains stable after that transform.
anchor = '  html = html.replace(/<title>'
idx = s.find(anchor)
if idx < 0:
    raise SystemExit('prerender title replacement contract changed')
seo = r'''  if (!robots.startsWith("noindex")) {
    const canonicalPath = page.canonicalPath || page.path || "/";
    const canonicalClean = canonicalPath.replace(/^\/(?:en|fr|de|es)(?=\/|$)/, "") || "/";
    const canonicalHref = `https://calabriavera.com${canonicalPath === "/" ? "" : canonicalPath}`;
    const alternateLinks = languages.map(({ lang, prefix }) => {
      const localized = `${prefix}${canonicalClean === "/" ? "/" : canonicalClean}` || "/";
      return `<link rel="alternate" hreflang="${lang}" href="https://calabriavera.com${localized === "/" ? "" : localized}" />`;
    }).join("") + `<link rel="alternate" hreflang="x-default" href="https://calabriavera.com${canonicalClean === "/" ? "" : canonicalClean}" />`;
    html = html.replace(/<link\s+rel=["']canonical["'][^>]*>/gi, "");
    html = html.replace(/<link\s+rel=["']alternate["'][^>]*hreflang=["'][^"']+["'][^>]*>/gi, "");
    html = html.replace("</head>", `<link rel="canonical" href="${canonicalHref}" />${alternateLinks}</head>`);
  }
'''
s = s[:idx] + seo + s[idx:]
p.write_text(s)

print('Activity indexing patch applied: live approved merge, Firestore detail fallback, 1000-row resolver, uncapped prerender, server canonical/hreflang')
