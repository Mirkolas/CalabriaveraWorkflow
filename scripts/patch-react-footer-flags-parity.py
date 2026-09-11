from pathlib import Path

root = Path('source/frontend-react')

# Copy the same flag assets used by production.
p = root / 'scripts/copy-legacy-assets.mjs'
s = p.read_text(encoding='utf-8')
needle = '  "assets/images/home/tropea-960.webp", "assets/images/home/tropea-1600.webp", "assets/images/home/sila-720.webp", "assets/images/home/sila-1280.webp", "assets/images/home/scilla-720.webp", "assets/images/home/capo-colonna-720.webp"\n];'
replacement = '  "assets/images/home/tropea-960.webp", "assets/images/home/tropea-1600.webp", "assets/images/home/sila-720.webp", "assets/images/home/sila-1280.webp", "assets/images/home/scilla-720.webp", "assets/images/home/capo-colonna-720.webp",\n  "assets/flags/it.svg", "assets/flags/en.svg", "assets/flags/fr.svg", "assets/flags/de.svg", "assets/flags/es.svg"\n];'
if needle not in s:
    raise SystemExit('assetFiles marker missing')
s = s.replace(needle, replacement, 1)
p.write_text(s, encoding='utf-8')

# Exact production footer structure and social destinations.
p = root / 'src/components/Layout.tsx'
s = p.read_text(encoding='utf-8')
s = s.replace('import PwaInstallButton from "./PwaInstallButton";\n', '')
marker = 'const languageNames = { it: "Italiano", en: "English", fr: "Français", de: "Deutsch", es: "Español" } as const;\n'
if marker not in s:
    raise SystemExit('languageNames marker missing')
s = s.replace(marker, marker + 'const footerBusinesses = { it: "Attività", en: "Businesses", fr: "Activités", de: "Betriebe", es: "Negocios" } as const;\n', 1)

