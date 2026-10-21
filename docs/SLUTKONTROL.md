# Slutkontrol af den faste køreplan

[English](SLUTKONTROL.en.md)

Kontrolgrundlag: beta.60 har beståede program-, platform-, pakke- og browserkontroller. Beta.61 er implementeret med W81 på kildecommit cd95b1b130bebe07c9ffc3d2c5fe380ca5058253. Program-, browser-, Windows-, HA- og pakkekontroller er bestået; Mac-jobbet står i GitHubs kø, og automatisk udgivelse afventer dette. Beta.61 er endnu ikke registreret udgivet. Main er fortsat stabil 1.11.1. Den faste udviklingsplan er afsluttet; hele ønskekøen er ikke et krav til næste stabile udgave.

## Gentagelige kontroller

- Python: `python -m unittest discover -s distrikt/tests -v`. Prøverne bruger midlertidige mapper og opdigtede data. Den tidligere private ZIP er ikke medleveret, og dens opgraderingsprøve springes udtrykkeligt over.
- JavaScript: kør hver `distrikt/tests/test_*.cjs` med `TZ=Europe/Copenhagen`. Den nye printprøve dækker uændrede formularudtræk/payloads, dansk/engelsk betjening, dobbeltklik, blokerede vinduer, ændret revision/formular/navigation, nyere dialoger og fejlet billedafkodning.
- Browser: `scripts/check_geo_browser.cjs` og `scripts/check_access_browser.cjs`, med Playwright 1.56.1 som isoleret testværktøj via `PLAYWRIGHT_MODULE`. Ingen browserafhængighed tilføjes appen. 320/390/768/1440 pixels, fiktivt login/API, rigtig DOM, dialogfokus, front/bagside samt samlet rapport som PDF. Eksterne tjenester erstattes af prøvesvar.
- Pakning: `python scripts/test_build_release.py` og `python -m unittest discover -s scripts -p test_build_beta.py -v`. Kontrollerer fuldstændige formularer, vejledningslinks, checksum, reproducerbar ZIP, programfiler uden runtime-data og separat betakanal.
- Faktiske pakker: `python scripts/check_release_smoke.py` prøver reproducerbar ZIP, alle HA-checksums og faktisk start af den udpakkede app med tomme midlertidige data og korrekt versionsvisning. `python scripts/build_release.py` og `python scripts/build_beta.py --output /tmp/ltm-ha-beta-review`. ZIP-integritet, indholdsfortegnelse og checksum kontrolleres. Tomme originalformularer og importskabelonen medfølger; private databaser, nøgler og forbindelsesfiler gør ikke.
- GitHub kræver desuden programprøver på flere Python-versioner, Mac-/Windows-startprøver og HA-containerkontrol før automatisk betaudgivelse. En stabil udgivelse er et særskilt trin.

## Afsluttede områder

Kortoversigt, adresser/kortkontrol, geografisk editor/import, avanceret opsætning/IB-import, Drive/QR med opdigtede svar, fejl/gemning, login/tastatur, printbetjening, programpakke samt slutdokumentation. Originale S-12-/S-13-filer og formularernes placering bevares. Print åbner aldrig automatisk for udlevering af ændrede kort.

## Lokale ejerprøver

Fysisk printer, egen HA/telefon/VPN, eget Google-samtykke og adgang ved aflevering/genudlevering, egen Datafordeler-konto samt eventuel skærmlæser står særskilt. Følg [restlisten](../Dette-skal-hjaelpes-manuelt.md). Disse punkter markeres ikke som afprøvet af de automatiske kontroller.

Se [print](PRINT.md), [installation](INSTALL.md), [betakanal](BETA.md), [begrænsninger](LIMITATIONS.md) og [køreplan](../KOREPLAN.md).

## Konkret vej til næste stabile udgave

1. W81-beta: kontrollér fravær af automatiske forslag, manuel korttegning, lokal IB-import og bevarede kort. Kræv grønne program-, browser-, platform- og HA-pakkekontroller på den præcise udgivelseskode.
2. W78 på ejerens HA: gentag den tidligere afbrudte adressehentning. Kontrollér fortsættelse, færdige udsnit og eventuel fejlkode. En fortsat fejl afklares før denne adressearbejdsgang erklæres stabil.
3. Ejerens korte slutprøve: tag privat backup, opdatér beta, genstart, log ind fra telefon, prøv udlevering/aflevering og gendannelse til en separat prøveinstallation. Kontrollér print/QR, hvis de bruges; afprøv natlig adressekontrol, hvis den aktiveres.
4. Afklar status på W61-oprydning hos GitHub og de åbne sikkerhedspunkter W06/W28/W56. Der er ikke dokumenteret en fuld sikkerhedsscanning eller krypteret nøglebackup. Den eksisterende LAN/VPN-adgangsmodel er ikke ændret. Før publicering skal åbne punkter være løst eller eksplicit afgrænset i udgivelsesnoterne sammen med ejeren.
5. Saml endelige begrænsninger, versionsnummer, ændringslog, opgraderings-/backupvej og pakkechecksums. Promovér først den verificerede kode til main og opret stabil udgivelse som et særskilt trin.

W16/automatisk inddeling er parkeret og fjernet fra aktiv app. W65 flerbruger er ikke bestilt. W74 hosting venter til efter stabil; W08 arkivering vurderes bagefter. Webdemoens manglende live-kontrol holdes særskilt fra lokal/HA-udgivelse. W58 fuld engelsk færdiggørelse står fortsat åbent; udgivelsen må ikke love fuld oversættelse før kontrol.
