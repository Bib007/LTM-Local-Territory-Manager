# Beta.81 · præcis verificering

1.11.2026 · [offentlig udgivelse](https://github.com/Bib007/LTM-Local-Territory-Manager/releases/tag/v1.12.2-beta.81)

- Kilde og tag: `48d69183969eaaafcd3830bb29ae78335b59c827`.
- Filtræ: `6143ea9cf3536586a109735f36352d48ac32a8e7`.
- Checks [41290427578](https://github.com/Bib007/LTM-Local-Territory-Manager/actions/runs/41290427578), Platformskontrol [41290427568](https://github.com/Bib007/LTM-Local-Territory-Manager/actions/runs/41290427568) og HA beta release [41290427605](https://github.com/Bib007/LTM-Local-Territory-Manager/actions/runs/41290427605): alle completed/success på samme præcise kilde.

612 programprøver med én forventet overspringning, JavaScript, Chromium/WebKit, Python 3.9/3.12/3.13, Mac, Windows, HA, officielle HA-beskedskemaer, 16 pakkeprøver, fem betaprøver, rigtig arkivopstart og designmanifest består. Normale statiske-/afhængighedskontroller er bestået; Codex Security er ikke kørt.

## Offentlige pakker

Begge pakker er hentet fra udgivelsen og sammenlignet byte for byte med lokale bygninger fra samme filtræ. Begge offentlige kontrolsumfiler er kontrolleret.

| Fil | Bytes | SHA-256 |
| --- | ---: | --- |
| LTM-HA-v1.12.2-beta.81.zip | 1276200 | `b687bcf34420c3a5ba625d0e486c17e5c84fc74459820a6a2a6dcc0f6c748868` |
| LTM-v1.12.2-beta.81.zip | 3714686 | `8439881b2f5a568319658255c597cb0231f7de83dfaedf6bc64f715fc8cde65f` |

Betakanal `45b73b3615395383682292e4ea8b95305d352257`: alle **150 filer** matcher den lokale kanalbygning byte for byte. Stabil/main er fortsat `bd47cc824638e653522f2d2badef2da91b14f613`, version 1.12.1. Beta har egne data/login og port 8788. Ingen eksisterende beta er overskrevet.

## Leveret

W108: Tjenestegrupper, tilsynsmand/assistent og særskilt pionermarkering i normal redigering, gruppefilter og kort-/historikvisning. Lokal XLSX-/CSV-import med entydigt navnematch, tydelig før/efter-visning, dublet-/funktionskontrol og konkret samlet godkendelse. Id, udlån, historik og personer udenfor filen bevares. Gruppefunktioner giver ingen konti eller adgangsrettigheder.

Ni målrettede dataprøver dækker bl.a. bevaret identitet, byttede gruppefunktioner, atomisk tilbageførsel ved lagerfejl, kolonner der mangler eller er tomme, privat backup/gendannelse og fortsat mulighed for flere kort. To rigtige lokale sessioner bevarer uafhængige rettelser og modstridende gruppevalg; en rettighedsændring stopper en allerede forberedt import. Et lokalt forløb med 5.000 opdigtede navne består. Browseren prøver rigtig Excel-download/upload, filter, normal rettelse og 390 px. Samme forløb består i begge CI-browsermotorer. Mistet kvittering og efterfølgende læsefejl bevirker ikke gentaget import.

W108 tæller som frigivet: **103/119 afsluttet eller afklaret, 16 åbne, cirka 87 %**. W106 er derefter under lokal udvikling og er ikke med i denne udgivelse. Ejerens nye grafikønske til konflikter er registreret under W65 og ikke løst i beta.81. W65, W13 og afsluttende sprogkontrol er fortsat åbne. OCR og automatisk kortinddeling forbliver på pause. Ingen ny stabil udgave er publiceret.
