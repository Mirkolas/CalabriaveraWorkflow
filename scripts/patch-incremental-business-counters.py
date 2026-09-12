from pathlib import Path

root=Path('source')

p=root/'tools/backup/incremental.mjs'
s=p.read_text(encoding='utf-8')
s=s.replace("businesses: ['updatedAt','createdAt'],", "businesses: ['backupUpdatedAt','updatedAt','createdAt'],")
p.write_text(s,encoding='utf-8')

p=root/'frontend-react/src/lib/businesses.ts'
s=p.read_text(encoding='utf-8')
s=s.replace('transaction.update(businessRef, { favoriteCount: f.increment(-1) });', 'transaction.update(businessRef, { favoriteCount: f.increment(-1), backupUpdatedAt: f.serverTimestamp() });')
s=s.replace('transaction.update(businessRef, { favoriteCount: f.increment(1) });', 'transaction.update(businessRef, { favoriteCount: f.increment(1), backupUpdatedAt: f.serverTimestamp() });')
p.write_text(s,encoding='utf-8')

p=root/'frontend-react/src/lib/business-detail-interactions.ts'
s=p.read_text(encoding='utf-8')
s=s.replace('tx.update(businessRef, { [field]: f.increment(1) });', 'tx.update(businessRef, { [field]: f.increment(1), backupUpdatedAt: f.serverTimestamp() });')
p.write_text(s,encoding='utf-8')

p=root/'firestore.rules'
s=p.read_text(encoding='utf-8')
s=s.replace("request.resource.data.diff(resource.data).affectedKeys().hasOnly(['favoriteCount'])", "request.resource.data.diff(resource.data).affectedKeys().hasOnly(['favoriteCount','backupUpdatedAt'])\n        && request.resource.data.backupUpdatedAt == request.time")
s=s.replace("request.resource.data.diff(resource.data).affectedKeys().hasOnly([field])\n        && request.resource.data[field] == resource.data[field] + 1", "request.resource.data.diff(resource.data).affectedKeys().hasOnly([field,'backupUpdatedAt'])\n        && request.resource.data.backupUpdatedAt == request.time\n        && request.resource.data[field] == resource.data[field] + 1")
p.write_text(s,encoding='utf-8')

p=root/'tests/backup.test.mjs'
s=p.read_text(encoding='utf-8')
if "business counters have a dedicated backup timestamp" not in s:
    s += r'''

test('business counters have a dedicated backup timestamp without changing updatedAt ordering',()=>{
  const business=readFileSync(new URL('../frontend-react/src/lib/businesses.ts',import.meta.url),'utf8');
  const metric=readFileSync(new URL('../frontend-react/src/lib/business-detail-interactions.ts',import.meta.url),'utf8');
  const incremental=readFileSync(new URL('../tools/backup/incremental.mjs',import.meta.url),'utf8');
  const rules=readFileSync(new URL('../firestore.rules',import.meta.url),'utf8');
  assert.match(business,/favoriteCount: f\.increment\(-1\), backupUpdatedAt: f\.serverTimestamp\(\)/);
  assert.match(business,/favoriteCount: f\.increment\(1\), backupUpdatedAt: f\.serverTimestamp\(\)/);
  assert.match(metric,/\[field\]: f\.increment\(1\), backupUpdatedAt: f\.serverTimestamp\(\)/);
  assert.match(incremental,/businesses: \['backupUpdatedAt','updatedAt','createdAt'\]/);
  assert.match(rules,/backupUpdatedAt == request\.time/);
});
'''
p.write_text(s,encoding='utf-8')
print('Tracked business counters for incremental backup')
