# LTM 1.12.0-beta.24

## Nyt siden beta.23

W30: navneforslag ved udlevering bruger nu mørkegrå baggrund med lys tekst. Den markerede række har lysere mørk baggrund og tydelig kant. Søgning og lokale navne/udlån er uændrede.

## Prøv især

1. Opdater Distrikt Beta på port 8788. Main er stadig stabil 1.11.1.
2. Åbn Udlever kort og skriv et par bogstaver fra et lokalt forkyndernavn.
3. Kontrollér læsbarhed på computer og telefon. Prøv hover, pil op/ned, Enter, Tab og Escape. Navnet skal først vælges, når du selv bekræfter det.
4. Den samlede guide og obligatoriske afsluttende rundtur fra beta.23 følger med. Ny opsætning afslutter til forsiden med planen; eksisterende fuldført opsætning bevares.

Den rigtige browser/CSS er kontrolleret ved 320/390/768/1440 px med fiktive navne: normal kontrast mindst 7:1, mørk baggrund, lys tekst ved markering og uændret tastaturvalg. Visuel kontrol er udført på smal/bred visning. Ingen privat forkynderliste er åbnet.

## Med fra beta.23


## Nyt siden beta.22

W25/W26: én samlet spørgsmålsguide med lokal introduktion og obligatorisk afsluttende rundtur. Afslut rundtur lukker guiden og åbner forsiden med din plan. Afbrydelse kan genoptages; eksisterende fuldført opsætning tvinges ikke gennem en ny tur. Import og kortinddeling er bevaret som værktøjer.

W27: direkte trin til egen Datafordeler-nøgle fra kortplanen og tydelig REST-frist 15. januar 2027. GraphQL-importen er allerede implementeret; egen konto og lille prøvehentning står særskilt.

## Prøv især

1. Opdater Distrikt Beta (port 8788). Main er stadig stabil 1.11.1.
2. Åbn guiden under Indstillinger → Generelt. På en tom ny/nulstillet beta starter den automatisk. Kontrollér lokal introduktion og vælg din brugsmåde.
3. Afslut spørgsmålene. En ny opsætning har Gem og start rundtur; svar alene fuldfører ikke forløbet.
4. Vælg Fortsæt senere under rundturen, og genåbn appen. Den gemte plan skal kunne fortsættes. Prøv dansk/engelsk uden at skifte turtrin.
5. Afslut sidste trin: guiden skal være lukket, forsiden åben og din plan synlig. Der skal ikke være oprettet kort eller IB af rundturen.
6. Med kortfunktion valgt: åbn nøgletrinnet i planen. Opret egen nøgle hos Datafordeleren og indsæt den kun i den lokale app. Start med én offentlig vej. Send aldrig nøglen i chat/feedback.

Offline Chromium kontrollerer rigtig DOM, lagring med opdigtede svar, afbrudt/genoptaget tur, sprog, afvist/dobbelt afslutning og lukning til forsiden ved 320/390/768/1440 px. Tidligere fuldførte indstillinger og ukendte felter dækkes af Python-prøver. Smal introduktion og bred afslutning er visuelt gennemgået. Egen HA/telefon, API-konto og printer er særskilte ejertrin.
