# LTM 1.12.0-beta.34

Ét ønskepunkt: W47. Alle ændringer fra beta.30–33 er med.

- Opsætningsplanen følger nu faktisk gemte indstillinger og oprettede data. Menighed, mappeminimum, begge printprofiler, forkynder, kort, ydergrænse, IB-import og registreret backup afslutter de relevante trin automatisk.
- Åbning, forhåndsvisning og afvist gemning tæller ikke. Fremdriften gemmes atomisk med handlingen og følger med ved Fortryd. Spring over og tidligere udførte trin bevares. Forbindelser og den samlede gennemgang af udleveringer bekræftes fortsat med Udført; én enkelt registrering er ikke bevis for hele gennemgangen.
- Nye installationer starter med mappeminimum 0, også for land. Eksisterende valg ændres ikke. Et ændret minimum eller et eksplicit indtastet og gemt 0 afslutter mappetrinnet; at gemme et andet felt godkender ikke standardværdien.

Tag fortsat en privat backup før opdatering. Ejerens faktiske API-hentning skal stadig prøves med rettelsen fra beta.30; grøn forbindelse alene er ikke nok. W61's eksterne GitHub-cache/PR-oprydning og udgivelsesmetadata er stadig åbne. W06 og den afhængige nøglebackup W56 er ikke færdigmeldt. Main er stabil 1.11.1.
