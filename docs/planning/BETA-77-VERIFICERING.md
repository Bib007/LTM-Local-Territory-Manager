# Beta.77 · verificeret udgivet 31.10.2026

[Udgivelsen](https://github.com/Bib007/LTM-Local-Territory-Manager/releases/tag/v1.12.2-beta.77) er en prerelease fra **ffb7638abae22925c54792b02109393dd5643ce1**, træ **a0056c78979dd9da1461902c326e82a08e00f771**. Tagget peger direkte på samme commit. Ingen eksisterende udgivelse er overskrevet.

**Checks 41226343976** og **HA beta release 41226343968** er completed/success på præcis denne commit. Kontrollerne omfatter Python 3.9/3.12/3.13, JavaScript, Chromium/WebKit, pakning, rigtig arkivstart, Mac, Windows og HA-container samt afhængigheds-/statisk kontrol. Det er ikke en Codex Security-scanning.

Den selvstændige **Platformskontrol 41225859244** bestod på **34a7e3b32ef170ec9609dca63b4006c30f976cc8**. Hele `distrikt/` er sammenlignet og identisk med udgivelseskilden. Den sidste commit rettede kun browsernes opdigtede API-svar; den udløser ikke det selvstændige platformworkflow. HA-udgivelsens egne Mac-/Windows-/HA-job bestod på selve udgivelsescommitten. Første kandidat blev stoppet af en manglende ny forbindelsesvej i browserfixture; kontrollen er rettet og genkørt, ikke sprunget over.

Lokalt består 572 Python-prøver (én forventet overspringning), JavaScript-suiten, 16 desktop-pakkeprøver, fem HA-pakkeprøver og rigtig arkivstart. Det udvidede profilforløb bruger rigtig midlertidig HTTP/SQLite, Playwright 1.56.1 og opdigtede konti. Normal daglig brug og korteditor er desuden prøvet på 320/390/768/1440 px. Mobilvisningen af konflikter er visuelt kontrolleret.

De to offentlige ZIP-pakker og deres kontrolsumfiler er hentet. Begge ZIP-filer matcher de lokale pakker fra udgivelsestræet byte for byte:

| Pakke | Bytes | SHA256 |
| --- | ---: | --- |
| LTM-HA-v1.12.2-beta.77.zip | 1.255.014 | `8c859539cda5f1e470ccda2095a246ee0e8506c2e2f90ca459d4890a05f749aa` |
| LTM-v1.12.2-beta.77.zip | 3.634.232 | `bff7fccbd85c0c346a5c7b3b6b8dbe7175e39f0bb1e1d5271105f3936b39ed79` |

Betakanal **c4d64b12807d56e0236d996f4385815de7d914a3**: alle **144 filer** matcher den lokalt genererede kanal fra samme kilde. Beta bruger **8788** og egne data/login. Stabil/main er uændret på **bd47cc824638e653522f2d2badef2da91b14f613**, version **1.12.1**, port **8787**.

W112–W115 er frigivet: rollebestemt backup-påmindelse, egen brugerfane og samlede forbindelser, skjulte forbindelser med serverkontrol og tydeligere opfølgninger. W65's konkrete beta.76-feedback er rettet med konfliktvalg, straks-opdateret påmindelse, velkomst og kontobackup/gendannelse i appen. W65 holdes åben til stabilslutkontrol. W83's første introduktion er også ejerbekræftet.

Fremdrift **98/119 afsluttet eller afklaret, 21 åbne, cirka 82 %**. Adressekontrol/W111 er efterfølgende under lokal udvikling og er **ikke** med i disse pakker. W106–W108, W110 og W117 mangler fortsat før næste stabile. W85/OCR og W16 er på pause. Ingen ny stabil udgave er publiceret.
