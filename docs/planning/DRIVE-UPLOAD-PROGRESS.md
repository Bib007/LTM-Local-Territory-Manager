# Google Drive-upload: synlig status og sikker genprøve

## Omfang og faser

Funktionen ved **Opdater Google Drive-upload** og **Vis husnumre og streger på kortet** viser nu kun en aktiv spinner under et trin, som faktisk udføres:

- **Forbereder** når kortdata/grundlag hentes og kontrolleres.
- **Genererer** mens SVG/PNG og eventuelt datooverlejring dannes.
- **Færdig med forhåndsvisningen** når det lokale billede er klar — **ikke** en påstand om vellykket upload.
- **Gemmer i uploadkøen** når godkendelsen sendes til den lokale server.
- **Venter på upload** mens serverens job ligger i kø eller afventer et automatisk nyt forsøg. Ingen upload-spinner.
- **Uploader til Google Drive** kun når serverens worker faktisk kalder Google Drive-uploaden. Signalet er en ikke-persistent `upload_active`-værdi i status-API'et.
- **Færdig** først når serverens status angiver `ready` eller `published`, og kortet stadig er aktuelt. Fejl vises med forklaring og den eksisterende server-side **Prøv upload igen**.

Når generering af ændrede husnumre/streger fejler, bevares den tidligere PNG og det tidligere valg; særskilt **Prøv igen** danner en ny forhåndsvisning. Godkendelse nulstilles ved ændring, og publicering kan ikke starte, mens billedet genereres. Den lokale publiceringsknap og serversidens idempotens kontrollerer dobbeltklik/lost-ack genforsøg.

## API og opbevaring

- `POST /api/share/publish`: Nyt **valgfrit** felt `request_id` (12–100 tegn; a-z/A-Z/0-9/_/-). Samme ID for samme kort returnerer den eksisterende køstatus uden at overskrive køen eller starte en ekstra upload. Eksisterende klienter uden feltet fungerer uændret.
- `GET /api/share/status`: Nyt boolesk felt `upload_active` pr. kort. Det er en **runtime-observation**, ikke en vedvarende status, og bliver `false` efter en fejl eller afsluttet API-kald. `request_id` returneres ikke i status.
- Ingen skema-/databasemigration. `request_id` gemmes i eksisterende publiceringsmetadata for at overleve genstart og mistet HTTP-svar. `upload_active` gemmes **ikke** i databasen.
- Eksisterende `queued`/`retry`/`failed`/`ready`/`published` og QR-/Google-fil-ID-forløb bevares. En uventet afbrydelse efter Googles succes, men før Google returnerer fil-ID, kan ikke garanteres deduplikeret hos Google alene; overvåg og undersøg sådanne tilfælde før automatisk gentagelse af en helt ny fil.
- Ingen ændring af de røde besøgspunkter. `showHouseNumbers` er kun et renderingsvalg for nummeretiketter og streger; `MapExport.publicVisitLayout` beholder punkterne.

## Parallel udvikling og sammenfletning

Arbejdet er afgrænset til feature-branchen `feature/drive-upload-progress-20261111`, oprettet fra `develop`. Ændringer skal reviewes og CI være grøn før merge til `develop`; der udgives **ingen Stable** her. GitHub-forbindelsen stiller kun repository-operationer til rådighed og kan ikke etablere et lokalt separat Git-worktree i denne session; branchisolering og små commits er anvendt, uden at ændre `develop` eller `main`.

Delte filer med konfliktrisiko: `distrikt/app/share-ui.js`, `distrikt/app/sharing.py`, `distrikt/app/i18n.js`, `distrikt/app/style.css`. Tests: `distrikt/tests/test_sharing.py`, `distrikt/tests/test_share_workflow_language.cjs`. Aftal rebase af den isolerede branch, når samtidige UI-/kortændringer rammer disse filer.

## Verificering med fiktive kort

- `python -m unittest distrikt.tests.test_sharing -v` — idempotent indkøning, slow worker, afbrudt Google-kald, retry, succes.
- `node distrikt/tests/test_share_workflow_language.cjs` — langsom rendering, parallelle klik, renderingfejl og genprøve; kø vs. faktisk upload; ny publicerings-ID og uændret godkendelsesformat.
- `node distrikt/tests/test_digital_card.cjs` — med/uden husnumre og streger; samme antal røde prikker.
- `node scripts/check_share_image_browser.cjs` med Playwright — PNG-forhåndsvisning og valgmuligheder i en rigtig browser med fiktive data.
- PR-CI `.github/workflows/check.yml` — Python, JavaScript, browser og øvrige kontrakter.

Ingen rigtig Google-konto, private kort eller autentificeringsfiler bruges i test.
