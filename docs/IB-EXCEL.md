# IB fra Excel eller CSV

W117 · kandidat til beta.79 · afventer udgivelseskontroller.

Åbn **Indstillinger → Import → Åbn lokal IB-import**. Hent Excel-skabelonen, og udfyld fanen **IB**. CSV virker også. Regnearket behandles af din lokale LTM-installation; det sendes ikke til en ekstern tjeneste.

## Udfyld filen

- Brug én linje pr. adresse eller lejlighed og kolonnerne `kortnummer`, `vejnavn`, `husnummer`, `postnummer`, `etage`, `dør`, `dato`.
- Vejnavn og husnummer skal kunne læses. De øvrige kolonner kan mangle; det vises i gennemgangen. Brug separate felter til etage og dør. Dato skrives som ÅÅÅÅ-MM-DD. Hvis den mangler, bruges dit datovalg i appen.
- Skabelonens kolonner er tekstfelter, så indtastede foranstillede nuller bevares. Hvis et andet regneark allerede har ændret et nummer eller en dato, kan LTM ikke genskabe det oprindelige indhold.
- Et postnummer skal være fire cifre eller tomt. Et manglende postnummer bliver ikke gættet. Manglen vises før og efter import.
- Angiv kortnummer, hvis linjen skal skrives manuelt eller ikke matcher entydigt. Du kan også vælge et standardkort i appen; det gælder kun filens linjer uden eget kortnummer. Et ukendt kortnummer opretter ikke et nyt kort og erstattes ikke med standardkortet.

LTM knytter kun linjen til en geografisk adresse ved et entydigt lokalt match på vej, husnummer, postnummer og etage/dør. Ellers kan en linje med et valgt kort oprettes som manuelt angivet IB. Det gælder også kort uden præcise adresser. Et manglende postnummer giver en manuel linje, selv om et muligt match findes. Der oprettes ingen geografisk adresse eller gættet lejlighed.

## Gennemgå før import

Vælg filen, og læs hver linje. Gennemgangen viser nye poster, dubletter, fejl og advarsler. Ekstra, ukendte kolonner vises som **importeres ikke**; originalfilen ændres ikke. Filer med fejl skal rettes. Ved nye manuelle eller ufuldstændige linjer skal du bekræfte, at du har gennemgået advarslerne, og derefter skrive **IMPORTÉR IB**.

Dubletter i filen og eksisterende IB springes over. Eksisterende datoer og oplysninger overskrives ikke. Godkendelsen er knyttet til den gennemgåede fil og det aktuelle kort-/adresse-/IB-grundlag. Hvis dette ændres, skal importen gennemgås igen. Det er en konkret importgodkendelse; almindelige uafhængige rettelser fra flere brugere kan fortsat gemmes samtidig.

Alle nye linjer gemmes samlet gennem den almindelige IB-validering. En fejl i en senere linje ruller hele importen og dens revisionsændringer tilbage. Ved mistet gemmekvittering skal de faktisk gemte data kontrolleres, før noget prøves igen. Ingen automatisk dobbeltimport.

## Efter import

Den manuelle linje står på kortets IB-bagside. Kun bagsiden markeres til genprint. Besøgstal, forside, kortgrænser og udleveringer bevares, også hvis kortet er udleveret. Gennemgå de fysiske kort efter behov.

Under **Kort og adresser → IB** ses **Postnummer mangler**, indtil det tilføjes i postens normale redigering og gemmes. En valgt geografisk adresse bruger sit lokale postnummer. En senere manuel postnummerrettelse opretter ikke automatisk geodata. Manglen og et kendt postnummer følger den almindelige private databackup.

I profiltilstand kræver importen de aktuelle kort-/IB-rettigheder på serveren. Postnummer er også omfattet af samtidighedskontrollen: uafhængige dato-/postnummerrettelser sammenføjes, mens to forskellige postnummerrettelser og deres udgangspunkt bevares til konfliktgennemgang.

## Kontrol og grænser

Op til 2 MB og 5.000 IB-linjer. XLSX-læseren genbruger grænser og afvisninger for formler, makroer, kryptering, eksterne datalink, XML-entiteter og udpakkede størrelser. Brug almindelige celleværdier; gem gamle XLS-filer som XLSX først. Der bruges ingen OCR eller automatisk billedfortolkning.

594 Python-prøver (én forventet overspringning), JavaScript-suiten og målrettet rigtig HTTP/browser består lokalt med opdigtede data. Den tomme XLSX er også læst uafhængigt med openpyxl 3.1.5 uden advarsler. Browseren dækker download, XLSX-upload, advarselsgodkendelse, printlinje, mangelpåmindelse og normal efterfølgende rettelse ved 390 px. En lagerfejl midt i importen, dubletter, to sessioner og konflikter er prøvet. Den fælles filimportprøve er tilpasset det nye eksplicit godkendte manuelle forløb; ingen OCR-kode eller genkendelseskvalitet er udviklet eller godkendt. Ejerens data er ikke brugt.

### Ekstra kontrol før publicering

Første beta.79-kandidat, 133095991bfbaad30e518d5adfe7e3c4c8720bab, blev bevidst afbrudt før publicering (HA beta release 41232252899), fordi en ældre afsluttet forhåndsvisning kunne genopbygge filvælgeren under læsning af en nyere fil. En målrettet prøve viste fejlen før rettelsen og består nu. Det rigtige browserforløb fastholder både den ældre HTTP-forespørgsel og den nyere XLSX-indlæsning for at kontrollere, at det nyeste filvalg og dets grundlag bevares. Gemte data blev ikke ændret af fejlen. Beta.79 var ikke udgivet, så nummeret er fortsat en kandidat; eksisterende betaer er ikke overskrevet. Den rettede kilde skal gennem alle udgivelseskontroller på ny.
