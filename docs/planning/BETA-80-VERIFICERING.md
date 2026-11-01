# Beta.80 · præcis verificering

1.11.2026 · [offentlig udgivelse](https://github.com/Bib007/LTM-Local-Territory-Manager/releases/tag/v1.12.2-beta.80)

- Udgivelsescommit og tag: `cf92787808b820edf72121400f0a901512ef47b3`.
- Filtræ: `83cb40bc57ea5e20189d13439ae54eaca9ed1d09`.
- Checks: [41250233958](https://github.com/Bib007/LTM-Local-Territory-Manager/actions/runs/41250233958), completed/success.
- Platformskontrol: [41250234017](https://github.com/Bib007/LTM-Local-Territory-Manager/actions/runs/41250234017), completed/success.
- HA beta release: [41250234027](https://github.com/Bib007/LTM-Local-Territory-Manager/actions/runs/41250234027), completed/success.

Alle tre forløb gælder samme præcise kilde. 601 Python-prøver består i CI med én forventet overspringning; Python 3.9/3.12/3.13, JavaScript, Chromium/WebKit, Mac, Windows, HA, officielle HA-beskedskemaer, 16 pakkeprøver, fem betapakkeprøver, arkivopstart og designmanifest består. De normale statiske-/afhængighedskontroller består. Codex Security er ikke kørt.

## Offentlige pakker og kanal

Begge ZIP-filer er hentet offentligt og sammenlignet **byte for byte** med lokale bygninger fra samme filtræ. Begge offentlige kontrolsumfiler er også kontrolleret.

| Fil | Bytes | SHA-256 |
| --- | ---: | --- |
| LTM-HA-v1.12.2-beta.80.zip | 1267545 | `3fec59629a9fb683334f24b6ee7f2a101b99516493365ca7ea0123e6501de1fb` |
| LTM-v1.12.2-beta.80.zip | 3686106 | `67b79ebf62d2a3ac1b28832bf704f3ec3a24dfeefc31c77d0e80f8e2f431475c` |

Betakanalen `2d82a3e2d2d40b49348e5cd0f94d5fa02c140f08` matcher den lokale kanalbygning i alle **147 filer**. Stabil/main er fortsat `bd47cc824638e653522f2d2badef2da91b14f613`, version 1.12.1. Beta har port 8788, egne data og eget login. Ingen eksisterende beta er overskrevet.

## Leveret og afgrænset

W107: Excel-/CSV-import accepterer kortnumre alene, manuelle vejlinjer og intervaller som 1–19. Intervaller bevares som tekst, uden geografiske opslag eller gættede besøgstal. Den almindelige redigering kan bevare eller udfylde ukendt antal. Kort, print, aktuelle totaler og CSV viser ukendt; nye gennemgange bevarer ukendt grundlag og bidrager ikke til besøgsskønnet.

Senere geografisk adressevalg bruger samme kort-id og kortnummer og bevarer udleveringer, manuel IB og tidligere hændelser. Vejlisten følger derefter de præcise adresser, og print kontrolleres igen. Importen har fortsat særskilt forhåndsvisning, godkendelse, atomisk lagring og aktuelle rettighedskontroller. Der er ikke genindført en generel afvisning efter andre brugeres ændringer.

Seks målrettede dataprøver dækker registerkort, bogstavelige intervaller, eksplicitte antal, blandede XLSX-linjer, senere geografivalg, uændret tidligere historik/IB og metadata efter normal antalsrettelse. Print-/CSV-prøven bevarer ukendt. Rigtigt lokalt profil-/browserforløb dækker import, tomt antal, registrering af gennemgang, senere antalsrettelse og mobilbredde 390 px; samme forløb består i Chromium/WebKit i CI. Excel-skabelonens 11 vejledningsceller er ændret; alle øvrige værdier, cellestile, formater, faner, frysning, sammenlagte celler, dimensioner og native valideringsregler er sammenlignet med kilden og bevaret. Ingen prøve er udført på ejerens installation.

W107 tæller som frigivet. Planen er **102/119 afsluttet eller afklaret, 17 åbne, cirka 86 %**. W106, W108, den afgrænsede W13-kontrol og stabilslutkontrol af profiler/sprog er stadig åbne. Kun opdigtede data er brugt. OCR og automatisk kortinddeling forbliver på pause. Ingen ny stabil version er publiceret.
