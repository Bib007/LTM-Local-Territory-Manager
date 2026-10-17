# Køreplan · næste version

**Samlet færdig: 50 % · 5 af 10 opgaver afsluttet.**

Hver afsluttet opgave giver 10 procentpoint efter implementering, relevante prøver og lagring på GitHub. Procenten gælder denne plan. Stabil grundudgave 1.11.1 og almindelig HA-installation følger main.

| Nr. | Opgave | Status | Samlet efter opgaven |
| --- | --- | --- | --- |
| 1 | Kortoversigt og filtre med bevaret kortposition | Færdig og prøvet | 10 % |
| 2 | Adresser, IB/genprintlister og kortkontrol | Færdig og prøvet | 20 % |
| 3 | Kortredigering, samlet grænse og import | Færdig og prøvet | 30 % |
| 4 | Avanceret opsætning og lokal IB-import | Færdig og prøvet | 40 % |
| 5 | Google Drive og QR med opdigtede svar | Færdig og prøvet | 50 % |
| 6 | Fælles fejl, bekræftelser og usikker gemning | I gang · beta.17 | 60 % |
| 7 | Login, tastatur og fokus | Afventer | 70 % |
| 8 | Printbetjening med uændrede originalformularer | Afventer | 80 % |
| 9 | Samlet programpakke og verifikation | Afventer | 90 % |
| 10 | Samlet kontrol, dokumentation og manuel restliste | Afventer | 100 % |

Opgave 5 kontrolleres med `test_share_workflow_language.cjs`, de eksisterende private/offentlige billed- og delingsprøver samt den udvidede offline-browserprøve. Fiktive status-/opskrifts-/QR-svar dækker samme offentlige godkendelses-payload på begge sprog, bevaret billede/checkbox/QR ved sprogskift, nyeste polling, sene previews, ændret revision, annulleret forbindelsesfil, dobbelt publicering og bevaret nyere dialog/navigation. Browserprøven bruger et genereret prøve-PNG til samtykkeforløbet; den kontakter ikke Google. Eget Google-samtykke og faktisk adgang fra telefon er fortsat ejertrin.

Opgave 4 kontrolleres med `test_setup_workflow_language.cjs` og samme offline-browserprøve: uændrede typer/nummerering, samme skrivepayload og danske bekræftelsesord på begge sprog, bevaret opsætningskort/kladdenavne og IB-kontrol ved sprogskift, ombyttede filindlæsninger samt ugyldiggørelse ved ændret dato, område, revision eller navigation. IB-fejl spærrer godkendelse. Ingen privat fil er brugt.

Opgave 3 kontrolleres med `test_geo_workflow_language.cjs` og den gentagelige offline-browserprøve `scripts/check_geo_browser.cjs` (Playwright som isoleret udviklingsværktøj). Prøverne dækker kanoniske formularværdier, uændrede brugerdata, kort/zoom/fokus/indtastninger ved sprogskift, importfil/valg, sene og ombyttede svar, annullering, kopierede gemmepayloads og nyere tegninger under gemning. Browserprøven kræves også af HA-beta-gaten. Mobilbredt kortvalg er rettet efter visuel kontrol.

Opgave 1 kontrolleres med `test_map_overview_language.cjs`; opgave 2 med `test_address_workflow_language.cjs`. Fiktive Chromium-arbejdsgange har prøvet bevaret kortinstans, søgning, faner og 320/390/768/1440 pixels. Der er ikke brugt private registreringer.

Fysisk print, eget Google-samtykke og hjemmenetværket er særskilte ejertrin. Udviklingsprøver bruger opdigtede data og offentliggør ikke rigtige kort.

## Punkt 6 · første del, beta.16

Fælles fejl skelner mellem læsning, afvisning, udløbet login, usikker skrivning og bekræftet gemning med fejlet genindlæsning. Usikre resultater stopper ventende skrivninger og autosave uden automatisk gensendelse. Eksplicit Opdater kræver afsluttet redigering og henter et nyt datasnapshot; forbindelsestjek ophæver ikke spærringen. Administrative previews bindes til formular, værdier og revision og beskytter mod dobbeltklik/sene svar. `test_request_safety.cjs`, `test_confirmation_safety.cjs`, adresseprøver og offline Chromium dækker disse forløb med opdigtede data.

Beta.17 fortsætter med gendannelse og beta-nulstilling: dobbeltanmodninger blokeres, sene svar bevarer nyere dialoger/navigation, og fejlet læsning efter bekræftet skrivning kræver kontrol frem for gentagelse. `test_transfer_safety.cjs` og offline Chromium med et forsinket import-svar dækker de nye forløb. Ingen rigtig backup er åbnet.

Beta.16 (`456f327`) og beta.17 (`0b3f715`) er verificeret udgivet med grøn Checks, Platformskontrol og HA beta release samt ZIP og checksum. Lokalt består 341 Python-prøver (én forventet overspringning), alle JavaScript-prøver, 7 program- og 3 betapakkeprøver samt offline Chromium ved fire bredder. Main er uændret `842541a` / 1.11.1.

Punktet er ikke færdigt: domænespecifikke fejltekster og øvrige skrive-/bekræftelsesforløb skal gennemgås. Næste konkrete kontrol er efterfølgende navigation/dialogåbning ved noter, IB og omstrukturering samt faste og parameteriserede backendfejl. Procenten forbliver 50 %. Derefter følger punkt 7, ikke ønskelisten.

## Aktuel arbejdsrækkefølge · 17.10.2026

Ejeren har prioriteret at få den faste køreplan færdig. Ønskelisten er på pause. Punkt 3–5 er afsluttet; punkt 6 er aktuelt, derefter følger 7–10 i rækkefølge. Nummererede HA-betaer og statusopdatering fortsætter; main er stabil.

Punkt 3 omfatter dansk/engelsk betjening i korteditor, samlet grænse og grænseimport, uændrede data-/formularkontrakter, bevaret kort/kladde ved sprogskift og beskyttelse mod forsinkede svar, der ellers kunne erstatte en nyere tegning. Det verificeres med fiktive arbejdsgange, geometri-/lagringsprøver og relevante program-/platform-/pakkekontroller. Backendfejl og resterende generelle fejltekster hører til punkt 6.

## Nye ønsker

Se [ønskelisten](OENSKELISTE.md) for førstegangsopsætning, guidet rundtur, Excel-import og ejerprioriteter. Opstart og eksisterende kortimport er færdige på develop. De resterende ønsker afventer nu den faste køreplan; se aftalen ovenfor. De nye ønsker ændrer ikke automatisk procentberegningen.

## Løbende betaprøver

Små afsluttede funktioner skal fremover udgives som nummererede HA-betaer med en kort konkret testliste. Det nye ejerønske W19 har prioritet -1. Betakanalen er adskilt fra stabil; betaudgivelser ændrer ikke i sig selv de faste ti opgavers procenttal.
