# Brugere, rettigheder og gendannelse

Vejledning til brugerprofiler i beta.77. Profiler er endnu ikke med i den stabile udgave.

## Aktivér individuelle konti

Åbn den eksisterende installation som hidtil. På en privat server logger du først ind med den eksisterende adgangskode. Vælg **Indstillinger → Aktivér brugerprofiler**. Opret administratorens brugernavn og en ny adgangskode med mindst 12 tegn, gentag koden og skriv **AKTIVÉR PROFILER**.

Distriktsdata flyttes eller slettes ikke. Herefter logger alle ind med individuel konto, også fra den lokale computer. Det gamle fælles login giver ikke adgang til profildata. Gem administratorens nye login privat, før du logger ud. Første aktivering kan ikke udføres uden installationens eksisterende adgang.

Tag almindelig databackup før aktivering og separat kontobackup bagefter. Efter aktivering skal installationen bruge en version med profiler. En ældre version som beta.75 kender ikke kontienes adgangsregler; den må kun bruges til en særskilt prøve med backup fra før aktiveringen. Den lokale startguides stop/opdatering virker også, når profiler er aktiveret.

## Brugere og egne roller

Vælg **Indstillinger → Brugere og roller**, eller brug genvejen i menuen. Brugerpanelet har sin egen fane. Opret først en rolle, giv den et navn og vælg rettigheder. Opret derefter brugeren, vælg en eller flere roller og angiv en første adgangskode. Der er ingen fast liste over, hvem der skal have hvilke rettigheder; administratoren bestemmer.

Vælg en eksisterende bruger for at ændre navn eller roller, deaktivere kontoen eller nulstille adgangskoden. Et tomt kodefelt bevarer koden. Deaktivering og nulstilling afslutter brugerens sessioner. Rolleændringer gælder også åbne sessioner. Den sidste aktive brugeradministrator kan ikke fjernes.

Læsning og redigering er adskilt. At administrere brugere giver ikke automatisk adgang til IB, noter, forkyndere eller distriktsdata. En samlet databackup kræver adgang til alle de oplysninger, den indeholder; gendannelse kræver også de nødvendige skriverettigheder. Handlinger, som ændrer flere datatyper, kræver de tilhørende rettigheder. Serveren kontrollerer adgangen ved hver handling.

**Se påmindelse om databackup** styrer, om rollen får påmindelsen på forsiden. Den giver ingen adgang til at hente eller gendanne data. En modtager uden backupadgang ser en besked om at få en administrator til at tage kopien. Eksisterende fulde administratorroller beholder påmindelsen ved opdatering; et senere fravalg huskes også efter genstart.

Datafordeler og Google Drive er samlet under **Indstillinger → Forbindelser**. Fanen vises kun med **Administrere forbindelser**. **Deling og QR** indeholder de digitale kort. Brugere uden brugeradministration ser ikke kataloget over roller og rettigheder. Serveren kontrollerer både forbindelses- og delingsadgang.

## Samtidig arbejde og gennemgang

Uafhængige rettelser kan gemmes samtidig. Ved forskellige rettelser til samme oplysning bevares udgangspunktet og begge forslag. Forsiden viser en påmindelse. Åbn **Gennemgå rettelser**, sammenlign den aktuelle værdi med de to rettelser, og vælg **Brug denne rettelse** eller **Behold aktuel · markér gennemgået**. Påmindelsen opdateres straks. At åbne listen ændrer intet.

Valget bruger den normale validering og gemmes sammen med kvitteringen. Hvis samme oplysning er ændret igen, skal gennemgangen åbnes på ny; ingen nyere rettelse overskrives lydløst. Beregnede felter og særlige handlinger ændres fortsat i deres almindelige formular. Udgangspunktet og begge rettelser bevares efter gennemgang.

Konflikter om kontoadgang vises kun til brugeradministratorer. Ved uens rettelser af rettigheder eller adgangskode bliver den gældende adgang stående, indtil administratoren har gennemgået og valgt en rettelse. Adgangskoder og hashes vises ikke i gennemgangen. Valg af adgangskode/deaktivering afslutter den berørte kontos sessioner. Den sidste administrator beskyttes også ved et konfliktvalg.

**Nyligt aktive (90 sek.)** viser, hvilke konti der for nylig har brugt appen. Det er ikke sikker viden om, hvem der er til stede lige nu.

