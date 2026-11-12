# Reversibel »Se bort fra« for opfølgninger (feature-PR)

## Afgrænsning og sikkerhed

- Kun **kortkontrol: geografisk overlap mellem to distriktskort** kan ignoreres. Alle øvrige typer, især genprint, udleveringer, DAR-adresseændringer og øvrige kortkontroller, forbliver synlige. Udvidelser kræver særskilt server-side klassificering af kritikalitet.
- »Se bort fra« er en **manuel, bekræftet handling**, aldrig automatisk. Den fjerner ikke adresser, kort, opgaver eller den oprindelige kontrol.
- Et ignoreret aktuelt overlap vises på fanen **Ignorerede** med seneste aktør og tidspunkt; **Genaktivér** bringer det tilbage til de aktive opfølgninger. Badge, dashboard og øvrige faner tæller kun aktive punkter.
- Adgangen håndhæves på serveren: visning af historikken kræver `cards.view` og `geo.view`; skrivning kræver derudover `geo.edit`. Ingen brugeridentitet accepteres fra klienten.
- Hvis kortoverlappet ikke længere findes, forsvinder den dynamiske opfølgning naturligt. Auditsporet bliver i databasen og backup; samme nøgle kan igen vises, hvis overlappet opstår på ny. Der sker ingen automatisk sletning.

## Database og migration

Ingen ændringer i tabelstruktur, `PRAGMA user_version` eller nye SQLite-filer. Hvert punkt gemmes som et `settings.records`-objekt med `entity='followup_ignore'`, deterministisk hash-ID, kanonisk nøgle, status, nyt opdateringstoken og **append-only `history`**. Hver hændelse indeholder `ignored`, server-tid, bruger-ID og navn (eller »Fælles login / system« uden profiler). Eksisterende backup/gendannelse af databasens settings-posteringer omfatter også disse poster. Tidligere data ændres ikke.

## API-kontrakt

- Eksisterende `POST /api/mutate`, ny `action='followup.ignore'` med `data: {key, ignored: boolean, expected_token: string}`. Nøglen er kanonisk JSON med `['checks','overlap',firstCardId,secondCardId]`, hvor kort-ID'er er sorteret. Serveren validerer strukturen, ikke-arkiverede kort, rettigheder og forventet token.
- Eksisterende `GET /api/state` tilføjer `followup_ignores: [{key,ignored,token,history}]` for autoriserede kort-/geografibrugere. Andre får `[]`; privat data udstilles ikke anonymt.
- Modstridende samtidige writes afvises ved forældet `expected_token`. Klienten skal hente ny tilstand; ændringer overskriver ikke andre brugeres audit.

## Delte filer og afhængigheder

Nyt modul: `distrikt/app/followup_store.py`. Delte: `store.py`, `profile_policy.py`, `workspace.js`, `i18n.js`. Regressionstests: `test_followup_ignore.py`, `test_profiles_integration.py`, `test_followups.cjs`.

**Parallelle PR'er** som ændrer opfølgningsindsamling, fælles klienttilstand, profiltilladelser eller den generelle SQLite-backup kan kræve manuel konfliktløsning. Hold ændringen isoleret fra øvrige igangværende features. Denne branch er oprettet direkte via GitHub-forbindelsen fra `develop`; et fysisk lokalt Git-worktree er ikke tilgængeligt i denne eksekvering, og hævdes ikke oprettet.

## Testmatrix

- Reversibel status: ignorer → reaktiver → ignorer, genåbning af SQLite, originale audit-events bevaret.
- Adgang: kortlæser uden geografi ser ingen status; geografisk læser kan se men ikke ændre; geografiredaktør kan ændre; server ignorerer forfalsket aktør.
- Kollision: to samtidige writes med samme token; kun den første accepteres. Forskellige profilbrugere bevares i audit.
- Sikkerhed: genprint, adresseændringer, udlån og ikke-overlapnøgler kan ikke skjules.
- Frontend: fane »Ignorerede«, tekst, menu-badge og reaktivering kontrolleres med syntetiske data. Eksisterende browser- og CI-tests skal fortsat være grønne.

**Releasepolitik:** PR mod `develop`; ingen merge uden review og grønne checks; ingen Stable-release fra denne feature. Saml godkendte features på `develop`, regressionstest på tværs og udgiv derefter én kontrolleret Stable.
