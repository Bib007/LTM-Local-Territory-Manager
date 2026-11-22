# LTM 1.12.39

Afgrænset Stable-rettelse af S-13 efter 1.12.38: Kalenderår og seneste 12 måneder bruger nu selve den originale S-13-formular frem for en ny separat tabel.

## Original S-13-formular for alle perioder

- **Kalenderår**, **Tjenesteår** og **Seneste 12 måneder** udfylder alle den eksisterende S-13-formular med dens oprindelige billedbaggrund, præcise felter, fire udleveringskolonner, kortnumre, tidligere gennemgange og udleverings-/gennemgangsdatoer.
- For kalenderår og rullende 12 måneder fremgår de præcise start-/slutdatoer tydeligt af en periodeoverskrift på samme side som formularen. Formularen er tilpasset perioden, ikke en officiel tjenesteårsrapport.
- Den særskilte HTML-tabel fra 1.12.38 bruges ikke længere. Samlet rapport/PDF og den særskilte periode-PDF viser begge S-13 på originalformularen.
- Tjenesteårets originale S-13 og direkte servergenererede PDF forbliver **uændrede**. Ingen data migreres eller redigeres.
- Hotfixen er isoleret til Stable-grenen; uafsluttede Beta-ændringer følger ikke med.

## Udgivelse

Udgivelsen kræver grønne PR- og Stable-workflowkontroller. Vælg det ønskede spor under **Stable release tracks** på `main`; macOS-server kræver fortsat separat fysisk godkendelse.

## English

LTM 1.12.39 corrects the 1.12.38 S-13 presentation: every reporting period now uses the actual original S-13 image form, its existing field positions and four assignment columns, rather than a substitute table. Calendar-year and rolling-period prints include a precise date-range caption and remain explicitly non-official period extracts. The original service-year S-13 and its direct downloadable PDF are unchanged. No existing records or unfinished Beta features are included in this change.
