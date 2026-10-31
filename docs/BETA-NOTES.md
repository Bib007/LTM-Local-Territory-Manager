# LTM 1.12.2-beta.79 · IB fra Excel

- Hent en tom Excel-skabelon, og upload XLSX eller CSV direkte i appen. Filen behandles lokalt.
- Importér også uden postnummer. Manglende oplysninger og ekstra kolonner vises tydeligt før import.
- Angiv kortnummer i filen, eller vælg et standardkort. En adresse uden sikkert match kan bevares som en manuel IB-linje på det valgte kort. Der gættes ingen geografisk adresse.
- Gennemgå advarslerne og bekræft importen. Dubletter springes over, og eksisterende IB overskrives ikke. Kun bagsiden markeres til genprint; besøgstal, grænser og udleveringer bevares.
- En mangelpåmindelse bliver på IB-listen, indtil postnummeret tilføjes. Samtidige uafhængige rettelser bevares; forskellige postnummerrettelser går til gennemgang.

Prøv et lille opdigtet regneark, også med manglende postnummer og en adresse uden match. Kontrollér den manuelle linje på det valgte kort og tilføj postnummeret bagefter. Brug ikke rigtige IB i offentlig feedback. [Vejledning](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/v1.12.2-beta.79/docs/IB-EXCEL.md).

Denne beta indeholder også profilrettelser, kontobackup, adressekontrol og HA-driftsbeskeder fra de tidligere betaer. Datoer på onlinekort, vejintervaller og tjenestegrupper mangler stadig før næste stabile. OCR og automatisk kortinddeling er på pause. Stabil er fortsat 1.12.1.
