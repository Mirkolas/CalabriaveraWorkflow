from pathlib import Path

p = Path('frontend-react/src/pages/OriginalHomePage.tsx')
s = p.read_text()
old_import = 'import { useEffect, useState, type KeyboardEvent, type MouseEvent } from "react";'
new_import = 'import { useEffect, useState, type CSSProperties, type KeyboardEvent, type MouseEvent } from "react";'
if old_import not in s:
    raise SystemExit('home React import contract changed')
s = s.replace(old_import, new_import, 1)

old = "style={{ backgroundImage: `linear-gradient(180deg,transparent 22%,rgba(0,0,0,.72)),url('${item.image}')` }}"
new = "style={{ \"--bg\": `url('${item.image}')` } as CSSProperties}"
if old not in s:
    raise SystemExit('home card background target not found')
s = s.replace(old, new, 1)

old_heart = '      aria-busy={busy || undefined}\n      onClick={(event) => void activate(event)}'
new_heart = '      aria-busy={busy || undefined}\n      data-favorite-id={id}\n      onClick={(event) => void activate(event)}'
if old_heart not in s:
    raise SystemExit('home favorite marker target not found')
s = s.replace(old_heart, new_heart, 1)
p.write_text(s)
