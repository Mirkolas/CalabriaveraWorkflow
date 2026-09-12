from pathlib import Path

root = Path("source/frontend-react")
admin = root / "src/pages/AdminPage.tsx"
generator = root / "scripts/copy-legacy-assets.mjs"

admin.write_text(r'''import { useEffect } from "react";
import { stripLanguagePath } from "../lib/language";
import { setPageSeo } from "../lib/seo";

type LegacyModule = {
  getCurrentUser?: () => Promise<unknown>;
  initAdmin?: (kind: string) => Promise<void>;
  installAdminRuntimeFixes?: () => void;
};

const CONTROL_ALIASES = new Set(["index", "impostazioni", "seo", "sistema"]);

const TITLES: Record<string, string> = {
  index: "Dashboard | CalabriaVera Admin",
  attivita: "Attività | CalabriaVera Admin",
  recensioni: "Recensioni | CalabriaVera Admin",
  blog: "Blog | CalabriaVera Admin",
  utenti: "Utenti | CalabriaVera Admin",
  categorie: "Categorie | CalabriaVera Admin",
  comuni: "Comuni | CalabriaVera Admin",
  messaggi: "Messaggi | CalabriaVera Admin",
  impostazioni: "Impostazioni | CalabriaVera Admin",
  seo: "SEO | CalabriaVera Admin",
  segnalazioni: "Dashboard | CalabriaVera Admin",
  comunicazioni: "Dashboard | CalabriaVera Admin",
  sistema: "Dashboard | CalabriaVera Admin",
};

function sectionFromPath() {
  const parts = stripLanguagePath(location.pathname).split("/").filter(Boolean);
  return parts[0] === "admin" && parts[1] ? parts[1] : "index";
}

function importLegacy(file: string) {
  const url = `/assets/js/${file}`;
  return import(/* @vite-ignore */ url) as Promise<LegacyModule>;
}

async function mountFinalLegacyAdmin(kind: string) {
  // Exact page-loader auth gate: authenticated users continue; guests go to login.
  const auth = await importLegacy("auth.js");
  const user = await auth.getCurrentUser?.();
  if (!user) {
    location.replace(`/login?next=${encodeURIComponent(location.pathname + location.search)}`);
    return;
  }

  // page-loader-core owns the base shell and the two legacy-owned screens
  // (Recensioni / Blog). The copied file is the BUILD-PATCHED admin.js.
  const base = await importLegacy("admin.js");
  if (typeof base.initAdmin !== "function") throw new Error("Legacy admin bootstrap missing");
  await base.initAdmin(kind);

  // page-loader.js installs these fixes for every admin page after core boot.
  const runtime = await importLegacy("admin-runtime-fixes.js");
  runtime.installAdminRuntimeFixes?.();

  // These scripts are page-specific in the authoritative pre-React HTML.
  if (CONTROL_ALIASES.has(kind)) {
    await importLegacy("admin-maintenance-toggle.js");
    await importLegacy("admin-automation-status.js");
  }
  if (kind === "attivita") await importLegacy("admin-critical-upgrades.js");
  if (kind === "messaggi") {
    await importLegacy("admin-critical-upgrades.js");
    await importLegacy("admin-conversation-delete-ui.js");
  }
  if (kind === "utenti") await importLegacy("admin-user-profile-ui.js");

  // scripts/build.mjs appends these in this order to every admin document.
  // The copied versions are build-patched: admin-console owns only Segnalazioni;
  // admin-upgrade owns Control Center, CRM, Utenti, Comunicazioni, Messaggi and tassonomie.
  await importLegacy("admin-console.js");
  await importLegacy("admin-upgrade.js");
}

export default function AdminPage() {
  const kind = sectionFromPath();
  useEffect(() => {
    setPageSeo({
      title: TITLES[kind] || "Dashboard | CalabriaVera Admin",
      description: kind === "index" || ["segnalazioni", "comunicazioni", "sistema"].includes(kind)
        ? "Area amministrativa CalabriaVera."
        : "CalabriaVera: il portale locale delle attività e dei servizi della Calabria.",
      path: location.pathname,
      robots: "noindex,nofollow",
    });
    void mountFinalLegacyAdmin(kind).catch((error) => {
      console.error("Admin legacy bridge:", error);
      const output = document.getElementById("admin-root");
      if (output) output.innerHTML = '<div class="notice" role="alert"><strong>Sezione amministrativa non disponibile.</strong><p>Impossibile caricare il pannello amministratore.</p></div>';
    });
  }, [kind]);

  return <section className="section container"><div id="admin-root"><div className="notice" role="status">Caricamento area amministrativa aggiornata…</div></div></section>;
}
''', encoding="utf-8")

text = generator.read_text(encoding="utf-8")
text = text.replace(
    'import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";',
    'import { copyFileSync, cpSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";\nimport { spawnSync } from "node:child_process";'
)

marker = 'console.log(`Pagine legacy: ${legalFiles.length}; asset locali copiati: ${assetFiles.length}`);'
block = r'''
// Admin parity uses the exact BUILD-PATCHED legacy modules rather than a rewritten approximation.
// Running build.mjs here reproduces patchAdminRuntime() from the authoritative pipeline.
const legacyBuild = spawnSync(process.execPath, [resolve(repoRoot, "scripts/build.mjs")], {
  cwd: repoRoot,
  stdio: "inherit",
});
if (legacyBuild.status !== 0) throw new Error(`Build legacy admin fallita (${legacyBuild.status})`);
const builtLegacyJs = resolve(repoRoot, "dist/assets/js");
const publicLegacyJs = resolve(reactRoot, "public/assets/js");
if (!existsSync(builtLegacyJs)) throw new Error(`Asset JS legacy build mancanti: ${builtLegacyJs}`);
if (existsSync(publicLegacyJs)) rmSync(publicLegacyJs, { recursive: true, force: true });
mkdirSync(dirname(publicLegacyJs), { recursive: true });
cpSync(builtLegacyJs, publicLegacyJs, { recursive: true });
const builtFirebaseConfig = resolve(repoRoot, "dist/firebase/firebase-config.js");
if (!existsSync(builtFirebaseConfig)) throw new Error(`Config Firebase legacy build mancante: ${builtFirebaseConfig}`);
const publicFirebaseConfig = resolve(reactRoot, "public/firebase/firebase-config.js");
mkdirSync(dirname(publicFirebaseConfig), { recursive: true });
copyFileSync(builtFirebaseConfig, publicFirebaseConfig);
console.log(`Bridge admin legacy: ${publicLegacyJs}`);
'''
if block.strip() not in text:
    if marker not in text:
        raise SystemExit("copy-legacy-assets marker not found")
    text = text.replace(marker, marker + "\n" + block)

virtual_routes = {
    '"/admin/segnalazioni": "pages/admin/segnalazioni.html"': '"/admin/segnalazioni": "pages/admin/index.html"',
    '"/admin/comunicazioni": "pages/admin/comunicazioni.html"': '"/admin/comunicazioni": "pages/admin/index.html"',
    '"/admin/sistema": "pages/admin/sistema.html"': '"/admin/sistema": "pages/admin/index.html"',
}
for old, new in virtual_routes.items():
    if old in text:
        text = text.replace(old, new)
    elif new not in text:
        raise SystemExit(f"route source marker not found: {old}")

generator.write_text(text, encoding="utf-8")
print("Patched exact final admin bridge + build-time legacy assets")
