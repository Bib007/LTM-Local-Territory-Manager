# LTM 1.12.19-beta.4 · Dine åbne opgaver på forsiden

Denne beta tilføjer en personlig opgavebesked på forsiden og retter den fejlede testkørsel fra udviklingsversionen. Stable 1.12.19 er uændret.

## Nyt

- **Dine egne opgaver ved velkomsten.** Når du er logget ind med adgang til Opgaver, viser forsiden kun antallet af **dine egne åbne, aktive opgaver**. Beskeden skjules automatisk, når der ikke er nogen.
- **Se mine opgaver.** Knappen åbner opgavelisten med **Mine opgaver** og **Åbne opgaver** valgt. Den starter med en opdateret visning.
- **Automatisk opdatering.** Når andre ændrer en opgaves ansvarshavende eller markerer den udført, opdateres beskeden ved den eksisterende statuskontrol (normalt inden for 30 sekunder), uden at du behøver genindlæse.
- **Korrekte rettigheder.** Uden adgang til opgaver vises intet antal. Andre brugeres opgaver, udførte eller ignorerede opgaver og ugentlige opgaver, der først er aktuelle senere, tælles ikke med.
- **Eksisterende opgavelister bevaret.** Ældre opfølgningsposter vises fortsat i de almindelige lister, så nyt personligt filter ikke ændrer gammel funktionalitet.

Den forrige beta 1.12.19-beta.3's rettelse af vejledende kortantal og øvrige forbedringer fra beta.2 er også med.

## Test med fiktive konti

1. Log ind som en fiktiv bruger med rettigheden **Se opgaver**, og tildel brugeren én opgave. Kontrollér beskeden **Du er ansvarlig for 1 åben opgave**.
2. Tildel en anden bruger en opgave. Den skal ikke påvirke dit tal.
3. Vælg **Se mine opgaver**; kontrollér at kun dine egne aktuelle opgaver vises.
4. Afslut opgaven, eller fjern ansvarshavende i en anden session. Kontrollér, at tallet ændrer sig eller forsvinder senest ved næste statuskontrol.
5. Gentag på telefon og computer og med en konto uden rettigheden **Se opgaver**.

**Home Assistant Beta** har fortsat eget login, egen datamappe og port 8788. Tag privat backup før opdateringen. Stable påvirkes ikke; pakken indeholder ingen brugerdata.

Læs [betavejledningen](BETA.md) for installation og [changeloggen](CHANGELOG.md) for den samlede ændringsliste.
