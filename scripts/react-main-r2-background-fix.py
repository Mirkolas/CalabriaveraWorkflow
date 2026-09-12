#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: react-main-r2-background-fix.py <private-repo-root>")
root = Path(sys.argv[1]).resolve()
cdn = "https://img.calabriavera.com/static"

home = root / "frontend-react/src/pages/OriginalHomePage.tsx"
s = home.read_text()
marker = 'const STATIC_IMAGE_CDN = "https://img.calabriavera.com/static";\n'
css = '''const HOME_R2_PARITY_CSS = `
body[data-page="home"] .cv-home-hero{background-image:linear-gradient(90deg,rgba(1,39,67,.78),rgba(1,39,67,.20) 58%,rgba(1,39,67,.03)),url('https://img.calabriavera.com/static/assets/images/home/tropea-1600.webp')!important;background-position:center 48%!important}
@media(max-width:850px){body[data-page="home"] .cv-home-hero{background-image:linear-gradient(90deg,rgba(1,39,67,.78),rgba(1,39,67,.20) 58%,rgba(1,39,67,.03)),url('https://img.calabriavera.com/static/assets/images/home/tropea-960.webp')!important}}
`;
'''
if "HOME_R2_PARITY_CSS" not in s:
    if marker not in s:
        raise SystemExit("Home CDN marker missing")
    s = s.replace(marker, marker + css, 1)
old = '    <div className="cv-original-home">\n      <section className="cv-home-hero">'
new = '    <div className="cv-original-home"><style>{HOME_R2_PARITY_CSS}</style>\n      <section className="cv-home-hero">'
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit("Home root target missing")
home.write_text(s)

blog = root / "frontend-react/src/pages/MagazinePage.tsx"
s = blog.read_text()
hero_rules = '''body[data-page="blog"] .article-hero{background-image:linear-gradient(90deg,rgba(2,45,77,.90),rgba(2,45,77,.42)),url('https://img.calabriavera.com/static/assets/images/home/sila-1280.webp')!important;background-position:center 52%!important}
@media(max-width:850px){body[data-page="blog"] .article-hero{background-image:linear-gradient(90deg,rgba(2,45,77,.90),rgba(2,45,77,.42)),url('https://img.calabriavera.com/static/assets/images/home/sila-720.webp')!important}}
'''
if "sila-1280.webp" not in s:
    needle = 'const BLOG_SECTIONS_CSS = `\n'
    if needle not in s:
        raise SystemExit("Blog CSS marker missing")
    s = s.replace(needle, needle + hero_rules, 1)
blog.write_text(s)

print("Applied exact legacy Home/Blog background rules with R2 URLs")
