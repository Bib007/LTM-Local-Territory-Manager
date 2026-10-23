# Slutkontrol af den faste køreplan

[English](SLUTKONTROL.en.md)

Kontrolgrundlag: beta.62 er verificeret udgivet 23.10.2026 fra kildecommit f94b9c29c6e114f035f9b7ee6516e0f939ddcf46. Program-, browser-, Mac-, Windows-, HA- og pakkekontroller er bestået. Det tidligere afbrudte Mac-job er genkørt uden kodeændring, og HA-udgivelsesgaten er completed/success. Main er fortsat stabil 1.11.1. Den faste udviklingsplan er afsluttet; hele ønskekøen er ikke et krav til næste stabile udgave.

## Gentagelige kontroller

- Python: `python -m unittest discover -s distrikt/tests -v`. Prøverne bruger midlertidige mapper og opdigtede data. Den tidligere private ZIP er ikke medleveret, og dens opgraderingsprøve springes udtrykkeligt over.
- JavaScript: kør hver `distrikt/tests/test_*.cjs` med `TZ=Europe/Copenhagen`. Den nye printprøve dækker uændrede formularudtræk/payloads, dansk/engelsk betjening, dobbeltklik, blokerede vinduer, ændret revision/formular/navigation, nyere dialoger og fejlet billedafkodning.
- Browser: `scripts/check_geo_browser.cjs` og `scripts/check_access_browser.cjs`, med Playwright 1.56.1 som isoleret testværktøj via `PLAYWRIGHT_MODULE`. Ingen browserafhængighed tilføjes appen. 320/390/768/1440 pixels, fiktivt login/API, rigtig DOM, dialogfokus, front/bagside samt samlet rapport som PDF. Eksterne tjenester erstattes af prøvesvar.
- Pakning: `python scripts/test_build_release.py` og `python -m unittest discover -s scripts -p test_build_beta.py -v`. Kontrollerer fuldstændige formularer, vejledningslinks, checksum, reproducerbar ZIP, programfiler uden runtime-data og separat betakanal.
- Faktiske pakker: `python scripts/check_release_smoke.py` prøver reproducerbar ZIP, alle HA-checksums og faktisk start af den udpakkede app med tomme midlertidige data og korrekt versionsvisning. `python scripts/build_release.py` og `python scripts/build_beta.py --output /tmp/ltm-ha-beta-review`. ZIP-integritet, indholdsfortegnelse og checksum kontrolleres. Tomme originalformularer og importskabelonen medfølger; private databaser, nøgler og forbindelsesfiler gør ikke.
- GitHub kræver desuden programprøver på flere Python-versioner, Mac-/Windows-startprøver og HA-containerkontrol før automatisk betaudgivelse. På develop er det stabile udgivelsesflow nu koblet til de samme genbrugelige Checks- og Platformskontrol-workflows fra præcis samme commit. Publiceringsjobbet afhænger af begge, kræver main og bevarer versionskontrol samt uforanderlige udgivne pakker. Selve stabile publicering køres først ved den særskilte promovering til main.

## Afsluttede områder

Kortoversigt, adresser/kortkontrol, geografisk editor/import, avanceret opsætning/IB-import, Drive/QR med opdigtede svar, fejl/gemning, login/tastatur, printbetjening, programpakke samt slutdokumentation. Originale S-12-/S-13-filer og formularernes placering bevares. Print åbner aldrig automatisk for udlevering af ændrede kort.

## Lokale ejerprøver

Fysisk printer, egen HA/telefon/VPN, eget Google-samtykke og adgang ved aflevering/genudlevering, egen Datafordeler-konto samt eventuel skærmlæser står særskilt. Følg [restlisten](../Dette-skal-hjaelpes-manuelt.md). Disse punkter markeres ikke som afprøvet af de automatiske kontroller.

Se [print](PRINT.md), [installation](INSTALL.md), [betakanal](BETA.md), [begrænsninger](LIMITATIONS.md) og [køreplan](../KOREPLAN.md).

[Kladde til næste stabile udgivelse](NAESTE-STABILE-UDGAVE.md) samler nyheder, opdateringsvej og de begrænsninger, der skal være synlige ved publicering.

