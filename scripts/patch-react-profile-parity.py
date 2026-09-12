from pathlib import Path

ROOT = Path('source')
profile = ROOT / 'frontend-react/src/pages/ProfilePage.tsx'
account = ROOT / 'frontend-react/src/lib/account.ts'

profile.write_text(r'''import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { changeAccountPassword, loadProfile, resendVerificationEmail, saveProfile, saveProfileAvatar } from "../lib/account";
import { logout, refreshVerification } from "../lib/auth";
import { languageFromPath, withLanguage, type Language } from "../lib/language";
import { navigate } from "../lib/navigation";
import { setPageSeo } from "../lib/seo";

type Profile = Awaited<ReturnType<typeof loadProfile>>;

type Copy = {
  pageTitle: string; profileTitle: string; personal: string; first: string; last: string; phone: string; marketing: string;
  save: string; saving: string; saved: string; loadError: string; saveError: string;
  avatar: string; avatarHint: string; avatarBusy: string; avatarSaved: string; avatarError: string; upload: string; editAvatar: string;
  security: string; currentPassword: string; newPassword: string; confirmPassword: string; changePassword: string; changingPassword: string;
  passwordSaved: string; passwordMismatch: string; passwordError: string; googleSecurity: string; googleLink: string;
  role: string; verification: string; verified: string; unverified: string; verifyHelp: string; resend: string; check: string;
  verificationDone: string; verificationPending: string; verificationSent: string; verificationAlready: string;
  continue: string; favorites: string; messages: string; admin: string; logout: string;
};

const COPY: Record<Language, Copy> = {
  it: { pageTitle:"Profilo", profileTitle:"Il tuo profilo", personal:"Dati personali", first:"Nome", last:"Cognome", phone:"Telefono", marketing:"Accetto comunicazioni commerciali opzionali.", save:"Salva profilo", saving:"Salvataggio…", saved:"Profilo aggiornato.", loadError:"L’account è attivo, ma il profilo non è disponibile. Ricarica per riprovare.", saveError:"Non è stato possibile salvare le modifiche.", avatar:"Immagine profilo", avatarHint:"JPG, PNG o WebP", avatarBusy:"Ottimizzazione immagine…", avatarSaved:"Immagine profilo aggiornata.", avatarError:"Impossibile aggiornare l’immagine profilo.", upload:"Carica foto", editAvatar:"Modifica immagine profilo", security:"Sicurezza", currentPassword:"Password attuale", newPassword:"Nuova password", confirmPassword:"Conferma nuova password", changePassword:"Cambia password", changingPassword:"Aggiornamento…", passwordSaved:"Password aggiornata.", passwordMismatch:"Le nuove password non coincidono.", passwordError:"Password non aggiornata. Controlla la password attuale e riprova.", googleSecurity:"Hai effettuato l’accesso con Google. Gestisci la password nelle impostazioni del tuo account Google.", googleLink:"Sicurezza account Google", role:"Ruolo", verification:"Verifica email", verified:"Email verificata", unverified:"Da verificare", verifyHelp:"Apri il link ricevuto via email, poi premi “Ho verificato l’email”.", resend:"Reinvia email di verifica", check:"Ho verificato l’email", verificationDone:"Verifica completata.", verificationPending:"Email non ancora verificata.", verificationSent:"Email inviata. Controlla anche lo spam.", verificationAlready:"L’indirizzo email risulta già verificato.", continue:"Continua", favorites:"I miei preferiti", messages:"I miei messaggi", admin:"Amministrazione", logout:"Esci dall’account" },
  en: { pageTitle:"Profile", profileTitle:"Your profile", personal:"Personal details", first:"First name", last:"Last name", phone:"Phone", marketing:"I agree to optional commercial communications.", save:"Save profile", saving:"Saving…", saved:"Profile updated.", loadError:"Your account is active, but the profile is unavailable. Reload to try again.", saveError:"Changes could not be saved.", avatar:"Profile picture", avatarHint:"JPG, PNG or WebP", avatarBusy:"Optimizing image…", avatarSaved:"Profile picture updated.", avatarError:"Unable to update the profile picture.", upload:"Upload photo", editAvatar:"Edit profile picture", security:"Security", currentPassword:"Current password", newPassword:"New password", confirmPassword:"Confirm new password", changePassword:"Change password", changingPassword:"Updating…", passwordSaved:"Password updated.", passwordMismatch:"The new passwords do not match.", passwordError:"Password not updated. Check your current password and try again.", googleSecurity:"You signed in with Google. Manage the password in your Google Account settings.", googleLink:"Google Account security", role:"Role", verification:"Email verification", verified:"Email verified", unverified:"To verify", verifyHelp:"Open the link received by email, then press “I verified my email”.", resend:"Resend verification email", check:"I verified my email", verificationDone:"Verification complete.", verificationPending:"Email is not verified yet.", verificationSent:"Email sent. Check your spam folder too.", verificationAlready:"Your email address is already verified.", continue:"Continue", favorites:"My favorites", messages:"My messages", admin:"Administration", logout:"Sign out" },
  fr: { pageTitle:"Profil", profileTitle:"Votre profil", personal:"Données personnelles", first:"Prénom", last:"Nom", phone:"Téléphone", marketing:"J’accepte les communications commerciales facultatives.", save:"Enregistrer le profil", saving:"Enregistrement…", saved:"Profil mis à jour.", loadError:"Le compte est actif, mais le profil est indisponible. Rechargez pour réessayer.", saveError:"Impossible d’enregistrer les modifications.", avatar:"Photo de profil", avatarHint:"JPG, PNG ou WebP", avatarBusy:"Optimisation de l’image…", avatarSaved:"Photo de profil mise à jour.", avatarError:"Impossible de mettre à jour la photo de profil.", upload:"Charger une photo", editAvatar:"Modifier la photo de profil", security:"Sécurité", currentPassword:"Mot de passe actuel", newPassword:"Nouveau mot de passe", confirmPassword:"Confirmer le nouveau mot de passe", changePassword:"Changer le mot de passe", changingPassword:"Mise à jour…", passwordSaved:"Mot de passe mis à jour.", passwordMismatch:"Les nouveaux mots de passe ne correspondent pas.", passwordError:"Mot de passe non modifié. Vérifiez le mot de passe actuel.", googleSecurity:"Vous êtes connecté avec Google. Gérez le mot de passe dans les paramètres de votre compte Google.", googleLink:"Sécurité du compte Google", role:"Rôle", verification:"Vérification e-mail", verified:"E-mail vérifié", unverified:"À vérifier", verifyHelp:"Ouvrez le lien reçu par e-mail, puis confirmez la vérification.", resend:"Renvoyer l’e-mail de vérification", check:"J’ai vérifié l’e-mail", verificationDone:"Vérification terminée.", verificationPending:"E-mail pas encore vérifié.", verificationSent:"E-mail envoyé. Vérifiez aussi les spams.", verificationAlready:"Votre adresse e-mail est déjà vérifiée.", continue:"Continuer", favorites:"Mes favoris", messages:"Mes messages", admin:"Administration", logout:"Se déconnecter" },
  de: { pageTitle:"Profil", profileTitle:"Dein Profil", personal:"Persönliche Daten", first:"Vorname", last:"Nachname", phone:"Telefon", marketing:"Ich stimme optionalen kommerziellen Mitteilungen zu.", save:"Profil speichern", saving:"Speichern…", saved:"Profil aktualisiert.", loadError:"Das Konto ist aktiv, aber das Profil ist nicht verfügbar. Lade neu und versuche es erneut.", saveError:"Änderungen konnten nicht gespeichert werden.", avatar:"Profilbild", avatarHint:"JPG, PNG oder WebP", avatarBusy:"Bild wird optimiert…", avatarSaved:"Profilbild aktualisiert.", avatarError:"Profilbild konnte nicht aktualisiert werden.", upload:"Foto hochladen", editAvatar:"Profilbild bearbeiten", security:"Sicherheit", currentPassword:"Aktuelles Passwort", newPassword:"Neues Passwort", confirmPassword:"Neues Passwort bestätigen", changePassword:"Passwort ändern", changingPassword:"Aktualisieren…", passwordSaved:"Passwort aktualisiert.", passwordMismatch:"Die neuen Passwörter stimmen nicht überein.", passwordError:"Passwort nicht aktualisiert. Prüfe das aktuelle Passwort.", googleSecurity:"Du hast dich mit Google angemeldet. Verwalte das Passwort in deinem Google-Konto.", googleLink:"Google-Konto Sicherheit", role:"Rolle", verification:"E-Mail-Bestätigung", verified:"E-Mail bestätigt", unverified:"Zu bestätigen", verifyHelp:"Öffne den Link aus der E-Mail und bestätige danach die Verifizierung.", resend:"Bestätigungs-E-Mail erneut senden", check:"E-Mail ist bestätigt", verificationDone:"Bestätigung abgeschlossen.", verificationPending:"E-Mail noch nicht bestätigt.", verificationSent:"E-Mail gesendet. Prüfe auch den Spam-Ordner.", verificationAlready:"Deine E-Mail-Adresse ist bereits bestätigt.", continue:"Weiter", favorites:"Meine Favoriten", messages:"Meine Nachrichten", admin:"Administration", logout:"Abmelden" },
  es: { pageTitle:"Perfil", profileTitle:"Tu perfil", personal:"Datos personales", first:"Nombre", last:"Apellidos", phone:"Teléfono", marketing:"Acepto comunicaciones comerciales opcionales.", save:"Guardar perfil", saving:"Guardando…", saved:"Perfil actualizado.", loadError:"La cuenta está activa, pero el perfil no está disponible. Recarga para intentarlo de nuevo.", saveError:"No se pudieron guardar los cambios.", avatar:"Foto de perfil", avatarHint:"JPG, PNG o WebP", avatarBusy:"Optimizando imagen…", avatarSaved:"Foto de perfil actualizada.", avatarError:"No se pudo actualizar la foto de perfil.", upload:"Subir foto", editAvatar:"Editar foto de perfil", security:"Seguridad", currentPassword:"Contraseña actual", newPassword:"Nueva contraseña", confirmPassword:"Confirmar nueva contraseña", changePassword:"Cambiar contraseña", changingPassword:"Actualizando…", passwordSaved:"Contraseña actualizada.", passwordMismatch:"Las nuevas contraseñas no coinciden.", passwordError:"No se pudo actualizar la contraseña. Comprueba la contraseña actual.", googleSecurity:"Has iniciado sesión con Google. Gestiona la contraseña desde la configuración de tu cuenta Google.", googleLink:"Seguridad de la cuenta Google", role:"Rol", verification:"Verificación del correo", verified:"Correo verificado", unverified:"Por verificar", verifyHelp:"Abre el enlace recibido por correo y después confirma la verificación.", resend:"Reenviar correo de verificación", check:"He verificado el correo", verificationDone:"Verificación completada.", verificationPending:"El correo todavía no está verificado.", verificationSent:"Correo enviado. Revisa también el spam.", verificationAlready:"Tu dirección de correo ya está verificada.", continue:"Continuar", favorites:"Mis favoritos", messages:"Mis mensajes", admin:"Administración", logout:"Cerrar sesión" },
};

export default function ProfilePage() {
  const language = languageFromPath();
  const copy = COPY[language];
  const [profile, setProfile] = useState<Profile | null>(null);
  const [busy, setBusy] = useState(false);
  const [avatarBusy, setAvatarBusy] = useState(false);
  const [passwordBusy, setPasswordBusy] = useState(false);
  const [verificationBusy, setVerificationBusy] = useState(false);
  const [avatarMenuOpen, setAvatarMenuOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const avatarInput = useRef<HTMLInputElement | null>(null);

  const refresh = async () => { const value = await loadProfile(); setProfile(value); return value; };

  useEffect(() => {
    setPageSeo({ title: `${copy.pageTitle} | CalabriaVera`, description: copy.profileTitle, path: "/profilo", robots: "noindex,nofollow" });
    let active = true;
    loadProfile().then((value) => { if (active) setProfile(value); }).catch((cause) => {
      if (!active) return;
      if (cause instanceof Error && cause.message === "AUTH_REQUIRED") navigate(withLanguage("/login?next=/profilo", language), true);
      else if (cause instanceof Error && cause.message === "ACCOUNT_SUSPENDED") navigate(withLanguage("/login?suspended=1", language), true);
      else setError(copy.loadError);
    });
    return () => { active = false; };
  }, [language, copy.pageTitle, copy.profileTitle, copy.loadError]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); setBusy(true); setMessage(""); setError("");
    const data = new FormData(event.currentTarget);
    try {
      await saveProfile({ firstName:String(data.get("firstName")||""), lastName:String(data.get("lastName")||""), phone:String(data.get("phone")||""), marketingConsent:data.get("marketingConsent")==="on" });
      await refresh(); setMessage(copy.saved);
    } catch { setError(copy.saveError); } finally { setBusy(false); }
  };

  const avatar = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]; event.target.value=""; if (!file) return;
    setAvatarMenuOpen(false); setAvatarBusy(true); setMessage(copy.avatarBusy); setError("");
    try { await saveProfileAvatar(file); await refresh(); setMessage(copy.avatarSaved); }
    catch { setMessage(""); setError(copy.avatarError); } finally { setAvatarBusy(false); }
  };

  const changePassword = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const form=event.currentTarget; const data=new FormData(form);
    const current=String(data.get("currentPassword")||""); const next=String(data.get("newPassword")||""); const confirm=String(data.get("confirmPassword")||"");
    setMessage(""); setError(""); if(next!==confirm){setError(copy.passwordMismatch);return;} setPasswordBusy(true);
    try{await changeAccountPassword(current,next);form.reset();setMessage(copy.passwordSaved);}catch{setError(copy.passwordError);}finally{setPasswordBusy(false);}
  };

  const resend = async () => {
    setBusy(true); setMessage(""); setError("");
    try { const sent=await resendVerificationEmail(); const latest=await refresh(); setMessage(sent?copy.verificationSent:latest.emailVerified?copy.verificationAlready:copy.verificationSent); }
    catch { setError(copy.saveError); } finally { setBusy(false); }
  };

  const checkVerification = async () => {
    setVerificationBusy(true); setMessage(""); setError("");
    try { const user=await refreshVerification(); await refresh(); setMessage(user.emailVerified?copy.verificationDone:copy.verificationPending); }
    catch { setError(copy.saveError); } finally { setVerificationBusy(false); }
  };

  const params = new URLSearchParams(location.search);
  const requestedNext=params.get("next")||withLanguage("/dashboard",language);
  const next=requestedNext.startsWith("/")&&!requestedNext.startsWith("//")?requestedNext:withLanguage("/dashboard",language);
  const avatarUrl=profile?String(profile.avatarDataUrl||""):"";
  const initials=profile?String(profile.firstName||profile.displayName||profile.email||"U").trim().charAt(0).toUpperCase()||"U":"U";

  return <section className="section container">
    <p className="eyebrow">CalabriaVera</p><h1>{copy.pageTitle}</h1>
    <div id="profile-root">
      {!profile&&!error?<p role="status">Caricamento profilo…</p>:null}
      {params.has("created")?<div className="notice" role="status"><strong>Account creato.</strong><p>{params.get("verification")==="failed"?"L’email di verifica non è stata inviata. Usa il pulsante Reinvia email.":"Ti abbiamo inviato una email di verifica. Controlla anche lo spam."}</p></div>:null}
      {error?<div className="notice" role="alert">{error}</div>:null}
      {message?<div className="notice" role="status">{message}</div>:null}
      {profile?<div className="grid-2"><div className="stack">
        <div className="card"><p className="eyebrow">{copy.personal}</p><h2>{copy.profileTitle}</h2>
          <div className="cv-profile-avatar-editor">
            <div className="cv-avatar-shell">
              <span className="cv-profile-avatar" id="profile-avatar-preview">{avatarUrl?<img src={avatarUrl} alt={copy.avatar}/>:initials}</span>
              <button type="button" className="cv-avatar-pencil" disabled={avatarBusy} aria-label={copy.editAvatar} aria-expanded={avatarMenuOpen} aria-controls="cv-avatar-menu" onClick={()=>setAvatarMenuOpen(v=>!v)}><svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="m16 3 5 5-12 12-6 1 1-6Z"/><path d="m14 5 5 5M4 15l5 5"/></svg></button>
              <div className="cv-avatar-menu" id="cv-avatar-menu" hidden={!avatarMenuOpen}><button type="button" onClick={()=>avatarInput.current?.click()}>{copy.upload}</button></div>
            </div>
            <label className="cv-avatar-original-input">{copy.avatar}<span className="muted small">{copy.avatarHint}</span><input ref={avatarInput} id="profile-avatar-file" type="file" accept="image/jpeg,image/png,image/webp" disabled={avatarBusy} onChange={avatar}/></label>
          </div>
          <p id="avatar-status" className="muted" role="status">{avatarBusy?copy.avatarBusy:""}</p>
          <form id="profile-form" className="form-grid" onSubmit={submit}><fieldset className="full form-grid" style={{border:0,padding:0,margin:0}} disabled={busy}>
            <label>{copy.first}<input name="firstName" maxLength={80} defaultValue={String(profile.firstName||"")}/></label>
            <label>{copy.last}<input name="lastName" maxLength={80} defaultValue={String(profile.lastName||"")}/></label>
            <label>{copy.phone}<input name="phone" type="tel" maxLength={40} defaultValue={String(profile.phone||"")}/></label>
            <label>Email<input disabled value={profile.email}/></label>
            <label className="full"><span><input type="checkbox" name="marketingConsent" defaultChecked={profile.marketingConsent===true}/> {copy.marketing}</span></label>
            <div className="full form-actions"><button className="button button-primary" disabled={busy||avatarBusy}>{busy?copy.saving:copy.save}</button></div>
          </fieldset></form>
        </div>
        <div className="card"><h2>{copy.security}</h2>{profile.passwordAccount?<form id="password-form" className="stack" onSubmit={changePassword}>
          <label>{copy.currentPassword}<input name="currentPassword" type="password" autoComplete="current-password" required/></label>
          <label>{copy.newPassword}<input name="newPassword" type="password" minLength={8} autoComplete="new-password" required/></label>
          <label>{copy.confirmPassword}<input name="confirmPassword" type="password" minLength={8} autoComplete="new-password" required/></label>
          <button className="button button-primary" disabled={passwordBusy}>{passwordBusy?copy.changingPassword:copy.changePassword}</button>
        </form>:<><p>{copy.googleSecurity}</p><a className="text-link" href="https://myaccount.google.com/security" target="_blank" rel="noopener noreferrer">{copy.googleLink}</a></>}</div>
      </div>
      <aside className="card"><p className="eyebrow">Account</p><h2>{String(profile.displayName||profile.email||"Account")}</h2><div className="stack">
        <div><span className="muted">{copy.role}</span><br/><strong>{String(profile.roleLabel||"Utente")}</strong></div>
        <div><span className="muted">{copy.verification}</span><br/><strong id="verification-state">{profile.emailVerified?copy.verified:copy.unverified}</strong></div>
        {!profile.emailVerified?<div id="verification-controls" className="stack"><p>{copy.verifyHelp}</p><button type="button" className="button button-secondary" disabled={busy||verificationBusy} onClick={()=>void resend()}>{copy.resend}</button><button type="button" className="button button-primary" disabled={verificationBusy} onClick={()=>void checkVerification()}>{copy.check}</button></div>:null}
        {profile.emailVerified?<button type="button" className="button button-primary" onClick={()=>navigate(next)}>{copy.continue}</button>:null}
        <button type="button" className="button button-secondary" onClick={()=>navigate(withLanguage("/preferiti",language))}>{copy.favorites}</button>
        <button type="button" className="button button-secondary" onClick={()=>navigate(withLanguage("/messaggi",language))}>{copy.messages}</button>
        {profile.isAdmin?<button type="button" className="button button-secondary" onClick={()=>navigate("/admin")}>{copy.admin}</button>:null}
        <button type="button" className="button button-secondary" onClick={async()=>{await logout();navigate(withLanguage("/",language),true);}}>{copy.logout}</button>
      </div></aside></div>:null}
    </div>
  </section>;
}
''', encoding='utf-8')

text = account.read_text(encoding='utf-8')
old = 'import { auditEvent, currentUser, queueUserEmailEvent, requireActiveUser } from "./auth";'
new = 'import { auditEvent, currentUser, ensureUserDoc, queueUserEmailEvent, requireActiveUser } from "./auth";'
if old not in text:
    raise SystemExit('account auth import marker missing')
text = text.replace(old, new, 1)
old = '  const user = await requireUser();\n  await user.reload().catch(() => undefined);\n  const { db, firestore: f } = await services();'
new = '  const user = await requireUser();\n  await user.reload().catch(() => undefined);\n  await ensureUserDoc(user);\n  const { db, firestore: f } = await services();'
if old not in text:
    raise SystemExit('loadProfile marker missing')
text = text.replace(old, new, 1)
account.write_text(text, encoding='utf-8')
print('PROFILE_PARITY_PATCHED')
