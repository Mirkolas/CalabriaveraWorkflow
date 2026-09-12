from pathlib import Path
import json

root = Path('source')
backup = root / 'tools/backup'

incremental = r'''import { google, post } from './api.mjs';

export const INCREMENTAL_SCHEMA_VERSION = 1;
export const DELTA_COLLECTIONS = {
  users: ['updatedAt','createdAt'],
  publicProfiles: ['updatedAt','createdAt'],
  businesses: ['updatedAt','createdAt'],
  reviews: ['updatedAt','createdAt'],
  favorites: ['createdAt'],
  conversations: ['updatedAt','createdAt'],
  messages: ['readAt','createdAt'],
  reports: ['updatedAt','createdAt'],
  notifications: ['readAt','updatedAt','createdAt'],
  campaigns: ['updatedAt','createdAt','sentAt','requestedAt'],
  adminOutreach: ['updatedAt','createdAt','sentAt','requestedAt'],
  revokedUsers: ['revokedAt','updatedAt','createdAt']
};

// Collezioni piccole: leggerle interamente costa poche centinaia di letture e rende
// esatte anche cancellazioni/modifiche legacy prive di timestamp uniforme.
export const FULL_REFRESH_COLLECTIONS = [
  'categories','subcategories','provinces','municipalities','settings','invites','blogPosts','magazineSources'
];

// Code e log operativi non devono essere resuscitati da un backup giornaliero.
// Restano disponibili nei backup completi manuali e nei log GitHub/Cloud Logging.
export const VOLATILE_COLLECTIONS = new Set([
  'emailEvents','adminActions','_mailDeliveries','auditLogs','adminAudit','magazineSyncRuns',
  'socialPublishRuns','adminSystemAlerts','rateLimits','businessMetricEvents'
]);

const rootName = project => `projects/${project}/databases/(default)/documents`;
const fullName = (project, path) => path.startsWith('projects/') ? path : `${rootName(project)}/${String(path).replace(/^\/+/, '')}`;
const relativeName = name => String(name || '').split('/documents/')[1] || '';
const topCollection = name => relativeName(name).split('/')[0] || '';
const isoMs = value => Number.isFinite(new Date(String(value || '')).getTime()) ? new Date(String(value)).getTime() : 0;

function decodeValue(value = {}) {
  if ('stringValue' in value) return value.stringValue;
  if ('timestampValue' in value) return value.timestampValue;
  if ('integerValue' in value) return Number(value.integerValue);
  if ('doubleValue' in value) return Number(value.doubleValue);
  if ('booleanValue' in value) return Boolean(value.booleanValue);
  if ('arrayValue' in value) return (value.arrayValue?.values || []).map(decodeValue);
  if ('mapValue' in value) return Object.fromEntries(Object.entries(value.mapValue?.fields || {}).map(([k,v]) => [k, decodeValue(v)]));
  if ('nullValue' in value) return null;
  return null;
}
export function decodeDocument(document) {
  return Object.fromEntries(Object.entries(document?.fields || {}).map(([key,value]) => [key, decodeValue(value)]));
}

async function readTime(project, api = google) {
  const rows = await api(`https://firestore.googleapis.com/v1/${rootName(project)}:runQuery`, post({ structuredQuery: { from: [{ collectionId: '_cvBackupClock' }], limit: 1 } }));
  const stamp = [...rows].reverse().find(row => row.readTime)?.readTime;
  if (!stamp) throw Error('Ora snapshot Firestore non disponibile per backup incrementale');
  return stamp;
}

function timeFilter(field, since, until) {
  return { compositeFilter: { op: 'AND', filters: [
    { fieldFilter: { field: { fieldPath: field }, op: 'GREATER_THAN', value: { timestampValue: since } } },
    { fieldFilter: { field: { fieldPath: field }, op: 'LESS_THAN_OR_EQUAL', value: { timestampValue: until } } }
  ] } };
}

async function runQuery(project, structuredQuery, api = google) {
  const rows = await api(`https://firestore.googleapis.com/v1/${rootName(project)}:runQuery`, post({ structuredQuery }));
  return rows.flatMap(row => row.document ? [row.document] : []);
}

export async function queryDeltaCollection(project, collectionId, fields, since, until, api = google) {
  const byName = new Map();
  for (const field of fields) {
    try {
      const documents = await runQuery(project, {
        from: [{ collectionId }],
        where: timeFilter(field, since, until),
        orderBy: [{ field: { fieldPath: field }, direction: 'ASCENDING' }]
      }, api);
      for (const document of documents) byName.set(document.name, document);
    } catch (error) {
      const message = String(error?.message || error || '');
      // A field missing from every document simply produces no rows. Index/precondition
      // failures are not ignored because that would make the backup silently incomplete.
      if (/FAILED_PRECONDITION|requires an index|index.*required/i.test(message)) throw error;
      throw error;
    }
  }
  return [...byName.values()];
}

export async function refreshCollection(project, collectionId, readTimeValue, api = google) {
  const url = new URL(`https://firestore.googleapis.com/v1/${rootName(project)}/${encodeURIComponent(collectionId)}`);
  url.searchParams.set('pageSize', '1000');
  url.searchParams.set('showMissing', 'false');
  if (readTimeValue) url.searchParams.set('readTime', readTimeValue);
  const docs = [];
  let pageToken = '';
  do {
    if (pageToken) url.searchParams.set('pageToken', pageToken); else url.searchParams.delete('pageToken');
    const data = await api(url.toString());
    docs.push(...(data.documents || []));
    pageToken = data.nextPageToken || '';
  } while (pageToken);
  return docs;
}

async function queryTombstones(project, since, until, api = google) {
  const docs = await runQuery(project, {
    from: [{ collectionId: '_cvBackupTombstones', allDescendants: true }],
    where: timeFilter('deletedAt', since, until),
    orderBy: [{ field: { fieldPath: 'deletedAt' }, direction: 'ASCENDING' }]
  }, api);
  return docs.map(document => ({ document, data: decodeDocument(document) }));
}

function removePath(map, project, targetPath) {
  const target = fullName(project, targetPath);
  map.delete(target);
  const prefix = `${target}/`;
  for (const name of [...map.keys()]) if (name.startsWith(prefix)) map.delete(name);
}

function cascadeBusiness(map, project, businessId) {
  const root = rootName(project);
  removePath(map, project, `businesses/${businessId}`);
  for (const [name, doc] of [...map]) {
    const data = decodeDocument(doc);
    if (String(data.businessId || '') === businessId || String(data.resourceId || '') === businessId || String(data.target || '') === businessId) map.delete(name);
    if (name.startsWith(`${root}/businesses/${businessId}/`)) map.delete(name);
  }
}

function cascadeConversation(map, project, conversationId) {
  removePath(map, project, `conversations/${conversationId}`);
  for (const [name, doc] of [...map]) if (String(decodeDocument(doc).conversationId || '') === conversationId) map.delete(name);
}

function cascadeUser(map, project, uid) {
  const businessIds = [];
  for (const [name, doc] of map) {
    const data = decodeDocument(doc);
    if (topCollection(name) === 'businesses' && String(data.ownerId || '') === uid) businessIds.push(relativeName(name).split('/')[1]);
  }
  for (const id of businessIds) cascadeBusiness(map, project, id);
  removePath(map, project, `users/${uid}`);
  removePath(map, project, `publicProfiles/${uid}`);
  const scalarKeys = ['userId','ownerId','reporterId','senderId','receiverId','recipientId','actorUid','requestedBy','updatedBy'];
  for (const [name, doc] of [...map]) {
    const data = decodeDocument(doc);
    if (scalarKeys.some(key => String(data[key] || '') === uid) || (Array.isArray(data.participantIds) && data.participantIds.map(String).includes(uid))) map.delete(name);
  }
}

export function mergeIncrementalSnapshot(previous, project, { changed = [], refreshed = {}, tombstones = [], signals = {}, until }) {
  const map = new Map((previous?.documents || []).filter(doc => !VOLATILE_COLLECTIONS.has(topCollection(doc.name))).map(doc => [doc.name, doc]));
  for (const collectionId of FULL_REFRESH_COLLECTIONS) {
    for (const name of [...map.keys()]) if (topCollection(name) === collectionId) map.delete(name);
    for (const doc of refreshed[collectionId] || []) map.set(doc.name, doc);
  }
  for (const doc of changed) {
    if (!VOLATILE_COLLECTIONS.has(topCollection(doc.name)) && !relativeName(doc.name).includes('/_cvBackupTombstones/')) map.set(doc.name, doc);
  }
  for (const row of tombstones) if (row?.data?.targetPath) removePath(map, project, row.data.targetPath);
  for (const id of signals.businessDeletes || []) cascadeBusiness(map, project, String(id));
  for (const id of signals.conversationDeletes || []) cascadeConversation(map, project, String(id));
  for (const id of signals.userDeletes || []) cascadeUser(map, project, String(id));
  return { project, database: '(default)', readTime: until, missingParents: 0, documents: [...map.values()].sort((a,b) => String(a.name).localeCompare(String(b.name))) };
}

async function querySignals(project, since, until, api = google) {
  const businessDeletes = new Set(), conversationDeletes = new Set(), userDeletes = new Set();
  const adminAudits = await queryDeltaCollection(project, 'adminAudit', ['createdAt','updatedAt'], since, until, api).catch(() => []);
  for (const doc of adminAudits) {
    const data = decodeDocument(doc);
    if (data.action === 'business.deleted' && data.businessId) businessDeletes.add(String(data.businessId));
  }
  const auditLogs = await queryDeltaCollection(project, 'auditLogs', ['createdAt'], since, until, api).catch(() => []);
  for (const doc of auditLogs) {
    const data = decodeDocument(doc);
    if (data.event === 'admin_conversation_deleted' && data.resourceId) conversationDeletes.add(String(data.resourceId));
  }
  const revoked = await queryDeltaCollection(project, 'revokedUsers', ['revokedAt','updatedAt','createdAt'], since, until, api).catch(() => []);
  for (const doc of revoked) userDeletes.add(relativeName(doc.name).split('/')[1]);
  return { businessDeletes: [...businessDeletes], conversationDeletes: [...conversationDeletes], userDeletes: [...userDeletes] };
}

async function refreshBusinessImages(project, snapshot, changedBusinessIds, until, api = google) {
  const map = new Map(snapshot.documents.map(doc => [doc.name, doc]));
  const root = rootName(project);
  for (const businessId of changedBusinessIds) {
    const prefix = `${root}/businesses/${businessId}/images/`;
    for (const name of [...map.keys()]) if (name.startsWith(prefix)) map.delete(name);
    let pageToken = '';
    do {
      const url = new URL(`https://firestore.googleapis.com/v1/${root}/businesses/${encodeURIComponent(businessId)}/images`);
      url.searchParams.set('pageSize','1000');
      url.searchParams.set('readTime', until);
      if (pageToken) url.searchParams.set('pageToken', pageToken);
      try {
        const data = await api(url.toString());
        for (const doc of data.documents || []) map.set(doc.name, doc);
        pageToken = data.nextPageToken || '';
      } catch (error) {
        if (Number(error?.status) === 404) pageToken = '';
        else throw error;
      }
    } while (pageToken);
  }
  return { ...snapshot, documents: [...map.values()].sort((a,b) => String(a.name).localeCompare(String(b.name))) };
}

export async function exportFirestoreIncremental(project, previous, api = google) {
  if (!previous?.readTime || !Array.isArray(previous?.documents)) throw Error('Baseline Firestore incrementale non valida');
  const since = previous.readTime;
  const until = await readTime(project, api);
  if (isoMs(until) <= isoMs(since)) throw Error('Cursore Firestore incrementale non avanzato');
  const changedMap = new Map();
  for (const [collectionId, fields] of Object.entries(DELTA_COLLECTIONS)) {
    const docs = await queryDeltaCollection(project, collectionId, fields, since, until, api);
    for (const doc of docs) changedMap.set(doc.name, doc);
  }
  const refreshed = {};
  for (const collectionId of FULL_REFRESH_COLLECTIONS) refreshed[collectionId] = await refreshCollection(project, collectionId, until, api);
  const tombstones = await queryTombstones(project, since, until, api).catch(error => {
    const message = String(error?.message || error || '');
    if (/NOT_FOUND/i.test(message)) return [];
    throw error;
  });
  const signals = await querySignals(project, since, until, api);
  let snapshot = mergeIncrementalSnapshot(previous, project, { changed: [...changedMap.values()], refreshed, tombstones, signals, until });
  const changedBusinessIds = [...changedMap.values()].filter(doc => topCollection(doc.name) === 'businesses').map(doc => relativeName(doc.name).split('/')[1]).filter(Boolean);
  snapshot = await refreshBusinessImages(project, snapshot, [...new Set(changedBusinessIds)], until, api);
  return { snapshot, stats: { since, until, changed: changedMap.size, tombstones: tombstones.length, refreshed: Object.fromEntries(Object.entries(refreshed).map(([k,v]) => [k,v.length])), signals } };
}
'''
(backup / 'incremental.mjs').write_text(incremental, encoding='utf-8')

