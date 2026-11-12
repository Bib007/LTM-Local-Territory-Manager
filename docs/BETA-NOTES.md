# LTM 1.12.19-beta.5 · 12 nye funktioner i samme Beta

Denne beta samler de tolv udviklingsopgaver fra PR #41–#52 og deres fælles integrationstests. Tidligere Beta-forbedringer er bevaret. **Stable 1.12.20 er uændret.**

## Nyt i denne beta

- **Forkyndere:** Samlet og filtreret optælling, grupperet visning og sikker sletning med bekræftelse, hvor eksisterende udleveringshistorik respekteres.
- **Gennemgange og historik:** Bedre oversigt med kontrolleret redigering af kendte datoer.
- **Sidste KTM-besøg:** Hjælpeteksten viser »Vælg tirsdagen i KTM-ugen«, mens gamle bemærkninger bevares.
- **Mobil og tablet:** S-13-forhåndsvisning uden Print; OpenStreetMap kan prøves igen, eller rapporten kan genereres uden baggrundskort.
- **Læg i mappen:** Flervalg og bekræftelse for flere udvalgte kort, med konflikt- og rettighedskontrol.
- **Distriktsnumre:** Separate offentlige og interne numre med sikker omnummerering, samtidig med at stabile kort-ID'er og relationer bevares.
- **Rapportudskrivning:** Vælg én af tre periodetyper eller alle tre; månedstidslinjen og »Sidste KTM besøg« vises korrekt.
- **Opfølgninger:** Reversibelt »Se bort fra« med hændelseshistorik, genaktivering og adgangsstyring.
- **Google Drive:** Ægte arbejdsstatus for generering/upload, beskyttelse mod dobbeltklik og sikker mulighed for at prøve igen.
- **DAR-etiketter:** Overstyr tekst på forsidens vej- og husnummerlinjer uden at ændre de originale DAR-adressedata.
- **S-12-layout:** Små, begrænsede justeringer af tekst/QR med nulstilling og korrekt A4-print.
- **Opdelingsforslag:** Lokal grænse for besøg pr. kort og mulighed for at ignorere/genaktivere konkrete forslag.

## Før du tester

1. **Tag en privat sikkerhedskopi af dine Beta-data**, og bevar den et sikkert sted. Brug gerne opdigtede kort og adresser til de nye funktionstests.
2. Kontrollér især kortnumre, udleveringshistorik, IB-forside/-bagside og S-12/S-13 PDF efter opdatering, før du printer fysiske kort.
3. Test gerne mobilvisning, Google Drive-status og afbrydelse/genforsøg. Del ikke følsomme IB- eller forkynderoplysninger offentligt.
4. Home Assistant Beta beholder sin **egen datamappe, login og port 8788**, adskilt fra Stable. Opdatering til Beta ændrer ikke Stable-installationen.

Automatiserede tests anvender fiktive data og omfatter blandt andet adgangsrettigheder, kort-/historikregression, responsive browsere, print, backup og platformskontrol.

Se [betavejledningen](BETA.md), den [danske changelog](CHANGELOG.md) og den [engelske changelog](CHANGELOG.en.md) for flere oplysninger.
