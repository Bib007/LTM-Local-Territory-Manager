# LTM 1.12.0-beta.9

## Nyt siden beta.8

Udlevering har en tydelig lokal forslagsliste til forkyndernavne. Søg på fornavn eller efternavn; listen prioriterer præcise navne og begyndelsen af navne. Op til otte forslag vises, og du kan indsnævre listen ved at skrive mere. Navne og søgetekst sendes ikke til en ekstern tjeneste.

Brug piletaster og Enter til at vælge, eller tryk på navnet. Escape lukker forslagene; Tab fortsætter uden at vælge. Enter i en åben liste gemmer ikke udleveringen ved et uheld. Et nyt navn kan stadig skrives frit og oprettes først, når udleveringen registreres. Dansk/engelsk sprogskift bevarer navnet og formularens øvrige kladde.

## Prøv især

1. Opdater **Distrikt Beta** og tag først privat backup af betadata.
2. Åbn Udlever kort. Søg på et eksisterende fornavn og derefter et efternavn; vælg med piletaster/Enter og med berøring.
3. Prøv Escape og Tab. Indtast et nyt navn uden at vælge et forslag; annuller og kontrollér, at der ikke er oprettet en forkynder. Registrer derefter en almindelig udlevering.
4. Skift dansk/engelsk under indtastningen. Navn, kortvalg og dato skal bevares.
5. Kontrollér listen på din telefon: navne skal kunne læses, listen rulles, og dato/gemknap nås.

Automatiske prøver bruger opdigtede navne og kontrollerer søgning, HTML-escaping, tastatur, IME, pointerhændelser, sprog og den eksisterende gemmekontrakt. Det er ikke en visuel mobil-/skærmlæserprøve; browserinstallationen til denne kørsels lokale visuelle kontrol var blokeret af en fejlbehæftet download. Egen HA/browser er fortsat en særskilt prøve.

DAR GraphQL fra beta.8 og den separate stabile installation bevares. Den ekstra KTM-opfølgningsliste er fortsat fjernet. Den faste køreplan står på 20 %.
