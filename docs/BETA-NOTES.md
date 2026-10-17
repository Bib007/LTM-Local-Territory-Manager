# LTM 1.12.0-beta.17

## Nyt siden beta.16

Gendannelse og beta-nulstilling er nu beskyttet mod dobbeltklik og sene svar. En allerede gennemført handling, hvor efterfølgende genindlæsning fejler, vises som gemt med behov for kontrol. Den bliver ikke sendt igen automatisk. En nyere formular eller side erstattes ikke af det gamle svar.

## Prøv især

1. Opdater Distrikt Beta, adskilt fra stabil, og brug kun opdigtede prøvedata. Hent en lokal backup i betaens indstillinger først.
2. Gendan en ufølsom prøvebackup. Kontrollér samtykke, indhold og den lokale sikkerhedskopi fra før import. Ingen rigtige databaser skal sendes til AI eller GitHub.
3. På en prøveinstallation: luk importdialogen under en langsom import, og åbn en anden formular. Et sent svar må ikke lukke den nyere formular. Afslut den, vælg Opdater og kontrollér det faktisk gemte resultat før videre arbejde.
4. Prøv Nulstil betadata med opdigtede registreringer. Det kræver fortsat NULSTIL BETA. Kontrollér tomme data, lokal sikkerhedskopi og mulighed for ny opsætning; stabil installation må ikke berøres.
5. Hvis appen melder, at handlingen er gemt, men genindlæsning mangler: vælg Opdater og kontrollér data. Kør ikke import/nulstilling igen for at teste forbindelsen.

Fiktive programprøver dækker samtykke/token, beta-begrænsning, dobbeltanmodninger, fejlet læsning efter bekræftet skrivning samt nyere dialoger og navigation. Offline Chromium dækker et forsinket accepteret import-svar ved 320/390/768/1440 pixels. Ingen rigtig backup er åbnet i disse prøver.

Fast køreplan: 50 % (5/10). Punkt 6 er i gang; domænespecifikke fejltekster og øvrige skrive-/bekræftelsesforløb skal færdiggøres før punkt 7. Ønskelisten venter fortsat. Egen HA/telefon, Google/Datafordeler og fysisk print er særskilte ejertrin.
