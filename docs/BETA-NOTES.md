# LTM 1.12.0-beta.38

Ét fejlpunkt: W62. Alle ændringer fra beta.30–37 er med.

- Forkert punktstatus i GraphQL er rettet. En kontrolleret nøgle kunne tidligere give tomme områdehentninger. Punktdata har en anden livscyklus end adresser/husnumre; de rigtige afgrænsede opslag og relationer bruges nu.
- Gamle GraphQL-grænsehentninger genprøves automatisk. Et ægte tomt resultat giver en advarsel, og et tomt svar kan ikke udgå områdets eksisterende lokale adresser.
- Prøv efter opdateringen Opdater hele området og en virkelig vej med din egen nøgle. Ejerprøven i beta.37 viste fejlen; den nye faktiske hentning er endnu ikke bekræftet. Ingen nøgle eller lokale adresser er brugt i udviklingstests.

Tag fortsat en privat backup før opdatering. Ejerens faktiske API-hentning skal prøves igen med beta.38; grøn forbindelse alene er ikke nok. W61's eksterne GitHub-cache/PR-oprydning og udgivelsesmetadata er stadig åbne. W06 og den afhængige nøglebackup W56 er ikke færdigmeldt. Main er stabil 1.11.1.
