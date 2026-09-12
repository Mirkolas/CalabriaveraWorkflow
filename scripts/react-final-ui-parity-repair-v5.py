from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: react-final-ui-parity-repair-v5.py <private-repo-root>")

root = Path(sys.argv[1]).resolve()

# Catalog: restore exact final pre-React labels/placeholders.
p = root / "frontend-react/src/pages/CatalogPage.tsx"
s = p.read_text()
marker = "const PAGE_SIZE = 18;\n"
insert = '''const PAGE_SIZE = 18;
const LEGACY_CATALOG_SEARCH: Record<Language, string> = {
  it: "Cosa stai cercando", en: "What are you looking for", fr: "Que cherchez-vous", de: "Wonach suchst du", es: "Qué buscas",
};
const LEGACY_CATALOG_ALL: Record<Language, string> = {
  it: "Tutti", en: "All", fr: "Tous", de: "Alle", es: "Todos",
};
'''
if "LEGACY_CATALOG_SEARCH" not in s:
    if marker not in s:
        raise SystemExit("Catalog constants insertion point missing")
    s = s.replace(marker, insert, 1)
s = s.replace('placeholder={uiText("searchWhatHint",language)}', 'placeholder={LEGACY_CATALOG_SEARCH[language]}')
s = s.replace('<option value="">{uiText("all",language)}</option>{categoryOptions.map', '<option value="">{LEGACY_CATALOG_ALL[language]}</option>{categoryOptions.map')
s = s.replace('<option value="">{uiText("all",language)}</option>{PROVINCES.map', '<option value="">{LEGACY_CATALOG_ALL[language]}</option>{PROVINCES.map')
s = s.replace('<option value="">{uiText("allCities",language)}</option>{cities.map', '<option value="">{LEGACY_CATALOG_ALL[language]}</option>{cities.map')
p.write_text(s)

# Styles: remove React-only catalog shift and include the exact legacy blog tab CSS.
p = root / "frontend-react/src/styles.css"
s = p.read_text()
s = s.replace('body[data-page="catalog"] .cv-smart-hint{font-size:10px;line-height:1.45;color:#607080;margin-top:-5px}', '')
marker = "/* cv-blog-tabs-legacy-parity */"
if marker not in s:
    s += '''\n\n/* cv-blog-tabs-legacy-parity */
body[data-page="blog"] .cv-blog-tabs{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 1.4rem;padding:6px;border:1px solid rgba(0,52,91,.12);border-radius:14px;background:#f5f8fa;width:max-content;max-width:100%}
body[data-page="blog"] .cv-blog-tab{appearance:none;border:0;border-radius:10px;padding:.72rem 1rem;background:transparent;color:#00345b;font-weight:800;line-height:1.15;cursor:pointer}
body[data-page="blog"] .cv-blog-tab:hover,body[data-page="blog"] .cv-blog-tab:focus-visible{background:#e8f0f5;outline:none}
body[data-page="blog"] .cv-blog-tab.is-active{background:#00345b;color:#fff;box-shadow:0 4px 14px rgba(0,52,91,.18)}
@media(max-width:560px){body[data-page="blog"] .cv-blog-tabs{display:grid;grid-template-columns:1fr 1fr;width:100%;gap:6px}body[data-page="blog"] .cv-blog-tab{padding:.68rem .55rem;font-size:.9rem}}
'''
p.write_text(s)

# Blog: CSS is bundled in React, so remove the broken runtime request for a file not copied to public/.
p = root / "frontend-react/src/pages/MagazinePage.tsx"
s = p.read_text()
block = '''  useEffect(() => {
    if (document.querySelector('link[data-cv-blog-sections]')) return;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/assets/css/blog-sections.css?v=20260905-2";
    link.dataset.cvBlogSections = "";
    document.head.appendChild(link);
  }, []);

'''
if block in s:
    s = s.replace(block, "", 1)
p.write_text(s)

