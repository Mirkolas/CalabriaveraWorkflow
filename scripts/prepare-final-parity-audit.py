from pathlib import Path

# Trigger the dynamic cutover gate for the validated Firebase production bridge.
# Re-run against the final hosting/R2 candidate after Firebase-emulator validation.
path = Path('automation/scripts/react-parity-audit-v2.cjs')
s = path.read_text()

old = "const min=clean==='/'?0.6:['/chi-siamo','/privacy-policy','/cookie-policy','/termini','/note-legali'].includes(clean)?0.75:0.15;const catalogDataRace=clean==='/catalogo'&&row.main.activityCards===0&&row.react.activityCards>0;if(!catalogDataRace&&(row.textSimilarity??1)<min)failures.push(`${row.route}: text similarity ${(row.textSimilarity||0).toFixed(2)} < ${min}`);"
new = "const min=clean==='/'?0.6:['/chi-siamo','/privacy-policy','/cookie-policy','/termini','/note-legali'].includes(clean)?0.75:0.15;const catalogDataRace=clean==='/catalogo'&&row.main.activityCards===0&&row.react.activityCards>0;const blogReferenceRace=clean==='/blog'&&row.main.blogCards===0&&row.react.blogCards>0;if(!catalogDataRace&&!blogReferenceRace&&(row.textSimilarity??1)<min)failures.push(`${row.route}: text similarity ${(row.textSimilarity||0).toFixed(2)} < ${min}`);"
if old not in s:
    raise SystemExit('text similarity gate anchor not found')
s = s.replace(old, new, 1)

old2 = "if(s.blogSnapshotStatus!==200||s.blogSnapshotCount<1||s.blogCards<1)failures.push(`blog snapshot/runtime incomplete (status=${s.blogSnapshotStatus}, count=${s.blogSnapshotCount}, cards=${s.blogCards})`);"
new2 = "if(s.blogSnapshotStatus!==200||s.blogSnapshotCount<1||s.blogCards<1)failures.push(`blog snapshot/runtime incomplete (status=${s.blogSnapshotStatus}, count=${s.blogSnapshotCount}, cards=${s.blogCards})`);const loadedBlogRows=report.routes.filter(row=>cleanRoute(row.route)==='/blog'&&row.main?.blogCards>0&&row.react?.blogCards>0);if(loadedBlogRows.length&&Math.max(...loadedBlogRows.map(row=>row.textSimilarity??0))<0.65)failures.push(`blog loaded-reference similarity below 0.65`);"
if old2 not in s:
    raise SystemExit('blog functional gate anchor not found')
s = s.replace(old2, new2, 1)

path.write_text(s)
print('Final parity audit prepared: catalog/blog data races are ignored only when main failed to load cards; loaded blog references must still reach 0.65 similarity.')
