from pathlib import Path
p=Path('source/frontend-react/src/pages/DashboardPage.tsx')
s=p.read_text(encoding='utf-8')
s=s.replace('import { businessPath, specificCategory } from "../lib/businesses";','import { businessPath } from "../lib/businesses";')
s=s.replace('function number(value: unknown) { return Number(value || 0).toLocaleString("it-IT"); }','const LOCALES = { it: "it-IT", en: "en-GB", fr: "fr-FR", de: "de-DE", es: "es-ES" } as const;\nfunction number(value: unknown, language: keyof typeof LOCALES) { return Number(value || 0).toLocaleString(LOCALES[language]); }')
s=s.replace('<div className="stat-grid"><div className="stat"><div>Attività</div><strong>{number(items.length)}</strong></div><div className="stat"><div>Visualizzazioni</div><strong>{number(totals.views)}</strong></div><div className="stat"><div>Click contatti</div><strong>{number(totals.contacts)}</strong></div><div className="stat"><div>Messaggi ricevuti</div><strong>{number(totals.requests)}</strong></div></div>','<div className="stat-grid"><div className="stat"><div>Attività</div><strong>{number(items.length, language)}</strong></div><div className="stat"><div>Visualizzazioni</div><strong>{number(totals.views, language)}</strong></div><div className="stat"><div>Click contatti</div><strong>{number(totals.contacts, language)}</strong></div><div className="stat"><div>Messaggi ricevuti</div><strong>{number(totals.requests, language)}</strong></div></div>')
for old,new in [
('{specificCategory(business)}','{business.category || ""}'),
('{number(business.views)}','{number(business.views, language)}'),
('{number(business.phoneClicks)}','{number(business.phoneClicks, language)}'),
('{number(business.whatsappClicks)}','{number(business.whatsappClicks, language)}'),
('{number(business.websiteClicks)}','{number(business.websiteClicks, language)}'),
('{number(business.favoriteCount)}','{number(business.favoriteCount, language)}'),
('{number(business.requestCount)}','{number(business.requestCount, language)}'),
('{number(business.reviewCount)}','{number(business.reviewCount, language)}'),
('{number(contacts(business))}','{number(contacts(business), language)}'),
]:
    s=s.replace(old,new)
s=s.replace('{business.status === "approved" ? <Link className="button button-secondary" href={withLanguage(businessPath(business), language)}>Apri scheda</Link> : null}', '<Link className="button button-secondary" href={withLanguage(`/attivita?id=${encodeURIComponent(business.id)}`, language)}>Apri scheda</Link>')
s=s.replace('return <section className="section container">\n    <div className="section-heading">','return <section className="section container"><div id="dashboard-root">\n    <div className="section-heading">')
s=s.replace('  </section>;\n}', '  </div></section>;\n}')
if 'specificCategory' in s: raise SystemExit('specificCategory still present')
if 'id="dashboard-root"' not in s: raise SystemExit('dashboard root missing')
if 'business.status === "approved" ?' in s: raise SystemExit('conditional open link still present')
p.write_text(s,encoding='utf-8')
print('DASHBOARD_PARITY_PATCHED')
