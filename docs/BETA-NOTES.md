# LTM 1.12.19-beta.12 · Præcise fejl ved DAR-adresseforslag

Når **Foreslå DAR-adresser fra vejlisten** ikke kan hente en vej, viser LTM nu, hvilken linje der gav fejlen: **kortnummer, vejnavn, postnummer og det eller de husnummerintervaller, du har skrevet i vejlisten**. Den oprindelige forklaring fra DAR/Datafordeleren vises som **Årsag**.

Et eksempel med opdigtede oplysninger:

> DAR-adresseforslag stoppede ved kort F-ERR, vej "Unlisted Test Way", postnummer 9999, husnumre fra vejlisten: 11–19. Årsag: Vejnavn og postnummer kunne ikke findes entydigt i DAR.

Det er **ikke muligt at udpege ét bestemt husnummer**, når DAR endnu ikke kan finde selve vejen og postnummeret. Derfor mærkes husnumrene udtrykkeligt som brugerens **vejlistenumre**, ikke som en adresse, DAR har afvist. Fejlen bliver synlig, så du kan kontrollere stavemåde og postnummer og åbne adresseforslaget igen.

Hvis hele vejen er hentet, men ingen aktive adresser findes i det valgte interval, oplyser LTM tilsvarende vej, postnummer og interval. Du kan fortsat gennemgå og godkende forslag, før kortet gemmes. Ingen afviste forslag gemmer adressevalg, IB eller andre private data på kortet. Andre beta-funktioner og Stable er uændrede.

## English

DAR street-list errors now identify the **card, street name, postcode and original street-list number ranges** that were being processed, as well as the underlying cause. The ranges come from the user's street list; a failed road lookup does **not** identify one specific incorrect house number. Errors remain visible for review and retry. Missing active addresses within an interval likewise identify the failing street and range. No rejected proposal writes card data.