# Legal pages: reproduce the final assets/js/legal-identity.js DOM transformation.
p = root / "frontend-react/src/pages/LegalPage.tsx"
p.write_text('''import { useEffect, useRef } from "react";
import { LEGAL_CONTENT } from "../generated/legal-content";
import { languageFromPath, type Language } from "../lib/language";
import { setPageSeo } from "../lib/seo";

type Kind = keyof typeof LEGAL_CONTENT;
type Identity = { heading: string; text: string };

const LEGAL_IDENTITY: Record<Language, Identity> = {
  it: { heading: "Titolare del sito e del trattamento", text: 'Il titolare del sito CalabriaVera e del trattamento dei dati personali è <strong>Mirko Sonotaca</strong>, con località di riferimento <strong>Marina di Gioiosa Ionica (RC), Italia</strong>, codice fiscale <strong>SNTMRK03C29D976R</strong>. Per comunicazioni, richieste privacy, rettifiche o segnalazioni è disponibile l’indirizzo <a href="mailto:info.calabriavera@gmail.com">info.calabriavera@gmail.com</a> e il numero <a href="tel:+393479975255">+39 347 997 5255</a>.' },
  en: { heading: "Website operator and data controller", text: 'The operator of the CalabriaVera website and the controller of personal data is <strong>Mirko Sonotaca</strong>, based in <strong>Marina di Gioiosa Ionica (RC), Italy</strong>, Italian tax code <strong>SNTMRK03C29D976R</strong>. For communications, privacy requests, corrections or reports, contact <a href="mailto:info.calabriavera@gmail.com">info.calabriavera@gmail.com</a> or <a href="tel:+393479975255">+39 347 997 5255</a>.' },
  fr: { heading: "Titulaire du site et responsable du traitement", text: 'Le titulaire du site CalabriaVera et responsable du traitement des données personnelles est <strong>Mirko Sonotaca</strong>, établi à <strong>Marina di Gioiosa Ionica (RC), Italie</strong>, code fiscal italien <strong>SNTMRK03C29D976R</strong>. Pour toute communication, demande relative à la vie privée, rectification ou signalement : <a href="mailto:info.calabriavera@gmail.com">info.calabriavera@gmail.com</a> ou <a href="tel:+393479975255">+39 347 997 5255</a>.' },
  de: { heading: "Websitebetreiber und Verantwortlicher für die Datenverarbeitung", text: 'Betreiber der Website CalabriaVera und Verantwortlicher für die Verarbeitung personenbezogener Daten ist <strong>Mirko Sonotaca</strong> mit Sitz in <strong>Marina di Gioiosa Ionica (RC), Italien</strong>, italienische Steuernummer <strong>SNTMRK03C29D976R</strong>. Für Mitteilungen, Datenschutzanfragen, Berichtigungen oder Meldungen: <a href="mailto:info.calabriavera@gmail.com">info.calabriavera@gmail.com</a> oder <a href="tel:+393479975255">+39 347 997 5255</a>.' },
  es: { heading: "Titular del sitio y responsable del tratamiento", text: 'El titular del sitio CalabriaVera y responsable del tratamiento de los datos personales es <strong>Mirko Sonotaca</strong>, con sede en <strong>Marina di Gioiosa Ionica (RC), Italia</strong>, código fiscal italiano <strong>SNTMRK03C29D976R</strong>. Para comunicaciones, solicitudes de privacidad, rectificaciones o avisos: <a href="mailto:info.calabriavera@gmail.com">info.calabriavera@gmail.com</a> o <a href="tel:+393479975255">+39 347 997 5255</a>.' },
};

export default function LegalPage({ kind }: { kind: Kind }) {
  const page = LEGAL_CONTENT[kind];
  const rootRef = useRef<HTMLDivElement>(null);
  const language = languageFromPath();

  useEffect(() => {
    setPageSeo({ title: page.title || "CalabriaVera", description: page.description || "CalabriaVera", path: location.pathname, robots: "index,follow" });
  }, [kind, page.title, page.description]);

  useEffect(() => {
    const prose = rootRef.current?.querySelector<HTMLElement>(".legal-page .legal-prose");
    if (!prose) return;
    const data = LEGAL_IDENTITY[language] || LEGAL_IDENTITY.it;
    if (kind === "privacy") {
      const firstHeading = prose.querySelector<HTMLHeadingElement>("h2");
      const firstParagraph = firstHeading?.nextElementSibling;
      if (firstHeading) firstHeading.textContent = `1. ${data.heading}`;
      if (firstParagraph?.tagName === "P") firstParagraph.innerHTML = data.text;
      return;
    }
    const existing = prose.querySelector<HTMLElement>(".legal-owner");
    if (!existing) return;
    existing.setAttribute("aria-label", data.heading);
    const heading = existing.querySelector<HTMLHeadingElement>("h2");
    const paragraph = existing.querySelector<HTMLParagraphElement>("p");
    if (heading) heading.textContent = data.heading;
    if (paragraph) paragraph.innerHTML = data.text;
  }, [kind, language, page.html]);

  return <div ref={rootRef} className="cv-legacy-content" dangerouslySetInnerHTML={{ __html: page.html }} />;
}
''')

print("React UI parity patch applied")
