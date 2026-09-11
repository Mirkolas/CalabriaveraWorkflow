from pathlib import Path

root = Path('source/frontend-react/src')

# Auth API: allow Google registration to persist the same consent metadata as main.
p = root / 'lib/auth.ts'
s = p.read_text(encoding='utf-8')
old = '''export async function loginGoogle() {\n  const { auth, sdk } = await authServices();\n  const provider = new sdk.GoogleAuthProvider();\n  provider.setCustomParameters({ prompt: "select_account" });\n  const result = await sdk.signInWithPopup(auth, provider);\n  await ensureUserDoc(result.user);\n  return requireActiveUser(result.user);\n}'''
new = '''export async function loginGoogle(extra: Record<string, unknown> = {}) {\n  const { auth, sdk } = await authServices();\n  const provider = new sdk.GoogleAuthProvider();\n  provider.setCustomParameters({ prompt: "select_account" });\n  const result = await sdk.signInWithPopup(auth, provider);\n  await ensureUserDoc(result.user, extra);\n  return requireActiveUser(result.user);\n}'''
if old not in s:
    raise SystemExit('loginGoogle marker missing')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

# Account API: owner/admin dashboard source parity.
p = root / 'lib/account.ts'
s = p.read_text(encoding='utf-8')
if 'export async function loadDashboardBusinesses()' not in s:
    s += r'''

export async function loadDashboardBusinesses() {
  const user = await requireUser();
  const token = await user.getIdTokenResult().catch(() => null);
  const admin = token?.claims.admin === true;
  const { db, firestore: f } = await services();
  const source = admin
    ? f.query(f.collection(db, "businesses"), f.orderBy("updatedAt", "desc"), f.limit(300))
    : f.query(f.collection(db, "businesses"), f.where("ownerId", "==", user.uid), f.limit(100));
  const snapshot = await f.getDocs(source);
  const items = snapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() }) as Business);
  if (!admin) items.sort((a, b) => {
    const time = (value: unknown) => value && typeof value === "object" && "toMillis" in value && typeof (value as { toMillis?: unknown }).toMillis === "function"
      ? Number((value as { toMillis: () => number }).toMillis())
      : new Date(String(value || 0)).getTime() || 0;
    return time(b.updatedAt) - time(a.updatedAt);
  });
  return { admin, items };
}
'''
p.write_text(s, encoding='utf-8')

