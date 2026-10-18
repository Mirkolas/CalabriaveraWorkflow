const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
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

function runReleaseCheck({ event = 'repository_dispatch', live = 'source-sha', changed = false, unavailable = false } = {}) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-release-check-test-'));
  try {
    const output = path.join(dir, 'output');
    const log = path.join(dir, 'calls');
    const comparison = Buffer.from(unavailable
      ? 'export async function inspectSeo() { throw new Error("temporary failure"); }'
      : `export async function inspectSeo() { return { needsSync: ${changed} }; }`).toString('base64');
    const fixtureRoot = portable(path.join(dir, 'check'));
    const block = runBlock(workflow('firebase-deploy.yml'), '- name: Evita una seconda release')
      .replaceAll('/tmp/cv-release-check', fixtureRoot)
      .replace(`from "${fixtureRoot}/tools/check-seo-sync.mjs"`, `from "${pathToFileURL(path.join(dir, 'check/tools/check-seo-sync.mjs')).href}"`);
    const script = `
      gh() {
        printf '%s\\n' "$*" >> "$MOCK_CALL_LOG"
        case "$*" in
          *commits/main*) printf 'source-sha\\n' ;;
          *contents/tools/check-seo-sync.mjs*) printf '%s' '${comparison}' ;;
          *contents/tools/lib/seo-snapshot.mjs*) printf '' ;;
          *contents/assets/js/magazine-rights.js*) printf '' ;;
          *) return 1 ;;
        esac
      }
      curl() { printf '%s\\n' 'curl' >> "$MOCK_CALL_LOG"; printf '%s' "$MOCK_LIVE_VERSION"; }
      export -f gh curl
      ${block}
    `;
    const result = spawnSync(bash, ['-c', script], {
      encoding: 'utf8',
      env: { ...process.env, PRIVATE_REPO: 'fixture/source', GH_TOKEN: 'fixture', GITHUB_EVENT_NAME: event,
        GITHUB_OUTPUT: portable(output), MOCK_CALL_LOG: portable(log), MOCK_LIVE_VERSION: live },
    });
    assert.equal(result.status, 0, result.stderr || result.error?.message);
    return { output: fs.readFileSync(output, 'utf8'), calls: fs.readFileSync(log, 'utf8') };
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
}

test('Duplicate source dispatch skips a release only when both source and public content match', () => {
  assert.match(runReleaseCheck().output, /should_deploy=false/);
  assert.match(runReleaseCheck({ changed: true }).output, /should_deploy=true/);
  assert.match(runReleaseCheck({ unavailable: true }).output, /should_deploy=true/);
  const newSource = runReleaseCheck({ live: 'older-source' });
  assert.match(newSource.output, /should_deploy=true/);
  assert.doesNotMatch(newSource.calls, /contents\/tools/);
  const manual = runReleaseCheck({ event: 'workflow_dispatch' });
  assert.match(manual.output, /should_deploy=true/);
  assert.doesNotMatch(manual.calls, /curl/);
});

