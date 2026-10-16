# Udviklingsplan

Dansk er hovedsprog. Den offentlige grundudgave er 1.11.0. Videre udvikling omfatter tydeligere betjening, valgfrit engelsk i flere arbejdsgange, bedre kladdebevaring og samlet udgivelseskontrol.

## Ét repository

- `main` indeholder den stabile udgave, som Home Assistant installerer fra den almindelige repositoryadresse.
- `develop` indeholder næste version under klargøring. Den er til udvikling og prøver og bruges ikke som almindelig HA-opdateringskilde.
- Hver stabil udgivelse får et fast versionstag og en programpakke. Nye ændringer samles via pull requests og relevante kontroller, før de føres til `main`.

Den samme kodebase bruges til Mac, Windows og Home Assistant. Installationer med rigtige data fortsætter på én hovedinstallation. En udviklingsprøve bruger egne opdigtede data og sin egen datamappe.

Ændringer udgives først som almindelige opdateringer, når de relevante program-, formular- og pakkekontroller består. Se [ændringslisten](CHANGELOG.md) og [kendte begrænsninger](docs/LIMITATIONS.md).
