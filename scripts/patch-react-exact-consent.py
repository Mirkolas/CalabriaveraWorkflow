from pathlib import Path

layout = Path('frontend-react/src/components/Layout.tsx')
s = layout.read_text()
old_import = 'import CookieConsent from "./CookieConsent";'
if old_import not in s:
    raise SystemExit('CookieConsent import contract changed')
s = s.replace(old_import, 'import CookieConsent, { openCookiePreferences } from "./CookieConsent";', 1)
old_expected = '    const expected = exactMainCss(cleanPath);'
new_expected = '    const expected = [...exactMainCss(cleanPath), "/assets/css/privacy-consent.css"];'
if old_expected not in s:
    raise SystemExit('route stylesheet insertion contract changed')
s = s.replace(old_expected, new_expected, 1)
footer_anchor = '''          <div><strong>{uiText("information", language)}</strong><p><Link href={withLanguage("/privacy-policy", language)}>{uiText("privacy", language)}</Link><br/><Link href={withLanguage("/cookie-policy", language)}>{uiText("cookies", language)}</Link><br/><Link href={withLanguage("/termini", language)}>{uiText("terms", language)}</Link><br/><Link href={withLanguage("/note-legali", language)}>{uiText("legalNotes", language)}</Link><br/><Link href={withLanguage("/contatti", language)}>{uiText("contacts", language)}</Link></p></div>\n'''
footer_line = '''          <div className="cv-consent-footer-line"><button type="button" data-cv-open-consent onClick={openCookiePreferences}>Preferenze cookie</button><span aria-hidden="true">·</span><Link href="/privacy-policy">Privacy</Link><span aria-hidden="true">·</span><Link href="/cookie-policy">Cookie</Link></div>\n'''
if footer_line not in s:
    if footer_anchor not in s:
        raise SystemExit('footer information block not found')
    s = s.replace(footer_anchor, footer_anchor + footer_line, 1)
layout.write_text(s)

copy = Path('frontend-react/scripts/copy-legacy-assets.mjs')
c = copy.read_text()
asset_marker = '  "assets/Logo.webp", "assets/Logo.png", "assets/site.webmanifest",'
asset_replacement = '  "assets/css/privacy-consent.css",\n  "assets/Logo.webp", "assets/Logo.png", "assets/site.webmanifest",'
if asset_replacement not in c:
    if asset_marker not in c:
        raise SystemExit('legacy asset copy contract changed')
    c = c.replace(asset_marker, asset_replacement, 1)

# The deployable legacy build rewrites/unifies page CSS after privacy-postbuild. The
# raw privacy stylesheet therefore is not, by itself, the final cascade seen by a
# browser. Keep the React copy raw for every rule except the two mobile banner
# values measured from the exact built backup output. Scope them to the banner so
# the already-matching preferences modal remains untouched.
loop_tail = '''for (const relative of assetFiles) {
  const source = resolve(repoRoot, relative);
  if (!existsSync(source)) continue;
  const target = resolve(reactRoot, "public", relative);
  mkdirSync(dirname(target), { recursive: true });
  copyFileSync(source, target);
}

const staticPublicFiles = ['''
loop_replacement = '''for (const relative of assetFiles) {
  const source = resolve(repoRoot, relative);
  if (!existsSync(source)) continue;
  const target = resolve(reactRoot, "public", relative);
  mkdirSync(dirname(target), { recursive: true });
  copyFileSync(source, target);
}
const privacyTarget = resolve(reactRoot, "public/assets/css/privacy-consent.css");
if (existsSync(privacyTarget)) {
  const deployParityMarker = "cv-consent-built-parity";
  let privacyCss = readFileSync(privacyTarget, "utf8");
  if (!privacyCss.includes(deployParityMarker)) {
    privacyCss += `\n/* ${deployParityMarker}: exact computed values from backup deploy output. */\n@media(max-width:760px){.cv-consent-banner h2{font-size:25.35px;line-height:28.392px;max-width:100%}.cv-consent-banner .cv-consent-actions .button{padding:10.24px 14.72px;max-width:100%}}\n`;
    writeFileSync(privacyTarget, privacyCss, "utf8");
  }
}

const staticPublicFiles = ['''
if 'cv-consent-built-parity' not in c:
    if loop_tail not in c:
        raise SystemExit('legacy asset copy loop contract changed')
    c = c.replace(loop_tail, loop_replacement, 1)
copy.write_text(c)