test('Health recovery requests maintenance without creating a new Firebase release', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-health-check-test-'));
  try {
    const log = path.join(dir, 'calls');
    const script = `
      gh() {
        if [ "$1" = 'api' ]; then printf '{}'; else printf '%s\\n' "$*" >> "$MOCK_CALL_LOG"; fi
      }
      jq() { cat > /dev/null; }
      export -f gh jq
      ${runBlock(workflow('scheduled-health.yml'), '- name: Verifica e ripristina i cicli schedulati')}
    `;
    const result = spawnSync(bash, ['-c', script], {
      encoding: 'utf8', env: { ...process.env, GITHUB_REPOSITORY: 'fixture/runner', MOCK_CALL_LOG: portable(log) },
    });
    assert.equal(result.status, 0, result.stderr || result.error?.message);
    const calls = fs.readFileSync(log, 'utf8').trim().split(/\r?\n/);
    assert.equal(calls.length, 5);
    assert.ok(calls.includes('workflow run firebase-deploy.yml --repo fixture/runner --ref main -f maintenance_only=true'));
    assert.ok(calls.filter(line => !line.includes('firebase-deploy.yml')).every(line => !line.includes('maintenance_only')));
    assert.match(workflow('firebase-deploy.yml'), /inputs\.maintenance_only != true/);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test('Hosting bandwidth exhaustion defers SEO without hiding unrelated failures', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-seo-quota-test-'));
  try {
    for (const status of [429, 509, 500]) {
      const output = path.join(dir, String(status));
      const script = `
        node() { printf 'Error: HTTP %s durante verifica SEO\\n' "$MOCK_HTTP_STATUS" >&2; return 1; }
        export -f node
        ${runBlock(workflow('seo-sync.yml'), '- name: Confronta i contenuti pubblici con la sitemap online')}
      `;
      const result = spawnSync(bash, ['-c', script], {
        encoding: 'utf8', env: { ...process.env, MOCK_HTTP_STATUS: String(status), GITHUB_OUTPUT: portable(output) },
      });
      if (status === 500) assert.equal(result.status, 1, result.stdout);
      else {
        assert.equal(result.status, 0, result.stderr || result.error?.message);
        assert.match(fs.readFileSync(output, 'utf8'), /needs_sync=false/);
        assert.match(result.stdout, /::warning::/);
      }
    }
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test('Safe cleanup uses an exact 20-day UTC calendar without a database read', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-maintenance-calendar-test-'));
  const anchor = Date.parse('2026-10-18T00:00:00Z') / 1000;
  try {
    for (const [days, event, expected] of [[0,'schedule',true],[1,'schedule',false],[19,'schedule',false],[20,'schedule',true],[40,'schedule',true],[-1,'schedule',false],[1,'workflow_dispatch',true]]) {
      const output = path.join(dir, `${days}-${event}`);
      const script = `
        date() { if [[ "$*" == *'2026-10-18T00:00:00Z'* ]]; then printf '%s' "$MOCK_ANCHOR"; else printf '%s' "$MOCK_TODAY"; fi; }
        export -f date
        ${runBlock(workflow('maintenance-cadence.yml'), '- name: Controlla il calendario senza leggere Firestore')}
      `;
      const result = spawnSync(bash, ['-c', script], { encoding:'utf8', env:{ ...process.env,
        EVENT_NAME:event, MOCK_ANCHOR:String(anchor), MOCK_TODAY:String(anchor + days * 86400), GITHUB_OUTPUT:portable(output) } });
      assert.equal(result.status, 0, result.stderr || result.error?.message);
      assert.match(fs.readFileSync(output,'utf8'), new RegExp(`should_run=${expected}`));
    }
    const magazine = workflow('magazine-retention.yml');
    assert.doesNotMatch(magazine, /schedule:|--apply/);
    assert.match(magazine, /--dry-run/);
  } finally { fs.rmSync(dir, { recursive:true, force:true }); }
});

test('Production deploy orders tests, verified R2 uploads, Cloudflare primary and Firebase fallback', () => {
  const text = workflow('firebase-deploy.yml');
  const markers = ['npm test', "CV_PRERENDER_OFFLINE: '0'", 'node tests/admin-readonly-e2e.cjs',
    'node frontend-react/scripts/upload-r2-static.mjs --apply', 'run: npx wrangler deploy',
    '- name: Verifica la release primaria su workers.dev', '- name: Aggiorna il fallback React su Firebase Hosting'];
  const positions = markers.map(marker => text.indexOf(marker));
  assert.ok(positions.every(position => position >= 0), 'A production gate is missing');
  assert.deepEqual([...positions].sort((a,b) => a-b), positions, 'Production deployment order changed');
  assert.match(text, /X-CalabriaVera-Hosting:/);
  const wrapper = workflow('cloudflare-worker-r2-api.yml');
  assert.doesNotMatch(wrapper, /repository_dispatch:|push:|CV_PRERENDER_OFFLINE/);
  assert.match(wrapper, /gh workflow run firebase-deploy\.yml/);
});

test('Firebase fallback HTTP509 does not fail Cloudflare production; HTTP500 still fails', () => {
  for (const status of [509, 500]) {
    const script = `
      curl() { printf '%s' "$MOCK_HTTP_STATUS"; }
      export -f curl
      ${runBlock(workflow('firebase-deploy.yml'), '- name: Verifica il fallback Firebase senza consumare la quota del dominio primario')}
    `;
    const result = spawnSync(bash, ['-c', script], { encoding:'utf8', env:{...process.env,MOCK_HTTP_STATUS:String(status)} });
    assert.equal(result.status, status === 509 ? 0 : 1, result.stderr || result.stdout);
    if (status === 509) assert.match(result.stdout, /::warning::/);
  }
});

test('Story preflight uses two R2 HEAD requests and respects missing assets', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cv-story-preflight-test-'));
  try {
    for (const status of [200, 404]) {
      const log = path.join(dir, String(status));
      const script = `
        node() {
          if [ "$1" = '-v' ] || [ "$1" = '--version' ]; then printf 'v22.0.0\\n'; return 0; fi
          if [ "$1" = 'tools/automation-cadence-runner.mjs' ]; then
            while [ "$1" != '--' ]; do shift; done
            shift
            "$@"
          else printf 'node %s\\n' "$*" >> "$MOCK_CALL_LOG"; fi
        }
        curl() { printf 'curl %s\\n' "$*" >> "$MOCK_CALL_LOG"; printf 'HTTP/2 %s\\r\\ncontent-type: image/jpeg\\r\\n' "$MOCK_HTTP_STATUS"; }
        sleep() { return 0; }
        export -f node curl sleep
        ${runBlock(workflow('magazine-sync.yml'), '- name: Pubblica Story promozionale se dovuta')}
      `;
      const result = spawnSync(bash, ['-c',script], { encoding:'utf8', env:{...process.env,
        MOCK_HTTP_STATUS:String(status),MOCK_CALL_LOG:portable(log),
        PROMO_FACEBOOK_STORY_IMAGE_URL:'https://img.calabriavera.com/static/assets/story.png',
        PROMO_INSTAGRAM_STORY_IMAGE_URL:'https://img.calabriavera.com/static/assets/story.jpg'} });
      assert.equal(result.status, status === 200 ? 0 : 1, result.stderr || result.stdout);
      const calls = fs.readFileSync(log,'utf8');
      assert.ok(calls.split('\n').filter(line=>line.startsWith('curl ')).every(line=>line.includes('--head') && !line.includes('?')));
      if (status === 200) {
        assert.equal(calls.split('\n').filter(line=>line.startsWith('curl ')).length,2);
        assert.match(calls,/node tools\/publish-promo-story.mjs/);
      } else assert.doesNotMatch(calls,/publish-promo-story/);
    }
  } finally { fs.rmSync(dir,{recursive:true,force:true}); }
});
