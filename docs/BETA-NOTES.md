# LTM 1.12.0-beta.35

Ét ønskepunkt: W52. Alle ændringer fra beta.30–34 er med.

- Indstillinger → Data viser de seneste 100 manuelle backupforsøg: ZIP oprettet, browserdownload startet eller filskrivning bekræftet af filvælgeren. Almindelig download er ikke bevis for en fil på disken; kontrollér filen i browseren.
- Annullering registrerer ingen backup. Fejlet filskrivning beholder kun ZIP-oprettelsen og udskyder ikke påmindelsen. Historikken gemmer ingen filstier eller nøgler og følger dataene ved gendannelse. ZIP'en indeholder historikken fra før dens egen oprettelse.
- Forsiden påminder efter mindst 14 kalenderdage, eller hvis ingen overførsel er registreret. Udsæt til i morgen skjuler feltet til næste kalenderdag. Ingen automatisk backup, upload eller ekstern besked.

Tag fortsat en privat backup før opdatering. Ejerens faktiske API-hentning skal stadig prøves med rettelsen fra beta.30; grøn forbindelse alene er ikke nok. W61's eksterne GitHub-cache/PR-oprydning og udgivelsesmetadata er stadig åbne. W06 og den afhængige nøglebackup W56 er ikke færdigmeldt. Main er stabil 1.11.1.