# Auth page: reproduce main's one-card flow while preserving React navigation/Firebase behavior.
p = root / 'pages/AuthPage.tsx'
p.write_text(r'''import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import Link from "../components/Link";
import { authErrorMessage, loginEmail, loginGoogle, registerEmail, resetPassword } from "../lib/auth";
import { languageFromPath, withLanguage, type Language } from "../lib/language";
import { navigate } from "../lib/navigation";
import { setPageSeo } from "../lib/seo";

const COPY: Record<Language, Record<string, string>> = {
  it: { loginHero: "Bentornato", registerHero: "Crea il tuo account", loginText: "Accedi per gestire attività, messaggi e preferiti.", registerText: "Registrati gratuitamente. Ti invieremo una email per verificare il tuo indirizzo.", login: "Accedi", register: "Registrati", first: "Nome", last: "Cognome", wait: "Attendi…", google: "Continua con Google", existing: "Hai già un account?", newAccount: "Non hai un account?", signIn: "Accedi", signUp: "Registrati", created: "Account creato. Controlla la tua email per verificare l’indirizzo." },
  en: { loginHero: "Welcome back", registerHero: "Create your account", loginText: "Sign in to manage businesses, messages and favorites.", registerText: "Register for free. We will send you an email to verify your address.", login: "Sign in", register: "Sign up", first: "First name", last: "Last name", wait: "Please wait…", google: "Continue with Google", existing: "Already have an account?", newAccount: "Don't have an account?", signIn: "Sign in", signUp: "Sign up", created: "Account created. Check your email to verify the address." },
  fr: { loginHero: "Bon retour", registerHero: "Créez votre compte", loginText: "Connectez-vous pour gérer activités, messages et favoris.", registerText: "Inscrivez-vous gratuitement. Nous vous enverrons un e-mail pour vérifier votre adresse.", login: "Connexion", register: "S’inscrire", first: "Prénom", last: "Nom", wait: "Veuillez patienter…", google: "Continuer avec Google", existing: "Vous avez déjà un compte ?", newAccount: "Vous n’avez pas de compte ?", signIn: "Connexion", signUp: "S’inscrire", created: "Compte créé. Consultez votre e-mail pour vérifier l’adresse." },
  de: { loginHero: "Willkommen zurück", registerHero: "Konto erstellen", loginText: "Melde dich an, um Betriebe, Nachrichten und Favoriten zu verwalten.", registerText: "Registriere dich kostenlos. Wir senden dir eine E-Mail zur Bestätigung deiner Adresse.", login: "Anmelden", register: "Registrieren", first: "Vorname", last: "Nachname", wait: "Bitte warten…", google: "Mit Google fortfahren", existing: "Schon registriert?", newAccount: "Noch kein Konto?", signIn: "Anmelden", signUp: "Registrieren", created: "Konto erstellt. Prüfe deine E-Mail, um die Adresse zu bestätigen." },
  es: { loginHero: "Bienvenido de nuevo", registerHero: "Crea tu cuenta", loginText: "Accede para gestionar actividades, mensajes y favoritos.", registerText: "Regístrate gratis. Te enviaremos un correo para verificar tu dirección.", login: "Acceder", register: "Registrarse", first: "Nombre", last: "Apellidos", wait: "Espera…", google: "Continuar con Google", existing: "¿Ya tienes cuenta?", newAccount: "¿No tienes cuenta?", signIn: "Acceder", signUp: "Registrarse", created: "Cuenta creada. Revisa tu correo para verificar la dirección." },
};

const GOOGLE_ICON = <svg className="cv-google-icon" viewBox="0 0 18 18" aria-hidden="true"><path fill="#EA4335" d="M17.64 9.205c0-.638-.057-1.252-.164-1.841H9v3.482h4.844a4.14 4.14 0 0 1-1.797 2.715v2.258h2.909c1.702-1.567 2.684-3.875 2.684-6.614Z"/><path fill="#4285F4" d="M9 18c2.43 0 4.468-.806 5.956-2.181l-2.909-2.258c-.806.54-1.835.859-3.047.859-2.344 0-4.328-1.585-5.037-3.715H.956v2.332A9 9 0 0 0 9 18Z"/><path fill="#FBBC05" d="M3.963 10.705A5.42 5.42 0 0 1 3.682 9c0-.592.102-1.167.281-1.705V4.963H.956A9 9 0 0 0 0 9c0 1.452.347 2.827.956 4.037l3.007-2.332Z"/><path fill="#34A853" d="M9 3.58c1.321 0 2.507.454 3.441 1.346l2.581-2.581C13.464.892 11.426 0 9 0A9 9 0 0 0 .956 4.963l3.007 2.332C4.672 5.165 6.656 3.58 9 3.58Z"/></svg>;

function ResetPanel({ busy, language, onBusy, onError, onMessage }: { busy: boolean; language: Language; onBusy: (value: boolean) => void; onError: (value: string) => void; onMessage: (value: string) => void }) {
  const [open, setOpen] = useState(false);
  const [lastReset, setLastReset] = useState(0);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (Date.now() - lastReset < 60_000) { onMessage("Attendi un minuto prima di richiedere un altro invio."); return; }
    const email = String(new FormData(event.currentTarget).get("resetEmail") || "");
    onBusy(true); onError(""); onMessage("Invio…");
    try {
      await resetPassword(email);
      setLastReset(Date.now());
      onMessage("Se esiste un account con questa email, riceverai il link per reimpostare la password. Controlla anche lo spam.");
    } catch (cause) { onMessage(""); onError(authErrorMessage(cause, language)); }
    finally { onBusy(false); }
  };
  return <>
    <button type="button" className="text-link" style={{ border: 0, background: "transparent", padding: 0, marginTop: "1rem" }} aria-expanded={open} aria-controls="reset-form" onClick={() => setOpen((value) => !value)}>Password dimenticata?</button>
    {open ? <form id="reset-form" className="stack" style={{ marginTop: "1rem" }} onSubmit={submit}><label>Email per il recupero<input type="email" name="resetEmail" autoComplete="email" required /></label><button disabled={busy} className="button button-secondary">Invia email di recupero</button></form> : null}
  </>;
}

export default function AuthPage({ mode }: { mode: "login" | "register" }) {
  const language = languageFromPath();
  const copy = COPY[language];
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const nextParam = new URLSearchParams(location.search).get("next") || withLanguage("/", language);
  const next = nextParam.startsWith("/") && !nextParam.startsWith("//") ? nextParam : withLanguage("/", language);

  useEffect(() => {
    const title = mode === "login" ? copy.login : copy.register;
    setPageSeo({ title: `${title} | CalabriaVera`, description: mode === "login" ? copy.loginText : copy.registerText, path: mode === "login" ? "/login" : "/registrazione", robots: "noindex,follow" });
  }, [mode, language, copy.login, copy.register, copy.loginText, copy.registerText]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.reportValidity()) return;
    const data = new FormData(form);
    setBusy(true); setError(""); setMessage("");
    try {
      if (mode === "login") {
        await loginEmail(String(data.get("email") || ""), String(data.get("password") || ""));
        navigate(next, true);
      } else {
        const password = String(data.get("password") || "");
        if (password !== String(data.get("passwordConfirm") || "")) { setError("Le password non coincidono."); return; }
        await registerEmail({ email: String(data.get("email") || ""), password, firstName: String(data.get("firstName") || ""), lastName: String(data.get("lastName") || ""), termsConsent: data.get("termsConsent") === "on", marketingConsent: data.get("marketingConsent") === "on" });
        setMessage(copy.created); form.reset();
      }
    } catch (cause) { setError(authErrorMessage(cause, language)); }
    finally { setBusy(false); }
  };

  const google = async () => {
    const terms = document.querySelector<HTMLInputElement>('#termsConsent');
    if (mode === "register" && !terms?.checked) { setError("Accetta i Termini e leggi la Privacy prima di continuare."); return; }
    const marketing = document.querySelector<HTMLInputElement>('#marketingConsent');
    setBusy(true); setError(""); setMessage("");
    try {
      await loginGoogle(mode === "register" ? { marketingConsent: marketing?.checked === true, termsAcceptedAt: new Date().toISOString(), termsVersion: "2026-09-01" } : {});
      navigate(next, true);
    } catch (cause) { setError(authErrorMessage(cause, language)); }
    finally { setBusy(false); }
  };

  return <section className="auth-shell"><div className="card" style={{ maxWidth: 620, margin: "auto" }}>
    <p className="eyebrow">CalabriaVera</p>
    <h1 style={{ fontSize: "clamp(2rem,6vw,3.4rem)" }}>{mode === "register" ? copy.registerHero : copy.loginHero}</h1>
    <p className="muted">{mode === "register" ? copy.registerText : copy.loginText}</p>
    <form id="auth-form" className="form-grid" onSubmit={submit}>
      {mode === "register" ? <><label>{copy.first}<input name="firstName" required maxLength={80} autoComplete="given-name" /></label><label>{copy.last}<input name="lastName" required maxLength={80} autoComplete="family-name" /></label></> : null}
      <label className="full">Email<input type="email" name="email" required maxLength={254} autoComplete="email" /></label>
      <label className="full">Password<input type="password" name="password" required minLength={mode === "register" ? 8 : undefined} autoComplete={mode === "register" ? "new-password" : "current-password"} /></label>
      {mode === "register" ? <><label className="full">Conferma password<input type="password" name="passwordConfirm" required minLength={8} autoComplete="new-password" /></label><p className="full muted">Usa almeno 8 caratteri; scegli una password lunga e diversa da quelle degli altri siti.</p><div className="full cv-consent-row"><input id="termsConsent" type="checkbox" name="termsConsent" required /><label htmlFor="termsConsent">Accetto i <Link className="text-link" href={withLanguage("/termini", language)} target="_blank" rel="noopener">Termini</Link> e dichiaro di aver letto la <Link className="text-link" href={withLanguage("/privacy-policy", language)} target="_blank" rel="noopener">Privacy Policy</Link> e le <Link className="text-link" href={withLanguage("/note-legali", language)} target="_blank" rel="noopener">Note legali</Link>.</label></div><div className="full cv-consent-row"><input id="marketingConsent" type="checkbox" name="marketingConsent" /><label htmlFor="marketingConsent">Accetto comunicazioni commerciali opzionali.</label></div></> : null}
      <p className="full form-status" role="status" aria-live="polite">{error || message}</p>
      <div className="full form-actions"><button disabled={busy} className="button button-primary" type="submit">{busy ? copy.wait : mode === "register" ? copy.register : copy.login}</button><button type="button" disabled={busy} onClick={() => void google()} className="button cv-google-button">{GOOGLE_ICON}<span>{copy.google}</span></button></div>
    </form>
    {mode === "login" ? <ResetPanel busy={busy} language={language} onBusy={setBusy} onError={setError} onMessage={setMessage} /> : null}
    <p className="muted">{mode === "register" ? copy.existing : copy.newAccount} <Link className="text-link" href={withLanguage(mode === "register" ? "/login" : "/registrazione", language)}>{mode === "register" ? copy.signIn : copy.signUp}</Link></p>
  </div></section>;
}
''', encoding='utf-8')

