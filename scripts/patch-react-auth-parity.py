from pathlib import Path

p = Path('source/frontend-react/src/pages/AuthPage.tsx')
s = p.read_text(encoding='utf-8')

# Registration must validate the same confirmation field as main before touching Firebase.
old = '''      } else {\n        await registerEmail({\n          email: String(data.get("email") || ""),\n          password: String(data.get("password") || ""),'''
new = '''      } else {\n        const password = String(data.get("password") || "");\n        const passwordConfirm = String(data.get("passwordConfirm") || "");\n        if (password !== passwordConfirm) throw new Error("PASSWORD_MISMATCH");\n        await registerEmail({\n          email: String(data.get("email") || ""),\n          password,'''
if old not in s:
    raise SystemExit('registration submit marker missing')
s = s.replace(old, new, 1)

# Match the main auth card shell instead of a separate two-column React-only design.
start = s.index('  return (\n')
end = s.rindex('\n  );\n}')
return_block = r'''  return (
    <section className="auth-shell">
      <div className="card" style={{ maxWidth: 620, margin: "auto" }}>
        <p className="eyebrow">CalabriaVera</p>
        <h1 style={{ fontSize: "clamp(2rem,6vw,3.4rem)" }}>{mode === "login" ? copy.loginHero : copy.registerHero}</h1>
        <p className="muted">{mode === "login" ? "Accedi per gestire attività, messaggi e preferiti." : "Registrati gratuitamente. Ti invieremo una email per verificare il tuo indirizzo."}</p>

        {error ? <p role="alert" className="form-status danger">{error === "PASSWORD_MISMATCH" ? "Le password non coincidono." : error}</p> : null}
        {message ? <p role="status" className="form-status success">{message}</p> : null}

        <form onSubmit={submit} className="form-grid">
          {mode === "register" ? <>
            <label>{copy.first}<input name="firstName" autoComplete="given-name" maxLength={80} required /></label>
            <label>{copy.last}<input name="lastName" autoComplete="family-name" maxLength={80} required /></label>
          </> : null}
          <label className="full">Email<input name="email" type="email" autoComplete="email" maxLength={254} required /></label>
          <label className="full">Password<input name="password" type="password" minLength={mode === "register" ? 8 : undefined} autoComplete={mode === "login" ? "current-password" : "new-password"} required /></label>
          {mode === "register" ? <>
            <label className="full">Conferma password<input name="passwordConfirm" type="password" minLength={8} autoComplete="new-password" required /></label>
            <p className="full muted">Usa almeno 8 caratteri; scegli una password lunga e diversa da quelle degli altri siti.</p>
            <div className="full cv-consent-row">
              <input id="termsConsent" name="terms" type="checkbox" required />
              <label htmlFor="termsConsent">Accetto i <Link className="text-link" href={withLanguage("/termini", language)} target="_blank" rel="noopener">Termini</Link> e dichiaro di aver letto la <Link className="text-link" href={withLanguage("/privacy-policy", language)} target="_blank" rel="noopener">Privacy Policy</Link> e le <Link className="text-link" href={withLanguage("/note-legali", language)} target="_blank" rel="noopener">Note legali</Link>.</label>
            </div>
            <div className="full cv-consent-row"><input id="marketingConsent" name="marketing" type="checkbox" /><label htmlFor="marketingConsent">Accetto comunicazioni commerciali opzionali.</label></div>
          </> : null}
          <div className="full form-actions">
            <button disabled={busy} className="button button-primary" type="submit">{busy ? copy.wait : mode === "login" ? copy.login : copy.register}</button>
            <button type="button" disabled={busy} onClick={google} className="button cv-google-button"><span aria-hidden="true">G</span><span>{copy.google}</span></button>
          </div>
        </form>

        {mode === "login" ? <ResetPanel busy={busy} setBusy={setBusy} setError={setError} setMessage={setMessage} language={language} /> : null}
        <p className="muted">{mode === "register" ? "Hai già un account?" : "Non hai un account?"} <Link className="text-link" href={withLanguage(mode === "register" ? "/login" : "/registrazione", language)}>{mode === "register" ? copy.login : copy.register}</Link></p>
      </div>
    </section>
  );'''
s = s[:start] + return_block + s[end+len('\n  );'):]

# Inline reset UI matching main, with cooldown to avoid repeated mail sends.
helper = r'''

function ResetPanel({ busy, setBusy, setError, setMessage, language }: { busy: boolean; setBusy: (value: boolean) => void; setError: (value: string) => void; setMessage: (value: string) => void; language: Language }) {
  const [open, setOpen] = useState(false);
  const [lastReset, setLastReset] = useState(0);
  const submitReset = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (Date.now() - lastReset < 60_000) { setMessage("Attendi un minuto prima di richiedere un altro invio."); return; }
    const data = new FormData(event.currentTarget);
    setBusy(true); setError(""); setMessage("");
    try {
      await resetPassword(String(data.get("resetEmail") || ""));
      setLastReset(Date.now());
      setMessage("Se esiste un account con questa email, riceverai il link per reimpostare la password. Controlla anche lo spam.");
    } catch (cause) { setError(authErrorMessage(cause, language)); }
    finally { setBusy(false); }
  };
  return <>
    <button type="button" className="text-link" style={{ border: 0, background: "transparent", padding: 0, marginTop: "1rem" }} aria-expanded={open} onClick={() => setOpen((value) => !value)}>Password dimenticata?</button>
    {open ? <form className="stack" style={{ marginTop: "1rem" }} onSubmit={submitReset}><label>Email per il recupero<input type="email" name="resetEmail" autoComplete="email" required /></label><button disabled={busy} className="button button-secondary">Invia email di recupero</button></form> : null}
  </>;
}
'''
s += helper

# Remove obsolete prompt reset helper from the page component.
reset_start = s.find('  const reset = async () => {')
if reset_start >= 0:
    reset_end = s.find('\n\n  return (', reset_start)
    if reset_end >= 0:
        s = s[:reset_start] + s[reset_end+2:]

p.write_text(s, encoding='utf-8')
print('React auth main-parity patch applied')
