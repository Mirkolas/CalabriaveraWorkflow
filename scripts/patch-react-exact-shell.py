from pathlib import Path

# 1) Route CSS must reflect the exact stylesheets present in the legacy HTML.
# The only dynamic global stylesheet injected by the legacy header renderer is
# language-modern.css. react-live-parity.css is the minimal React bridge.
p = Path('frontend-react/scripts/copy-legacy-assets.mjs')
s = p.read_text()
old = '''  const usesExtendedCascade = styles.some((href) => CORE_STYLES.some((core) => assetPath(core) === assetPath(href)));
  const parityStyles = [...(usesExtendedCascade ? CORE_STYLES : []), ...(PAGE_STYLES[page] || []), liveParityCss];
  for (const href of parityStyles) {
    const pathOnly = assetPath(href);
    styles = styles.filter((current) => assetPath(current) !== pathOnly);
    styles.push(href);
  }
'''
new = '''  const parityStyles = ["/assets/css/language-modern.css", liveParityCss];
  for (const href of parityStyles) {
    const pathOnly = assetPath(href);
    styles = styles.filter((current) => assetPath(current) !== pathOnly);
    styles.push(href);
  }
'''
if old not in s:
    raise SystemExit('route cascade block not found')
s = s.replace(old, new, 1)
p.write_text(s)

# 2) Match the shell markup emitted by assets/js/components.js in the exact backup.
p = Path('frontend-react/src/components/Layout.tsx')
s = p.read_text()

def rep(old: str, new: str, label: str):
    global s
    if old not in s:
        raise SystemExit(f'{label}: target not found')
    s = s.replace(old, new, 1)

rep('const LOGO = "/assets/Logo.png";', 'const LOGO = "/assets/Logo.webp";', 'logo')
rep('<header className="cv-site-header site-header cv-header">', '<header className="site-header cv-header">', 'header classes')
rep('<div className="container cv-site-header__inner header-inner">', '<div className="container header-inner">', 'header inner')
rep('className="cv-brand brand"', 'className="brand"', 'brand class')
rep('<img className="brand-logo" src={LOGO} alt="CalabriaVera" width="188" height="46" decoding="async" />', '<img className="brand-logo" src={LOGO} alt="CalabriaVera" />', 'brand image attrs')
rep('<nav className="cv-desktop-nav primary-nav"', '<nav className="primary-nav"', 'desktop nav')
rep('<div className="cv-header-actions header-actions">', '<div className="header-actions">', 'header actions')

# Desktop account wrapper exists in the legacy renderer and is used by its CSS.
needle = '''            {!authReady ? <div className="cv-guest-actions guest-actions"><Link href={withLanguage("/login", language)} className="button button-secondary cv-account-login">{uiText("login", language)}</Link><Link href={withLanguage("/registrazione", language)} className="button button-primary cv-account-register">{uiText("register", language)}</Link></div> : user ? <details className="cv-account-menu account-menu">'''
replacement = '''            <div className="desktop-account">{!authReady ? <div className="guest-actions"><Link href={withLanguage("/login", language)} className="button button-secondary cv-account-login">{uiText("login", language)}</Link><Link href={withLanguage("/registrazione", language)} className="button button-primary cv-account-register">{uiText("register", language)}</Link></div> : user ? <details className="account-menu">'''
rep(needle, replacement, 'desktop account open')
rep('''              <summary className="cv-account-trigger" aria-label={uiText("account", language)} title={uiText("account", language)}><AccountIcon /></summary>
              <div className="cv-account-popover account-links">''', '''              <summary className="cv-account-trigger" aria-label={uiText("account", language)} title={uiText("account", language)}><AccountIcon /></summary>
              <div className="account-links">''', 'account links class')
