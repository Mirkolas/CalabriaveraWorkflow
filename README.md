# Public workflow runner

Questo repository pubblico esegue i workflow usando il sorgente del repository privato, scaricato soltanto sul runner temporaneo. Il codice applicativo, il nome del repository privato e gli identificativi hardcoded presenti nel sorgente non vengono copiati nel repository pubblico.

## Regola di configurazione

Le configurazioni applicative mantengono **gli stessi nomi e lo stesso tipo** del repository privato:

- cio che nel privato e una **Repository Variable** viene letto con `vars.*` anche qui;
- cio che nel privato e un **Repository Secret** viene letto con `secrets.*` anche qui;
- i valori che nel workflow privato erano hardcoded vengono letti dal sorgente privato a runtime, senza duplicarli nei file pubblici.

Gli unici valori tecnici aggiuntivi sono necessari per permettere al runner pubblico di leggere il sorgente privato:

- Secret `PRIVATE_REPO`: `owner/repository` del sorgente privato.
- Secret PAT: preferibilmente `PRIVATE_REPO_PAT`. Per compatibilita i workflow riconoscono anche `PERSONAL_ACCESS_TOKEN`, `PAT`, `GH_PAT` o `GITHUB_PAT`. Il PAT deve avere accesso in lettura al repository privato; backup/restore richiedono anche i permessi necessari per release/contenuti privati.

## Repository Variables originali

Copia con lo stesso nome e valore del repository privato:

- `FIREBASE_AUTO_DEPLOY_ENABLED`
- `FIREBASE_WIF_PROVIDER`
- `FIREBASE_DEPLOY_SERVICE_ACCOUNT`
- `BACKUPS_ENABLED`
- `FIREBASE_BACKUP_SERVICE_ACCOUNT`
- `FIREBASE_RESTORE_SERVICE_ACCOUNT`
- `APPS_SCRIPT_ENABLED`
- `BLOG_AUTOMATION_DISABLED`
- `FIREBASE_BLOG_WIF_PROVIDER`
- `FIREBASE_BLOG_SERVICE_ACCOUNT`
- `META_GRAPH_VERSION`
- `META_PAGE_ID`
- `META_IG_USER_ID`
- `SOCIAL_FACEBOOK_ENABLED`
- `SOCIAL_INSTAGRAM_ENABLED`
- `SOCIAL_MAX_DESTINATION_ATTEMPTS`

## Repository Secrets originali

Copia con lo stesso nome e valore del repository privato:

- `CLASPRC_JSON`
- `CALABRIAVERA_BACKUP_ENCRYPTION_KEY`
- `FIREBASE_AUTH_HASH_CONFIG`
- `META_PAGE_ACCESS_TOKEN`
- `META_INSTAGRAM_ACCESS_TOKEN`
- `SMOKE_TEST_EMAIL`
- `SMOKE_TEST_PASSWORD`

Non servono i vecchi secret aggiuntivi `FIREBASE_PROJECT_ID`, `SITE_URL`, `APPS_SCRIPT_ID`, `APPS_SCRIPT_DEPLOYMENT_ID`, `ADMIN_ALERT_EMAIL`, `PROMO_FACEBOOK_STORY_IMAGE_URL`, `PROMO_INSTAGRAM_STORY_IMAGE_URL`, `BACKUP_ENCRYPTION_KEY` o service-account JSON creati durante la prima migrazione: non fanno parte della configurazione originale.

## Rilevamento sorgente privato

`Private source watcher` controlla ogni 15 minuti il commit corrente del branch `main`. Nel repository pubblico conserva soltanto un'impronta SHA-256 e non salva lo SHA originale del sorgente.

Quando rileva una versione nuova avvia:

- `Verify private source`
- `Firebase deploy`
- `Apps Script deploy`

I workflow schedulati di backup, SEO e automazioni contenuti continuano con le stesse cadenze del privato.

## Workload Identity Federation

I nomi delle Variables WIF sono identici al privato. Tuttavia Google Cloud vede ora come identita OIDC il repository pubblico. Se il provider WIF e limitato esplicitamente al nome del repository privato, occorre autorizzare anche questo repository pubblico nel provider/policy Google Cloud; copiare la stessa Variable da solo non cambia la policy lato Google.

## Test

`Configuration test` non esegue deploy: verifica accesso al sorgente privato, installazione, test, backup test, validazione e build. I workflow applicativi usano poi direttamente le stesse Variables e Secrets del privato.
