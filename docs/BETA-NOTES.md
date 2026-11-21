# LTM 1.13.0-beta.1

Dette er en Beta med ny brugsstatistik under Indstillinger. Den er adskilt fra Stable og ændrer ikke gemte distriktsdata.

## Ny funktion

- Vælg Indstillinger → Brugsstatistik → Beregn statistik.
- Se anslået samlet arbejdstid, systemets registrerede aktivitetsperioder, antal redigeringer og dage med aktivitet.
- Se estimater pr. identificeret bruger og samlet for fælles login/ukendt bruger. Sammenlign redigeringer og tidsestimat måned for måned med brugerfilter.
- Eksisterende aktivitetshistorik bruges automatisk. Tid fra før registreringen startede, og arbejde uden gemte ændringer, kan ikke genskabes.

## Vigtige begrænsninger

- Tid tælles kun mellem to faktisk gemte redigeringer med højst 15 minutter imellem. Enkeltstående ændringer og længere pauser giver ingen minutter. Der lægges ingen gættet tid til før første eller efter sidste handling.
- Dette er ikke serverens oppetid, et login-/tilstedeværelsesregnskab eller en præcis tidsregistrering. Tiden er et konservativt estimat ud fra hændelserne.
- Summeret arbejdstid lægger brugernes perioder sammen; systemets aktivitetstid tæller overlappende perioder én gang.
- Fælles login og hændelser uden sikker brugeridentitet tilskrives ikke navngivne brugere. Nogle automatiske handlinger indgår ikke i aktivitetsloggen.
- Adgangen kræver Administrere indstillinger. Funktionen læser lokale hændelser og gemmer eller eksporterer ingen personlige statistikdata.

## Test som Beta

1. Verificér versionen 1.13.0-beta.1 i den særskilte beta-installation (port 8788 og datamappen Distrikt-beta).
2. Åbn Indstillinger → Brugsstatistik, og prøv Beregn statistik. Kontrollér tom historik, ældre hændelser og brugere.
3. Opret et par fiktive kortændringer med kort tids mellemrum. Kontrollér, at statistikken stiger, men ikke tilskrives en forkert bruger.
4. Kontrollér, at en bruger uden Administrere indstillinger ikke kan hente statistik, og at Stable fortsat fungerer uændret.

## English

New read-only usage estimates in Settings, retrospectively derived from saved audit events. Work-time totals, per-user and monthly views are estimates from pairs of edits within 15 minutes, not actual presence or uptime. Shared or unidentified events stay unattributed. The endpoint requires Manage settings; no data migration.
