# Brugere og samtidige ændringer · W65/W83

## Mål

Administrator opretter brugere, egne roller og rettigheder i appen. Flere kan være logget ind og arbejde samtidig. Uafhængige rettelser skal kunne gemmes uden at overskrive hinanden. Hvis samme oplysning ændres forskelligt fra samme eller forskellige udgangspunkter, gemmes begge rettelser og udgangspunktet til konkret gennemgang. Forsiden skal minde om uløste konflikter. Et muligt onlineoverblik viser kun nylig aktivitet og skal ikke hævdes at være præcis tilstedeværelse.

## Første isolerede grundlag

`concurrent_edits.reconcile` sammenligner fiktive felter fra tre snapshots: udgangspunkt, nuværende værdi og indsendt værdi. Ændringer på forskellige tilladte felter sammenføjes; samme ændring to gange er ikke en konflikt. Uens ændringer af samme felt giver en konflikt med alle tre værdier. Det nyeste gemmeforslag bliver den aktuelle værdi, og begge forslag skal gemmes sammen med konflikten. Fravær af et felt holdes adskilt fra null. Lister og indlejrede objekter betragtes foreløbig som ét felt. Selve sammenligningen skriver ikke data. En isoleret prototype kan gemme en ændring og lokale konfliktposter i samme eksisterende databasetransaktion; en fejl under konfliktlagring ruller hele ændringen tilbage. To samtidige tråde, samme/forskellige felter samt backup og gendannelse er prøvet med opdigtede data. Prototypens skrive-callback skal senere kobles til den normale validering og dens følgevirkninger.

En separat snapshot-prototype gemmer redigeringens oprindelige værdier i serverens hukommelse, bundet til session og post. Et kortlevet, tilfældigt bevis kan kun bruges én gang ved en vellykket gemning; en fejlet transaktion kan forsøges igen inden udløb. Session, post, udløb, logout, hukommelsesgrænse og samtidige forsøg er prøvet med opdigtede data. Den er endnu ikke koblet til serveren. Integration skal genkontrollere aktiv session og rettigheder ved selve skrivningen og afklare nedlukning og ukendt gemmeresultat.

En separat, ikke tilsluttet kontoprototype understøtter individuelle brugere, administratorstyrede roller/rettigheder, serverkontrol af de aktuelle rettigheder ved hvert kald, udløb og tilbagekaldelse af sessioner, begrænset loginforsøg pr. klient og konto samt en tidsafgrænset liste over nyligt aktive konti. Samme konto med flere sessioner vises kun én gang. Sidste aktive administrator kan ikke fjernes. Adgangskoder gemmes kun som saltede hashes i en privat separat fil, der ikke medfølger almindelig backup eller programpakken; den eksisterende login-/gendannelsesfunktion er endnu ikke migreret. Prototypen bruger PBKDF2-HMAC-SHA256 med 600.000 iterationer og registrerer arbejdsfaktoren pr. konto. OWASP foretrækker generelt Argon2id eller scrypt til nye systemer; valg, ydeevne og hele adgangsflowet skal vurderes før frigivelse. Kilder: [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) og [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html).

**Ikke aktivt:** Funktionen er ikke koblet på API, brugergrænseflade, databaser eller automatisk gemning. Der er endnu ingen brugerprofiler, aktivitetsvisning eller konfliktpåmindelser. Fiktive enhedsprøver bekræfter sammenligning, men beviser ikke samtidig brug på en rigtig installation.

## Før dette må tilsluttes

1. Serveren udsteder et kortlevet snapshot for den konkrete bruger/session og post; klientens påståede udgangspunkt må ikke alene stoles på. Flere faner og flere sessioner på samme konto skal kunne skelnes.
2. Serveren kontrollerer den aktuelle konto og dens rettigheder ved hvert relevant læse- og skrivekald. Administrator kan oprette, ændre, deaktivere og nulstille konti, roller og rettigheder. Ingen hardkodet ejerliste.
3. Sammenligning, validering, gemning og varsel om konflikt skal udføres atomisk under databasens eksisterende lås/transaktion. Hvis konfliktens versioner ikke kan gemmes, må selve skrivningen ikke bekræftes. Bevar eksisterende beskyttelse mod dobbelt udlevering og ukendt gemmeresultat.
4. Påmindelse og gennemgang viser kun poster, som den aktuelle bruger har ret til at se. IB og andre private værdier må kun findes lokalt; læg ikke private værdier, adgangskoder eller sessionsnøgler i logs, telemetry eller offentlige prøver. Konflikter må ikke markeres løst ved blot at åbne dem.
5. Kun faktiske modstridende ændringer håndteres. Den tidligere generelle afvisning om ændringer fra en anden fane/enhed genindføres ikke. Uafhængige gemninger på samme eller forskellige poster må ikke afvises alene fordi en anden også har gemt.
6. Udrulning skal bevare eksisterende installationer og login, håndtere migration/backup/rollback samt afprøves med to samtidige sessionsforløb på rigtig lokal server, inkl. rettighedsændringer, mistet forbindelse og gendannelse. Ingen reelle brugerdata bruges i prøver.

Disse punkter er arbejdsgrundlag, ikke leverede funktioner. Opbevaringstid for aktivitetslog og konkrete valg ved konfliktløsning er ikke fastlagt; undgå at opfinde ejerbeslutninger. OCR og automatisk kortinddeling forbliver på pause.