# export.mjs: allow capture to reuse an incrementally reconstructed Firestore snapshot.
path = backup / 'export.mjs'
s = path.read_text(encoding='utf-8')
s = s.replace('export async function capture(project, repository) {', 'export async function capture(project, repository, options = {}) {')
s = s.replace("  const firestore = await exportFirestore(project); put('firestore.json', firestore); log(`Firestore: ${firestore.documents.length} documenti, incluse sottocollezioni.`);", "  const firestore = options.firestoreSnapshot || await exportFirestore(project); put('firestore.json', firestore); log(`Firestore: ${firestore.documents.length} documenti (${options.firestoreMode || 'full'}).`);")
s = s.replace("const metadata = { project, repository, started, completed: new Date().toISOString(), commit: sourceCommit, counts:", "const metadata = { project, repository, started, completed: new Date().toISOString(), commit: sourceCommit, firestoreCursor: firestore.readTime, firestoreMode: options.firestoreMode || 'full', incrementalSchemaVersion: options.incrementalSchemaVersion || 0, counts:")
path.write_text(s, encoding='utf-8')

# releases.mjs: find newest verified backup without guessing tags.
path = backup / 'releases.mjs'
s = path.read_text(encoding='utf-8')
insert = '''\nexport async function latestVerifiedBackup(repository) {\n  const releases = await pages(`/repos/${repository}/releases`);\n  const valid = releases.map(release => ({ release, meta: releaseMeta(release) })).filter(row => row.meta?.verified === true && !row.release.draft);\n  valid.sort((a,b) => Number(b.meta.sequence || 0) - Number(a.meta.sequence || 0));\n  return valid[0]?.release || null;\n}\n'''
if 'export async function latestVerifiedBackup' not in s:
    s = s.replace('export async function downloadBackup', insert + '\nexport async function downloadBackup')
