from pathlib import Path

path = Path('source/tools/backup/run.mjs')
s = path.read_text(encoding='utf-8')
old = "  const localOnly = process.argv.includes('--local-only');\n  const incremental = process.argv.includes('--incremental');\n  let captureResult;"
new = "  const localOnly = process.argv.includes('--local-only');\n  const incremental = process.argv.includes('--incremental');\n  const activateIncrementalBaseline = process.argv.includes('--baseline-v1');\n  if (incremental && activateIncrementalBaseline) throw Error('Modalità backup incompatibili: usa --incremental oppure --baseline-v1');\n  let captureResult;"
if old not in s:
    raise SystemExit('run.mjs mode marker not found')
s = s.replace(old, new)
old = "    captureResult = await capture(project, repository, { firestoreMode: 'baseline', incrementalSchemaVersion: INCREMENTAL_SCHEMA_VERSION });"
new = "    captureResult = await capture(project, repository, { firestoreMode: activateIncrementalBaseline ? 'baseline' : 'full', incrementalSchemaVersion: activateIncrementalBaseline ? INCREMENTAL_SCHEMA_VERSION : 0 });"
if old not in s:
    raise SystemExit('run.mjs baseline marker not found')
s = s.replace(old, new)
path.write_text(s, encoding='utf-8')

path = Path('source/tests/backup.test.mjs')
s = path.read_text(encoding='utf-8')
if "--baseline-v1" not in s:
    s += "\ntest('Backup incrementale richiede baseline esplicita e i full di emergenza restano schema 0',()=>{\n  const source=readFileSync(new URL('../tools/backup/run.mjs',import.meta.url),'utf8');\n  assert.match(source,/activateIncrementalBaseline = process\\.argv\\.includes\\('--baseline-v1'\\)/);\n  assert.match(source,/incrementalSchemaVersion: activateIncrementalBaseline \\? INCREMENTAL_SCHEMA_VERSION : 0/);\n});\n"
    s = s.replace("import { randomBytes } from 'node:crypto';", "import { randomBytes } from 'node:crypto';\nimport { readFileSync } from 'node:fs';")
path.write_text(s, encoding='utf-8')
print('Explicit incremental baseline guard applied')
