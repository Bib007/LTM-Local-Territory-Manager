# Køreplan · næste version

**Samlet færdig: 40 % · 4 af 10 opgaver afsluttet.**

Hver afsluttet opgave giver 10 procentpoint efter implementering, relevante prøver og lagring på GitHub. Procenten gælder denne plan. Stabil grundudgave 1.11.1 og almindelig HA-installation følger main.

| Nr. | Opgave | Status | Samlet efter opgaven |
| --- | --- | --- | --- |
| 1 | Kortoversigt og filtre med bevaret kortposition | Færdig og prøvet | 10 % |
| 2 | Adresser, IB/genprintlister og kortkontrol | Færdig og prøvet | 20 % |
| 3 | Kortredigering, samlet grænse og import | Færdig og prøvet | 30 % |
| 4 | Avanceret opsætning og lokal IB-import | Færdig og prøvet | 40 % |
| 5 | Google Drive og QR med opdigtede svar | Næste | 50 % |
| 6 | Fælles fejl, bekræftelser og usikker gemning | Afventer | 60 % |
| 7 | Login, tastatur og fokus | Afventer | 70 % |
| 8 | Printbetjening med uændrede originalformularer | Afventer | 80 % |
| 9 | Samlet programpakke og verifikation | Afventer | 90 % |
| 10 | Samlet kontrol, dokumentation og manuel restliste | Afventer | 100 % |

Opgave 4 kontrolleres med `test_setup_workflow_language.cjs` og samme offline-browserprøve: uændrede typer/nummerering, samme skrivepayload og danske bekræftelsesord på begge sprog, bevaret opsætningskort/kladdenavne og IB-kontrol ved sprogskift, ombyttede filindlæsninger samt ugyldiggørelse ved ændret dato, område, revision eller navigation. IB-fejl spærrer godkendelse. Ingen privat fil er brugt.

Opgave 3 kontrolleres med `test_geo_workflow_language.cjs` og den gentagelige offline-browserprøve `scripts/check_geo_browser.cjs` (Playwright som isoleret udviklingsværktøj). Prøverne dækker kanoniske formularværdier, uændrede brugerdata, kort/zoom/fokus/indtastninger ved sprogskift, importfil/valg, sene og ombyttede svar, annullering, kopierede gemmepayloads og nyere tegninger under gemning. Browserprøven kræves også af HA-beta-gaten. Mobilbredt kortvalg er rettet efter visuel kontrol.

Opgave 1 kontrolleres med `test_map_overview_language.cjs`; opgave 2 med `test_address_workflow_language.cjs`. Fiktive Chromium-arbejdsgange har prøvet bevaret kortinstans, søgning, faner og 320/390/768/1440 pixels. Der er ikke brugt private registreringer.

Fysisk print, eget Google-samtykke og hjemmenetværket er særskilte ejertrin. Udviklingsprøver bruger opdigtede data og offentliggør ikke rigtige kort.

## Aktuel arbejdsrækkefølge · 17.10.2026

Ejeren har prioriteret at få den faste køreplan færdig. Ønskelisten sættes på pause. Punkt 3 afsluttes før punkt 4, og derefter fortsættes med de øvrige faste punkter. Nummererede HA-betaer og statusopdatering fortsætter; main er stabil.

Punkt 3 omfatter dansk/engelsk betjening i korteditor, samlet grænse og grænseimport, uændrede data-/formularkontrakter, bevaret kort/kladde ved sprogskift og beskyttelse mod forsinkede svar, der ellers kunne erstatte en nyere tegning. Det verificeres med fiktive arbejdsgange, geometri-/lagringsprøver og relevante program-/platform-/pakkekontroller. Backendfejl og resterende generelle fejltekster hører til punkt 6.

## Nye ønsker

Se [ønskelisten](OENSKELISTE.md) for førstegangsopsætning, guidet rundtur, Excel-import og ejerprioriteter. Opstart og eksisterende kortimport er færdige på develop. De resterende ønsker afventer nu den faste køreplan; se aftalen ovenfor. De nye ønsker ændrer ikke automatisk procentberegningen.

## Løbende betaprøver

Små afsluttede funktioner skal fremover udgives som nummererede HA-betaer med en kort konkret testliste. Det nye ejerønske W19 har prioritet -1. Betakanalen er adskilt fra stabil; betaudgivelser ændrer ikke i sig selv de faste ti opgavers procenttal.