## Konkret vej til næste stabile udgave

1. W81-beta: kontrollér fravær af automatiske forslag, manuel korttegning, lokal IB-import og bevarede kort. Kræv grønne program-, browser-, platform- og HA-pakkekontroller på den præcise udgivelseskode.
2. W78 på ejerens HA er bekræftet bestået 23.10.2026: API-adressehentning virker, men opleves langsom. W82 om løbende aktivitet og antal adresser er registreret til efter næste stabile udgave.
3. Ejerens korte slutprøve: tag privat backup, opdatér beta, genstart, log ind fra telefon, prøv udlevering/aflevering og gendannelse til en separat prøveinstallation. Kontrollér print/QR, hvis de bruges; afprøv natlig adressekontrol, hvis den aktiveres.
4. Afklar de åbne sikkerhedspunkter W06/W28/W56. Ejeren har 23.10.2026 besluttet, at W61-oprydningen hos GitHub ikke blokerer næste stabile udgivelse; supportsagen forbliver åben. Der er ikke dokumenteret en fuld sikkerhedsscanning eller krypteret nøglebackup. Den eksisterende LAN/VPN-adgangsmodel er ikke ændret. Før publicering skal åbne punkter være løst eller eksplicit afgrænset i udgivelsesnoterne sammen med ejeren.
5. Saml endelige begrænsninger, versionsnummer, ændringslog, opgraderings-/backupvej og pakkechecksums. Promovér først den verificerede kode til main og opret stabil udgivelse som et særskilt trin.

W16/automatisk inddeling er parkeret og fjernet fra aktiv app. W65 flerbruger er ikke bestilt. W74 hosting venter til efter stabil; W08 arkivering vurderes bagefter. Ejeren har 23.10.2026 bekræftet, at webdemoen ser fin ud; en samlet demosynkronisering og særskilte arbejdsgange markeres ikke automatisk bestået. W58 fuld engelsk færdiggørelse står fortsat åbent; udgivelsen må ikke love fuld oversættelse før kontrol.

Ejeropfølgning 23.10.2026: Den generelle HA-prøve er bekræftet bestået og skal ikke bestilles igen. API-adressehentningen og demoens første åbning er nu også ejerbekræftet. Separat gendannelse og fysiske print-/QR-prøver registreres kun ved konkret bekræftelse. Feedbackmenuen forenkles før stabil; W82 er udtrykkeligt placeret efter stabil.

Ejerafklaring 23.10.2026: Drive og gendannelse fungerer uden problemer og er godkendt af ejeren. GitHub Support er udtrykkeligt fjernet som udgivelsesblokering; gammel offentlig historik er ikke dermed dokumenteret ryddet. Den ønskede Codex Security-scanning er ikke startet: scanner-/preflightadgang mangler i den aktuelle session. W28 forbliver åben.

## Manuel sikkerhedskontrol · kandidat beta.62

Efter ejerens valg er den alternative [manuelle kodegennemgang](SIKKERHEDSGENNEMGANG-2026-10.md) udført. To konkrete punkter er rettet: forældet PDF-afhængighed og XLSX DTD-kontrol ved UTF-16. Lokale sikkerheds-/regressionsprøver er bestået. Den præcise kandidats CI-/platformkontroller skal fortsat være grønne før udgivelse. Codex Security er ikke kørt; systempakker, komplet belastningstest og uafhængig penetrationstest er ikke dækket. W06-arkitektur og W56 beskrives fortsat som ikke leveret.

## Stabil 1.12.0 · udgivelsesbeslutning 23.10.2026

Ejeren har godkendt publicering. ADS-planens relevante præsentationspunkter er indarbejdet i forside, billeder, startlinks og særskilte brugerrettede udgivelsesnoter. Den alternative manuelle sikkerhedsgennemgang med de to rettelser er gennemført og beskrevet i rapporten; den må ikke betegnes en Codex Security-scanning. De tidligere åbne beslutninger ovenfor er afklaret ved ejerens efterfølgende godkendelse. Ekstern oprydning, fremtidig arkitektur og nøglebackup er fortsat ikke gennemført. Den stabile kandidat skal stadig bestå sin egen fulde automatiske udgivelseskontrol.