old_end = '''            </details> : <div className="cv-guest-actions guest-actions"><Link href={withLanguage("/login", language)} className="button button-secondary cv-account-login">{uiText("login", language)}</Link><Link href={withLanguage("/registrazione", language)} className="button button-primary cv-account-register">{uiText("register", language)}</Link></div>}

            <button type="button" className="cv-menu-button menu-button" onClick={() => setMenuOpen((value) => !value)} aria-expanded={menuOpen} aria-controls="cv-mobile-nav" aria-label="Menu"><span /><span /><span /></button>'''
new_end = '''            </details> : <div className="guest-actions"><Link href={withLanguage("/login", language)} className="button button-secondary cv-account-login">{uiText("login", language)}</Link><Link href={withLanguage("/registrazione", language)} className="button button-primary cv-account-register">{uiText("register", language)}</Link></div>}</div>

            <button type="button" className="menu-button" id="menu-toggle" onClick={() => setMenuOpen((value) => !value)} aria-expanded={menuOpen} aria-controls="mobile-nav">Menu</button>'''
rep(old_end, new_end, 'desktop account close/menu')

old_mobile = '''        {menuOpen ? <nav id="cv-mobile-nav" className="cv-mobile-menu primary-mobile" aria-label="Navigazione mobile"><div className="container">
          {nav.map(([label, href, key]) => <Link key={key} href={href} className={isActive(key) ? "is-active" : ""}>{label}</Link>)}
          {authReady ? user ? <><Link href={withLanguage("/profilo", language)}>{uiText("profile", language)}</Link><Link href={withLanguage("/dashboard", language)}>{uiText("dashboard", language)}</Link><Link href={withLanguage("/messaggi", language)}>{uiText("messages", language)}</Link><Link href={withLanguage("/preferiti", language)}>{uiText("favorites", language)}</Link><Link href={withLanguage("/aggiungi-attivita", language)}>{uiText("addBusiness", language)}</Link>{admin ? <Link href="/admin">Admin</Link> : null}<button type="button" onClick={() => void signOut()}>{uiText("logout", language)}</button></> : <><Link href={withLanguage("/login", language)}>{uiText("login", language)}</Link><Link href={withLanguage("/registrazione", language)}>{uiText("register", language)}</Link></> : null}
        </div></nav> : null}'''
new_mobile = '''        {menuOpen ? <nav id="mobile-nav" className="container primary-mobile" aria-label="Navigazione mobile">
          {nav.map(([label, href, key]) => <Link key={key} href={href} className={isActive(key) ? "is-active" : ""}>{label}</Link>)}
          {authReady ? user ? <><Link href={withLanguage("/profilo", language)}>{uiText("profile", language)}</Link><Link href={withLanguage("/dashboard", language)}>{uiText("dashboard", language)}</Link><Link href={withLanguage("/messaggi", language)}>{uiText("messages", language)}</Link><Link href={withLanguage("/preferiti", language)}>{uiText("favorites", language)}</Link><Link href={withLanguage("/aggiungi-attivita", language)}>{uiText("addBusiness", language)}</Link>{admin ? <Link href="/admin">Admin</Link> : null}<button type="button" onClick={() => void signOut()}>{uiText("logout", language)}</button></> : <><Link href={withLanguage("/login", language)}>{uiText("login", language)}</Link><Link href={withLanguage("/registrazione", language)}>{uiText("register", language)}</Link></> : null}
        </nav> : null}'''
rep(old_mobile, new_mobile, 'mobile nav')

# Remove post-backup social footer additions. Consent line stays because the exact
# backup privacy-consent.js dynamically inserts that same line.
start = s.find('            <div className="social-links" data-footer-social')
if start < 0:
    raise SystemExit('social footer block start not found')
end = s.find('            </div>', start)
if end < 0:
    raise SystemExit('social footer block end not found')
s = s[:start] + s[end + len('            </div>\n'):]

rep('<span className="cv-whatsapp-help" aria-hidden="true">Ti serve aiuto?</span>', '', 'whatsapp help')

p.write_text(s)
