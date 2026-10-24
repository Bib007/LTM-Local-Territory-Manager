# W85 · Lokal fotoimport · teknisk forundersøgelse 24.10.2026

## Ny status · beta.72-kandidat

IB-billedkø er implementeret til kontrol: højst 20 PNG/JPEG-originaler, lokal klargøring, asynkron native OCR, redigerbar tekst, separat kortvalg pr. billede, præcise lokale adresse-/lejlighedsmatches, eksplicit linjespring, påkrævede datoer, eksisterende IB-forhåndsvisning og IMPORTÉR IB. HA medtager dansk/engelsk motor og sprogdata. Mac/Windows bruger en separat lokal Tesseract-installation og viser manglende motor/dansk. Ingen cloud-/AI-tjeneste eller automatisk adresseoprettelse. Native proces har tidsgrænse, én aktiv læsning, stop/oprydning, faste argumenter og ingen diagnostik med private filnavne/tekst.

W85 er **fortsat åben**: S-12-forsider, fuld foto-kortoprettelse, manglende adresseopfølgninger og mere layoutfortolkning mangler. OCR er et forslag, ikke en garanti for håndskrift eller flerespaltede billeder. Nedenstående er den historiske forundersøgelse fra før implementeringen. Beta.72 er endnu ikke verificeret udgivet. Ved serverlukning afventes nu også oprydning af en aktiv OCR-proces.

## Historisk forundersøgelse


Status: **Forundersøgelse, ikke leveret fotoimport.** Excel-/CSV-køen er allerede leveret. Dette dokument beskriver næste selvstændige implementering efter beta.70; ingen ny OCR-afhængighed, API eller billedoverførsel er indført.

## Det eksisterende forløb skal genbruges

- `card-import-ui.js`: højst 20 Excel-/CSV-filer, separat forhåndsvisning og godkendelse pr. fil, manuel overgang til næste fil og beskyttelse mod sene svar. Genimplementér ikke denne kø.
- `card_import.py`: indlæsning og validering af kortdata; behold de eksisterende kort-/områderegler og godkendelsen `IMPORTÉR KORT`.
- `setup_store.py`: `setup.ib.preview` matcher lokalt, og `setup.ib.apply` kræver godkendelse. Fotos må ikke omgå dette forløb eller oprette IB på ukendte adresser.
- Konkrete importkontroller ved ændrede data skal bevares. Den generelle afvisning ved andre faners gemning skal fortsat være pauset indtil profiler.

## Afhængigheder og foreløbig retning

Appens nuværende HA-image installerer kun Python. Den har ingen OCR-motor eller danske sprogdata. Den lokale udviklingsmaskine har Tesseract 5.3.4 med `eng` og `osd`, men ikke `dan`. Det beviser ikke, hvad der findes på ejerens HA, Mac eller Windows.

Tesseracts officielle dokumentation beskriver motor og sprogdata som separate installationer. Den beskriver Linux-pakker, Homebrew/MacPorts og Windows-installationer. En native motor på appens egen maskine er et muligt første spor: HA kan medtage motor og danske sprogdata i image-bygningen, mens desktop skal have en kontrolleret installations-/registreringsvej. Ingen installation på ejerens maskiner er forsøgt.

En browsermotor er også undersøgt. Tesseract.js kræver lokal distribution af worker, core/WASM og sprogdata for at undgå standardhentninger fra CDN. LTM's nuværende server bruger en eksplicit liste over serverbare filer og `script-src 'self'` uden WASM-tilladelse. Browserløsningen kræver derfor særskilt pakning, licens-/versionskontrol, CSP-vurdering og rigtig browserprøve på lokal HTTP-adresse. Indlæs ikke automatisk motor eller sprogdata fra en CDN.

Foreløbig implementeringsrækkefølge: afgrænset native OCR-adapter med eksplicit status for motor/sprogdata, dernæst redigerbare tekstforslag og eksisterende importgodkendelser. Valget er en teknisk arbejdsretning, ikke en færdig platformsgaranti. Endelig pakning skal kunne kontrolleres på HA, Mac og Windows, før funktionen meldes færdig.