# Dashboard: same owner/admin analytics and actions as the main implementation.
p = root / 'pages/DashboardPage.tsx'
p.write_text(r'''import { useEffect, useMemo, useState } from "react";
import Link from "../components/Link";
import { loadDashboardBusinesses } from "../lib/account";
import { deleteOwnBusiness } from "../lib/business-owner";
import { businessPath, specificCategory } from "../lib/businesses";
import { languageFromPath, localizedField, withLanguage } from "../lib/language";
import { navigate } from "../lib/navigation";
import { setPageSeo } from "../lib/seo";
import type { Business } from "../types";

function number(value: unknown) { return Number(value || 0).toLocaleString("it-IT"); }
function sum(items: Business[], key: string) { return items.reduce((total, item) => total + Number(item[key] || 0), 0); }
function contacts(item: Business) { return Number(item.phoneClicks || 0) + Number(item.whatsappClicks || 0) + Number(item.websiteClicks || 0); }
function statusLabel(status: unknown) { return ({ approved: "Pubblicata", pending: "In revisione", rejected: "Rifiutata", suspended: "Sospesa" } as Record<string, string>)[String(status || "")] || String(status || "Bozza"); }

export default function DashboardPage() {
  const language = languageFromPath();
  const [items, setItems] = useState<Business[] | null>(null);
  const [admin, setAdmin] = useState(false);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState("");

  useEffect(() => {
    setPageSeo({ title: "Dashboard | CalabriaVera", description: "Gestisci le attività e consulta le statistiche.", path: "/dashboard", robots: "noindex,nofollow" });
    let active = true;
    loadDashboardBusinesses().then(({ admin: isAdmin, items: rows }) => { if (active) { setAdmin(isAdmin); setItems(rows); } }).catch((cause) => {
      if (!active) return;
      if (cause instanceof Error && cause.message === "AUTH_REQUIRED") navigate(withLanguage("/login?next=/dashboard", language), true);
      else if (cause instanceof Error && cause.message === "ACCOUNT_SUSPENDED") navigate(withLanguage("/login?suspended=1", language), true);
      else { setItems([]); setError("Impossibile caricare la dashboard."); }
    });
    return () => { active = false; };
  }, [language]);

  const totals = useMemo(() => items ? { views: sum(items, "views"), contacts: items.reduce((total, item) => total + contacts(item), 0), requests: sum(items, "requestCount") } : null, [items]);

  const removeBusiness = async (business: Business) => {
    if (admin || deletingId || !window.confirm(`Eliminare definitivamente “${business.name || "questa attività"}”?`)) return;
    setDeletingId(business.id); setError("");
    try { await deleteOwnBusiness(business.id); setItems((current) => current ? current.filter((item) => item.id !== business.id) : current); }
    catch { setError("Impossibile eliminare l’attività."); }
    finally { setDeletingId(""); }
  };

  if (items === null) return <section className="section container"><div className="notice"><strong>CalabriaVera</strong><p>Caricamento della dashboard…</p></div></section>;

  return <section className="section container">
    <div className="section-heading"><div><p className="eyebrow">{admin ? "Area amministratore" : "Area proprietario"}</p><h1>{admin ? "Statistiche attività" : "Le tue attività"}</h1><p className="muted">{admin ? "Panoramica delle prestazioni delle attività presenti su CalabriaVera." : "Gestisci le tue schede e controlla come vengono consultate e contattate."}</p></div>{admin ? <Link className="button button-secondary" href="/admin/attivita">Gestisci attività</Link> : <Link className="button button-primary" href={withLanguage("/aggiungi-attivita", language)}>Aggiungi attività</Link>}</div>
    {error ? <div className="notice"><strong>{error}</strong></div> : null}
    {items.length && totals ? <><div className="stat-grid"><div className="stat"><div>Attività</div><strong>{number(items.length)}</strong></div><div className="stat"><div>Visualizzazioni</div><strong>{number(totals.views)}</strong></div><div className="stat"><div>Click contatti</div><strong>{number(totals.contacts)}</strong></div><div className="stat"><div>Messaggi ricevuti</div><strong>{number(totals.requests)}</strong></div></div>
      <div className="result-list cv-analytics-list" style={{ marginTop: "2rem" }}>{items.map((business) => { const name = localizedField<string>(business, "name", language) || business.name || "Attività"; return <article key={business.id} className="card cv-analytics-card"><div className="meta-row"><span>{specificCategory(business)}</span><span>·</span><span>{business.comune || ""}</span><span className={`badge status-${business.status || ""}`}>{statusLabel(business.status)}</span>{business.verified ? <span className="badge badge-verified">Verificata</span> : null}</div><h3>{name}</h3><div className="cv-analytics-grid"><div><span>Visualizzazioni</span><strong>{number(business.views)}</strong></div><div><span>Telefono</span><strong>{number(business.phoneClicks)}</strong></div><div><span>WhatsApp</span><strong>{number(business.whatsappClicks)}</strong></div><div><span>Sito web</span><strong>{number(business.websiteClicks)}</strong></div><div><span>Preferiti ricevuti</span><strong>{number(business.favoriteCount)}</strong></div><div><span>Messaggi ricevuti</span><strong>{number(business.requestCount)}</strong></div><div><span>Recensioni</span><strong>{number(business.reviewCount)}</strong></div><div><span>Click contatti</span><strong>{number(contacts(business))}</strong></div></div><div className="business-actions" style={{ marginTop: "1rem" }}>{business.status === "approved" ? <Link className="button button-secondary" href={withLanguage(businessPath(business), language)}>Apri scheda</Link> : null}{admin ? <Link className="button button-secondary" href="/admin/attivita">Gestisci</Link> : <><Link className="button button-secondary" href={withLanguage(`/aggiungi-attivita?id=${encodeURIComponent(business.id)}`, language)}>Modifica</Link><button className="button button-secondary danger" type="button" disabled={Boolean(deletingId)} onClick={() => void removeBusiness(business)}>{deletingId === business.id ? "Eliminazione…" : "Elimina"}</button></>}</div></article>; })}</div></> : <div className="empty-state"><p className="eyebrow">{admin ? "Statistiche" : "Inizia da qui"}</p><h2>{admin ? "Nessuna attività disponibile" : "Nessuna attività associata"}</h2><p>{admin ? "Non ci sono ancora attività da mostrare." : "Inserisci gratuitamente la prima attività. Potrai modificarla dalla dashboard mentre attende la moderazione."}</p>{admin ? null : <Link className="button button-primary" href={withLanguage("/aggiungi-attivita", language)}>Aggiungi la tua attività</Link>}</div>}
  </section>;
}
''', encoding='utf-8')

print('Auth and dashboard parity patch applied')
