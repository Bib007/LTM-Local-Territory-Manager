# Brugere og samtidige ændringer · W65/W83

## Mål

Administrator opretter brugere, egne roller og rettigheder i appen. Flere kan være logget ind og arbejde samtidig. Uafhængige rettelser skal kunne gemmes uden at overskrive hinanden. Hvis samme oplysning ændres forskelligt fra samme eller forskellige udgangspunkter, gemmes begge rettelser og udgangspunktet til konkret gennemgang. Forsiden skal minde om uløste konflikter. Et muligt onlineoverblik viser kun nylig aktivitet og skal ikke hævdes at være præcis tilstedeværelse.

## Første isolerede grundlag

`concurrent_edits.reconcile` sammenligner fiktive felter fra tre snapshots: udgangspunkt, nuværende værdi og indsendt værdi. Ændringer på forskellige tilladte felter sammenføjes; samme ændring to gange er ikke en konflikt. Uens ændringer af samme felt giver en konflikt med alle tre værdier. Det nyeste gemmeforslag bliver den aktuelle værdi, og begge forslag skal gemmes sammen med konflikten. Fravær af et felt holdes adskilt fra null. Lister og indlejrede objekter betragtes foreløbig som ét felt. Selve sammenligningen skriver ikke data. En isoleret prototype kan gemme en ændring og lokale konfliktposter i samme eksisterende databasetransaktion; en fejl under konfliktlagring ruller hele ændringen tilbage. To samtidige tråde, samme/forskellige felter samt backup og gendannelse er prøvet med opdigtede data. Prototypens skrive-callback skal senere kobles til den normale validering og dens følgevirkninger.

En separat snapshot-prototype gemmer redigeringens oprindelige værdier i serverens hukommelse, bundet til session og post. Et kortlevet, tilfældigt bevis kan kun bruges én gang ved en vellykket gemning; en fejlet transaktion kan forsøges igen inden udløb. Session, post, udløb, logout, hukommelsesgrænse og samtidige forsøg er prøvet med opdigtede data. Den er endnu ikke koblet til serveren. Integration skal genkontrollere aktiv session og rettigheder ved selve skrivningen og afklare nedlukning og ukendt gemmeresultat.

En separat, ikke tilsluttet kontoprototype understøtter individuelle brugere, administratorstyrede roller/rettigheder, serverkontrol af de aktuelle rettigheder ved hvert kald, udløb og tilbagekaldelse af sessioner, begrænset loginforsøg pr. klient og konto samt en tidsafgrænset liste over nyligt aktive konti. Samme konto med flere sessioner vises kun én gang. Sidste aktive administrator kan ikke fjernes. Adgangskoder gemmes kun som saltede hashes i en privat separat fil, der ikke medfølger almindelig backup eller programpakken; den eksisterende login-/gendannelsesfunktion er endnu ikke migreret. Prototypen bruger PBKDF2-HMAC-SHA256 med 600.000 iterationer og registrerer arbejdsfaktoren pr. konto. OWASP foretrækker generelt Argon2id eller scrypt til nye systemer; valg, ydeevne og hele adgangsflowet skal vurderes før frigivelse. Kilder: [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) og [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html).

## Dataadgang og rettigheder · 31.10.2026

`ProfileWorkspace` forbinder konti, den rigtige lokale database, redigeringsudgangspunkter og konfliktgennemgang i et internt serverlag. Klienten må ikke levere rettigheder, brugeridentitet eller et påstået udgangspunkt. Kontoens aktuelle rettigheder afgør, hvilke moduler og udtrykkeligt tilladte felter der returneres. IB, noter, forkyndere og udlån har særskilte læserettigheder. Nye databasefelter og ukendte konflikttyper udleveres ikke automatisk. Aktivitetsrækker følger ikke med adgang til noter. Brugerstyring giver ikke implicit læseadgang til alle private data.

Konflikter læses kun med den relevante læserettighed; en udtrykkelig kvittering kræver også redigeringsrettigheden og gemmer den autentificerede kontos identitet. At åbne listen løser ingen konflikter. Kontolåsen holdes før databaselåsen, så en rolleændring ikke kan komme ind mellem tilladelseskontrol og handling. Deaktivering og rolleændringer er prøvet på eksisterende sessioner. Redigeringsudgangspunktet hentes fra databasen og bindes til sessionen. Dette lag udstiller endnu ingen almindelige gemmehandlinger.

