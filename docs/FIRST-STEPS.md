# Første gang med LTM

[English](FIRST-STEPS.en.md) · [Installation](INSTALL.md)

Fra beta.23 er der én samlet opsætningsguide. På en tom installation åbnes den automatisk og forklarer lokal drift, én fælles HA-installation, backup og valgfri Google-deling. Vælg enkel udlevering eller kortfunktion, KML/GeoJSON, din måde at oprette kort på og eventuel IB-import.

Vælg **Gem og start rundtur** efter spørgsmålene. Svarene gemmes, men først **Afslut rundtur** markerer opsætningen som fuldført. Derefter lukkes guiden, og forsiden viser din personlige plan med genveje til de rigtige værktøjer. Rundturen opretter ingen kort, adresser eller IB. **Fortsæt senere** eller lukning afbryder uden at fuldføre; en gemt, uafsluttet plan genåbnes ved næste start. Tidligere fuldførte installationer tvinges ikke gennem rundturen igen. Genåbn samme guide under **Indstillinger → Generelt**.

Har du valgt kortfunktion, er **Forbind adressekilden · egen API-nøgle** en del af planen. Se [Datafordeler-vejledningen](DATAFORDELER.md); nøglen oprettes hos Datafordeleren og indtastes kun i din lokale app.

Har du adresserne fordelt i forvejen, vælg **Adresserne er allerede fordelt på kort**, eller åbn importen under **Indstillinger → Avanceret**. [Excel og CSV](KORTIMPORT.md) forklarer skabelonen.

Alle papirkort behøver ikke være digitaliseret, før LTM tages i brug. Begynd med kortnumre og eksisterende udleveringer, og tilføj adresser, grænser og print senere på de samme kort.

## 1. Brug én hovedinstallation

Følg installationsguiden for en komplet udgivelse. HA-versionen åbnes fra computer og telefon som den samme private app; hver enhed skal ikke have sin egen database.

Flyttes en eksisterende installation, bruges privat eksport/import. En almindelig opdatering af samme installation bevarer datamappen og kræver ikke ny import.

## 2. Opret kortnumrene

Åbn **Distriktskort**, og opret et midlertidigt kort, eller brug hurtig oprettelse til flere numre. Et midlertidigt kort har en rigtig registrering og udleveringshistorik, men mangler endnu vejliste og printklart kort.

Navngiv områder efter de lokale forhold, fx by og land. Vælg kendt distriktstype, hvis den kendes. Oplysningerne kan rettes senere.

## 3. Registrer allerede udleverede kort

Tilføj forkyndere under **Forkyndere**. Brug derefter **Registrer eksisterende udlevering** med den kendte udleveringsdato for hvert kort, der allerede er ude. En ukendt gennemgangsdato skal ikke erstattes med en opdigtet dato.

Åbn en forkynder for at se vedkommendes aktive kort. Midlertidige kort kan udleveres og afleveres, mens resten af oplysningerne tilføjes.

## 4. Daglig brug

| Betegnelse | Betydning |
| --- | --- |
| Forside | Overblik og genveje |
| Udleverede distriktskort | Kort, som en forkynder har |
| Kort i mappen | Ledige kort i den fysiske mappe |
| Kort i kassen | Ledige kort i kassen derhjemme |
| Aflever til kassen | Kortet registreres tilbage i kassen |
| Gennemgået | En afsluttet gennemgang registreres |
| Opgaver | Punkter til senere opfølgning · kun åbne tælles |

Læg de kort, der faktisk medbringes, i mappen i appen. Ved udlevering vælges forkynder og dato. Ved aflevering registreres, om kortet er gennemgået, og eventuelt en opgave til senere. **Afleverede kort går til kassen**, ikke automatisk tilbage til mappen.

Hver registreret gennemgang tæller, også flere gennemgange af samme kort. Anslåede besøg bygger på adresser/enheder på kortet og er ikke en registrering af de enkelte husbesøg. Tjenesteåret løber fra **1. september til 31. august**.

## 5. Tilføj detaljerne

- Importér eller tegn den samlede grænse, kontrollér den, og hent adresser indenfor. Virkelige KML-filer og registreringer bliver private.
- Udfyld eksisterende kort enkeltvis. [Automatisk inddeling](AUTOMATISK-INDDELING.md) er et forslag til nye kort, som skal gennemgås før oprettelse.
- Vælg IB fra det konkrete korts egne adresser.
- Brug almindeligt papir til den første printtilpasning, og gem printerprofilen.
- [Google Drive og QR](GOOGLE-DRIVE.md) er valgfrit.

Tag en privat backup efter opsætningen. Opbevar en kopi uden for appens maskine med begrænset adgang. Adgangskoder og backup skal ikke i GitHub eller AI-samtaler.
