# LTM 1.12.0-beta.39

Ét fejlpunkt: W62. Alle ændringer fra beta.30–38 er med.

- Beta.38 gav fortsat en generisk afvisning på både grænse og enkelt vej. Nu vises en sikker GQL-fejlkategori, entitet og genkendt fejlkode/feltnavn. Ingen rå leverandørtekst, søgeværdier, URL'er eller nøgler vises.
- Ved genkendte størrelsesfejl reduceres sidestørrelse, alias-batches og om nødvendigt grænseudsnit med faste grænser. Andre afvisninger genprøves ikke som størrelsesfejl. Filtre, tidspunkt, cursor og fuldstændighedskontrol bevares.
- Prøv først én vej. Hvis den stadig afvises, oplys kun GQL-diagnostikken fra appen. Den reelle afvisningsårsag og fungerende adressehentning er endnu ikke bekræftet; W62 er åben.

Tag fortsat en privat backup før opdatering. Ejerens faktiske API-hentning skal prøves igen med beta.39; grøn forbindelse alene er ikke nok. W61's eksterne GitHub-cache/PR-oprydning og udgivelsesmetadata er stadig åbne. W06 og den afhængige nøglebackup W56 er ikke færdigmeldt. Main er stabil 1.11.1.
