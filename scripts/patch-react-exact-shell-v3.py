from pathlib import Path
import runpy

# Reuse the validated exact-backup shell/cascade patch, then close the only
# remaining browser mismatch found by v2: the exact backup footer grid has
# three children. The React-only consent shortcut was added after that backup.
runpy.run_path(str(Path(__file__).with_name('patch-react-exact-shell.py')), run_name='__main__')

p = Path('frontend-react/src/components/Layout.tsx')
s = p.read_text()
old = '''          <div className="cv-consent-footer-line"><button type="button" data-cv-open-consent onClick={openCookiePreferences}>{uiText("cookiePreferences", language)}</button><span aria-hidden="true">·</span><Link href={withLanguage("/privacy-policy", language)}>{uiText("privacy", language)}</Link><span aria-hidden="true">·</span><Link href={withLanguage("/cookie-policy", language)}>{uiText("cookies", language)}</Link></div>\n'''
if old not in s:
    raise SystemExit('React-only consent footer line not found')
s = s.replace(old, '', 1)
old_import = 'import CookieConsent, { openCookiePreferences } from "./CookieConsent";'
if old_import not in s:
    raise SystemExit('CookieConsent import target not found')
s = s.replace(old_import, 'import CookieConsent from "./CookieConsent";', 1)
p.write_text(s)
