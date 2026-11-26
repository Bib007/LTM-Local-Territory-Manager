# Massehandling: udvalgte distriktskort i mappen

## Formål og arbejdsgang

I **Distriktskort → Liste** afkrydses konkrete kort. Valget bevares, når man søger, skifter område eller statusfilter; “Vælg viste kort” udvider kun med de kort, der aktuelt er synlige. Oversigten viser alle valgte kort og markerer udleverede og allerede flyttede kort med årsag. Tryk **Læg N i mappen**, kontrollér antal, kortnumre og de kort der springes over, og bekræft. Resultatet viser kortnumre for succes og fejl hver for sig. Kun succesfuldt flyttede kort fravælges.

En enkelt statusændring bevarer kort-ID, kortnummer, adresser, udleveringer, gennemgange og IB. Der oprettes **ikke** en udleverings-/gennemgangsbegivenhed ved flytning til mappen; den eksisterende aktivitetslog beskriver placeringen. Eksisterende status- og beholdningsoversigter opdateres fra det seneste server-snapshot uden manuel genindlæsning.

## API og datakontrakt

Ny handling via eksisterende `POST /api/mutate`: `folder.set_many`.

```json
{"action":"folder.set_many","data":{"ids":["fictional-card-a","fictional-card-b"],"in_folder":true,"expected_in_folder":false},"include_state":true}
```

Den kræver præcis samme tilladelser som `folder.set`: `cards.view`, `loans.view`, `loans.manage`. Serveren afviser ugyldige/duplikerede ID'er, 0 eller over 500 kort, og ukorrekt destination/forventet tilstand **før** behandling. Svaret indeholder `result.count`, `result.updated: string[]` og `result.skipped: {id,reason}[]` samt den sædvanlige revision, session-snapshot og ved `include_state` den opdaterede tilstand.

Hele handlingen kører med eksisterende databaselås og transaktion. Hvert kort går igennem den eksisterende `folder.set`-kontrol (aktivt udlån og forventet placering). Ugyldige/ændrede kort afvises enkeltvis; andre kort behandles. Uventede database-/systemfejl ruller transaktionen tilbage frem for at give et misvisende delvist resultat. Når samme bekræftelse gentages, er allerede flyttede kort afvist uden ekstra skrivning eller aktivitetsregistrering. Frontend blokerer desuden dobbelt bekræftelse, og eksisterende WriteGuard kræver eksplicit kontrol ved usikre netværkssvar.

## Afhængigheder og parallel udvikling

- **Database:** Ingen skemaændringer, migration eller genberegning af historik. Bruger eksisterende `cards.in_folder`, aktive `loans`, revisions-/aktivitetslog og fortrydelsesmekanisme.
- **API:** Additiv handling; den oprindelige `folder.set`-kontrakt er urørt. Resultatet af `mutate()` gøres nu tilgængeligt for UI-kaldere uden at ændre forespørgsel eller opdateringsrækkefølge.
- **Delte filer:** `distrikt/app/store.py`, `profile_policy.py`, `app.js`, `admin.js`, `i18n.js`, den eksisterende browser-test og profil-integrationstesten. Andre parallelle PR'er, der ændrer disse filer eller kortidentifikatorer/visningsnumre, skal konflikttjekkes og testes igen før merge.
- **Kortidentitet:** API'et bruger teknisk `card.id`, aldrig det menneskelige kortnummer. En senere feature med offentlige/interne numre skal fortsat levere den samme stabile ID.
- **Releases:** Feature-PR alene mod `develop`. Ingen merge uden review/grøn CI, og ingen Stable-release som del af denne opgave.

## Kontrol

Fiktive data, ingen rigtige adresser eller personoplysninger:

```sh
python -m unittest distrikt.tests.test_folder_many -v
python -m unittest distrikt.tests.test_profiles_integration -v
node distrikt/tests/test_folder_many.cjs
node scripts/check_english_forms_browser.cjs
```

Dækker 0/1/mange, ugyldige/duplikerede ID'er, gentagelser, flere filtre, blandede placeringer, ændring mellem preview og bekræftelse, tilladelsesafslag og to samtidige brugere. Playwright-scriptet kræver installeret browser og er også del af den øvrige CI. Fysiske mobil-/tabletenheder og rigtige menighedsdata bruges ikke i disse tests.

## Tilbageførsel

Ændringen kan fjernes ved at revert'e PR'en uden migration. Den eksisterende kortaktivitet/fortrydelsesmekanisme håndterer de almindelige kortplaceringer; operatøren skal kontrollere den aktuelle status før eventuel manuel tilbageflytning, fordi kort kan være udleveret i mellemtiden.
