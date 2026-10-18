# LTM 1.12.0-beta.37

Ét opfølgningspunkt: W52. Alle ændringer fra beta.30–36 er med, inklusive W53's ugentlige opgaver.

- Backupdatoen og appens i dag følger samme lokale serverkalender. Påmindelsen kommer dermed ikke en dag for tidligt, når en backup er registreret efter lokal midnat, men stadig på forrige UTC-dato.
- Sommer-/vintertid er dækket af syntetiske tests. Det er en læseberegning; gemte tidsstempler, backupfiler, historik og udsættelser ændres ikke.
- Alle ugentlige opgaver og backupfunktionerne fra beta.34–36 er bevaret. Ingen automatisk backup, kortflytning, upload eller ekstern besked.

Tag fortsat en privat backup før opdatering. Ejerens faktiske API-hentning skal stadig prøves med rettelsen fra beta.30; grøn forbindelse alene er ikke nok. W61's eksterne GitHub-cache/PR-oprydning og udgivelsesmetadata er stadig åbne. W06 og den afhængige nøglebackup W56 er ikke færdigmeldt. Main er stabil 1.11.1.