p = Path('frontend-react/src/components/CookieConsent.tsx')
p.write_text(r'''import { useEffect, useState } from "react";
import Link from "./Link";

const CONSENT_KEY = "cv-cookie-consent-v3";
const LEGACY_KEYS = ["cv-cookie-consent-v2", "cv-consent"] as const;
const CONSENT_VERSION = 3;
const CONSENT_MAX_AGE_MS = 180 * 24 * 60 * 60 * 1000;

type ConsentRecord = {
  version: 3;
  scope: "technical-only";
  savedAt: string;
  expiresAt: string;
  necessary: true;
  preferences: false;
  analytics: false;
  marketing: false;
  source: string;
};

function clearLegacy() {
  try { LEGACY_KEYS.forEach((key) => localStorage.removeItem(key)); } catch {}
}

function emptyRecord(source: string): ConsentRecord {
  const savedAt = Date.now();
  return {
    version: CONSENT_VERSION,
    scope: "technical-only",
    savedAt: new Date(savedAt).toISOString(),
    expiresAt: new Date(savedAt + CONSENT_MAX_AGE_MS).toISOString(),
    necessary: true,
    preferences: false,
    analytics: false,
    marketing: false,
    source,
  };
}

function readConsent(): ConsentRecord | null {
  try {
    const parsed = JSON.parse(localStorage.getItem(CONSENT_KEY) || "null") as ConsentRecord | null;
    if (parsed?.version === CONSENT_VERSION && parsed.scope === "technical-only") {
      const saved = Date.parse(parsed.savedAt || "");
      const expires = Date.parse(parsed.expiresAt || "");
      if (Number.isFinite(saved) && Number.isFinite(expires) && expires > Date.now()) return parsed;
    }
    if (parsed) localStorage.removeItem(CONSENT_KEY);
  } catch {}
  clearLegacy();
  return null;
}

function persist(source: string) {
  const record = emptyRecord(source);
  try {
    localStorage.setItem(CONSENT_KEY, JSON.stringify(record));
    clearLegacy();
  } catch {}
  window.dispatchEvent(new CustomEvent("cv:consent-change", { detail: record }));
  return record;
}

export default function CookieConsent() {
  const [visible, setVisible] = useState(false);
  const [preferences, setPreferences] = useState(false);

  useEffect(() => {
    setVisible(!readConsent());
    const open = () => { setVisible(true); setPreferences(true); };
    window.addEventListener("cv:open-consent", open);
    return () => window.removeEventListener("cv:open-consent", open);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("cv-consent-modal-open", visible && preferences);
    return () => document.documentElement.classList.remove("cv-consent-modal-open");
  }, [visible, preferences]);

  if (!visible) return null;

  const saveAndClose = (source: string) => {
    persist(source);
    setPreferences(false);
    setVisible(false);
  };
  const closePreferences = () => setPreferences(false);

  if (preferences) return <div className="cv-consent-overlay" data-cv-consent-modal="" onClick={(event) => { if (event.target === event.currentTarget) closePreferences(); }} onKeyDown={(event) => { if (event.key === "Escape") closePreferences(); }}><div className="cv-consent-dialog" role="dialog" aria-modal="true" aria-labelledby="cv-consent-title">
    <div className="cv-consent-dialog-head"><div><span className="cv-consent-kicker">CalabriaVera</span><h2 id="cv-consent-title">Preferenze privacy e cookie</h2></div><button type="button" className="cv-consent-close" data-cv-consent-close aria-label="Chiudi preferenze" onClick={closePreferences} autoFocus>×</button></div>
    <p>Vedi le tecnologie presenti su questa versione del sito e scegli quelle opzionali quando sono effettivamente in uso. I servizi necessari restano sempre attivi.</p>
    <div className="cv-consent-categories">
      <label className="cv-consent-category is-required"><span><strong>Necessari</strong><small>Autenticazione, sicurezza, consenso, continuità della sessione e funzioni richieste dall’utente.</small></span><input type="checkbox" data-cv-consent-toggle="necessary" checked disabled readOnly/><i aria-hidden="true"/></label>
      <label className="cv-consent-category is-inactive"><span><strong>Preferenze · non in uso</strong><small>Memorizzazione di scelte facoltative dell’interfaccia e personalizzazione non indispensabile. Non in uso su questa versione del sito.</small></span><input type="checkbox" data-cv-consent-toggle="preferences" disabled/><i aria-hidden="true"/></label>
      <label className="cv-consent-category is-inactive"><span><strong>Statistiche · non in uso</strong><small>Strumenti di misurazione non essenziali, se configurati. Non in uso su questa versione del sito.</small></span><input type="checkbox" data-cv-consent-toggle="analytics" disabled/><i aria-hidden="true"/></label>
      <label className="cv-consent-category is-inactive"><span><strong>Marketing e profilazione · non in uso</strong><small>Tecnologie pubblicitarie, social o di profilazione non necessarie, se configurate. Non in uso su questa versione del sito.</small></span><input type="checkbox" data-cv-consent-toggle="marketing" disabled/><i aria-hidden="true"/></label>
    </div>
    <p className="cv-consent-links"><Link href="/cookie-policy">Cookie Policy</Link><Link href="/privacy-policy">Privacy Policy</Link></p>
    <div className="cv-consent-actions cv-consent-actions--modal"><button type="button" className="button button-secondary" data-cv-consent-reject onClick={() => saveAndClose("preferences-reject")}>Rifiuta non necessari</button><button type="button" className="button button-primary" data-cv-consent-save onClick={() => saveAndClose("preferences-save")}>Salva preferenze</button></div>
  </div></div>;

  return <section className="cv-consent-banner" data-cv-consent-banner="" role="dialog" aria-modal="true" aria-labelledby="cv-cookie-title">
    <button type="button" className="cv-consent-close" data-cv-consent-dismiss aria-label="Continua senza tecnologie non necessarie" onClick={() => saveAndClose("dismiss")}>×</button>
    <div className="cv-consent-copy"><span className="cv-consent-kicker">Privacy</span><h2 id="cv-cookie-title">Privacy e cookie su CalabriaVera</h2><p>Al momento usiamo soltanto tecnologie necessarie al funzionamento e alle funzioni richieste. Statistiche e marketing non sono installati e non possono essere pre-autorizzati.</p><p className="cv-consent-links"><Link href="/cookie-policy">Cookie Policy</Link><Link href="/privacy-policy">Privacy Policy</Link></p></div>
    <div className="cv-consent-actions"><button type="button" className="button button-secondary" data-cv-consent-customize onClick={() => setPreferences(true)}>Vedi preferenze</button><button type="button" className="button button-primary" data-cv-consent-continue onClick={() => saveAndClose("technical-only-continue")}>Continua</button></div>
  </section>;
}

export function openCookiePreferences() {
  window.dispatchEvent(new Event("cv:open-consent"));
}
''')
