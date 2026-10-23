# Køreplan · næste version

**Samlet færdig: 100 % · 10 af 10 udviklingsopgaver afsluttet.**

Hver afsluttet opgave giver 10 procentpoint efter implementering, relevante prøver og lagring på GitHub. Procenten gælder denne plan. Stabil grundudgave 1.11.1 og almindelig HA-installation følger main.

| Nr. | Opgave | Status | Samlet efter opgaven |
| --- | --- | --- | --- |
| 1 | Kortoversigt og filtre med bevaret kortposition | Færdig og prøvet | 10 % |
| 2 | Adresser, IB/genprintlister og kortkontrol | Færdig og prøvet | 20 % |
| 3 | Kortredigering, samlet grænse og import | Færdig og prøvet | 30 % |
| 4 | Avanceret opsætning og lokal IB-import | Færdig og prøvet | 40 % |
| 5 | Google Drive og QR med opdigtede svar | Færdig og prøvet | 50 % |
| 6 | Fælles fejl, bekræftelser og usikker gemning | Færdig og prøvet · beta.20 | 60 % |
| 7 | Login, tastatur og fokus | Færdig og prøvet · beta.21 | 70 % |
| 8 | Printbetjening med uændrede originalformularer | Færdig og prøvet · beta.22 | 80 % |
| 9 | Samlet programpakke og verifikation | Færdig og prøvet · beta.22 | 90 % |
| 10 | Samlet kontrol, dokumentation og manuel restliste | Færdig og prøvet · beta.22 | 100 % |

Opgave 5 kontrolleres med `test_share_workflow_language.cjs`, de eksisterende private/offentlige billed- og delingsprøver samt den udvidede offline-browserprøve. Fiktive status-/opskrifts-/QR-svar dækker samme offentlige godkendelses-payload på begge sprog, bevaret billede/checkbox/QR ved sprogskift, nyeste polling, sene previews, ændret revision, annulleret forbindelsesfil, dobbelt publicering og bevaret nyere dialog/navigation. Browserprøven bruger et genereret prøve-PNG til samtykkeforløbet; den kontakter ikke Google. Eget Google-samtykke og faktisk adgang fra telefon er fortsat ejertrin.

Opgave 4 kontrolleres med `test_setup_workflow_language.cjs` og samme offline-browserprøve: uændrede typer/nummerering, samme skrivepayload og danske bekræftelsesord på begge sprog, bevaret opsætningskort/kladdenavne og IB-kontrol ved sprogskift, ombyttede filindlæsninger samt ugyldiggørelse ved ændret dato, område, revision eller navigation. IB-fejl spærrer godkendelse. Ingen privat fil er brugt.

Opgave 3 kontrolleres med `test_geo_workflow_language.cjs` og den gentagelige offline-browserprøve `scripts/check_geo_browser.cjs` (Playwright som isoleret udviklingsværktøj). Prøverne dækker kanoniske formularværdier, uændrede brugerdata, kort/zoom/fokus/indtastninger ved sprogskift, importfil/valg, sene og ombyttede svar, annullering, kopierede gemmepayloads og nyere tegninger under gemning. Browserprøven kræves også af HA-beta-gaten. Mobilbredt kortvalg er rettet efter visuel kontrol.

Opgave 1 kontrolleres med `test_map_overview_language.cjs`; opgave 2 med `test_address_workflow_language.cjs`. Fiktive Chromium-arbejdsgange har prøvet bevaret kortinstans, søgning, faner og 320/390/768/1440 pixels. Der er ikke brugt private registreringer.

Fysisk print, eget Google-samtykke og hjemmenetværket er særskilte ejertrin. Udviklingsprøver bruger opdigtede data og offentliggør ikke rigtige kort.

## Punkt 8–10 · afslutning af den faste plan

Beta.22 afslutter printbetjening, programpakke og slutkontrol. Printdialogens felter/valg bevares ved sprogskift. Popup-knapper følger det valgte sprog; selve kort- og rapportindholdet og S-12-/S-13-originalerne bevares. Dobbeltklik, sene aktiver, ændrede felter/revisioner/navigation og nyere dialoger er kontrolleret. Fejlet billedafkodning spærrer print. Profilgemning godkender aldrig genprint.

