# S-13 på mobil og robust rapportkort uden OpenStreetMap

Dato: 11. november 2026 · feature-branch: `fix/s13-mobile-osm-fallback-20261111` · mål: `develop`.

## Ændringer og årsager

- **S-13 på skærm:** Den originale formular gengives fortsat med sin PDF-opmålte SVG-viewBox og originale baggrund, men SVG'en skaleres nu responsivt inden for telefonens/tablettens bredde. Forhåndsvisningen vises på rapportsiden uden at åbne Print. Print-dokumentets egne A4-regler (15 mm margener) er uændrede.
- **OSM på mobil:** Leaflet-kortet får et ekstra `invalidateSize` efter layout; dette mindsker risikoen for en forkert beregnet kortstørrelse ved initial mobilvisning og rotation. Kortlaget benytter fortsat HTTPS og CORS, som er nødvendigt for at kopiere rasterfliser til print-canvas.
- **Fejl ved OSM:** Blokerede fliser (`tileerror`), manglende Leaflet-bibliotek eller langvarig indlæsning får en tydelig fejlmeddelelse. De to handlinger er **Prøv igen** og **Generér uden baggrundskort**. Ingen langvarig spinner uden timeout.
- **Kortfri generering:** Kortbaggrunden er *valgfri*. Ved kortfri generering tegnes eksisterende distriktsgrænser, fuldførelsesfarver, distriktsnumre og samlet distriktsgrænse i en selvstændig SVG baseret på de gemte koordinater. De tre rapportperioder, registerdata, A4-print og S-13-appendiks genereres stadig.
- **Fejlet rastercapture:** Browserens canvas kan afvise tegning fra fremmede rasterfliser pga. CORS eller billedfejl. Korteksporten giver en fejl, som kan løses ved at vælge kortfri generering; den sletter ingen data. Der er ikke bygget en browser-specifik omgåelse af CORS.

## Afhængigheder og samtidighed

| Type | Ændring / kontrakt |
| --- | --- |
| Database | **Ingen migrering, nye felter eller ændring i databasefiler** |
| HTTP/API | **Ingen ændring i endpoint, payload eller API-kontrakt** |
| Delte front-end-filer | `distrikt/app/report-map.js`, `report-print.js`, `app.js`, `style.css` |
| Test/CI | `distrikt/tests/test_report_mobile_fallback.cjs`, `scripts/check_report_mobile_browser.cjs`, `.github/workflows/check.yml` |
| Andet arbejde | Løs konflikter i ovennævnte filer, før denne PR flettes. Ændr ikke `main`, release-workflows eller versionsnumre. |

Alle tests skal benytte opdigtede grænser, numre, personer og adresser. Testning må aldrig læse eller ændre menighedens virkelige distrikt-/IB-data.

## Automatiseret testplan

- Node/V8-kontrakter: S-13-SVG uden Print, original A4-stil, fejlvalg, kortfri SVG og uændrede fiktive adresselister.
- Playwright: mobil Safari-lignende **WebKit** og **Chromium**; iPhone portræt/landskab, Android-viewport, iPad portræt/landskab og desktop.
- Mockede kortfliser: kun fiktive HTTPS-billeder; succes, langsomt net, offline, blokerede fliser og timeout. Testen kontrollerer S-13-aspect ratio, ingen horisontal overflow, kortoverlejringer, fallback-handlinger og at tegningen ikke går i uendelig loading.
- Chromium PDF: kontrollerer A4 MediaBox. De eksisterende IB-printtests og alle øvrige CI-checks skal stadig være grønne.
- Browserens CORS/canvas-tegning kontrolleres med syntetisk tile-respons. Virkelig belastning af `tile.openstreetmap.org` udføres **ikke** i automatiserede tests.

## Begrænsninger og fysisk verifikation

Ingen fysisk iPhone, iPad, Android-telefon/-tablet, Mac eller Windows-PC er blevet testet som led i denne kodeændring. WebKit/Chromium i automatiserede headless-browsere er emulering, ikke fysisk hardware eller en garanti for alle Safari-versioner.

Før godkendt merge bør en reviewer på virkelige enheder kontrollere: S-13 kan ses i appen uden Print, rotation og zoom, A4/PDF-udskrift, langsomt Wi-Fi/offline-kort og begge fejlknapper. Bekræft også privatliv og ingen deling af virkelige IB-oplysninger.

## Git- og releaseproces

Oprettet som en selvstændig branch fra seneste kendte `develop` og committet udelukkende på den. Der er **ikke** oprettet en lokal Git-worktree, da ændringerne blev udført gennem GitHub-forbindelsen uden lokal repository-checkout. Lokalt arbejde i en separat worktree skal i givet fald udføres af en udvikler ved checkout.

PR'en skal forblive åben, indtil review, alle relevante CI-checks og den samlede regression er grønne. Derefter kan godkendte PR'er samles på `develop`; ingen Stable-release udføres af denne ændring.
