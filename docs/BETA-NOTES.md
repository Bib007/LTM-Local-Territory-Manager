# LTM 1.12.0-beta.22

## Nyt siden beta.21

Den faste udviklingsplan er afsluttet: 100 % (10/10). Printbetjeningen er dansk/engelsk med bevaret indtastning. Originale S-12/S-13-formularer, kortmål og danske rapporter er bevaret. Dobbeltklik, sene svar og ændret grundlag beskyttes; manglende billeder spærrer print.

Den samlede programpakke indeholder nu alle linkede vejledninger. Brudte lokale vejledningslinks og manglende original S-12-PDF stopper pakningen. Der følger en dansk/engelsk printguide og slutkontrol med tydelig ejerrestliste.

## Prøv især

1. Opdater Distrikt Beta på port 8788. Main er fortsat stabil 1.11.1.
2. Åbn et opdigtet kort → Print forside. Vælg A4, fuldt tryk og mål/placering. Skift dansk/engelsk: værdierne skal bevares.
3. Vælg Fremvis og print. Se originalkortet og vælg 100 % uden sidehoved/sidefod. Kontroller fysisk A4 først og derefter rigtige kort. Gentag med bagside.
4. Prøv samlet rapport samt separat original S-13. Kontroller tjenesteår, kortudsnit, navne/datoer, sideskift og fortsættelser.
5. En preview/PDF/profilgemning må aldrig godkende genprint. Godkend først den ændrede side, når det fysiske resultat er kontrolleret.
6. Ved fejlet profilgemning: læs gemmestatus og brug Opdater, når appen kræver det. Gentag ikke en usikker skrivning.

Automatiske prøver bruger opdigtede data: 347 Python-prøver (én forventet overspringning), alle JavaScript-prøver, 12 pakkeprøver og offline Chromium ved fire bredder. Printprøverne laver faktiske front-/bagside-/rapport-PDF'er. Egen printer, HA/telefon/VPN, Google, Datafordeler og eventuel skærmlæser står fortsat som lokale ejerprøver.

[Printguide](PRINT.md) · [Slutkontrol](SLUTKONTROL.md) · [Ejerrestliste](../Dette-skal-hjaelpes-manuelt.md)

Den faktiske pakkestart afslørede en gammel versionsetiket i API-svaret. Appens viste version følger nu den kørende servers version; HTTP-prøven kontrollerer begge kanaler mod ping.
