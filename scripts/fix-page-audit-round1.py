from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
layout = root / 'frontend-react/src/components/Layout.tsx'
tests = root / 'tests/site-stability.test.mjs'


def read(path):
    return path.read_text(encoding='utf-8')


def write(path, text):
    path.write_text(text, encoding='utf-8')

s = read(layout)
anchor = 'const LOGO = "https://img.calabriavera.com/static/assets/Logo.webp";\n'
flag_helper = 'const FLAG_CDN = "https://img.calabriavera.com/static/assets/flags";\nconst flagStyle = (lang: string) => ({ backgroundImage: `url("${FLAG_CDN}/${lang}.svg")` });\n'
if 'const FLAG_CDN =' not in s:
    if anchor not in s:
        raise SystemExit('Layout: LOGO anchor not found')
    s = s.replace(anchor, anchor + flag_helper)

old_current = '<span className={`cv-language-flag cv-language-flag--${language}`} aria-hidden="true" />'
new_current = '<span className={`cv-language-flag cv-language-flag--${language}`} style={flagStyle(language)} aria-hidden="true" />'
if old_current in s:
    s = s.replace(old_current, new_current)
elif 'style={flagStyle(language)}' not in s:
    raise SystemExit('Layout: current-language flag not found')

old_option = '<span className={`cv-language-flag cv-language-flag--${lang}`} aria-hidden="true" />'
new_option = '<span className={`cv-language-flag cv-language-flag--${lang}`} style={flagStyle(lang)} aria-hidden="true" />'
if old_option in s:
    s = s.replace(old_option, new_option)
elif 'style={flagStyle(lang)}' not in s:
    raise SystemExit('Layout: language option flag not found')
write(layout, s)

s = read(tests)
marker = "React language selector usa le bandiere dal CDN R2"
if marker not in s:
    s += r'''

test('React language selector usa le bandiere dal CDN R2', () => {
  const layout = read('frontend-react/src/components/Layout.tsx');
  assert.match(layout, /https:\/\/img\.calabriavera\.com\/static\/assets\/flags/);
  assert.match(layout, /style=\{flagStyle\(language\)\}/);
  assert.match(layout, /style=\{flagStyle\(lang\)\}/);
  assert.doesNotMatch(layout, /["'`]\/assets\/flags\//);
});
'''
write(tests, s)

print('Language flags now use the R2 CDN')
