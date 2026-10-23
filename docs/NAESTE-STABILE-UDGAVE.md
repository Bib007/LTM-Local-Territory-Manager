# Næste stabile LTM · kladde til udgivelsesnoter

Status 23.10.2026: Den stabile kanal er fortsat **1.11.1**. Den verificerede betakanal er **1.12.0-beta.61**. Dette er en kladde til næste stabile udgave, ikke en udgivelsesmeddelelse. Den [afsluttende kontrol](SLUTKONTROL.md) skal være afklaret før promovering til main.

## Det vigtigste siden den stabile grundudgave

- **Kom i gang med eksisterende kort:** samlet opsætningsguide, personlig plan og rundtur. Start med kortnumre og udleveringer; tilføj adresser og kort senere. Importér allerede fordelte kort fra Excel/CSV og gennemgange/udleveringer fra S-13 med lokal forhåndsvisning, kontrol af fejl og dubletter samt særskilt godkendelse.
- **Arbejd med kort og adresser:** kortoversigt, manuel korteditor, samlet distriktsgrænse og KML/GeoJSON-import. Datafordeler-adresser i et udsnit hentes på tværs af postnumre. Større hentninger har delresultater, pause og fortsættelse; midlertidige læsefejl kan genprøves. Kortdata kan indeholde veje, bygninger, vandløb og jernbaner.
- **Daglig administration:** overblik over kort i mappen, udleverede kort og kort i kassen; forkyndere, opgaver, noter og historik. Telefon- og tabletbetjening er forbedret. Gemmestatus kan vise den fulde årsag, hvis en ændring afvises.
- **Print og deling:** betjening til kortforside, IB-bagside, S-13 og rapporter med de eksisterende originalformularer. Valgfri publicering af et gennemgået PNG-kort til Google Drive med QR-link; lokale IB-/forkynder-/udlånsdata indgår ikke i denne billeddeling.
- **Backup og flytning:** privat sikkerhedskopi, kontrolleret gendannelse og læsbar eksport til gennemgang. Forbindelser og API-nøgler er fortsat adskilt fra almindelig data-/PDF-/CSV-eksport.
- **Løbende hjælp:** dansk som hovedsprog, engelsk betjening med angivne begrænsninger og feedbackformular med valgfrie billeder uden krav om en konto. Ingen lokal installationsdata vedhæftes automatisk.

Automatiske forslag til distriktsgrænser og kortinddeling er sat på pause og fjernet fra aktiv app og API. Brug den manuelle korteditor. Eksisterende kort bevares; generatorens kode og prøver ligger i [arkivet](ARKIVERET-AUTOFORDELING.md) til senere udvikling.

## Før opdatering

1. Hent en **privat backup i den app, der faktisk bruges**, og opbevar den udenfor installationen. Appdata er ikke dækket af HA's almindelige backup. Behold den fungerende installation og backup, indtil opdateringen er kontrolleret.
2. Kontrollér den aktuelle stabile versions udgivelsesnoter og [installations-/opdateringsvejledningen](INSTALL.md). En almindelig opdatering af samme installation bevarer datamappen. Flytning mellem forskellige installationer bruger appens kontrollerede eksport/import.
3. Opbevar nødvendige adgangskoder og forbindelsesoplysninger privat. Google-forbindelser og Datafordeler-nøgler følger ikke med den almindelige backup; en flyttet installation kan kræve ny lokal opsætning eller nyt samtykke.
4. Kontrollér efter opdateringen: login, kort og historik, udlevering/aflevering samt eventuelle print- og QR-arbejdsgange. Afprøv gendannelse i en separat prøveinstallation.

Stabil HA og beta er separate installationer med egne data og login. Den stabile app bruger port **8787**; beta bruger **8788**. Installation eller opdatering af beta flytter ikke automatisk data til den stabile app. Se [betavejledningen](BETA.md).

## Kendte begrænsninger, der skal med i den endelige meddelelse

- Adressehentning er afhængig af adressekilde og netforbindelse. Ejeren har 23.10.2026 bekræftet, at API-adressehentningen virker, men opleves langsom. Løbende aktivitet og adresseantal (W82) er planlagt efter næste stabile udgave. Gemte, færdige udsnit bevares; dette er ikke en garanti for, at et vedvarende netproblem forsvinder.
- Natlig adressekontrol er et tilvalg. Egen aktivering, tidszone, faktisk natlig kørsel og fortsættelse efter genstart kontrolleres på installationen, hvis funktionen bruges.
- Fuld engelsk oversættelse er ikke afsluttet. Brugerdata og kanoniske værdier oversættes ikke; originale formularer og relevante rapporttekster er danske.
- Fysisk print, rigtige Google-samtykker/QR-links og ejerens HA/telefon skal kontrolleres lokalt. Fiktive browserprøver erstatter ikke disse prøver.
- Separat krypteret nøglebackup, større ændringer til HA-adgang og flerbrugerredigering er ikke leveret som del af denne kladde. Egen hosting som nyt installationsprodukt er planlagt efter næste stabile udgave.
- Webdemoen er særskilt og bruger fiktive data. Den er ikke ejerens installation og følger ikke nødvendigvis samme funktioner eller versionsnummer.

## Uafklaret før offentliggørelse

API-adressehentning, generel HA-drift samt Drive og gendannelse er ejerbekræftet. Ejeren har besluttet, at W61's eksterne GitHub-oprydning ikke blokerer næste stabile udgivelse; oprydningen er ikke dokumenteret færdig. Relevante print-/QR-prøver og afgrænsningen af W06/W28/W56 skal fremgå af den endelige beslutning. En fuld sikkerhedsscanning er ikke dokumenteret. Åbne punkter må ikke præsenteres som beståede.

Det stabile publiceringsflow på develop kræver de fulde program-/browser-/pakkeprøver samt Mac, Windows og HA-container på samme commit. Kun publiceringsjobbet har skriverettigheder, det kræver main, og eksisterende udgivne versioner overskrives ikke. Flowet erstatter ikke de lokale ejerprøver eller beslutningen om at promovere en version til main.

Før publicering omskrives denne kladde med det valgte stabile versionsnummer, endelig afgrænsning, verificerede pakkechecksums og afsluttede ejerprøver. Brugeren skal kunne se nyheder og opdateringsvej uden at læse hele betahistorikken.