`test_print_workflow.cjs`, rapportprøver og udvidet `check_geo_browser.cjs` dækker dette med opdigtede data, faktiske indlejrede printbilleder og browser-PDF af front, bagside og samlet rapport ved 320/390/768/1440 pixels. Smal/bred printdialog og originalkort er visuelt kontrolleret. De 347 Python-prøver (én forventet overspringning), alle JavaScript-prøver og 12 pakkeprøver består lokalt.

Pakkekontrollen fandt seks eksisterende brudte vejledningslinks. De linkede filer følger nu med; alle relative Markdown-links kontrolleres ved pakning. Original S-12-PDF er et krævet aktiv. Den komplette program-ZIP og separate HA-beta er bygget med checksum; identiske inddata giver identiske ZIP-filer. GitHub-gates kontrollerer desuden Python-varianter, Mac, Windows og HA før betaudgivelse. Status for udgivelsen skal læses på GitHub; lokale prøver er ikke i sig selv en udgivelse.

Se [printvejledning](../PRINT.md), [slutkontrol](../SLUTKONTROL.md) og [lokal restliste](../help/Dette-skal-hjaelpes-manuelt.md). Fysisk print, egen HA/telefon/VPN, eget Google-/Datafordeler-samtykke og eventuel skærmlæser er udtrykkeligt ejerprøver. Main er fortsat stabil 1.11.1. Ønskelisten er ikke behandlet i denne afslutning.

## Punkt 7 · login, tastatur og fokus

Beta.21 har dansk/engelsk login uden genskabte felter, dobbelt indsendelse, uendelig ventetid eller lagring af kode som præference. Den offentlige loginfil har en lille selvstændig oversættelse; generel app-sprogfil og data forbliver loginbeskyttede. Adgangskontrol/cookies/rategrænse er uændrede. Dialoger navngives fra overskrift, almindelige feltlabels forbindes, startfokus prioriteres, Tab/Shift+Tab afgrænses, og fokus returneres til åbneren efter lukning/genoptegning. Escape beholder gemmekontrollen.

`test_login_ui.cjs`, `test_dialog_focus.cjs`, LAN-prøver, `check_access_browser.cjs` og den udvidede app-browserprøve dækker fiktivt login i begge kanaler ved fire bredder, metadata/felter/payloads, native dialogfokus, tastatur og afvist Escape ved usikker gemning. Smalt/bredt login er visuelt kontrolleret. Egen HA/telefon/skærmlæser er særskilte ejerprøver. Samlet 70 % (7/10); næste er punkt 8 med uændrede originalformularer.

## Punkt 6 · beta.16–20

Fælles fejl skelner mellem læsning, afvisning, udløbet login, usikker skrivning og bekræftet gemning med fejlet genindlæsning. Usikre resultater stopper ventende skrivninger og autosave uden automatisk gensendelse. Eksplicit Opdater kræver afsluttet redigering og henter et nyt datasnapshot; forbindelsestjek ophæver ikke spærringen. Administrative previews bindes til formular, værdier og revision og beskytter mod dobbeltklik/sene svar. `test_request_safety.cjs`, `test_confirmation_safety.cjs`, adresseprøver og offline Chromium dækker disse forløb med opdigtede data.

Beta.17 fortsætter med gendannelse og beta-nulstilling: dobbeltanmodninger blokeres, sene svar bevarer nyere dialoger/navigation, og fejlet læsning efter bekræftet skrivning kræver kontrol frem for gentagelse. `test_transfer_safety.cjs` og offline Chromium med et forsinket import-svar dækker de nye forløb. Ingen rigtig backup er åbnet.

Beta.16 (`456f327`) og beta.17 (`0b3f715`) er verificeret udgivet med grøn Checks, Platformskontrol og HA beta release samt ZIP og checksum. Lokalt består 341 Python-prøver (én forventet overspringning), alle JavaScript-prøver, 7 program- og 3 betapakkeprøver samt offline Chromium ved fire bredder. Main er uændret `842541a` / 1.11.1.