path.write_text(s, encoding='utf-8')

# run.mjs: incremental mode downloads previous verified archive and merges only changes.
path = backup / 'run.mjs'
s = path.read_text(encoding='utf-8')
s = s.replace("import { publishBackup } from './releases.mjs';", "import { downloadBackup, latestVerifiedBackup, publishBackup } from './releases.mjs';\nimport { exportFirestoreIncremental, INCREMENTAL_SCHEMA_VERSION } from './incremental.mjs';")
s = s.replace("  const localOnly = process.argv.includes('--local-only');\n  const { files, metadata } = await capture(project, repository);", "  const localOnly = process.argv.includes('--local-only');\n  const incremental = process.argv.includes('--incremental');\n  let captureResult;\n  if (incremental) {\n    const latest = await latestVerifiedBackup(repository);\n    if (!latest) throw Error('INCREMENTAL_BASELINE_REQUIRED: nessun backup verificato disponibile');\n    const previous = await downloadBackup(repository, latest.tag_name, key);\n    if (Number(previous.archive.metadata.incrementalSchemaVersion || 0) !== INCREMENTAL_SCHEMA_VERSION) {\n      console.log('Backup incrementale non ancora attivo: serve una baseline manuale compatibile. Nessuna lettura Firestore eseguita.');\n      process.exit(0);\n    }\n    const previousFirestore = JSON.parse(previous.archive.files.get('firestore.json')?.toString() || 'null');\n    const delta = await exportFirestoreIncremental(project, previousFirestore);\n    console.log(JSON.stringify({ firestoreIncremental: delta.stats }));\n    captureResult = await capture(project, repository, { firestoreSnapshot: delta.snapshot, firestoreMode: 'incremental', incrementalSchemaVersion: INCREMENTAL_SCHEMA_VERSION });\n  } else {\n    captureResult = await capture(project, repository, { firestoreMode: 'baseline', incrementalSchemaVersion: INCREMENTAL_SCHEMA_VERSION });\n  }\n  const { files, metadata } = captureResult;")
path.write_text(s, encoding='utf-8')

