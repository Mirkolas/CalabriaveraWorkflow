from pathlib import Path

p = Path('frontend-react/src/styles.css')
s = p.read_text()
old = '.cv-site-shell{min-height:100vh;background:#fff;color:var(--cv-ink)}'
new = '.cv-site-shell{min-height:100vh}'
if old not in s:
    raise SystemExit('cv-site-shell inheritance override not found')
s = s.replace(old, new, 1)
p.write_text(s)
