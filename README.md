# Public workflow runner

Questo repository pubblico esegue i workflow usando il sorgente del repository privato, scaricato soltanto sul runner temporaneo. Il codice applicativo, il nome del repository privato e gli identificativi hardcoded presenti nel sorgente non vengono copiati nel repository pubblico.

## Regola di configurazione

### Sitemap e Google Search Console

`seo-sync.yml` confronta i dati pubblici con il manifest pubblicato e avvia il deploy quando serve. Le modifiche arrivate durante la build sono confrontate con l'istante di lettura dei dati. Il cron è richiesto ogni 5 minuti, ma GitHub può ritardare l'esecuzione.

Il deploy controlla gli HTML generati, pubblica il sito, verifica sitemap, lingue e `noindex` delle aree personali, quindi invia `sitemap.xml` tramite la Search Console API ufficiale. Non usa Google Indexing API, riservata a tipi di contenuto non pertinenti a questo sito. L'invio è una segnalazione a Google e non garantisce l'indicizzazione.

Per abilitare l'invio, attivare **Search Console API** nel progetto Google Cloud e aggiungere l'indirizzo già configurato in `FIREBASE_DEPLOY_SERVICE_ACCOUNT` come **utente completo** della proprietà Search Console. Non occorrono chiavi JSON aggiuntive: viene usata l'identità federata esistente. La variabile facoltativa `SEARCH_CONSOLE_SITE` permette di usare la proprietà dominio `sc-domain:calabriavera.com`; in assenza si usa `https://calabriavera.com/`.

Il riepilogo del deploy distingue `submitted` da `access-required` (HTTP 403). Un problema di accesso a Search Console viene segnalato esplicitamente senza annullare la pubblicazione del sito già verificata; altri errori API fanno fallire lo step.

La verifica manuale `verify.yml` accetta `source_ref`, un branch o SHA nel repository privato già configurato. Consente di verificare una correzione prima del merge senza pubblicarla.

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

Le pianificazioni correnti sono riportate sotto, in UTC. Il controllo condiviso in `.github/workflows/scheduled-retry-gate.yml` protegge i workflow che lo richiamano; non aggiunge da solo ulteriori esecuzioni cron.

Il gate calcola la campagna corrente, legge tramite GitHub Actions API le run schedulate dello stesso workflow e applica queste regole:

- se nella campagna non esiste ancora un successo, il tentativo corrente esegue il lavoro reale;
- appena un tentativo termina con successo, i tentativi schedulati successivi della stessa campagna terminano senza avviare il lavoro reale;
- se un tentativo fallisce, il successivo rimane disponibile e riprova;
- `workflow_dispatch` e `repository_dispatch` non vengono bloccati dal gate;
- se l'API usata dal gate non e temporaneamente disponibile, il sistema preferisce eseguire il tentativo invece di rischiare di saltare la campagna;
- le concurrency schedulate non cancellano il tentativo in corso e gli intervalli sono dimensionati rispetto ai timeout dei job, per evitare sovrapposizioni inutili.

Campagne attive:

- `source-watch.yml`: ogni ora al minuto 02;
- `seo-sync.yml`: ogni 5 minuti;
- `magazine-sync.yml`: ogni 6 ore al minuto 17; include feed social e Story, con le rispettive cadenze interne;
- `firebase-deploy.yml`: manutenzione giornaliera alle 02:17; il deploy avviene con push del workflow, dispatch manuale o dispatch dal watcher;
- `daily-backup.yml`: backup giornaliero alle 02:41;
- `scheduled-health.yml`: controllo e recupero dei cicli ogni ora al minuto 07.

Gli orari GitHub Actions sono indicativi: il servizio può ritardare le esecuzioni. `promo-story.yml` e `cleanup-old-workflow-runs.yml` non sono workflow separati presenti in questo repository.

Gli errori temporanei di quota Firestore nella sincronizzazione SEO e nella manutenzione Firebase vengono considerati retryable: il job termina senza segnare un falso successo, cosi il tentativo successivo della stessa campagna puo riprovare.

## Rilevamento sorgente privato

`Sorgente privato - Trigger automatici` usa un controllo orario. Per non perdere modifiche a causa delle run saltate, il watcher prende come riferimento l'ultima run in cui il job `watch` e stato realmente eseguito con successo, non una semplice run completata dal gate.

Quando rileva modifiche applica gli equivalenti dei trigger del repository privato e avvia solo i workflow necessari.

## Workload Identity Federation

I nomi delle Variables WIF sono identici al privato. Tuttavia Google Cloud vede ora come identita OIDC il repository pubblico. Se il provider WIF e limitato esplicitamente al nome del repository privato, occorre autorizzare anche questo repository pubblico nel provider/policy Google Cloud; copiare la stessa Variable da solo non cambia la policy lato Google.

## Test

`Verifica codice e backup` controlla il ramo principale del sorgente privato: accesso, dipendenze e audit, test, backup test, validazione, build statica e build React. Non pubblica il sito. Il rilevamento di una PR avvia questo controllo di main, non certifica il codice della PR.

Il deploy Firebase esegue i test browser pubblici desktop/mobile e il percorso catalogo-scheda-mappa nello stesso job dopo la pubblicazione. Non crea account di test. `Production - Browser smoke test` permette di ripetere il controllo manualmente; attivando `authenticated` verifica anche l'accesso con un account dedicato, già verificato, configurato nei Secrets `SMOKE_TEST_EMAIL` e `SMOKE_TEST_PASSWORD`.

I controlli pubblici non certificano le operazioni amministrative, l'invio email, il ripristino di un backup o la pubblicazione effettiva su Meta. I workflow applicativi usano le stesse Variables e Secrets del privato.
