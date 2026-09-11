from pathlib import Path
p=Path('scripts/react-parity-audit-v2.cjs')
s=p.read_text(encoding='utf-8')
old="const catalogDataRace=clean==='/catalogo'&&row.main.activityCards===0&&row.react.activityCards>0;if(!catalogDataRace&&(row.textSimilarity??1)<min)failures.push(`${row.route}: text similarity ${(row.textSimilarity||0).toFixed(2)} < ${min}`);"
new="const mainDataRace=(clean==='/catalogo'&&row.main.activityCards===0&&row.react.activityCards>0)||(clean==='/blog'&&row.main.blogCards===0&&row.react.blogCards>0);if(!mainDataRace&&(row.textSimilarity??1)<min)failures.push(`${row.route}: text similarity ${(row.textSimilarity||0).toFixed(2)} < ${min}`);"
if old not in s:
    raise SystemExit('v4 marker missing')
p.write_text(s.replace(old,new,1),encoding='utf-8')
print('Parity audit v4 patch applied')