Beta.18 beskytter de efterfølgende dialog-/navigationshandlinger ved noter, IB og omstrukturering. Previewet bindes til formularens værdier, alle valgte adresser og revisionen; bekræftelsen kræver uændret kontrol og blokerer dobbeltklik. Nyere lokale tegninger og filtervalg bevares også ved sene gemmesvar. `test_write_followups.cjs` og offline Chromium dækker normale og forsinkede forløb.

Beta.19 lokaliserer faste og parameteriserede fejl fra kort, adresser, udlån, IB, opsætning, administration og backup. Oprindelig dansk fejltekst bevares; navne, numre og talgrænser behandles som data og oversættes ikke. Kildekataloget kontrolleres mod Python-raises i de syv kernemoduler. HTTP-/UI-/Chromium-prøver kontrollerer afvisning uden skrivning, sprogskift, IB-linjefejl og sikre fallback-beskeder. Tekniske fejl fra eksterne tjenester kan fortsat vises uændret som diagnostik.

Beta.20 afslutter punkt 6: særskilte opsætnings-, IB-/kortimport-, delings- og onboarding-skrivninger bruger fælles kvitterings-/læsefasekontrol. Nyere sessioner, formularer og snapshots bevares; bekræftet skrivning med fejlet efterfølgende læsning kræver Opdater frem for gentagelse. `test_special_write_safety.cjs` og offline Chromium dækker oprettelse med fejlet læsning og kontrol uden dobbeltskrivning. Supplerende hændelsesprøver dækker lokale billedvalg, downloads, farver, Se bort fra og nye oprydningskontroller. Samlet 60 % (6/10). Herefter punkt 7: login, tastatur og fokus. Ønskelisten er fortsat på pause.

## Aktuel arbejdsrækkefølge · 17.10.2026

Ejeren har prioriteret at få den faste køreplan færdig. Ønskelisten er på pause. Punkt 1–10 er nu afsluttet i udviklingskoden. Ønskelisten er ikke genoptaget i denne afslutning. Nummererede HA-betaer og statusopdatering fortsætter; main er stabil.

Punkt 3 omfatter dansk/engelsk betjening i korteditor, samlet grænse og grænseimport, uændrede data-/formularkontrakter, bevaret kort/kladde ved sprogskift og beskyttelse mod forsinkede svar, der ellers kunne erstatte en nyere tegning. Det verificeres med fiktive arbejdsgange, geometri-/lagringsprøver og relevante program-/platform-/pakkekontroller. Backendfejl og resterende generelle fejltekster hører til punkt 6.

## Nye ønsker

Se [ønskelisten](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/develop/OENSKELISTE.md) for førstegangsopsætning, guidet rundtur, Excel-import og ejerprioriteter. Opstart og eksisterende kortimport er færdige på develop. Den faste køreplan er afsluttet; de resterende ønsker står fortsat i deres egen kø. De nye ønsker ændrer ikke automatisk procentberegningen.

## Løbende betaprøver

Små afsluttede funktioner skal fremover udgives som nummererede HA-betaer med en kort konkret testliste. Det nye ejerønske W19 har prioritet -1. Betakanalen er adskilt fra stabil; betaudgivelser ændrer ikke i sig selv de faste ti opgavers procenttal.

Den faktiske pakkestart afslørede en gammel versionsetiket i API-svaret. Appens viste version følger nu den kørende servers version; HTTP-prøven kontrollerer begge kanaler mod ping.

## Efter fast plan · ønskelisten genoptaget

17.10.2026: Ejeren har godkendt fortsættelse på ønskelisten. W25/W26 (prioritet 2) samler den normale guide og obligatorisk rundtur med afslutning. W27 (prioritet 3) følger op på adresseimport, januarfrist og egen API-nøgle. Se OENSKELISTE.md. De nye ønsker ændrer ikke den afsluttede faste plans 100 %.
