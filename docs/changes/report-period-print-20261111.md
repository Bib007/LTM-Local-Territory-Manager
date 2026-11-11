# Rapportudskrivning: valg af periodetype og månedstidslinje

## Omfang

- PDF-valg i rapportvisningen: kalenderår, tjenesteår, seneste 12 måneder eller det **eksplicitte** valg »Alle tre perioder«.
- Udskrivning tager udgangspunkt i den aktuelle fane. Ingen implicit samling af perioder.
- En enkelt periode indeholder dens egne tal, månedstidslinje, kort og statusforklaring; tjenesteårets originale S-13 medtages kun ved tjenesteår eller alle tre.
- Markering af nyeste KTM-besøg **inden for den valgte periodes datointerval** er gul med teksten »Sidste KTM besøg« og dato. Ingen opdigtet markering ved manglende besøgsregistrering.
- Aggergerede rapportlæsere får samme periodevalg, men kun de allerede autoriserede sammendragstal – ingen nye persondata, kort eller rå gennemgange.

## Eksisterende datoregler, som bevares

- `Workspace.periodBounds('calendar')`: 1. januar til 31. december i valgt kalenderår, afkortet ved `state.today`.
- `Workspace.periodBounds('service')` bruger fortsat `yearBounds()`: 1. september til 31. august i valgt tjenesteår, afkortet ved `state.today`.
- `Workspace.periodBounds('rolling')`: sidste 12 måneder frem til i dag; eksisterende håndtering af 29. februar bevares.
- Alle registreringer filtreres fortsat inklusivt på start- og slutdato. Ingen ændringer til tjenesteårsberegning, registreringer eller datakilde.
- `Workspace.monthlyComparison()` og dets skudårs-/delmånedssammenligning er ikke ændret.

## Flerbrugerarbejde og afhængigheder

- Feature-branch: `feature/report-period-print-timeline-20261111`, oprettet fra `develop` ved `cb684ff30f9f51e78f0e419318edb2d48df740eb`.
- **Database/migration:** ingen. **API-kontrakter:** ingen. **Gemte indstillinger:** ingen; periodevalget er kun klienttilstand under udskrivning.
- **Delte filer med konfliktmulighed:** `distrikt/app/workspace.js`, `distrikt/app/report-print.js`, `distrikt/app/profiles-ui.js`, `distrikt/app/i18n.js`, `.github/workflows/check.yml` og eksisterende rapporttests. Hold rettelser til disse filer isoleret og opdatér branchen fra den aktuelle `develop` før review.
- Arbejdet er skrevet til en selvstændig GitHub-branch gennem den tilsluttede GitHub-forbindelse. Et lokalt separat `git worktree` kan ikke oprettes her, fordi miljøet ikke kan hente repositoryet direkte. Ved lokal videreudvikling oprettes det med `git worktree add ../ltm-report-period feature/report-period-print-timeline-20261111`, efter `git fetch`.
- Ingen direkte commits på `develop` eller `main`. Ingen automatisk merge eller Stable-udgivelse.

## Test og godkendelse

- `node distrikt/tests/test_report_language.cjs`: alle fire valgmuligheder, korrekte overskrifter/kortsider, S-13-afgrænsning, markering, tomme perioder og uændrede start/slutdatoer.
- `node distrikt/tests/test_print_workflow.cjs`: asynkron klargøring af kun valgte kortbilleder, dobbeltklik og ændret rapportgrundlag.
- `node distrikt/tests/test_monthly_comparison.cjs`: særligt årsskifte og skudårsgrænser.
- `scripts/check_report_period_pdf_browser.cjs` køres i Actions med Chromium og Poppler: rigtige A4-PDF'er, alle 4 valg med både fiktive gennemgange/KTM-besøg og tomme registreringer (8 scenarier).
- Resten af `.github/workflows/check.yml` køres på PR'en. Rigtige fysiske printere og enheder er ikke testet.

Merge først efter review, opdatering mod nyeste `develop` og grønt CI. Efter andre godkendte PR'er er samlet på `develop`, køres fælles regressionstest og derefter planlægges én separat, kontrolleret Stable-release.
