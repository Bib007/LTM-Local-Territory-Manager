# LTM 1.12.0-beta.30

Tre ønskepunkter: W62, W55 og W46.

- W62: Hent vej med egen API-nøgle går direkte til DAR GraphQL. Det gamle systems vejforslag kan ikke længere blokere hentningen. Gælder også adresser til vejene i et lille OSM-udsnit. Skriv det præcise officielle navn og postnummer, hvis forslagstjenesten er utilgængelig.
- W55: Afvist API-adgang forklarer nu, at en ny nøgle kan være op til 15 minutter om at blive aktiv. Andre fejl forklares ikke som ventetid. Dansk/engelsk og bevidst genprøve er bevaret.
- W46: Gem sikkerhedskopi som… tilbyder navn og placering, hvor browseren tillader det. Annullering henter intet og registrerer ikke succes. Almindelig download er altid tilgængelig; browserens downloadindstillinger bestemmer da placeringen. Ingen automatisk upload.

Testet med opdigtede oplysninger. Ejerens faktiske API-hentning skal stadig prøves efter opdateringen; grøn forbindelse alene er ikke nok. Prøv én vej med lejligheder, et lille område og opdatering. Send aldrig nøglen eller private adresser i chat/feedback.

W63: Bred kontrol af faste eksempler afsluttet; nye regressionstests efterprøver tomme adressefelter. W61: Alle udgivelsespakker og grene/tags er renset og verificeret; resterende GitHub-cache/PR-henvisninger og udgivelsesmetadata kræver ekstern oprydning. Main er fortsat stabil 1.11.1.