Den nye oversigt er **ikke** en erstatning for den eksisterende `/api/state`: kortgeometri, forbindelser, eksport, gendannelse og øvrige HTTP-veje skal stadig gennemgås før tilslutning. Loginmigration, brugerflade og fulde HTTP-/browserprøver udestår. Otte nye prøver bruger rigtige lokale konti og SQLite med opdigtede data, inklusive samtidig rettighedsændring. Ingen eksisterende installation er migreret.

**Ikke aktivt i appen:** Funktionerne er ikke koblet på HTTP-API, brugergrænseflade eller appens almindelige gemning. Prøverne bruger isolerede lokale databaser. Der er endnu ingen frigivne brugerprofiler, aktivitetsvisning eller konfliktpåmindelser. Disse prøver beviser ikke samtidig brug på en rigtig ejerinstallation.

## Før dette må tilsluttes

1. Serveren udsteder et kortlevet snapshot for den konkrete bruger/session og post; klientens påståede udgangspunkt må ikke alene stoles på. Flere faner og flere sessioner på samme konto skal kunne skelnes.
2. Serveren kontrollerer den aktuelle konto og dens rettigheder ved hvert relevant læse- og skrivekald. Administrator kan oprette, ændre, deaktivere og nulstille konti, roller og rettigheder. Ingen hardkodet ejerliste.
3. Sammenligning, validering, gemning og varsel om konflikt skal udføres atomisk under databasens eksisterende lås/transaktion. Hvis konfliktens versioner ikke kan gemmes, må selve skrivningen ikke bekræftes. Bevar eksisterende beskyttelse mod dobbelt udlevering og ukendt gemmeresultat.
4. Påmindelse og gennemgang viser kun poster, som den aktuelle bruger har ret til at se. IB og andre private værdier må kun findes lokalt; læg ikke private værdier, adgangskoder eller sessionsnøgler i logs, telemetry eller offentlige prøver. Konflikter må ikke markeres løst ved blot at åbne dem.
5. Kun faktiske modstridende ændringer håndteres. Den tidligere generelle afvisning om ændringer fra en anden fane/enhed genindføres ikke. Uafhængige gemninger på samme eller forskellige poster må ikke afvises alene fordi en anden også har gemt.
6. Udrulning skal bevare eksisterende installationer og login, håndtere migration/backup/rollback samt afprøves med to samtidige sessionsforløb på rigtig lokal server, inkl. rettighedsændringer, mistet forbindelse og gendannelse. Ingen reelle brugerdata bruges i prøver.

Disse punkter er arbejdsgrundlag, ikke leverede funktioner. Opbevaringstid for aktivitetslog og konkrete valg ved konfliktløsning er ikke fastlagt; undgå at opfinde ejerbeslutninger. OCR og automatisk kortinddeling forbliver på pause.

## Samlet lokal profilprøve · 31.10.2026

Et separat HTTP-forløb samler nu login, bruger-/rollepanel, nyligt aktive brugere og udtrykkelig konfliktkvittering. Det binder kun til 127.0.0.1 på en ledig port og kan ikke startes fra den almindelige LTM-startguide. Konti skal være initialiseret af ejeren på forhånd; der er ingen offentlig oprettelse af første administrator. Der bruges HttpOnly/SameSite-cookie og et separat forespørgselstoken pr. session samt kontrol af vært og origin. Adgangskoder, brugernavne og forespørgsler logges ikke.

Fire HTTP-prøver verificerer login, oprettelse af roller og brugere, begrænset adgang, deaktivering, afvisning af forkert origin/sessionstoken, logout og beskyttelse af sidste administrator. Den gamle `/api/state` og backup-API findes ikke i denne prøve; de må ikke tilsluttes uden adgangskontrol. Browserprøven ligger i `scripts/check_profile_browser.cjs` og bruger kun midlertidige opdigtede konti.

**Stadig åbent før frigivelse:** overgangen fra eksisterende login, administratorgendannelse og kontobackup, alle almindelige appfunktioner med rettigheder, samtidige domænevaliderede gemninger med sideeffekter/aktivitet, håndtering af ukendt gemmeresultat, samlet konfliktvisning i appens forside og engelsk. Profilprøven er ikke en ny betaudgivelse eller en færdig flerbrugerudgave.

Browserforløbet er nu bestået i Chromium med projektets Playwright 1.56.1: rigtig HTTP/login, rolle- og brugeroprettelse, logout, begrænset bruger og mobilbredde 390 px uden vandret overløb. Ingen eksterne forbindelser tillades i prøven. Et mobilbillede er visuelt kontrolleret. Dette dækker profilprøven, ikke den endnu manglende integration med hele appen.