# React deletion tombstones for high-cardinality collections and owner business deletion.
helper = r'''import type { DocumentReference, Firestore, Transaction, WriteBatch } from "firebase/firestore";

type FirestoreSdk = typeof import("firebase/firestore");

export function tombstoneRef(f: FirestoreSdk, target: DocumentReference) {
  return f.doc(target, "_cvBackupTombstones", "delete");
}
export function tombstonePayload(f: FirestoreSdk, target: DocumentReference, actorUid: string) {
  return { targetPath: target.path, actorUid, deletedAt: f.serverTimestamp(), schemaVersion: 1 };
}
export function trackedDeleteInBatch(f: FirestoreSdk, batch: WriteBatch, target: DocumentReference, actorUid: string) {
  batch.set(tombstoneRef(f, target), tombstonePayload(f, target, actorUid));
  batch.delete(target);
}
export function trackedDeleteInTransaction(f: FirestoreSdk, transaction: Transaction, target: DocumentReference, actorUid: string) {
  transaction.set(tombstoneRef(f, target), tombstonePayload(f, target, actorUid));
  transaction.delete(target);
}
export async function trackedDelete(f: FirestoreSdk, db: Firestore, target: DocumentReference, actorUid: string) {
  const batch = f.writeBatch(db);
  trackedDeleteInBatch(f, batch, target, actorUid);
  await batch.commit();
}
'''
lib = root / 'frontend-react/src/lib'
(lib / 'backup-tombstones.ts').write_text(helper, encoding='utf-8')