Hvis forbindelsen afbrydes under gemning, kan ændringen allerede være gemt. Brug **Opdater**, kontrollér resultatet og fortsæt derefter. Send ikke samme handling igen, før resultatet er kontrolleret. En udløbet redigeringssession skal åbnes igen; ændringer fra andre brugere kræver ikke i sig selv en generel genindlæsning.

## To forskellige sikkerhedskopier

Appens almindelige ZIP-backup indeholder distriktsdata og deres konfliktgennemgang. Konti, roller, adgangskodehashes og forbindelsesnøgler følger ikke med. Gendannelse af denne ZIP beholder installationens eksisterende konti og login.

Den separate **kontobackup** indeholder konti, roller, introduktionsstatus og eventuelle kontokonflikter, herunder saltede adgangskodehashes. Den indeholder ingen aktive sessioner. Den er ikke krypteret og skal opbevares privat og lokalt, adskilt fra almindelig deling. Den løser ikke W56 om krypteret backup af forbindelser. Gem begge typer, hvis hele installationen skal kunne flyttes eller gendannes.

## Kontobackup i appen

En brugeradministrator finder **Konti og roller** under **Indstillinger → Backup og vedligeholdelse**. Vælg **Hent kontobackup**, og kontrollér den hentede JSON-fil. At hente kontobackup giver ikke adgang til distriktsdata.

Åbn **Gendan konti og roller fra fil**, vælg filen, og angiv din nuværende adgangskode. Forhåndsvisningen viser antal brugere og roller. Skriv **GENDAN KONTI**, hvis de aktuelle konti skal erstattes. En privat kopi af de nuværende konti gemmes først på serveren. Distriktsdata og forbindelser bevares. Alle skal logge ind igen med et login fra sikkerhedskopien.

Forhåndsvisningen gælder fem minutter og kun i den session, som åbnede den. Ændrede konti/roller kræver en ny forhåndsvisning. Appen accepterer filer på højst 8 MB; større kontofiler kan behandles med det lokale værktøj. En afbrudt gemmekvittering må ikke føre til automatisk gentagelse: log ind igen, og kontrollér kontiene.

Hvis administratorens login er glemt, kan en anden brugeradministrator nulstille det. Hvis ingen kan logge ind, bruges det lokale værktøj nedenfor med LTM stoppet. Der findes ingen offentlig funktion til at omgå login eller oprette en ny administrator uden eksisterende adgang.

## Lokal kontobackup og administratorgendannelse

Find installationens faktiske datamappe, og stop LTM. Kør værktøjet fra programmets mappe med den Python-installation, der starter LTM. Eksemplerne bruger en opdigtet sti; erstat den med den rigtige mappe. Beta, stabil og privat server har hver sine data.

```sh
python3 app/profile_recovery.py --data-dir "/sti/til/ltm-data" --backup "/privat/mappe/ltm-konti.json"
python3 app/profile_recovery.py --data-dir "/sti/til/ltm-data" --recover-admin
python3 app/profile_recovery.py --data-dir "/sti/til/ltm-data" --restore "/privat/mappe/ltm-konti.json"
```

På Windows kan kommandoen hedde `python` i stedet for `python3`. I Home Assistant-containeren ligger programmet under `/opt/distrikt/app`; stabil bruger `/data/distrikt`, beta `/data/distrikt-beta`. Her kræves lokal administratoradgang til at starte en engangsproces fra samme containerimage med datamappen tilsluttet. Den normale tilføjelse skal være stoppet først. Dette er ikke en funktion i den offentlige app.

Gendannelse af administrator spørger lokalt efter brugernavn og en ny, skjult adgangskode. Den bevarer distriktsdata og øvrige konti. En eksisterende konto med navnet får administratoradgang igen. Kontogendannelse kræver bekræftelsen **GENDAN KONTI**, gemmer først en privat kopi af nuværende konti og afslutter alle sessioner. En beskadiget kontofil bevares separat før gendannelse af en gyldig kontobackup. Værktøjet afviser at arbejde, mens LTM bruger samme datamappe.

Start LTM igen, og kontrollér login med den ønskede administrator. Der sendes ingen konti, adgangskoder eller distriktsdata til en ekstern tjeneste af disse funktioner.
