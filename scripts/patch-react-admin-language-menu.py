from pathlib import Path

admin = Path('frontend-react/src/pages/AdminPage.tsx')
s = admin.read_text()

old_import = 'import { navigate } from "../lib/navigation";'
new_import = 'import { navigate } from "../lib/navigation";\nimport { languageFromPath, stripLanguagePath, withLanguage } from "../lib/language";'
if old_import not in s:
    raise SystemExit('Admin navigation import contract changed')
s = s.replace(old_import, new_import, 1)

old_section = '''function sectionFromPath() {
  const parts=location.pathname.split("/").filter(Boolean);
  return parts.length <= 1 ? "index" : parts.at(-1) || "index";
}
'''
new_section = '''function sectionFromPath() {
  const parts=stripLanguagePath(location.pathname).split("/").filter(Boolean);
  if (parts[0] !== "admin") return "index";
  return parts[1] || "index";
}
function adminHref(path: string) {
  return withLanguage(path, languageFromPath());
}
'''
if old_section not in s:
    raise SystemExit('Admin section parser contract changed')
s = s.replace(old_section, new_section, 1)

old_menu = 'href={href}>{label}</Link>)}</aside>'
new_menu = 'href={adminHref(href)}>{label}</Link>)}</aside>'
if old_menu not in s:
    raise SystemExit('Admin menu link contract changed')
s = s.replace(old_menu, new_menu, 1)

old_blog = '<Link className="text-link" href="/admin/blog">Gestisci blog</Link>'
new_blog = '<Link className="text-link" href={adminHref("/admin/blog")}>Gestisci blog</Link>'
if old_blog not in s:
    raise SystemExit('Overview admin link contract changed')
s = s.replace(old_blog, new_blog, 1)
admin.write_text(s)

layout = Path('frontend-react/src/components/Layout.tsx')
l = layout.read_text()
# Keep Admin links in the selected language in both desktop and mobile account menus.
l = l.replace('{admin ? <Link href="/admin">Admin</Link> : null}', '{admin ? <Link href={withLanguage("/admin", language)}>Admin</Link> : null}')
if l.count('withLanguage("/admin", language)') < 2:
    raise SystemExit('Expected both localized Admin account links')

anchor = '''  useEffect(() => {
    setMenuOpen(false);
    const page = exactMainPage(cleanPath) || (cleanPath.startsWith("/admin/") ? `admin-${cleanPath.split("/").filter(Boolean).at(-1)}` : cleanPath.replace(/^\\//, "") || "app");
'''
replacement = '''  useEffect(() => {
    setMenuOpen(false);
    document.querySelectorAll<HTMLDetailsElement>(".cv-header details[open]").forEach((details) => { details.open = false; });
    const page = exactMainPage(cleanPath) || (cleanPath.startsWith("/admin/") ? `admin-${cleanPath.split("/").filter(Boolean).at(-1)}` : cleanPath.replace(/^\\//, "") || "app");
'''
if anchor not in l:
    raise SystemExit('Layout route effect contract changed')
l = l.replace(anchor, replacement, 1)

insert_before = '''  const signOut = async () => {
'''
outside_effect = '''  useEffect(() => {
    const closeDetails = (target?: EventTarget | null) => {
      document.querySelectorAll<HTMLDetailsElement>(".cv-header details[open]").forEach((details) => {
        if (!target || !(target instanceof Node) || !details.contains(target)) details.open = false;
      });
    };
    const onDocumentClick = (event: MouseEvent) => closeDetails(event.target);
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      closeDetails();
      setMenuOpen(false);
    };
    document.addEventListener("click", onDocumentClick);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("click", onDocumentClick);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, []);

'''
if insert_before not in l:
    raise SystemExit('Layout signOut anchor changed')
l = l.replace(insert_before, outside_effect + insert_before, 1)
layout.write_text(l)
