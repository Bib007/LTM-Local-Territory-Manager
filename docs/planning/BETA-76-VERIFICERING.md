# Beta.76 · verificeret udgivet 31.10.2026

[Udgivelsen](https://github.com/Bib007/LTM-Local-Territory-Manager/releases/tag/v1.12.2-beta.76) er en prerelease fra **65ee595170b413e03186e0427447ac4c15fc99c8**, træ **e7a757127bedd09d7557c9918af5f67444ecce3a**. Tagget peger direkte på denne commit. Ingen eksisterende beta er overskrevet.

Alle tre kontroller er completed/success på netop denne commit:

- Checks **41208420559**: Python 3.9/3.12/3.13, JavaScript, pakker og alle browserforløb, herunder profiler i Chromium/WebKit.
- Platformskontrol **41208420426**: Mac, Windows og Home Assistant.
- HA beta release **41208420483**: afhængigheds-/statisk kontrol, program/browser/platforme og faktisk publicering. Dette er ikke en Codex Security-scanning.

Lokal kontrol: 564 Python-prøver (én forventet overspringning), alle JavaScript-prøver, 16 desktop-pakkeprøver, fem HA-pakkeprøver, rigtig arkivstart og det almindelige profilforløb med Playwright 1.56.1 og opdigtede oplysninger. Mobilvisning ved 390 px er kontrolleret.

Begge offentlige ZIP-pakker er hentet og sammenlignet byte for byte med lokale, deterministiske pakker fra samme filtræ:

| Pakke | Bytes | SHA256 |
| --- | ---: | --- |
| LTM-HA-v1.12.2-beta.76.zip | 1.247.054 | `6f2357bab97f618ded13522f7789dc6047c7cd83a1bd9627dd3a1449ca606cd9` |
| LTM-v1.12.2-beta.76.zip | 3.606.421 | `33358dfdd11243bd3d380180a9a3b775203ccef55e677f84371ab5360a28102b` |

Betakanalen er **21040c5829bbf7d3f7309f0068757b5484d99f11**. Alle **142 filer** matcher byte for byte den lokalt genererede kanal fra samme udgivelseskilde, inklusive manifest, port **8788** og adskilte beta-data/login. Stabil/main er uændret på **bd47cc824638e653522f2d2badef2da91b14f613**, version **1.12.1**, port **8787**.

Leveret i første integrerede profilbeta: aktivering fra eksisterende adgang, personligt login, administratorstyrede konti/roller/rettigheder, begrænset serveradgang, samtidige uafhængige rettelser, konfliktbevaring og gennemgang med forsidepåmindelse, nylig aktivitet, individuel introduktion, ændrede rettigheder under sessionen og separat lokal kontobackup/gendannelse. Lokal stop/opdatering og begrænset udlånsret er prøvet særskilt. Ukendt gemmeresultat kræver stadig kontrol; den generelle revisionsafvisning er ikke genindført.

W83's individuelle introduktion er frigivet. W65 holdes åben til stabilslutkontrol og opfølgning på første profilbeta. Dette er ingen prøve på ejerens installation. Nye W106–W108, W110 og W111 er ikke med i beta.76. W85/OCR og W16 forbliver på pause. Ingen ny stabil udgave er publiceret.
