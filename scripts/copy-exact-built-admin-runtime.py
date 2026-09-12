from pathlib import Path
import re, shutil, sys

if len(sys.argv)!=3:
    raise SystemExit('usage: copy-exact-built-admin-runtime.py LEGACY_DIST REACT_PUBLIC')
src=Path(sys.argv[1]).resolve(); dst=Path(sys.argv[2]).resolve()
roots=[
 'assets/js/admin.js','assets/js/admin-console.js','assets/js/admin-upgrade.js',
 'assets/js/admin-maintenance-toggle.js','assets/js/admin-automation-status.js',
 'assets/js/admin-critical-upgrades.js','assets/js/admin-conversation-delete-ui.js',
 'assets/js/admin-user-profile-ui.js'
]
rx=re.compile(r'''(?:from\s*|import\s*\()\s*["']([^"']+)["']''')
queue=[src/r for r in roots]; seen=set()
while queue:
    f=queue.pop(0).resolve()
    if f in seen: continue
    if not f.is_file(): raise SystemExit(f'missing admin runtime dependency: {f}')
    try: rel=f.relative_to(src)
    except ValueError: raise SystemExit(f'dependency escaped dist: {f}')
    seen.add(f)
    text=f.read_text()
    for spec in rx.findall(text):
        clean=spec.split('?',1)[0].split('#',1)[0]
        if clean.startswith(('http:','https:')): continue
        if clean.startswith('/'):
            dep=(src/clean.lstrip('/')).resolve()
        elif clean.startswith('.'):
            dep=(f.parent/clean).resolve()
        else:
            continue
        if dep.suffix=='.js' and dep.is_file() and dep not in seen: queue.append(dep)
for f in sorted(seen):
    rel=f.relative_to(src); out=dst/rel; out.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(f,out)
print(f'Copied {len(seen)} exact built admin runtime modules')
for f in sorted(seen): print(f.relative_to(src))
