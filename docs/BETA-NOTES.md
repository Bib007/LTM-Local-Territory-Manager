# LTM 1.12.2-beta.77 · Profilrettelser og backup i appen

Denne beta samler dine første tilbagemeldinger på profilerne med oprydning i indstillinger og tydeligere opfølgninger.

- Sammenlign de to rettelser i en mere overskuelig visning, og vælg hvilken der skal bruges. Du kan også beholde den aktuelle værdi. Påmindelsen opdateres straks uden genindlæsning.
- Find **Konti og roller** under **Backup og vedligeholdelse**. Hent en separat kontobackup, eller gendan den efter adgangskode, forhåndsvisning og bekræftelsen **GENDAN KONTI**. Distriktsdata bevares, og alle logger ind igen.
- Rettigheden **Se påmindelse om databackup** styrer påmindelsen pr. rolle. Den giver ingen ret til at hente eller gendanne data.
- **Brugere og roller** har egen indstillingsfane. Datafordeler og Google Drive findes samlet under **Forbindelser**. Fanen vises kun med den relevante rettighed; delte kort er fortsat under **Deling og QR**.
- Forsiden siger velkommen til brugeren. Hvert punkt i **Opfølgninger** forklarer næste skridt.

Prøv kun de nye ting med opdigtede betaoplysninger: vælg en tidligere rettelse, kontrollér påmindelsen uden genindlæsning, vælg en rolles backup-påmindelse og find den nye kontobackup. Dit allerede bekræftede profilgrundforløb, den generelle HA-prøve, Drive og almindelig datagendannelse skal ikke gentages.

Kontobackup er en privat JSON-fil med adgangskodehashes. Den er ikke krypteret og følger ikke med den almindelige databackup. Glemt administratorlogin kan fortsat gendannes lokalt på serveren; der er ingen offentlig omgåelse. [Vejledning](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/v1.12.2-beta.77/docs/BRUGERE.md).

Alle tidligere betafunktioner er med. Datoer på digitale kort, vejintervaller, tjenestegrupper, IB fra Excel, HA-driftsstatus og rettelsen af adressekontrollens gentagne venten er endnu ikke med. OCR og automatisk kortinddeling er fortsat på pause. Stabil er fortsat 1.12.1.