path = lib / 'businesses.ts'; s = path.read_text(encoding='utf-8')
if 'backup-tombstones' not in s:
    s = 'import { trackedDeleteInTransaction } from "./backup-tombstones";\n' + s
s = s.replace('transaction.delete(favoriteRef);\n        return false;', 'trackedDeleteInTransaction(f, transaction, favoriteRef, user.uid);\n        return false;')
s = s.replace('transaction.delete(favoriteRef);\n      if (Number(business.data().favoriteCount || 0) > 0)', 'trackedDeleteInTransaction(f, transaction, favoriteRef, user.uid);\n      if (Number(business.data().favoriteCount || 0) > 0)')
path.write_text(s, encoding='utf-8')

path = lib / 'notifications.ts'; s = path.read_text(encoding='utf-8')
if 'backup-tombstones' not in s:
    s = 'import { trackedDelete } from "./backup-tombstones";\nimport { currentUser } from "./auth";\n' + s
s = s.replace('  const { db, f } = await services();\n  await f.deleteDoc(f.doc(db, "notifications", id));', '  const [user, { db, f }] = await Promise.all([currentUser(), services()]);\n  if (!user) throw new Error("AUTH_REQUIRED");\n  await trackedDelete(f, db, f.doc(db, "notifications", id), user.uid);')
path.write_text(s, encoding='utf-8')

path = lib / 'business-owner.ts'; s = path.read_text(encoding='utf-8')
if 'backup-tombstones' not in s:
    s = 'import { trackedDelete } from "./backup-tombstones";\n' + s
s = s.replace('  await f.deleteDoc(ref);', '  await trackedDelete(f, db, ref, user.uid);')
path.write_text(s, encoding='utf-8')

# Firestore rules for nested tombstones. They are write-only metadata and cannot be forged for another user's resource.
path = root / 'firestore.rules'; s = path.read_text(encoding='utf-8')
marker = '    match /categories/{id} { allow read: if true; allow write: if admin(); }'
rules = r'''    match /favorites/{id}/_cvBackupTombstones/{marker} {
      allow read: if false;
      allow create: if activeUser()
        && get(/databases/$(database)/documents/favorites/$(id)).data.userId == request.auth.uid
        && request.resource.data.actorUid == request.auth.uid
        && request.resource.data.targetPath == "favorites/" + id
        && request.resource.data.deletedAt == request.time;
      allow update, delete: if false;
    }
    match /notifications/{id}/_cvBackupTombstones/{marker} {
      allow read: if false;
      allow create: if activeUser()
        && get(/databases/$(database)/documents/notifications/$(id)).data.recipientId == request.auth.uid
        && request.resource.data.actorUid == request.auth.uid
        && request.resource.data.targetPath == "notifications/" + id
        && request.resource.data.deletedAt == request.time;
      allow update, delete: if false;
    }
    match /businesses/{id}/_cvBackupTombstones/{marker} {
      allow read: if false;
      allow create: if activeUser() && businessOwner(id)
        && request.resource.data.actorUid == request.auth.uid
        && request.resource.data.targetPath == "businesses/" + id
        && request.resource.data.deletedAt == request.time;
      allow update, delete: if false;
    }
'''
if rules.strip() not in s:
    if marker not in s: raise SystemExit('firestore rules insertion marker missing')
    s = s.replace(marker, rules + marker)
