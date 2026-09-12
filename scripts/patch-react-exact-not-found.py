from pathlib import Path

p = Path('frontend-react/src/App.tsx')
s = p.read_text()
old = '''function NotFoundPage() {
  const language = languageFromPath();
  const labels = {
    it: ["Pagina non trovata", "La pagina richiesta non esiste o è stata spostata.", "Torna alla home"],
    en: ["Page not found", "The requested page does not exist or has been moved.", "Back to home"],
    fr: ["Page introuvable", "La page demandée n’existe pas ou a été déplacée.", "Retour à l’accueil"],
    de: ["Seite nicht gefunden", "Die angeforderte Seite existiert nicht oder wurde verschoben.", "Zur Startseite"],
    es: ["Página no encontrada", "La página solicitada no existe o se ha movido.", "Volver al inicio"],
  }[language];
  return <section className="container cv-not-found"><span>404</span><h1>{labels[0]}</h1><p>{labels[1]}</p><Link href={withLanguage("/", language)} className="cv-btn cv-btn--gold">{labels[2]}</Link></section>;
}
'''
new = '''function NotFoundPage() {
  const language = languageFromPath();
  return <section className="section container"><p className="eyebrow">CalabriaVera</p><h1>Pagina non trovata</h1><div className="prose"><p>La pagina richiesta non è disponibile o è stata spostata.</p><div className="form-actions"><Link className="button button-primary" href={withLanguage("/", language)}>Torna alla home</Link><Link className="button button-secondary" href={withLanguage("/catalogo", language)}>Apri il catalogo</Link></div></div></section>;
}
'''
if old not in s:
    raise SystemExit('React not-found block changed')
s = s.replace(old, new, 1)
p.write_text(s)
