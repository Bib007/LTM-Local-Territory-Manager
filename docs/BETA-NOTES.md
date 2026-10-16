# LTM 1.12.0-beta.7

## Nyt siden beta.6

**Kortdata → Datafordeleren · egen API-nøgle** har en trinvis vejledning til at oprette konto, IT-system og API-key. Forbindelsen kontrolleres mod DAR v3, før en ny nøgle gemmes lokalt. Du kan kontrollere en gemt forbindelse eller fjerne nøglen igen.

Nøglen vises ikke i appens status eller adresse-/kortdata og følger ikke med portable sikkerhedskopier. Den sendes kun fra din lokale app til den faste officielle Datafordeler-adresse for autentifikation. Hvis en ny nøgle eller kontrol fejler, bevares den tidligere gemte nøgle. Beta-nulstilling bevarer forbindelsen.

Dette er første del af kildeovergangen. **Adresseimporten bruger fortsat den hidtidige kilde.** En kontrolleret DAR v3-forbindelse betyder endnu ikke, at importen er flyttet.

## Prøv især

1. Åbn Kortdata og følg vejledningen under Datafordeleren. Opret en API-key på dit eget IT-system, og indtast den lokalt i LTM.
2. Vælg Kontrollér og gem nøgle. Kontrollér den tydelige status og at feltet bliver tomt efter indsendelse.
3. Genåbn appen, og kontrollér den gemte forbindelse. Prøv eventuelt en forkert erstatningsnøgle: den gamle forbindelse skal bevares.
4. Eksportér en privat sikkerhedskopi. Forbindelsen skal sættes op igen på en anden installation; nøglen følger ikke med.

Den uønskede ekstra KTM-opfølgningsliste er fjernet siden beta.6. De øvrige rapporttal og original S-13 bevares. Stabil udgave er fortsat 1.11.1.
