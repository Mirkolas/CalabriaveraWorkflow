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

## Tentativi schedulati protetti

Tutti i workflow che usano `schedule` hanno **cinque occasioni di esecuzione per ogni campagna logica**. Il controllo condiviso e in `.github/workflows/scheduled-retry-gate.yml`.

Il gate calcola la campagna corrente, legge tramite GitHub Actions API le run schedulate dello stesso workflow e applica queste regole:

- se nella campagna non esiste ancora un successo, il tentativo corrente esegue il lavoro reale;
- appena un tentativo termina con successo, i tentativi schedulati successivi della stessa campagna terminano senza avviare il lavoro reale;
- se un tentativo fallisce, il successivo rimane disponibile e riprova;
- `workflow_dispatch` e `repository_dispatch` non vengono bloccati dal gate;
- se l'API usata dal gate non e temporaneamente disponibile, il sistema preferisce eseguire il tentativo invece di rischiare di saltare la campagna;
- le concurrency schedulate non cancellano il tentativo in corso e gli intervalli sono dimensionati rispetto ai timeout dei job, per evitare sovrapposizioni inutili.

Campagne attive:

- `source-watch.yml`: ogni ora, 5 tentativi ai minuti 02, 12, 22, 32 e 42;
- `seo-sync.yml`: ogni ora, 5 tentativi ai minuti 03, 13, 23, 33 e 43;
- `magazine-sync.yml`: ogni 2 ore, 5 tentativi distribuiti nell'intera finestra per lasciare terminare un job fino a 24 minuti;
- `firebase-deploy.yml`: manutenzione schedulata ogni 4 ore, 5 tentativi;
- `daily-backup.yml`: una campagna giornaliera dalle 02:30 UTC, 5 tentativi;
- `promo-story.yml`: una campagna giornaliera dalle 06:41 UTC, 5 tentativi;
- `cleanup-old-workflow-runs.yml`: una campagna settimanale la domenica dalle 03:00 UTC, 5 tentativi.

Gli errori temporanei di quota Firestore nella sincronizzazione SEO e nella manutenzione Firebase vengono considerati retryable: il job termina senza segnare un falso successo, cosi il tentativo successivo della stessa campagna puo riprovare.

## Rilevamento sorgente privato

`Private source watcher` usa una campagna oraria con cinque tentativi protetti. Appena un tentativo riesce, gli altri quattro non eseguono nuovamente il controllo. Per non perdere modifiche a causa delle run di retry saltate, il watcher prende come riferimento l'ultima run in cui il job `watch` e stato realmente eseguito con successo, non una semplice run completata dal gate.

Quando rileva modifiche applica gli equivalenti dei trigger del repository privato e avvia solo i workflow necessari.

## Workload Identity Federation

I nomi delle Variables WIF sono identici al privato. Tuttavia Google Cloud vede ora come identita OIDC il repository pubblico. Se il provider WIF e limitato esplicitamente al nome del repository privato, occorre autorizzare anche questo repository pubblico nel provider/policy Google Cloud; copiare la stessa Variable da solo non cambia la policy lato Google.

## Test

`Configuration test` non esegue deploy: verifica accesso al sorgente privato, installazione, test, backup test, validazione e build. I workflow applicativi usano poi direttamente le stesse Variables e Secrets del privato.
