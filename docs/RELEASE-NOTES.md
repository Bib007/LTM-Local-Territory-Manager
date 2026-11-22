# LTM 1.12.38

Afgrænset Stable-hotfix på 1.12.37: S-13-oplysninger følger nu den periode, man vælger i rapporten. Kalenderår og seneste 12 måneder er tilføjet uden at trække uafsluttede Beta-funktioner med.

## S-13 efter periode

- Vælg **Kalenderår**, **Tjenesteår** eller **Seneste 12 måneder** under Rapporter og historik. For kalenderår kan du vælge historiske år.
- Tal, udleveringer og gennemgangsdatoer i S-13-visningen følger den præcise periode. En gennemgang uden for perioden tælles ikke med.
- For tjenesteår vises den uændrede originale S-13, som fortsat kan hentes direkte som lokal PDF.
- For kalenderår og seneste 12 måneder vises et tydeligt mærket, ikke-officielt **S-13-periodeudtræk**. Det kan printes/gemmes som PDF alene eller indgå i den samlede rapport.
- Eksisterende Stable-rapporttal og øvrige funktioner bevares. Ingen registreringer ændres, og der sker ingen datamigrering.

## Udgivelse

Udgiv først efter grønne PR-kontroller på den præcise kode. GitHubs **Stable release tracks** skal derefter køres manuelt på `main` for hvert ønsket spor. macOS-server kræver fortsat særskilt fysisk godkendelse.

## English

LTM 1.12.38 adds period-specific S-13 assignment and completion details to calendar-year and rolling-12-month reports while preserving the original S-13 and direct PDF download for service years. Each non-service-year extract is clearly marked as non-official. Previous Stable functionality and stored records remain unchanged; unreleased Beta functionality is excluded. The Stable release remains manually dispatched per platform after green checks.
