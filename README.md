# Public workflow runner

Questo repository pubblico esegue GitHub Actions usando il sorgente di un repository privato senza copiarlo nel repository pubblico.

Il checkout privato avviene soltanto sul runner temporaneo tramite secret. Nei file pubblici non sono presenti in chiaro nome del repository sorgente, PAT, ID progetto, URL applicativi, account di servizio, ID Apps Script o credenziali social.

## Come vengono rilevati i push privati

`Private source watcher` viene eseguito ogni 15 minuti quando `RUNNER_ENABLED=true`. Legge con il PAT soltanto il commit corrente del branch `main`, ne calcola una seconda impronta SHA-256 e salva nella cache pubblica solo quell'impronta. Lo SHA originale e il nome del repository privato non vengono scritti nel repository o nei log.

Quando l'impronta cambia, il watcher avvia nel repository pubblico:

- `Verify private source`
- `Firebase deploy`
- `Apps Script deploy`

Il watcher puo anche essere avviato manualmente; l'opzione `force` forza i tre workflow anche se la versione non e cambiata.

## Secrets di base

Configura in **Settings → Secrets and variables → Actions**:

- `PRIVATE_REPO`: repository sorgente privato nel formato `owner/repository`.
- `PRIVATE_REPO_PAT`: PAT con accesso al repository privato. Per operazioni di backup/ripristino che modificano release, tag o contenuti servono anche i relativi permessi di scrittura.
- `RUNNER_ENABLED`: imposta esattamente `true` solo dopo i test manuali; abilita watcher e cron.
- `FIREBASE_PROJECT_ID`
- `SITE_URL`

## Firebase

Puoi usare JSON oppure Workload Identity Federation.

Deploy:
- JSON: `FIREBASE_SERVICE_ACCOUNT`
- oppure WIF: `FIREBASE_WIF_PROVIDER` + `FIREBASE_DEPLOY_SERVICE_ACCOUNT`

Backup:
- JSON: `FIREBASE_BACKUP_SERVICE_ACCOUNT`
- oppure WIF: `FIREBASE_WIF_PROVIDER` + `FIREBASE_BACKUP_WIF_SERVICE_ACCOUNT`
- `BACKUP_ENCRYPTION_KEY`
- `FIREBASE_AUTH_HASH_CONFIG`

Restore:
- JSON: `FIREBASE_RESTORE_SERVICE_ACCOUNT`
- oppure WIF: `FIREBASE_WIF_PROVIDER` + `FIREBASE_RESTORE_WIF_SERVICE_ACCOUNT`
- `BACKUP_ENCRYPTION_KEY`
- `FIREBASE_AUTH_HASH_CONFIG`

Automazioni contenuti:
- JSON: `FIREBASE_BLOG_SERVICE_ACCOUNT`
- oppure WIF: `FIREBASE_BLOG_WIF_PROVIDER` + `FIREBASE_BLOG_WIF_SERVICE_ACCOUNT`

**Nota WIF:** se il provider Google Cloud era limitato al nome del vecchio repository privato, va autorizzato anche questo repository pubblico. In alternativa usa temporaneamente il corrispondente secret JSON.

## Social

- `META_GRAPH_VERSION`
- `META_PAGE_ID`
- `META_IG_USER_ID`
- `META_PAGE_ACCESS_TOKEN`
- `META_INSTAGRAM_ACCESS_TOKEN`
- `ADMIN_ALERT_EMAIL`
- `SOCIAL_FACEBOOK_ENABLED`
- `SOCIAL_INSTAGRAM_ENABLED`
- `SOCIAL_MAX_DESTINATION_ATTEMPTS`
- `PROMO_FACEBOOK_STORY_IMAGE_URL`
- `PROMO_INSTAGRAM_STORY_IMAGE_URL`

## Apps Script

- `CLASPRC_JSON`
- `APPS_SCRIPT_ID`
- `APPS_SCRIPT_DEPLOYMENT_ID`
- `LEGACY_SITE_URL` (solo se serve la sostituzione automatica)

## Browser smoke test

- `SMOKE_TEST_EMAIL`
- `SMOKE_TEST_PASSWORD`

## Cutover sicuro

1. Copia i secret nel repository pubblico e lascia `RUNNER_ENABLED` diverso da `true`.
2. Avvia manualmente `Verify private source`, `Firebase deploy`, `Browser smoke test`, `Encrypted backup`, `SEO sync` e le modalita di `Content automation` che vuoi verificare. I test manuali funzionano anche con i cron disabilitati.
3. Verifica `Apps Script deploy`; se usi WIF, verifica prima l'autorizzazione del nuovo repository pubblico su Google Cloud.
4. Imposta `RUNNER_ENABLED=true`: da quel momento watcher e cron pubblici diventano operativi.
5. Solo dopo run pubbliche riuscite disattiva i trigger automatici dei workflow nel repository privato, evitando doppie esecuzioni.

I workflow privati non vengono disattivati automaticamente da questa configurazione: restano il fallback finche non completi manualmente il cutover delle credenziali.
