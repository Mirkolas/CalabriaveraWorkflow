# Public workflow runner

Questo repository pubblico esegue GitHub Actions usando il sorgente di un repository privato senza copiarlo nel repository pubblico.

Il checkout privato avviene solo sul runner temporaneo tramite secret. I workflow non contengono in chiaro nome del repository privato, token, ID progetto, URL applicativi, account di servizio o credenziali social.

## Secrets di base

Configura in **Settings → Secrets and variables → Actions**:

- `PRIVATE_REPO`: repository sorgente privato nel formato `owner/repository`.
- `PRIVATE_REPO_PAT`: PAT con accesso minimo necessario al repository privato.
- `RUNNER_ENABLED`: imposta esattamente `true` solo dopo aver completato e testato tutti i secret; protegge i workflow schedulati.
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
- `LEGACY_SITE_URL` (solo se deve essere sostituito automaticamente)

## Browser smoke test

- `SMOKE_TEST_EMAIL`
- `SMOKE_TEST_PASSWORD`

## Cutover sicuro

1. Copia i secret nel repository pubblico.
2. Lascia `RUNNER_ENABLED` diverso da `true`.
3. Avvia manualmente `Verify private source`, `Firebase deploy`, `Browser smoke test` e le automazioni che vuoi verificare.
4. Quando i test sono riusciti, imposta `RUNNER_ENABLED=true` per attivare i cron pubblici.
5. Solo a quel punto disattiva i corrispondenti trigger automatici nel repository privato, evitando esecuzioni duplicate.

I workflow `repository_dispatch` sono gia predisposti per ricevere in seguito eventi di push dal repository privato tramite un relay minimo, senza spostare il lavoro pesante fuori da questo repository pubblico.