path.write_text(s, encoding='utf-8')

# Collection-group single-field index for nested tombstone query.
path = root / 'firestore.indexes.json'; data = json.loads(path.read_text(encoding='utf-8'))
overrides = data.setdefault('fieldOverrides', [])
entry = {"collectionGroup":"_cvBackupTombstones","fieldPath":"deletedAt","indexes":[{"order":"ASCENDING","queryScope":"COLLECTION_GROUP"},{"order":"DESCENDING","queryScope":"COLLECTION_GROUP"}]}
if not any(x.get('collectionGroup') == '_cvBackupTombstones' and x.get('fieldPath') == 'deletedAt' for x in overrides): overrides.append(entry)
path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')

# Tests: pure merge proves updates, deletes and cascades without touching Firebase.
path = root / 'tests/backup.test.mjs'; s = path.read_text(encoding='utf-8')
if "./incremental.mjs" not in s:
    s = s.replace("import { restoreFirestore, authImportBody, hostingCliConfig } from '../tools/backup/restore.mjs';", "import { restoreFirestore, authImportBody, hostingCliConfig } from '../tools/backup/restore.mjs';\nimport { mergeIncrementalSnapshot, INCREMENTAL_SCHEMA_VERSION } from '../tools/backup/incremental.mjs';")
append = r'''

test('Backup incrementale: merge sostituisce modifiche, applica tombstone e non conserva code volatili',()=>{
  const root='projects/demo/databases/(default)/documents';
  const wire=(path,fields={})=>({name:`${root}/${path}`,fields:Object.fromEntries(Object.entries(fields).map(([k,v])=>[k,{stringValue:String(v)}])),updateTime:'2026-09-12T00:00:00Z'});
  const previous={project:'demo',database:'(default)',readTime:'2026-09-11T00:00:00Z',documents:[wire('businesses/b1',{name:'Old'}),wire('favorites/u_b1',{userId:'u'}),wire('emailEvents/e1',{type:'x'})]};
  const changed=[wire('businesses/b1',{name:'New'})];
  const tombstones=[{data:{targetPath:'favorites/u_b1'}}];
  const merged=mergeIncrementalSnapshot(previous,'demo',{changed,refreshed:{},tombstones,signals:{},until:'2026-09-12T00:00:00Z'});
  assert.equal(INCREMENTAL_SCHEMA_VERSION,1);
  assert.equal(merged.documents.some(d=>d.name.endsWith('/favorites/u_b1')),false);
  assert.equal(merged.documents.some(d=>d.name.endsWith('/emailEvents/e1')),false);
  assert.equal(merged.documents.find(d=>d.name.endsWith('/businesses/b1')).fields.name.stringValue,'New');
});

test('Backup incrementale: segnali di cancellazione rimuovono le cascate principali',()=>{
  const root='projects/demo/databases/(default)/documents';
  const v=x=>({stringValue:x}); const arr=x=>({arrayValue:{values:x.map(v)}});
  const docs=[
    {name:`${root}/users/u1`,fields:{}},
    {name:`${root}/businesses/b1`,fields:{ownerId:v('u1')}},
    {name:`${root}/reviews/r1`,fields:{businessId:v('b1'),userId:v('u2')}},
    {name:`${root}/conversations/c1`,fields:{participantIds:arr(['u2','u3'])}},
    {name:`${root}/messages/m1`,fields:{conversationId:v('c1'),senderId:v('u2')}}
  ];
  const previous={project:'demo',database:'(default)',readTime:'2026-09-11T00:00:00Z',documents:docs};
  const merged=mergeIncrementalSnapshot(previous,'demo',{changed:[],refreshed:{},tombstones:[],signals:{businessDeletes:['b1'],conversationDeletes:['c1'],userDeletes:['u1']},until:'2026-09-12T00:00:00Z'});
  assert.equal(merged.documents.length,0);
});
'''
if 'Backup incrementale: merge sostituisce modifiche' not in s: s += append
path.write_text(s, encoding='utf-8')

print('Incremental backup v1 patch applied')
