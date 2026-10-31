# Brugere, rettigheder og gendannelse

Denne vejledning beskriver den integrerede udviklingsudgave. Profiler er endnu ikke frigivet i stabil eller beta.

## Aktivér individuelle konti

Åbn den eksisterende installation som hidtil. På en privat server logger du først ind med den eksisterende adgangskode. Vælg **Indstillinger → Aktivér brugerprofiler**. Opret administratorens brugernavn og en ny adgangskode med mindst 12 tegn, gentag koden og skriv **AKTIVÉR PROFILER**.

Distriktsdata flyttes eller slettes ikke. Herefter logger alle ind med individuel konto, også fra den lokale computer. Det gamle fælles login giver ikke adgang til profildata. Gem administratorens nye login privat, før du logger ud. Første aktivering kan ikke udføres uden installationens eksisterende adgang.

## Brugere og egne roller

Vælg **Brugere og roller**. Opret først en rolle, giv den et navn og vælg rettigheder. Opret derefter brugeren, vælg en eller flere roller og angiv en første adgangskode. Der er ingen fast liste over, hvem der skal have hvilke rettigheder; administratoren bestemmer.

Vælg en eksisterende bruger for at ændre navn eller roller, deaktivere kontoen eller nulstille adgangskoden. Et tomt kodefelt bevarer koden. Deaktivering og nulstilling afslutter brugerens sessioner. Rolleændringer gælder også åbne sessioner. Den sidste aktive brugeradministrator kan ikke fjernes.

Læsning og redigering er adskilt. At administrere brugere giver ikke automatisk adgang til IB, noter, forkyndere eller distriktsdata. En samlet databackup kræver adgang til alle de oplysninger, den indeholder; gendannelse kræver også de nødvendige skriverettigheder. Handlinger, som ændrer flere datatyper, kræver de tilhørende rettigheder. Serveren kontrollerer adgangen ved hver handling.

## Samtidig arbejde og gennemgang

Uafhængige rettelser kan gemmes samtidig. Ved forskellige rettelser til samme oplysning bevares udgangspunktet og begge forslag. Forsiden viser en påmindelse. Åbn **Gennemgå rettelser**, kontrollér den aktuelle værdi, ret om nødvendigt oplysningen i dens almindelige formular og vælg **Markér gennemgået**. At åbne listen ændrer intet.

Konflikter om kontoadgang vises kun til brugeradministratorer. Ved uens rettelser af rettigheder eller adgangskode bliver den gældende adgang stående, indtil administratoren har gennemgået og eventuelt gemt en ny rettelse. Adgangskoder og hashes vises ikke i gennemgangen.

**Nyligt aktive (90 sek.)** viser, hvilke konti der for nylig har brugt appen. Det er ikke sikker viden om, hvem der er til stede lige nu.

Hvis forbindelsen afbrydes under gemning, kan ændringen allerede være gemt. Brug **Opdater**, kontrollér resultatet og fortsæt derefter. Send ikke samme handling igen, før resultatet er kontrolleret. En udløbet redigeringssession skal åbnes igen; ændringer fra andre brugere kræver ikke i sig selv en generel genindlæsning.

## To forskellige sikkerhedskopier

Appens almindelige ZIP-backup indeholder distriktsdata og deres konfliktgennemgang. Konti, roller, adgangskodehashes og forbindelsesnøgler følger ikke med. Gendannelse af denne ZIP beholder installationens eksisterende konti og login.

Den separate **kontobackup** indeholder konti, roller, introduktionsstatus og eventuelle kontokonflikter, herunder saltede adgangskodehashes. Den indeholder ingen aktive sessioner. Den er ikke krypteret og skal opbevares privat og lokalt, adskilt fra almindelig deling. Den løser ikke W56 om krypteret backup af forbindelser. Gem begge typer, hvis hele installationen skal kunne flyttes eller gendannes.

Kontoværktøjet bruges lokalt på serveren med LTM stoppet. Der findes ingen offentlig funktion til at omgå login eller oprette en ny administrator.

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
