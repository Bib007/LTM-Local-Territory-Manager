# Udviklingsplan

Dansk er hovedsprog. Den offentlige grundudgave er 1.11.1. Videre udvikling omfatter tydeligere betjening, valgfrit engelsk i flere arbejdsgange, bedre kladdebevaring og samlet udgivelseskontrol.

## Ét repository

- `main` indeholder den stabile udgave, som Home Assistant installerer fra den almindelige repositoryadresse.
- `beta` er den genererede HA-betakanal fra en kontrolleret prerelease. Den har separat identitet, port og data og kan installeres ved siden af stabil.
- `develop` indeholder næste version under klargøring. Den er til udvikling og prøver og bruges ikke som almindelig HA-opdateringskilde.
- Hver stabil udgivelse får et fast versionstag og en programpakke. Nye ændringer samles via pull requests og relevante kontroller, før de føres til `main`.

Den samme kodebase bruges til Mac, Windows og Home Assistant. Installationer med rigtige data fortsætter på én hovedinstallation. En udviklingsprøve bruger egne opdigtede data og sin egen datamappe.

Ændringer udgives først som almindelige opdateringer, når de relevante program-, formular- og pakkekontroller består. Se [ændringslisten](../CHANGELOG.md) og [kendte begrænsninger](../LIMITATIONS.md).

[Næste versions nummererede køreplan](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/develop/KOREPLAN.md).

Små sammenhængende funktioner udgives løbende som nummererede HA-betaer med en kort testliste. Se [betavejledningen](../BETA.md). Betaversioner genbruges ikke til ændret kode; `main` og den seneste stabile release ændres ikke ved en beta.
