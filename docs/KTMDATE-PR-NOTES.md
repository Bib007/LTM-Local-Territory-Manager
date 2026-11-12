# KTM-besøgsdato: tirsdagen i KTM-ugen

## Adfærd og kompatibilitet

- Datoen i besøgsdialogen repræsenterer tirsdagen i den uge, hvor KTM-besøget finder sted; den er ikke nødvendigvis dagen for et konkret møde.
- Ved ny registrering vælges seneste tirsdag som standard (UTC-kalenderdag, uden lokal tidszoneforskydning). Nye datoer og ændrede datoer valideres som tirsdag både i klient og på server. Den eksisterende regel om, at datoen ikke må ligge i fremtiden, er uændret.
- Registreringer med andre ugedage fra tidligere versioner **omskrives ikke**. De kan fortsat vises og gemmes med uændret dato, mens ændringer af dato kræver en tirsdag. Intet automatisk dataskift eller migrering.
- Bemærkningsfeltet er fjernet **kun fra KTM-besøgsdialogen**. Historiske `visits[].note` forbliver i databasen, synlige i den eksisterende besøgsoversigt og med i nuværende backup/eksport. Øvrige noter/opgaver ændres ikke.
- API `visit.save` accepterer stadig `note` fra ældre klienter. Hvis `note` udelades, bevares det eksisterende felt uændret; på nye poster er standarden tom tekst. Dette undgår utilsigtet sletning ved redigering.

## Undersøgte afhængigheder og integrationsrisici

- **Database:** `distrikt/app/store.py` fortsætter med samme SQLite-records/payload; **ingen skemaændring**, ingen datamigrering. Backups/udtræk i `distrikt/app/readable_export.py` berøres ikke.
- **API-kontrakt:** `visit.save` validerer fremover nye/ændrede besøgsdatoer som tirsdag; ældre klienter, der vælger andre ugedage, får en valideringsfejl. Oprettelse og redigering uden `note` har nu ikke-destruktiv semantik.
- **Rapport:** `distrikt/app/workspace.js` læser de eksisterende `visits[].date` til de gule markeringer, og `visitList()` viser historiske `note`; ingen ændringer i periodetyper, markører eller rapportberegning.
- **Delte filer / parallelle PR'er:** `distrikt/app/app.js` (KTM-dialog, submit-handler), `distrikt/app/i18n.js` og `distrikt/tests/test_report_language.cjs` kan overlappe arbejdet med rapportudskrivning og oversættelser. Opdatér branchen mod nyeste `develop`, kontrollér konflikter og kør hele rapport-/i18n-testpakken før merge. `distrikt/app/store.py` deler central datomutation med andre udviklingsopgaver.
- **Sikkerhed og adgang:** Rettighedskontrol for den eksisterende `visit.save`-handling er uændret. Ingen persondata er tilføjet.

## Verifikation

- Node-kontrakttest `distrikt/tests/test_report_language.cjs`: præcis dansk hjælpetekst, engelsk oversættelse, dato-default på tirsdag, dialog uden note-felt, historiske noter stadig synlige, rapport på syntetiske data.
- Python `distrikt/tests/test_workflows.py`: tirsdagskrav ved oprettelse/redigering, ugyldig/fremtidig dato, ældre ikke-tirsdage, bevaring ved udeladt `note` og SQLite-genåbning.
- CI-workflow `.github/workflows/check.yml`: øvrige Python-/JavaScript-, rapport- og browserkontroller kører på PR.
- Merge og Stable-release er **ikke** en del af denne opgave; afvent review og grøn CI.
