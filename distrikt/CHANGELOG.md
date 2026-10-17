# Ændringsliste

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
