# Gennemgange & historik – implementering og sikkerhed

## Funktion

Under **Rapporter og historik → Gennemgange & historik** vises hvert kort i en kompakt række med de to seneste udleveringsforløb, kronologisk fra venstre mod højre. Hver udlevering har en udleveringsdato og en eventuel indleveringsdato. Alle øvrige eksisterende udleveringer og løse gennemgange findes under **Hele historikken**.

Datoer kan rettes med dansk tekstindtastning (DD.MM.ÅÅÅÅ), Enter/Tab eller native datovælger. Indtastning kan også være ISO (ÅÅÅÅ-MM-DD). Søgning finder kort, område og forkynder; filtrene viser aktive kort, kort uden historik og ulogiske eksisterende forløb. 100 kort vises ad gangen; flere indlæses efter behov.

**+ Udlevering** registrerer en ny udlevering knyttet til en *eksisterende* forkynder og eventuelt en indlevering. Brugeren skal særskilt markere, om kortet også blev gennemgået. Ellers skabes ingen completion ved indlevering. Ukendte besøgstal gætt es ikke (visits=0, visits_unknown=true). Eksisterende gennemgang på samme dato knyttes til udleveringen, hvis den endnu ikke er knyttet til andet udlån.

## Datamodel og API

- Ingen ekstra tabeller, databasemigration eller baggrundskørsel. LTM's eksisterende `loans`, `completions`, `cards`, `publishers` og aktivitetsposter genbruges.
- To nye actions på det eksisterende `POST /api/mutate`: `history.grid.add` og `history.grid.edit`. Begge kræver eksisterende global `revision` og bliver afvist ved ændringer i mellemtiden. `history.grid.edit` kræver `id`, `field=assigned|returned`, `date=ISO|null`. `history.grid.add` kræver `card_id`, `publisher_id`, `assigned`, valgfri `returned` og eksplicit `completed`.
- På serveren kontrolleres datoer, fremtid, rækkefølge, overlap, arkivering, dubletter, genoprettelige poster og sammenknyttede gennemgange. Alle ændringer er atomare via eksisterende SQLite-transaktion.
- Rettighedskrav på begge actions: `cards.view`, `loans.view`, `loans.manage`, `publishers.view`, `history.view`, `history.edit`. Ingen nye privilegier eller dataeksponering.
- Eksisterende activity-log med aktør og ændrede moduler bruges; `workflow.undo` er tilgængelig indtil 120 sekunder og kun så længe ingen anden ændring er udført. Gendannelse af gamle sikkerhedskopier følger fortsat de eksisterende restore-rutiner.

## Eksisterende import, backup og begrænsninger

Brug **Sikkerhedskopi** før større rettelser og **Importér CSV / S-13** for flere rækker. Eksisterende historieimport har en *toårsgrænse for afsluttet historik*; den ændres ikke stiltiende i denne PR. Individuel indtastning i gitteret tillader ældre datoer og er ikke begrænset af importens cutoff. Importen har allerede forhåndskontrol, dubletdetektion og atomar apply. CSV, PDF og andre importregler ændres ikke her.

Ændring af en indleveringsdato, som er knyttet til en completion, flytter samme completion i stedet for at skabe en ny. Krydsning af en anden completion, dubletdato og sletning af indleveringsdato med completion afvises. Andre gamle datoer, data og besøgstal bevares. En *ukendt* indlevering får ingen automatisk completion. Ret ældre/korrupte historikforløb som separate gennemgåede ændringer.

## Samtidig udvikling og integration

- Feature-branch: `feature/gennemgange-historik-grid`, basis `develop` fra 9. november 2026.
- Delte backendfiler: `distrikt/app/store.py`, `distrikt/app/profile_policy.py`.
- Delte frontendfiler: `distrikt/app/workspace.js`, `distrikt/app/index.html`, `distrikt/app/server.py`. Resten af implementeringen ligger i nye selvstændige `history_grid.py`, `history-grid.js`, `history-grid.css`.
- Kontrakt: frontend bruger kun eksisterende `state.loans`, `state.completions`, `state.cards`, `state.publishers`, `state.revision`. Ingen nye offentlige endpoints eller skemaændringer.
- Berøringsflader: `loan.correct`, `loan.finish`, `completion.record`, `setup.history-import.*`, `workflow.undo` og rapporternes S-13. Review historik og S-13 regression, især sammenkædede datoer.
- Testfilernes fixtures er fiktive. Ingen private kort, forkyndere eller realdata læses eller uploades. Fysiske iPhone-, Android-, iPad- og Mac/Windows-enheder er ikke testet af denne PR.

## Test og releasegate

Kør `python -m unittest discover -s distrikt/tests -p 'test_history_grid.py' -v` og `node distrikt/tests/test_history_grid_ui.cjs`, dernæst hele `.github/workflows/check.yml` med alle eksisterende tests og browser-tests. Kontroller to tidsforløb, igangværende udleveringer, ukendte datoer, krydsende dateringer, udleveringer i gendannelse, samtidige revisioner, rollebeskyttelse og transaktionsrollback. Merge ikke før review og grøn CI. Ingen Stable-release fra denne PR; integrér godkendte PR'er på develop, regressionsprøv og lav først derefter separat kontrolleret Stable.
