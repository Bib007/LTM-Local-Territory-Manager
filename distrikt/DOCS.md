# Installer Distrikt på Home Assistant OS

[English guide](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/INSTALL.en.md)

## Installation fra repository

1. Tilføj `https://github.com/Bib007/LTM-Local-Territory-Manager` under HA → Indstillinger → Apps / Tilføjelser → butik → ⋮ → Repositories.
2. Vælg **Distrikt → Installer**. HA henter programfilerne og bygger installationen. Der skal ikke kopieres programfiler med Samba.
3. I konfigurationen sættes **Privat adresse** (`access_host`) til HA-maskinens faste private IP eller lokale værtsnavn, uden http://, port eller skråstreg.
4. Vælg **Appens adgangskode** (`password`) på mindst 12 tegn. Det er appens eget login.
5. Behold port **8787 → 8787**, slå start ved opstart til, og start appen.
6. Åbn `http://DIN_PRIVATE_IP:8787` i browseren, og log ind.

## Eksisterende lokal HA-app

Repositoryudgaven har en anden HA-identitet og sin egen datamappe. Første flytning kræver en privat backup/import:

1. Hent en frisk backup i den gamle app under Indstillinger → Backup og gendannelse.
2. Stop den gamle app, før den nye startes på samme port. Behold den gamle installation og backup.
3. Importér backup gennem den nye app. Import erstatter data og fletter ikke; gennemgå oversigten før bekræftelse.
4. Google-forbindelsen følger ikke med backup og skal tilsluttes igen, hvis den bruges.

Senere repository-opdateringer installeres direkte i HA. En normal opdatering i samme installation kræver ikke import af backup. Afinstallér ikke den fungerende app for at opdatere.

## Data og backup

Appen bruger sin vedvarende `/data/distrikt`-mappe og har ikke adgang til HA-API, Supervisor-API eller andre apps' data. De oprindelige tomme formularer følger med; egne registreringer bliver på systemet.

**Appdata er udeladt af HA-backup.** Tag private backups gennem appen, også før opdatering, flytning og afinstallation. En almindelig HA-backup alene indeholder ikke distriktsdatabaserne.

## Adgang udefra

Forbind telefon eller computer til VPN på egen router, og åbn samme private appadresse som hjemme. VPN-regler skal tillade HA-maskinen og port 8787. Ingress og Nabu Casa bruges ikke; åbn ikke en offentlig internetport til appen.

## Hvis appen ikke åbner

- Kontrollér at adgangskoden har mindst 12 tegn, og se appens log.
- Brug præcis den adresse, som står i `access_host`, og port 8787.
- Hvis VPN fejler, men hjemmets Wi-Fi virker, kontrolleres VPN-ruter/firewall. En fast privat IP er ofte lettere gennem VPN end `.local`.
- Adgangskoden kan ændres i HA-konfigurationen efterfulgt af genstart. Sessioner udløber efter 12 timer eller genstart.

[Fuld dansk installationsguide](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/INSTALL.md) · [Valgfri Google og QR](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/GOOGLE-DRIVE.md)

## IB fra billeder · beta

Under **Indstillinger → Import → IB fra billeder** kan du indlæse fotos af IB-bagsider. Dette er et deltrin: billeder af S-12-forsider opretter endnu ikke distriktskort.

1. Vælg PNG-/JPEG-billeder, højst 20, højst 12 MB hver og 60 MB samlet. HEIC og PDF skal først gemmes som PNG eller JPEG. Originalerne bliver i browseren; en klargjort PNG sendes til dit eget lokale LTM-system.
2. Vælg det rigtige kort for billedet. Ret den genkendte tekst og vælg **Lav redigerbare forslag**. En tydelig adresse med en dato sidst på linjen, fx `Fiktivvej 8 - 24.10.2026`, kan give et forslag. Lejligheder kræver korrekt etage og dør. Eksemplet er opdigtet.
3. Kontrollér hver linje mod billedet. Vælg en adresse fra kortet og ret datoen, eller spring linjen over. Overskrifter, støj og uklare linjer bliver ikke stiltiende ignoreret. Genkendelsen kan tage fejl, især ved håndskrift, skygger og flere spalter.
4. Vælg **Kontrollér IB-forslag**, gennemgå resultatet, skriv **IMPORTÉR IB** og godkend. Intet gemmes ved alene at vælge eller læse et billede. Dobbeltregistrerede IB springes over; eksisterende IB overskrives ikke. Besøgstal og forsider ændres ikke; berørte bagsider skal ajourføres.
5. Vælg selv, hvornår næste billede skal læses. Kortvalget nulstilles pr. billede. Lukning eller fejl fortryder ikke tidligere godkendte billeder. Ved ukendt gemmeresultat skal du kontrollere med **Opdater** før et nyt forsøg.

Genkendelsen bruger lokal Tesseract. Ingen ekstern AI, cloud-OCR eller fjernserver modtager billederne eller IB-teksten. Midlertidige billed-/tekstfiler slettes efter læsningen. Resultater opbevares kortvarigt i serverens hukommelse og fjernes ved afslutning, spring over, lukning eller efter fem minutter. Appens almindelige IB-data lagres først efter din godkendelse.

### Motor på Home Assistant, Mac og Windows

HA-betaen med billedimport installerer motoren samt danske og engelske sprogdata, når appens image bygges. Genstart/opdatér appen som normalt. Motoren hentes ikke under billedlæsningen.

På Mac og Windows skal Tesseract installeres separat på den maskine, hvor **LTM-serveren** kører. Det er ikke nødvendigt på en telefon, der åbner en eksisterende HA-installation. På Mac beskriver [Tesseracts officielle installationsguide](https://tesseract-ocr.github.io/tessdoc/Installation.html) Homebrew og MacPorts. Ved Homebrew kan motor og ekstra sprog installeres med `brew install tesseract tesseract-lang`. På Windows henviser den officielle guide til Windows-installationer; medtag dansk (`dan`) og engelsk (`eng`) og gør `tesseract` tilgængelig på PATH eller i den almindelige installationsmappe `Program Files/Tesseract-OCR`. LTM kører ingen automatisk installationskommando på desktop.

Åbn importen igen efter installation. Appen viser, om motoren er tilgængelig. Hvis kun engelsk er installeret, vises en advarsel om at kontrollere æ, ø og å. Håndskrift er ikke garanteret genkendt; ret teksten manuelt eller brug den eksisterende CSV-import.
