# LTM 1.12.2-beta.76 · Brugere og samtidige rettelser

Denne beta samler den første integrerede udgave af brugerprofiler. Alle tidligere betaforbedringer er med.

- Aktivér personligt login fra **Indstillinger** med din eksisterende adgang. Opret administratorens nye login; distriktsdata bevares.
- Opret brugere og egne roller. Administratoren vælger selv rettighederne i appen.
- Flere kan arbejde samtidig. Uafhængige rettelser sammenføjes; forskellige rettelser til samme oplysning bevares med deres udgangspunkt og en påmindelse på forsiden.
- Nye profiler får egen introduktion. Overblikket viser **nylig aktivitet (90 sek.)**, ikke sikker tilstedeværelse.
- Ændrede rettigheder gælder åbne sessioner. Ukendt gemmeresultat kræver stadig kontrol, før du fortsætter.

Prøv på betaen med opdigtede oplysninger: aktivér profiler, opret en rolle og bruger, åbn to sessioner, gem først forskellige felter og derefter samme felt, og gennemgå påmindelsen. Prøv også første login og en rolleændring. Den generelle HA-, Drive- og datagendannelsesprøve skal ikke gentages.

[Brugere og gendannelse](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/v1.12.2-beta.76/docs/BRUGERE.md) forklarer den separate lokale kontobackup og administratorgendannelse. Konti følger ikke med almindelig databackup. Efter aktivering skal installationen bruge en version med profiler; ældre versioner kender ikke de nye adgangsregler.

Opdater HA-betaen som normalt, eller hent den samlede programpakke til Mac, Windows og Linux. Python skal stadig installeres separat. W106–W108 og HA-driftsstatus/W110 er endnu ikke med. OCR og automatisk kortinddeling er fortsat på pause. Stabil forbliver 1.12.1.
