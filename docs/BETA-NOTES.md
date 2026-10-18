# LTM 1.12.0-beta.33

Ét ønskepunkt: W54. Alle ændringer fra beta.30–32 er med.

- Hurtig oprettelse har nu Interval med start og slut inklusive, valgfrit antal cifre/nuludfyldning og ét valgfrit bogstav foran numrene. 0–300 med fire cifre giver 0000–0300, i alt 301 kort. Et prefix bevares, fx k0–k99 eller b100–b199.
- Alle endelige numre, antal og dubletter vises før godkendelse. Højst 500 kort pr. oprettelse; ugyldige intervaller og dubletter stopper hele oprettelsen. Eksisterende, arkiverede og gendannelige numre reserveres uanset store/små bogstaver. Eksisterende kort overskrives ikke.
- Egen liste virker som før, hvor 1–10 er ét bogstaveligt kortnummer. At skifte nummereringsmetode opretter intet. Dansk/engelsk skifter uden at miste valgte værdier.

Tag fortsat en privat backup før opdatering. Ejerens faktiske API-hentning skal stadig prøves med rettelsen fra beta.30; grøn forbindelse alene er ikke nok. W61's eksterne GitHub-cache/PR-oprydning og udgivelsesmetadata er stadig åbne. W06 og den afhængige nøglebackup W56 er ikke færdigmeldt. Main er stabil 1.11.1.
