from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "source")
p = root / "frontend-react/src/pages/LegalPage.tsx"
s = p.read_text(encoding="utf-8")

start = s.index("const SOURCE_BY_KIND = {")
end = s.index("\n} as const;", start) + len("\n} as const;")
source = '''const SOURCE_BY_KIND = {
  privacy: "/legacy/privacy-policy.html",
  cookie: "/legacy/cookie-policy.html",
  terms: "/legacy/termini.html",
  legal: "/legacy/note-legali.html",
  about: "/legacy/chi-siamo.html",
  contacts: "/legacy/contatti.html",
} as const;'''
s = s[:start] + source + s[end:]

# The abbreviated React copies are intentionally removed: the legacy pages are the source of truth until cutover.
static_start = s.index("const STATIC_HTML:")
extract_start = s.index("\nfunction extractMain", static_start)
s = s[:static_start] + "const STATIC_HTML: Partial<Record<Kind, string>> = {};\n" + s[extract_start:]

old_extract = '''function extractMain(html: string) {
  const doc = new DOMParser().parseFromString(html, "text/html");
  const main = doc.querySelector("main");
  if (!main) return "<p>Contenuto non disponibile.</p>";
  main.querySelectorAll("script").forEach((node) => node.remove());
  main.querySelectorAll("a[href^='/']").forEach((node) => {
    const href = node.getAttribute("href");
    if (href) node.setAttribute("href", href.replace(/\\.html(?=($|[?#]))/, ""));
  });
  return main.innerHTML;
}
'''
new_extract = '''function extractMain(html: string) {
  const doc = new DOMParser().parseFromString(html, "text/html");
  const main = doc.querySelector("main");
  if (!main) return { content: "<p>Contenuto non disponibile.</p>", title: "", description: "" };
  main.querySelectorAll("script").forEach((node) => node.remove());
  main.querySelectorAll("a[href^='/']").forEach((node) => {
    const href = node.getAttribute("href");
    if (href) node.setAttribute("href", href.replace(/\\.html(?=($|[?#]))/, ""));
  });
  return {
    content: main.innerHTML,
    title: doc.querySelector("title")?.textContent?.trim() || "",
    description: doc.querySelector('meta[name="description"]')?.getAttribute("content")?.trim() || "",
  };
}
'''
if old_extract not in s:
    raise SystemExit("extractMain marker not found")
s = s.replace(old_extract, new_extract, 1)

old_effect = '''    const [title, description] = META[kind];
    setPageSeo({ title, description });
    const staticContent = STATIC_HTML[kind];
    if (staticContent) { setContent(staticContent); setFailed(false); return; }
    const source = SOURCE_BY_KIND[kind];
    let active = true;
    fetch(source, { cache: "force-cache" })
      .then((response) => response.ok ? response.text() : Promise.reject(new Error(String(response.status))))
      .then((html) => { if (active) setContent(extractMain(html)); })
      .catch(() => { if (active) setFailed(true); });
'''
new_effect = '''    const [fallbackTitle, fallbackDescription] = META[kind];
    setPageSeo({ title: fallbackTitle, description: fallbackDescription, path: location.pathname, robots: "index,follow" });
    const staticContent = STATIC_HTML[kind];
    if (staticContent) { setContent(staticContent); setFailed(false); return; }
    const source = SOURCE_BY_KIND[kind];
    let active = true;
    fetch(source, { cache: "no-cache" })
      .then((response) => response.ok ? response.text() : Promise.reject(new Error(String(response.status))))
      .then((html) => {
        if (!active) return;
        const legacy = extractMain(html);
        setContent(legacy.content);
        setFailed(false);
        setPageSeo({ title: legacy.title || fallbackTitle, description: legacy.description || fallbackDescription, path: location.pathname, robots: "index,follow" });
      })
      .catch(() => { if (active) setFailed(true); });
'''
if old_effect not in s:
    raise SystemExit("LegalPage effect marker not found")
s = s.replace(old_effect, new_effect, 1)
p.write_text(s, encoding="utf-8")
