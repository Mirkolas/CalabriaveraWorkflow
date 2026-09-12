from pathlib import Path

p = Path('frontend-react/src/components/Layout.tsx')
s = p.read_text()
if '<div id="site-header">' in s:
    print('site-header wrapper already present')
    raise SystemExit(0)
old_open = '    <div className="cv-site-shell">\n      <header className="site-header cv-header">'
new_open = '    <div className="cv-site-shell">\n      <div id="site-header">\n        <header className="site-header cv-header">'
if old_open not in s:
    raise SystemExit('Layout header opening contract not found')
s = s.replace(old_open, new_open, 1)
old_close = '      </header>\n\n      <main id="main-content" className="cv-site-main">'
new_close = '        </header>\n      </div>\n\n      <main id="main-content" className="cv-site-main">'
if old_close not in s:
    raise SystemExit('Layout header closing contract not found')
s = s.replace(old_close, new_close, 1)
p.write_text(s)
print('Exact #site-header wrapper restored')
