#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: react-main-integration-resolve.py <private-repo-root>")

root = Path(sys.argv[1]).resolve()

layout = root / "frontend-react/src/components/Layout.tsx"
text = layout.read_text()
old = 'const LOGO = "/assets/Logo.webp";'
new = 'const LOGO = "https://img.calabriavera.com/static/assets/Logo.png";'
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("Layout LOGO target missing")
layout.write_text(text)

home = root / "frontend-react/src/pages/OriginalHomePage.tsx"
text = home.read_text()
cdn = 'const STATIC_IMAGE_CDN = "https://img.calabriavera.com/static";'
if cdn not in text:
    anchor = 'import { MAIN_COMMON_CITIES } from "../generated/main-static-options";\n\n'
    if anchor not in text:
        raise SystemExit("Home CDN insertion point missing")
    text = text.replace(anchor, anchor + cdn + "\n", 1)

for asset in [
    "assets/images/home/tropea-960.webp",
    "assets/images/home/sila-720.webp",
    "assets/images/home/scilla-720.webp",
    "assets/images/home/capo-colonna-720.webp",
]:
    local = f'image: "/{asset}"'
    remote = f'image: `${{STATIC_IMAGE_CDN}}/{asset}`'
    if local in text:
        text = text.replace(local, remote, 1)
    elif remote not in text:
        raise SystemExit(f"Home image target missing: {asset}")

local_logo = 'src="/assets/Logo.png"'
remote_logo = 'src={`${STATIC_IMAGE_CDN}/assets/Logo.png`}'
if local_logo in text:
    text = text.replace(local_logo, remote_logo, 1)
elif remote_logo not in text:
    raise SystemExit("Home logo target missing")

home.write_text(text)
print("Resolved certified React conflicts while preserving current R2 image URLs")
