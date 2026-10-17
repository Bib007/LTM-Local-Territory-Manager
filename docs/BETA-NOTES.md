# LTM 1.12.0-beta.21

## Nyt siden beta.20

Fast punkt 7 er afsluttet. Login har dansk/engelsk betjening med bevaret indtastning, tidsgrænse, tydelige fejl og beskyttelse mod dobbelt indsendelse. Kun sprogvalget gemmes som præference. Loginets adgangskontrol, cookie og rategrænse er uændrede; den generelle sprogfil og appdata er stadig beskyttede.

Dialoger har tydelig overskrift som navn, sammenknyttede feltlabels, startfokus og Tab/Shift+Tab inden for dialogen. Lukning returnerer til åbneren, også hvis listen blev tegnet igen. Escape følger fortsat kontrollen for gemning/ugemte felter.

## Prøv især

1. Opdater Distrikt Beta, adskilt fra stabil. Brug din kode kun i din egen lokale app; send den ikke i chat eller feedback.
2. På login: indtast en ufølsom forkert prøvekode og skift dansk/engelsk. Feltet skal bevares, og fejlen skal følge sproget. Indsend derefter med tastaturet. Respektér ventetiden efter gentagne fejl.
3. Log ind normalt lokalt. Kontrollér at sprogvalget følger med. Ingen registreringer ændres af login.
4. Åbn et kort med tastaturet og vælg redigering. Kontrollér feltlabels, Tab/Shift+Tab og fokus ved lukning med Escape.
5. Ved usikker gemning: afvis lukning. Teksten og fokus skal blive i dialogen; der må ikke ske en ny gemning. Afslut derefter bevidst og brug Opdater til kontrol.

Offline Chromium dækker almindelig/beta-login ved 320/390/768/1440 pixels med opdigtet kode, samme POST-payload, fejl/sprogskift og tastaturindsendelse. Appprøven kontrollerer native dialoger, labels, Tab/Shift+Tab, Escape og fokusretur. LAN-prøver kontrollerer uændrede beskyttede adresser. Skærmbilleder af smalt/bredt login er visuelt gennemgået; egen HA/telefon og skærmlæser er særskilte ejerprøver.

Fast køreplan: 70 % (7/10). Næste er punkt 8: printbetjening med uændrede originalformularer. Ønskelisten venter fortsat, og main er stabil 1.11.1.
