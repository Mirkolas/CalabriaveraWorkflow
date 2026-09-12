from pathlib import Path

# Runtime public dataset: merge the static snapshot with current approved Firestore rows.
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
p.write_text(s)

print('Activity indexing patch applied: live approved merge, Firestore detail fallback, uncapped prerender')
