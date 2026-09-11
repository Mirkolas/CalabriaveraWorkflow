from pathlib import Path

root = Path('source')

# 1) Use the canonical manifest from main while preserving the page theme color exactly.
p = root / 'frontend-react/index.html'
s = p.read_text(encoding='utf-8')
s = s.replace('<link rel="manifest" href="/manifest-react.webmanifest" />', '<link rel="manifest" href="/assets/site.webmanifest" />')
p.write_text(s, encoding='utf-8')

# 2) Install prompt parity component, safe during SSR/prerender.
p = root / 'frontend-react/src/components/PwaInstallButton.tsx'
p.write_text('''import { useEffect, useState } from "react";\nimport { languageFromPath, type Language } from "../lib/language";\n\ntype InstallPromptEvent = Event & { prompt: () => Promise<void>; userChoice: Promise<{ outcome: "accepted" | "dismissed" }> };\n\nconst COPY: Record<Language, { install: string; ios: string }> = {\n  it: { install: "Installa CalabriaVera", ios: "Su iPhone/iPad: apri il menu Condividi di Safari e scegli “Aggiungi a schermata Home”." },\n  en: { install: "Install CalabriaVera", ios: "On iPhone/iPad: open Safari Share and choose “Add to Home Screen”." },\n  fr: { install: "Installer CalabriaVera", ios: "Sur iPhone/iPad : ouvrez Partager dans Safari puis choisissez « Sur l’écran d’accueil »." },\n  de: { install: "CalabriaVera installieren", ios: "Auf iPhone/iPad: in Safari Teilen öffnen und „Zum Home-Bildschirm“ wählen." },\n  es: { install: "Instalar CalabriaVera", ios: "En iPhone/iPad: abre Compartir en Safari y elige «Añadir a pantalla de inicio»." },\n};\n\nfunction hasWindow() { return typeof window !== "undefined" && typeof navigator !== "undefined"; }\nfunction standalone() {\n  if (!hasWindow()) return false;\n  return window.matchMedia?.("(display-mode: standalone)").matches || (window.navigator as Navigator & { standalone?: boolean }).standalone === true;\n}\nfunction isIos() { return hasWindow() && /iphone|ipad|ipod/i.test(navigator.userAgent || ""); }\n\nexport default function PwaInstallButton() {\n  const language = languageFromPath();\n  const copy = COPY[language];\n  const [promptEvent, setPromptEvent] = useState<InstallPromptEvent | null>(null);\n  const [visible, setVisible] = useState(false);\n\n  useEffect(() => {\n    if (!hasWindow()) return;\n    if (!standalone() && isIos()) setVisible(true);\n    const before = (event: Event) => {\n      if (standalone()) return;\n      event.preventDefault();\n      setPromptEvent(event as InstallPromptEvent);\n      setVisible(true);\n    };\n    const installed = () => { setPromptEvent(null); setVisible(false); };\n    window.addEventListener("beforeinstallprompt", before);\n    window.addEventListener("appinstalled", installed);\n    return () => { window.removeEventListener("beforeinstallprompt", before); window.removeEventListener("appinstalled", installed); };\n  }, []);\n\n  if (!visible || standalone()) return null;\n  const install = async () => {\n    if (promptEvent) {\n      await promptEvent.prompt();\n      await promptEvent.userChoice.catch(() => undefined);\n      setPromptEvent(null);\n      setVisible(false);\n      return;\n    }\n    if (isIos()) window.alert(copy.ios);\n  };\n\n  return <button type="button" className="cv-pwa-install" onClick={() => void install()}>{copy.install}</button>;\n}\n''', encoding='utf-8')

# 3) Add the button to the footer.
p = root / 'frontend-react/src/components/Layout.tsx'
s = p.read_text(encoding='utf-8')
if 'import PwaInstallButton from "./PwaInstallButton";' not in s:
    s = s.replace('import Link from "./Link";', 'import Link from "./Link";\nimport PwaInstallButton from "./PwaInstallButton";')
old = '<div className="cv-footer-contact"><a href="mailto:info.calabriavera@gmail.com">info.calabriavera@gmail.com</a><a href="tel:+393479975255">+39 347 997 5255</a></div>'
new = '<div className="cv-footer-contact"><a href="mailto:info.calabriavera@gmail.com">info.calabriavera@gmail.com</a><a href="tel:+393479975255">+39 347 997 5255</a><PwaInstallButton /></div>'
if old in s:
    s = s.replace(old, new, 1)
