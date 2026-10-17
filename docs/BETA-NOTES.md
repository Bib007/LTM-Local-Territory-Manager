# LTM 1.12.0-beta.14

## Nyt siden beta.13

Avanceret opsætning har dansk/engelsk i alle fire trin: ydergrænse/adresser, områder/nummerering, kontrol/oprettelse og lokal IB-import. Sprogskift bevarer kort, kladdenavne/-numre, geometri og IB-kontrol. Type- og nummereringsværdier samt CSV-format bevares. Bekræftelsesordene er fortsat **OPRET KORT** og **IMPORTÉR IB** på begge sprog.

Langsomme forslag og filindlæsninger kan ikke erstatte nyere kontrol. En ny fil, ændret dato eller fejl ugyldiggør ældre IB-kontrol. Felter er spærret under selve oprettelsen. Eksisterende kort, historik og IB overskrives ikke.

## Prøv især

1. Opdater **Distrikt Beta**. Brug opdigtede kort og IB i denne prøve. Stabil installation fortsætter separat.
2. Åbn **Indstillinger → Avanceret → Opsæt distrikter**. Udfyld område, type, nummerering og forbogstaver. Skift sprog og kontrollér, at værdierne bevares.
3. Lav et forslag. Ret navn og nummer, se kortet, og skift sprog. Kontrollér igen før udtrykkelig oprettelse med **OPRET KORT**.
4. Hent IB-skabelonen, og prøv en ufølsom CSV med én gyldig og én ugyldig adresse. Kontrollér, at fejl spærrer import. Skift sprog under kontrolvisningen.
5. Vælg en rettet fil. Ændr standarddatoen og kontrollér, at en ny kontrol kræves. Godkend kun korrekte rækker med **IMPORTÉR IB**. Kontrollér berørte bagsider; forsiders besøgstal skal være uændrede.

Fiktive programprøver kontrollerer samme payload på begge sprog, ugyldige bekræftelser, sene forslag, ombyttede filer og dato-/navigationsskift. Offline Chromium kontrollerer rigtig app/Leaflet ved 320/390/768/1440 pixels. Egne private filer er ikke åbnet. Egen HA/telefon, konti og fysisk print er særskilte prøver.

Den faste køreplan er 40 % (4/10); næste er Google/QR med opdigtede svar. Ønskelisten venter fortsat.
