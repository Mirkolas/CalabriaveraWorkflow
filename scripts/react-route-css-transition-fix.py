#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: react-route-css-transition-fix.py <private-repo-root>")

root = Path(sys.argv[1]).resolve()
layout = root / "frontend-react/src/components/Layout.tsx"
s = layout.read_text()

old = '''  useEffect(() => {\n    const expected = exactMainCss(cleanPath);\n    const nodes = [...document.querySelectorAll<HTMLLinkElement>('link[data-cv-main-parity]')];\n    const current = nodes.map((node) => new URL(node.href, location.origin).pathname);\n    if (current.length === expected.length && current.every((href, index) => href === expected[index])) return;\n    nodes.forEach((node) => node.remove());\n    for (const href of expected) {\n      const link = document.createElement("link");\n      link.rel = "stylesheet";\n      link.href = href;\n      link.dataset.cvMainParity = "";\n      document.head.appendChild(link);\n    }\n  }, [snapshot, cleanPath]);\n'''

new = '''  useEffect(() => {\n    const expected = exactMainCss(cleanPath);\n    const nodes = [...document.querySelectorAll<HTMLLinkElement>('link[data-cv-main-parity]:not([data-cv-main-parity-stage])')];\n    const current = nodes.map((node) => new URL(node.href, location.origin).pathname);\n    if (current.length === expected.length && current.every((href, index) => href === expected[index])) return;\n\n    let cancelled = false;\n    let committed = false;\n    const staged: HTMLLinkElement[] = [];\n    const loads = expected.map((href) => new Promise<void>((resolve, reject) => {\n      const link = document.createElement("link");\n      link.rel = "stylesheet";\n      link.href = href;\n      link.media = "not all";\n      link.dataset.cvMainParityStage = "";\n      link.addEventListener("load", () => resolve(), { once: true });\n      link.addEventListener("error", () => reject(new Error(`Impossibile caricare ${href}`)), { once: true });\n      staged.push(link);\n      document.head.appendChild(link);\n    }));\n\n    void Promise.all(loads).then(() => {\n      if (cancelled) return;\n      for (const link of staged) {\n        link.media = "all";\n        link.dataset.cvMainParity = "";\n        delete link.dataset.cvMainParityStage;\n      }\n      nodes.forEach((node) => node.remove());\n      committed = true;\n    }).catch((error) => {\n      if (!cancelled) console.warn("[CalabriaVera] CSS route non caricato; mantengo lo stile corrente.", error);\n      staged.forEach((node) => node.remove());\n    });\n\n    return () => {\n      cancelled = true;\n      if (!committed) staged.forEach((node) => node.remove());\n    };\n  }, [snapshot, cleanPath]);\n'''

if new in s:
    print("Route CSS transition fix already present")
elif old in s:
    s = s.replace(old, new, 1)
    layout.write_text(s)
    print("Applied atomic route CSS swap: old stylesheet remains active until new stylesheet is loaded")
else:
    raise SystemExit("Layout route CSS swap block not found")