## Faktisk lokal prøve

En reproducerbar prøve blev kørt med Pillow og den allerede installerede Tesseract-motor. Billedet blev dannet fra teksten nedenfor med DejaVu Sans 38 px på hvid baggrund, 1500 × 650 px. Tre varianter blev aflæst med `tesseract <fil> stdout -l eng --psm 6`: original, 2 graders rotation og halveret opløsning. Alle tre processer afsluttede med kode 0 og gengav de nedenstående linjer korrekt bortset fra ekstra tomme linjer.

```text
FIKTIVT PROEVEKORT - ingen rigtige oplysninger
Kort 901 - Fiktivt omraade
Fiktivvej 2-14 (lige)
Proevevaenget 1-9 (ulige)
IB-bagside - opdigtede adresser
Fiktivvej 8 - 24.10.2026
Proevevaenget 3 - 12.09.2026
```

Dette er kun en trykt, syntetisk ASCII-prøve. Den dokumenterer hverken danske bogstaver, håndskrift, et fotograferet S-12-layout, flerespaltet IB, skygger, perspektiv, mobilformat eller nogen bestemt genkendelsesprocent. Der blev ikke brugt private data, og intet billede blev sendt til en ekstern tjeneste. Prøvefilerne er midlertidige udviklingsfiler; de er ikke en ny offentlig eksempelpakke.

## Implementeringens konkrete krav

1. Afgræns filtyper, antal, samlede bytes og billeddimensioner. Afvis ugyldige/for store billeder før genkendelse. HEIC/PDF understøttes ikke stiltiende som PNG/JPEG.
2. Kør lokal genkendelse som en begrænset jobkø, uden shell, uden brugerbestemt programsti/argumenter, med tidsgrænse, begrænset samtidighed, afbrydelse og oprydning af midlertidige filer. Undlad filindhold og genkendt IB i logning/fejl.
3. Vis det valgte billede og redigerbar tekst. Kortnummer, område, vej, husnumre, lige/ulige, besøgstal og IB-dato må ikke gættes til sikre værdier. Uklare oplysninger skal rettes af brugeren. OCR-laget skal kræve en gennemset dato, før IB-teksten sendes til den eksisterende forhåndsvisning; den nuværende CSV-imports standarddato må ikke stiltiende blive en aflæst fotodato.
4. Normalisér tekst til de eksisterende kort-/IB-forhåndsvisninger. IB matches kun mod det valgte korts lokale adresser. Manglende og tvetydige matches skal vises særskilt; ingen automatisk oprettelse af adresser eller IB.
5. Adskil fotos af forsider og IB-bagsider, og lad brugeren bekræfte koblingen til kortnummeret. Gentagende filnavne må ikke koble sider automatisk.
6. Hver fil får godkendelse, spring over og tydelig køstatus. Et sent OCR-svar må ikke overskrive næste fil, en nyere kladde eller en lukket dialog. Godkendte filer bevares ved fejl på næste fil.
7. Tilbyd grænsetegning efter godkendt kortoprettelse. Ingen automatisk kortinddeling eller ændring af eksisterende grænser.
8. Prøv fiktive fotos/layouts og fejlforløb på HA/Mac/Windows, dansk/engelsk, telefon/tablet, manglende motor/sprog, timeout, forkerte filtyper, dubletter, ukendt gemmeresultat og ændrede importdata. Kontrollér netværksfravær under genkendelse.

## Primære kilder

- [Tesseract: installation og sprogdata](https://tesseract-ocr.github.io/tessdoc/Installation.html), læst 24.10.2026.
- [Tesseract.js: lokal installation af worker, core og sprogdata](https://github.com/naptha/tesseract.js/blob/master/docs/local-installation.md), læst 24.10.2026. Eksemplernes versionsnumre er eksempler, ikke valgte afhængigheder til LTM.