elif '<PwaInstallButton />' not in s:
    raise SystemExit('footer contact marker missing')
p.write_text(s, encoding='utf-8')

# 4) Match main service-worker refresh behavior.
p = root / 'frontend-react/src/main.tsx'
s = p.read_text(encoding='utf-8')
old = '''if ("serviceWorker" in navigator) {\n  window.addEventListener("load", () => {\n    window.setTimeout(() => {\n      void navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(() => undefined);\n    }, 1000);\n  }, { once: true });\n}\n'''
new = '''if ("serviceWorker" in navigator && location.protocol === "https:") {\n  window.addEventListener("load", () => {\n    window.setTimeout(() => {\n      void navigator.serviceWorker.register("/sw.js", { scope: "/", updateViaCache: "none" }).then(async (registration) => {\n        const key = "cv-sw-last-update";\n        const interval = 60 * 60 * 1000;\n        let last = 0;\n        try { last = Number(localStorage.getItem(key) || 0); } catch {}\n        if (Date.now() - last >= interval) {\n          try { localStorage.setItem(key, String(Date.now())); } catch {}\n          await registration.update().catch(() => undefined);\n        }\n      }).catch(() => undefined);\n    }, 1000);\n  }, { once: true });\n}\n'''
if old in s:
    s = s.replace(old, new, 1)
elif 'updateViaCache: "none"' not in s:
    raise SystemExit('service worker marker missing')
p.write_text(s, encoding='utf-8')

# 5) Preserve the legacy offline page and provide navigation fallback.
p = root / 'frontend-react/public/offline.html'
p.write_text('''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta name="theme-color" content="#075b8f"><link rel="icon" href="/assets/favicon.ico"><title>Offline | CalabriaVera</title><style>body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;background:#f5f7fa;color:#173042;font-family:Arial,Helvetica,sans-serif}.card{width:min(100%,520px);box-sizing:border-box;padding:32px;border:1px solid #dfe6ec;border-radius:16px;background:#fff;box-shadow:0 14px 38px rgba(4,36,59,.08)}h1{margin-top:0;font-size:2rem}p{line-height:1.55;color:#586875}a{display:inline-block;margin-top:10px;padding:12px 18px;border-radius:10px;background:#075b8f;color:#fff;text-decoration:none;font-weight:700}@media(max-width:560px){body{padding:16px}.card{padding:24px}h1{font-size:1.65rem}}</style></head><body><main class="card"><h1>Connessione non disponibile</h1><p>CalabriaVera non riesce a raggiungere Internet. Le pagine già caricate possono restare disponibili, mentre dati aggiornati, messaggi e account richiedono la connessione.</p><a href="/">Riprova</a></main></body></html>''', encoding='utf-8')

p = root / 'frontend-react/public/sw.js'
s = p.read_text(encoding='utf-8')
if 'const OFFLINE_URL' not in s:
    s = s.replace('const STATIC_CACHE = "calabriavera-react-static-v1";', 'const STATIC_CACHE = "calabriavera-react-static-v2";\nconst OFFLINE_URL = "/offline.html";')
if 'cache.add(OFFLINE_URL)' not in s:
    s = s.replace('self.addEventListener("install", () => self.skipWaiting());', 'self.addEventListener("install", (event) => { event.waitUntil(caches.open(STATIC_CACHE).then((cache) => cache.add(OFFLINE_URL)).catch(() => undefined).then(() => self.skipWaiting())); });')
marker = '''self.addEventListener("fetch", (event) => {\n  const request = event.request;\n  const url = new URL(request.url);\n  if (!cacheable(request, url)) return;\n'''
replacement = '''self.addEventListener("fetch", (event) => {\n  const request = event.request;\n  const url = new URL(request.url);\n  if (request.method === "GET" && request.mode === "navigate" && url.origin === self.location.origin) {\n    event.respondWith(fetch(request).catch(async () => (await caches.match(OFFLINE_URL)) || Response.error()));\n    return;\n  }\n  if (!cacheable(request, url)) return;\n'''
if marker in s:
    s = s.replace(marker, replacement, 1)
elif 'request.mode === "navigate"' not in s:
    raise SystemExit('sw fetch marker missing')
p.write_text(s, encoding='utf-8')

print('React PWA parity patch applied')
