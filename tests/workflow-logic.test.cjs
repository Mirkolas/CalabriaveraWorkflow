const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { test } = require('node:test');

const workflow = name => fs.readFileSync(path.join(__dirname, '../.github/workflows', name), 'utf8');
const bash = process.platform === 'win32'
  ? path.join(process.env.ProgramFiles || 'C:/Program Files', 'Git/bin/bash.exe')
  : '/bin/bash';
const portable = value => value.replaceAll('\\', '/');

function runBlock(text, marker) {
  const start = text.indexOf(marker);
  assert.notEqual(start, -1, `Missing workflow step: ${marker}`);
  const block = text.slice(start).match(/        run: \|\r?\n((?:          .*\r?\n|\r?\n)*)/);
  assert.ok(block, `Missing shell block: ${marker}`);
  return block[1].replace(/^ {10}/gm, '');
}

function runMagazine(marker, event, cron, notDue = false, failQuota = false) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-workflow-test-'));
  try {
    const log = path.join(dir, 'calls.log');
    const script = `
      node() {
        # Ubuntu login profiles may query the runtime version before the block.
        if [ "$1" = "-v" ] || [ "$1" = "--version" ]; then printf 'v22.0.0\\n'; return 0; fi
        if [ "$1" = "tools/automation-cadence-runner.mjs" ]; then
          if [ "$MOCK_CADENCE_NOT_DUE" = "true" ]; then return 0; fi
          while [ "$1" != "--" ]; do shift; done
          shift
          "$@"
        else
          printf '%s\\n' "$*" >> "$MOCK_NODE_LOG"
          if [ "$MOCK_QUOTA_FAILURE" = "true" ]; then echo 'RESOURCE_EXHAUSTED' >&2; return 1; fi
        fi
      }
      date() {
        if [ "$*" = "-u +%H" ]; then printf '09\\n'; else command date "$@"; fi
      }
      export -f node date
      ${runBlock(workflow('magazine-sync.yml'), marker)}
    `;
    const result = spawnSync(bash, ['-c', script], {
      encoding: 'utf8',
      env: {
        ...process.env,
        GITHUB_EVENT_NAME: event,
        SCHEDULED_CRON: cron,
        GITHUB_OUTPUT: portable(path.join(dir, 'output')),
        MOCK_NODE_LOG: portable(log),
        MOCK_CADENCE_NOT_DUE: String(notDue),
        MOCK_QUOTA_FAILURE: String(failQuota),
      },
    });
    assert.equal(result.status, 0, result.stderr || result.error?.message);
    if (failQuota) assert.match(fs.readFileSync(path.join(dir, 'output'), 'utf8'), /quota_exhausted=true/);
    return fs.existsSync(log) ? fs.readFileSync(log, 'utf8').trim().split(/\r?\n/) : [];
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

test('Magazine keeps four six-hour campaigns and binds daily work to scheduled event time', () => {
  const text = workflow('magazine-sync.yml');
  const cron = [...text.matchAll(/- cron: '([^']+)'/g)].map(match => match[1]);
  assert.deepEqual(cron, ['17 0 * * *', '17 6 * * *', '17 12,18 * * *']);
  assert.match(text, /SCHEDULED_CRON: \$\{\{ github\.event\.schedule \}\}/);
  const marker = '- name: Manutenzione quotidiana Magazine';
  const importMarker = '- name: Controlla tutte le fonti e pubblica i nuovi contenuti';
  assert.deepEqual(runMagazine(importMarker, 'schedule', cron[0], true), [], 'Import cadence not_due must remain respected');
  const maintenance = ['tools/reconcile-magazine.mjs', 'tools/enforce-positive-magazine.mjs', 'tools/backfill-blog-covers.mjs'];
  const delayedMidnight = runMagazine(marker, 'schedule', cron[0], true);
  for (const script of maintenance) assert.ok(delayedMidnight.includes(script), `Delayed midnight run missed ${script}`);
  for (const other of [cron[1], cron[2]]) {
    const calls = runMagazine(marker, 'schedule', other);
    for (const script of maintenance) assert.ok(!calls.includes(script), `Maintenance repeated for ${other}`);
    assert.ok(runMagazine(importMarker, 'schedule', other).includes('tools/publish-magazine-batch.mjs'));
  }
  const manual = runMagazine(marker, 'workflow_dispatch', '');
  for (const script of maintenance) assert.ok(!manual.includes(script), 'Manual blog run must preserve the daily maintenance cadence');
});

test('Maintenance quota exhaustion stops remaining work and guards Social and Story', () => {
  const marker = '- name: Manutenzione quotidiana Magazine';
  assert.deepEqual(runMagazine(marker, 'schedule', '17 0 * * *', false, true), ['tools/reconcile-magazine.mjs']);
  const text = workflow('magazine-sync.yml');
  for (const name of ['Pubblica la coppia Social se dovuta', 'Pubblica Story promozionale se dovuta']) {
    const condition = text.slice(text.indexOf(`- name: ${name}`)).match(/if: ([^\r\n]+)/)?.[1];
    assert.ok(condition?.includes("steps.maintenance.outputs.quota_exhausted != 'true'"), name);
  }
});

test('Meta expiry check runs in delayed 06 UTC campaign and on explicit manual checks', () => {
  const marker = '- name: Controlla validità e scadenza token Meta';
  assert.deepEqual(runMagazine(marker, 'schedule', '17 6 * * *'), ['tools/check-meta-token-expiry.mjs']);
  assert.deepEqual(runMagazine(marker, 'schedule', '17 0 * * *'), []);
  assert.deepEqual(runMagazine(marker, 'schedule', '17 12,18 * * *'), []);
  assert.deepEqual(runMagazine(marker, 'workflow_dispatch', ''), ['tools/check-meta-token-expiry.mjs']);
});

test('Source watcher applies private path filters and social flags before dispatch', () => {
  const text = workflow('source-watch.yml');
  const script = text.match(/WORK="\$work" node <<'NODE'\r?\n([\s\S]*?)^          NODE/m)?.[1].replace(/^ {10}/gm, '');
  assert.ok(script, 'Missing source-watch Node program');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-source-watch-test-'));
  try {
    fs.mkdirSync(path.join(dir, 'workflows'));
    fs.mkdirSync(path.join(dir, 'commits'));
    fs.writeFileSync(path.join(dir, 'pr-heads'), '');
    for (const [name, filters] of Object.entries({
      'apps-script-deploy.yml': ['paths:', "  - 'apps-script/**'"],
      'firebase-deploy.yml': ['paths-ignore:', "  - '**/*.md'", "  - 'tools/**'", "  - 'apps-script/**'"],
      'magazine-sync.yml': ['paths:', "  - 'tools/publish-social.mjs'"],
      'seo-sync.yml': ['paths:', "  - 'tools/seo*.mjs'"],
    })) {
      fs.writeFileSync(path.join(dir, 'workflows', name), `on:\n  push:\n${filters.map(line => `    ${line}`).join('\n')}\n`);
    }
    const evaluate = (files, message = '') => {
      const output = path.join(dir, 'outputs');
      fs.writeFileSync(output, '');
      fs.writeFileSync(path.join(dir, 'commits', '1.json'), JSON.stringify({ files: files.map(filename => ({ filename })), commit: { message } }));
      const result = spawnSync(process.execPath, ['-e', script], {
        encoding: 'utf8', env: { ...process.env, WORK: dir, GITHUB_OUTPUT: output, FORCE: 'false' },
      });
      assert.equal(result.status, 0, result.stderr);
      return Object.fromEntries(fs.readFileSync(output, 'utf8').trim().split('\n').map(line => line.split('=')));
    };
    assert.equal(evaluate(['docs/readme.md']).deploy, 'false');
    assert.equal(evaluate(['frontend-react/src/App.tsx']).deploy, 'true');
    assert.equal(evaluate(['apps-script/Email.gs']).apps, 'true');
    assert.equal(evaluate(['tools/seo-static.mjs']).seo, 'true');
    const social = evaluate(['tools/publish-social.mjs'], '[social-dry-run]');
    assert.equal(social.verify, 'true');
    assert.equal(social.magazine, 'true');
    assert.equal(social.deploy, 'false');
    assert.equal(social.social_dry_run, 'true');
    assert.equal(social.social_publish, 'false');
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