start = s.index('      <footer className="cv-site-footer footer">')
end = s.index('\n\n      {showBusinessReport', start)
footer = r'''      <footer className="footer">
        <div className="container footer-grid">
          <div className="footer-brand-copy">
            <Link href={withLanguage("/", language)} aria-label="CalabriaVera home"><img className="footer-logo" src="/assets/Logo.png" alt="CalabriaVera" loading="lazy" decoding="async" fetchPriority="low" /></Link>
            <p>{uiText("footerCopy", language)}</p>
            <div className="footer-contact"><a href="mailto:info.calabriavera@gmail.com">info.calabriavera@gmail.com</a><a href="tel:+393479975255">+39 347 997 5255</a></div>
            <div className="social-links" data-footer-social="" aria-label="Social CalabriaVera">
              <a className="social-link" href="https://www.instagram.com/info.calabriavera/" target="_blank" rel="noopener noreferrer" aria-label="Instagram CalabriaVera" title="Instagram"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M7.7 2h8.6A5.7 5.7 0 0 1 22 7.7v8.6a5.7 5.7 0 0 1-5.7 5.7H7.7A5.7 5.7 0 0 1 2 16.3V7.7A5.7 5.7 0 0 1 7.7 2Zm-.2 2A3.5 3.5 0 0 0 4 7.5v9A3.5 3.5 0 0 0 7.5 20h9a3.5 3.5 0 0 0 3.5-3.5v-9A3.5 3.5 0 0 0 16.5 4h-9Zm9.75 1.5a1.25 1.25 0 1 1 0 2.5 1.25 1.25 0 0 1 0-2.5ZM12 7a5 5 0 1 1 0 10 5 5 0 0 1 0-10Zm0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z" /></svg></a>
              <a className="social-link" href="https://wa.me/393479975255" target="_blank" rel="noopener noreferrer" aria-label="WhatsApp CalabriaVera" title="WhatsApp"><svg className="whatsapp-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12.04 2a9.84 9.84 0 0 0-8.43 14.91L2 22l5.23-1.55A9.94 9.94 0 0 0 12.04 21.7h.01A9.85 9.85 0 0 0 12.04 2Zm0 17.99h-.01a8.2 8.2 0 0 1-4.18-1.14l-.3-.18-3.1.92.93-3.02-.2-.31a8.14 8.14 0 1 1 6.86 3.73Zm4.47-6.1c-.24-.12-1.45-.72-1.68-.8-.22-.08-.39-.12-.55.12-.17.25-.64.8-.79.97-.14.16-.29.18-.53.06-.25-.12-1.04-.38-1.98-1.23a7.42 7.42 0 0 1-1.37-1.7c-.14-.25-.02-.38.11-.5.11-.11.24-.29.36-.43.12-.15.17-.25.25-.41.08-.17.04-.31-.02-.43-.06-.12-.55-1.34-.76-1.84-.2-.48-.4-.41-.55-.42h-.47c-.16 0-.43.06-.65.31-.23.24-.86.84-.86 2.04 0 1.21.88 2.37 1 2.53.13.16 1.73 2.64 4.2 3.7.58.25 1.04.4 1.4.52.59.18 1.12.16 1.54.1.47-.07 1.45-.6 1.66-1.18.2-.58.2-1.08.14-1.18-.06-.1-.22-.16-.47-.28Z" /></svg></a>
              <a className="social-link" href="https://www.facebook.com/profile.php?id=61580665768182" target="_blank" rel="noopener noreferrer" aria-label="Facebook CalabriaVera" title="Facebook"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M13.8 22v-9h3l.45-3.5H13.8V7.26c0-1.01.28-1.7 1.73-1.7h1.85V2.43c-.32-.04-1.42-.13-2.7-.13-2.67 0-4.5 1.63-4.5 4.63V9.5H7.16V13h3.02v9h3.62Z" /></svg></a>
            </div>
          </div>
          <div><strong>{uiText("explore", language)}</strong><p><Link href={withLanguage("/catalogo", language)}>{footerBusinesses[language]}</Link><br /><Link href={withLanguage("/mappa", language)}>{uiText("map", language)}</Link><br /><Link href={withLanguage("/blog", language)}>{uiText("magazine", language)}</Link><br /><Link href={withLanguage("/chi-siamo", language)}>{uiText("about", language)}</Link></p></div>
          <div><strong>{uiText("information", language)}</strong><p><Link href={withLanguage("/privacy-policy", language)}>{uiText("privacy", language)}</Link><br /><Link href={withLanguage("/cookie-policy", language)}>{uiText("cookies", language)}</Link><br /><Link href={withLanguage("/termini", language)}>{uiText("terms", language)}</Link><br /><Link href={withLanguage("/note-legali", language)}>{uiText("legalNotes", language)}</Link><br /><Link href={withLanguage("/contatti", language)}>{uiText("contacts", language)}</Link></p></div>
          <div className="cv-consent-footer-line"><button type="button" onClick={openCookiePreferences}>{uiText("cookiePreferences", language)}</button><span aria-hidden="true">·</span><Link href={withLanguage("/privacy-policy", language)}>{uiText("privacy", language)}</Link><span aria-hidden="true">·</span><Link href={withLanguage("/cookie-policy", language)}>{uiText("cookies", language)}</Link></div>
        </div>
      </footer>'''
s = s[:start] + footer + s[end:]
p.write_text(s, encoding='utf-8')

# The production bottom consent row is part of the footer grid and spans all columns.
p = root / 'public/assets/css/react-live-parity.css'
s = p.read_text(encoding='utf-8')
s += r'''
.footer .footer-logo{width:min(280px,100%)!important;max-width:280px!important;height:auto!important}
.cv-consent-footer-line{grid-column:1/-1;display:flex;align-items:center;justify-content:center;gap:10px;margin-top:18px;padding-top:28px;border-top:1px solid rgba(255,255,255,.14);font-size:12px;color:rgba(255,255,255,.82)}
.cv-consent-footer-line button{appearance:none;border:0;background:transparent;color:inherit;font:inherit;padding:0;text-decoration:underline;cursor:pointer}
.cv-consent-footer-line a{color:inherit;text-decoration:underline}
@media(max-width:700px){.footer .footer-logo{width:min(230px,100%)!important}.cv-consent-footer-line{flex-wrap:wrap;padding-top:20px;margin-top:8px}}
'''
p.write_text(s, encoding='utf-8')

print('Footer and flag parity patch applied')
