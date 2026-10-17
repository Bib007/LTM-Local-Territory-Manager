# Ændringsliste

## 1.12.0-beta.13 · Korteditor og grænser

- Dansk/engelsk betjening i geografisk korteditor, samlet grænse og KML/GeoJSON-import. Sprogskift bevarer kort, zoom, fokus, valgte adresser, tegning, formularer og importfil. Gemte typer og API-værdier ændres ikke.
- Forsinkede forhåndsvisninger, oprydning og import kan ikke erstatte nyere kladder/dialoger. Gemning bruger en fast kopi, afviser ændret/annulleret valg før skrivning og bevarer en nyere tegning under gemning. Dobbeltgemning og reference-deling af kortgrænser er rettet.
- Gentagelige fiktive Chromium-prøver ved 320/390/768/1440 pixels kræves før HA-betaudgivelse. Kortvælgeren holder sig inden for en smal skærm. Fast køreplans punkt 3 er afsluttet; planen er 30 %, og ønskelisten venter.

## 1.12.0-beta.12 · Digitalt QR-kort

- Delt kortbillede får et nyt blåt layout med stor kortflade, tydeligt kortnummer/navn og miniature af printforsiden i hjørnet. Den blanke S-12-forside og printets vejlinjeformatering genbruges.
- Miniaturen bygges kun af den offentlige opskrift, ikke af private kortdata. IB, noter og kortholdere indgår ikke. Lange navne og tætte/tomme kort er afprøvet i fiktive SVG/PNG-billeder.
- Eksisterende QR-links og adgangscyklus bevares. Ældre layout markeres til manuel opdatering; nyt billede kræver fortsat preview og udtrykkelig godkendelse.

## 1.12.0-beta.11 · Kurvede og sammenhængende vejskel

- Automatisk inddeling kan følge vejens faktiske knæk og kurver. Samme-navn-vejstykker forbindes kun ved præcist fælles endepunkt uden forgrening; huller lukkes ikke ved gæt.
- Tvetydige skæringer, løkker, selvkrydsning og komplekse grænsekrydsninger afvises. Areal, overlap, hvert adressepunkt og hele huse kontrolleres. Manuelle rettelser og eksplicit samlet oprettelse bevares.
- Dansk/engelsk inddelingsvejledning beskriver lokale vejdata, kontrol og begrænsninger. Naturlige skel er næste del af W16; ønsket er ikke markeret afsluttet.

## 1.12.0-beta.10 · Første vejbaserede skel

- Automatisk kortinddeling foretrækker nu egnede, lokalt hentede gennemgående lige vejstykker som skel, også på skrå. Ingen nye netkald og ingen automatisk kortoprettelse.
- Korte vejfragmenter forlænges ikke kunstigt. Husenes lejligheder og faktiske adressepunkter bevares samlet. Manglende egnede vejstykker giver en tydelig markering af geometrisk deling til manuel rettelse.
- Vejdata indgår i kontrollen af forældede forhåndsvisninger. Kurvede veje, sammensatte vejforløb og naturlige skel er fortsat udestående under W16.

## 1.12.0-beta.9 · Forkynderforslag

- Udlevering får en lokal søge- og forslagsliste med fornavn/efternavn, højst otte forslag, tastaturvalg og berøring. Søgetekst og navne forlader ikke appen.
- Nye navne kan fortsat skrives frit og oprettes først ved registrering. Escape/Tab vælger ikke et navn; Enter i en åben liste gemmer ikke ved et uheld. Dansk/engelsk og formularens data bevares.
- Programprøver dækker hændelser og gemmekontrakt; visuel mobil-/skærmlæserkontrol står særskilt.

## 1.12.0-beta.8

- Gemt Datafordeler-nøgle bruges nu til vej-, postnummer- og grænsehentning via DAR GraphQL. Komplette sider, lokale joins og stabile DAR-ID'er bevarer lejligheder og eksisterende registreringer.
- Genoptagelse kræver samme kilde og skemafingeraftryk. Gamle REST-hentninger blandes ikke med GraphQL. Ved kildeskift vælges en ny opdatering; lokale adresser bevares.
- Checkpoint og adresseimport gemmes samlet. Netfejl stopper ved den aktuelle vej/udsnit; pause og genstart bevarer afsluttede dele. Præcise distriktsgrænser filtreres lokalt.
- Flere officielle vej-ID'er med samme navn/postnummer behandles samlet, så adresser ikke fejlagtigt foreslås udgået mellem delene.

## 1.12.0-beta.7

- Kortdata får trinvis vejledning til egen Datafordeler-konto og API-key, lokal lagring og eksplicit forbindelseskontrol. Nøglen udelades fra portable sikkerhedskopier.
- Dette klargør DAR v3-forbindelsen; selve adresseimporten flyttes i et efterfølgende trin.

## 1.12.0-beta.6

- Den ekstra opfølgningsliste er fjernet fra KTM-rapporten og samlet PDF efter ejerens ønske. De øvrige rapportoversigter og original S-13 bevares.

## 1.12.0-beta.5

- Opsætningsguidens radioknapper arver ikke længere tekstfelters fulde bredde. Valgtekst og forklaring holdes inden for deres boks på smalle skærme.

## 1.12.0-beta.4

- Rapporten får en aktuel opfølgningsliste med manglende historik, gennemgange over 12 måneder og aktuelle udlån over fire måneder.
- Kort vises én gang med datoer og årsager; arkiverede kort udelades. Ingen personnavne, noter eller IB-adresser føjes til listen. Samme liste følger samlet PDF.

## 1.12.0-beta.3

- Fast topbar ved rulning på computer og mobil; logoet åbner forsiden med kontrol af ugemte ændringer.
- Fuldt projektlogo i topbaren på computer, kompakt mærke på mobil og tydelig beta-identitet.
- HA-ikon og logo følger nu både normal programpakke og betapakke.

## 1.12.0-beta.2

- Betaen kan nulstille testdata med bekræftelse, automatisk lokal sikkerhedskopi og kontrol af delte kort. Login og forbindelser bevares.

## 1.12.0-beta.1

Spørgsmål ved første start, personlig opsætningsplan, guidet rundtur og lokal XLSX-/CSV-import af allerede fordelte kort med adresser og områder. Præcise lejligheder kan bruges til lokal IB-import.


- Blå identitet og valgfri velkomstguide.
- Dansk/engelsk navigation, centrale kort-/udleveringsformularer, forkyndere, opgaver, indstillinger, rapportskærme, kortoversigt og adresselister.
- Kladder bevares ved sprogskift og flere forsinkede forhåndsvisninger.
- Forbindelseskontrol bekræfter ikke en usikker gemning.
- Backupoversigten sammenligner synlige kort og noter korrekt og bevarer arkiverede poster.
- Originalt dansk print, gemte værdier og datastier bevares.

## 1.11.0

- Første offentlige repositoryudgave til Home Assistant OS.
- Lokal administration, kort og adresser, udleveringer, gennemgange og IB.
- De tomme originale S-12/S-13-formularer følger med.
- Dansk installationsvejledning med engelsk som ekstra valg.
- Ingen ændring af eksisterende databaseskema eller appens lokale datasti.
- Lokal programstart undgår unødvendige reverse DNS-opslag.
