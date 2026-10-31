# Beta.79 · præcis verificering

31.10.2026 · [offentlig udgivelse](https://github.com/Bib007/LTM-Local-Territory-Manager/releases/tag/v1.12.2-beta.79)

- Udgivelsescommit og tag: `9c15398b90a582eadd85c0318a599343fa93cec2`.
- Filtræ: `a8d3cab273542156cd8e8e117401e5c3a22b8969`.
- Checks: [41247984241](https://github.com/Bib007/LTM-Local-Territory-Manager/actions/runs/41247984241), completed/success.
- Platformskontrol: [41247984256](https://github.com/Bib007/LTM-Local-Territory-Manager/actions/runs/41247984256), completed/success.
- HA beta release: [41247984304](https://github.com/Bib007/LTM-Local-Territory-Manager/actions/runs/41247984304), completed/success.

Alle tre kørsler gælder samme præcise udgivelsescommit. Python 3.9/3.12/3.13, JavaScript, Chromium/WebKit, Mac, Windows, HA, pakker, arkivopstart og designmanifest består. 594 Python-prøver med én forventet overspringning, 16 pakkeprøver og fem betapakkeprøver består lokalt. HA-beskedopskriftens særskilte officielle kontrol og de sædvanlige statiske-/afhængighedskontroller består. Codex Security er ikke kørt.

## Offentlige pakker

Begge ZIP-filer er hentet fra udgivelsen og sammenlignet **byte for byte** med lokale bygninger fra samme filtræ. Begge offentlige kontrolsumfiler er også kontrolleret.

| Fil | Bytes | SHA-256 |
| --- | ---: | --- |
| LTM-HA-v1.12.2-beta.79.zip | 1266046 | `dc9e48324cfa5855a7d9ef906fb24291c28cbe413c708a624173ea3465c152b3` |
| LTM-v1.12.2-beta.79.zip | 3677786 | `6f60e113301767f90bfb629034a3a200b4fc93d6834361419504dd1e8fbade49` |

Betakanalen er `c91b3b17245ff515fa51d76e85e901013ae028d7`; alle **147 filer** matcher den lokale kanalbygning byte for byte. Stabil/main er fortsat `bd47cc824638e653522f2d2badef2da91b14f613`, version 1.12.1. Beta har fortsat port 8788, eget login og egne data.

## Leveret og afgrænset

W117: Lokal XLSX-/CSV-import, tom Excel-skabelon, synlige mangler/ekstra kolonner, udtrykkelig gennemgang af manuelle linjer på et valgt kort, dubletter, samlet lagring og normal efterfølgende postnummerrettelse. Besøgstal, forside, kortgrænser og udleveringer bevares. Der gættes ingen geografisk adresse. Den private databackup bevarer postnummer og mangelpåmindelse.

To rigtige lokale login-sessioner bevarer uafhængige dato-/postnummerrettelser; modsatrettede postnumre og deres udgangspunkt gemmes til gennemgang. En lagerfejl under anden linje ruller hele importen tilbage. Browseren dækker download/upload, mobilvisning, advarselsgodkendelse, printlinje og mangelpåmindelse. Et hurtigt filskift prøves med både en forsinket ældre HTTP-forespørgsel og en endnu ikke afsluttet nyere XLSX-indlæsning.

Første kandidat `133095991bfbaad30e518d5adfe7e3c4c8720bab`, HA beta release **41232252899**, blev afbrudt før publicering for at rette den beviste filskiftsfejl. Ingen kontrol blev sprunget over; alle kontroller blev kørt igen på den rettede kilde. Der fandtes ingen udgivet beta.79, og ingen eksisterende beta blev overskrevet.

Kun opdigtede konti, kort og IB er brugt. Ingen OCR-kode eller genkendelseskvalitet er udviklet eller godkendt. W117 tæller nu som frigivet; de specifikke nye ejerprøver er klar i tabellen. W107 er efterfølgende under udvikling og er ikke med i denne udgivelse. W65 er fortsat åben til stabilslutkontrol. W106–W108 og den afsluttende gennemgang mangler før næste stabile; ingen ny stabil version er publiceret.
