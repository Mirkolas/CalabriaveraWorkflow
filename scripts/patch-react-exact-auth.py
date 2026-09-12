from pathlib import Path

p = Path('frontend-react/src/pages/AuthPage.tsx')
s = p.read_text()

s = s.replace(
    'import { authErrorMessage, loginEmail, loginGoogle, registerEmail, resetPassword, type AuthResult } from "../lib/auth";',
    'import { authErrorMessage, loginEmail, loginGoogle, registerEmail, resetPassword, watchUser, type AuthResult } from "../lib/auth";',
    1,
)

start = s.index('function ResetPanel(')
end = s.index('\n\nexport default function AuthPage', start)
reset = r'''function ResetPanel({ language }: { language: Language }) {
  const [open, setOpen] = useState(false);
  const [lastReset, setLastReset] = useState(0);
  const [resetEmail, setResetEmail] = useState("");
  const [resetBusy, setResetBusy] = useState(false);
  const [resetStatus, setResetStatus] = useState("");

  const toggle = () => {
    const nextOpen = !open;
    if (nextOpen) {
      setResetEmail(document.querySelector<HTMLInputElement>('#auth-form input[name="email"]')?.value || "");
      setResetStatus("");
    }
    setOpen(nextOpen);
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (Date.now() - lastReset < 60_000) { setResetStatus("Attendi un minuto prima di richiedere un altro invio."); return; }
    const email = String(new FormData(event.currentTarget).get("resetEmail") || "");
    setResetBusy(true); setResetStatus("Invio…");
    try {
      await resetPassword(email);
      setLastReset(Date.now());
      setResetStatus("Se esiste un account con questa email, riceverai il link per reimpostare la password. Controlla anche lo spam.");
    } catch (cause) { setResetStatus(authErrorMessage(cause, language)); }
    finally { setResetBusy(false); }
  };

  return <>
    <button type="button" id="reset" className="text-link" style={{ border: 0, background: "transparent", padding: 0, marginTop: "1rem" }} aria-expanded={open} aria-controls="reset-form" onClick={toggle}>Password dimenticata?</button>
    {open ? <form id="reset-form" className="stack" style={{ marginTop: "1rem" }} onSubmit={submit}><label>Email per il recupero<input type="email" name="resetEmail" autoComplete="email" required defaultValue={resetEmail} /></label><button disabled={resetBusy} className="button button-secondary">Invia email di recupero</button><p id="reset-status" role="status" aria-live="polite">{resetStatus}</p></form> : null}
  </>;
}'''
s = s[:start] + reset + s[end:]

needle = '''  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const nextParam = new URLSearchParams(location.search).get("next") || withLanguage("/", language);
  const next = nextParam.startsWith("/") && !nextParam.startsWith("//") ? nextParam : withLanguage("/", language);
'''
replacement = '''  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [existingUser, setExistingUser] = useState<import("firebase/auth").User | null | undefined>(undefined);
  const pageParams = new URLSearchParams(location.search);
  const nextParam = pageParams.get("next") || withLanguage("/", language);
  const next = nextParam.startsWith("/") && !nextParam.startsWith("//") ? nextParam : withLanguage("/", language);
  const accountNotice = pageParams.get("suspended") === "1" ? "Account sospeso. Contatta l’assistenza per informazioni." : "";
'''
if needle not in s:
    raise SystemExit('auth state block not found')
s = s.replace(needle, replacement, 1)

seo_end = '''  useEffect(() => {
    const title = mode === "login" ? copy.login : copy.register;
    setPageSeo({ title: `${title} | CalabriaVera`, description: mode === "login" ? copy.loginText : copy.registerText, path: mode === "login" ? "/login" : "/registrazione", robots: "noindex,follow" });
  }, [mode, language, copy.login, copy.register, copy.loginText, copy.registerText]);
'''
if seo_end not in s:
    raise SystemExit('seo effect not found')
s = s.replace(seo_end, seo_end + '''
  useEffect(() => watchUser((user) => setExistingUser(user)), []);
''', 1)

s = s.replace(
    '    setBusy(true); setError(""); setMessage("");\n    try {\n      if (mode === "login") {',
    '    setBusy(true); setError(""); setMessage(mode === "register" ? "Creazione account e invio verifica…" : "Accesso…");\n    try {\n      if (mode === "login") {',
    1,
)
s = s.replace(
    '    setBusy(true); setError(""); setMessage("");\n    try {\n      finish(await loginGoogle',
    '    setBusy(true); setError(""); setMessage("Accesso con Google…");\n    try {\n      finish(await loginGoogle',
    1,
)

return_marker = '  return <section className="auth-shell"><div className="card" style={{ maxWidth: 620, margin: "auto" }}>'
if return_marker not in s:
    raise SystemExit('guest return marker not found')
pre = '''  if (existingUser === undefined) return <section className="section container"><div id="auth-root"><p role="status">Caricamento accesso…</p></div></section>;

  if (existingUser) return <section className="section container"><div id="auth-root"><section className="auth-shell"><div className="card" style={{ maxWidth: 620, margin: "auto" }}><h1 style={{ fontSize: "2.5rem" }}>Accesso effettuato</h1><p>{existingUser.email || ""}</p><p>{existingUser.emailVerified ? "Il tuo account è pronto." : "Controlla la casella email e completa la verifica dal Profilo."}</p><div className="form-actions"><Link className="button button-primary" href={withLanguage("/profilo", language)}>Apri il profilo</Link><Link className="button button-secondary" href={next}>Continua</Link></div></div></section></div></section>;

  return <section className="section container"><div id="auth-root"><section className="auth-shell"><div className="card" style={{ maxWidth: 620, margin: "auto" }}>'''
s = s.replace(return_marker, pre, 1)

s = s.replace(
    '<p className="full form-status" role="status" aria-live="polite">{error || message}</p>',
    '<p className="full form-status" id="auth-status" role="status" aria-live="polite">{error || message || accountNotice}</p>',
    1,
)
s = s.replace(
    '{busy ? copy.wait : mode === "register" ? copy.register : copy.login}',
    '{mode === "register" ? copy.register : copy.login}',
    1,
)
s = s.replace(
    '<ResetPanel busy={busy} language={language} onBusy={setBusy} onError={setError} onMessage={setMessage} />',
    '<ResetPanel language={language} />',
    1,
)

old_end = '''    <p className="muted">{mode === "register" ? copy.existing : copy.newAccount} <Link className="text-link" href={withLanguage(mode === "register" ? "/login" : "/registrazione", language)}>{mode === "register" ? copy.signIn : copy.signUp}</Link></p>
  </div></section>;
}'''
new_end = '''    <p className="muted">{mode === "register" ? copy.existing : copy.newAccount} <Link className="text-link" href={withLanguage(mode === "register" ? "/login" : "/registrazione", language)}>{mode === "register" ? copy.signIn : copy.signUp}</Link></p>
  </div></section></div></section>;
}'''
if old_end not in s:
    raise SystemExit('auth return close not found')
s = s.replace(old_end, new_end, 1)

p.write_text(s)
