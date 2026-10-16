# Installation og opdatering

[English](INSTALL.en.md) · [Kom i gang](FIRST-STEPS.md)

**Stabil grundudgave: 1.11.0.** Brug den almindelige repositoryadresse til HA; `develop` er til næste version og er ikke en almindelig opdateringskilde.

## Home Assistant OS

Programmet kører som en separat app/tilføjelse med eget login og normalt port **8787**. Det åbnes på hjemmenetværket eller via VPN på egen router. Det bruger ikke Ingress eller Nabu Casa.

### Installation fra repository

Dette er standardvejen uden manuel kopiering af programfiler:

1. Åbn **Indstillinger → Apps / Tilføjelser → butik** i HA.
2. Åbn **⋮ → Repositories**, og tilføj `https://github.com/Bib007/LTM-Local-Territory-Manager`. [Direkte HA-link](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FBib007%2FLTM-Local-Territory-Manager).
3. Vælg **Distrikt → Installer**. HA henter selv programfiler og bygger installationen.
4. Under konfiguration sættes `access_host` til HA-maskinens faste private IP, uden `http://`, port eller skråstreg.
5. Vælg en adgangskode på mindst 12 tegn under `password`. Det er appens egen kode.
6. Behold port **8787 → 8787**, start appen, og åbn dens private webadresse.

Fremtidige programopdateringer installeres fra HA. Der skal ikke kopieres programfiler via Samba. Opret ikke portviderestilling fra internettet til appen.

<a id="existing-local-app-safe-update"></a>

### Opdater en eksisterende lokal app

En eksisterende **lokalt installeret** app kan opdateres i den samme lokale mappe:

1. Hent en privat backup under **Indstillinger → Backup og gendannelse** i appen.
2. Stop kun Distrikt i HA. Afinstallér ikke appen.
3. Pak den komplette udgivelses-ZIP ud på din Mac, og forbind til HA's `local_apps`-deling.
4. Start `Opdater-Home-Assistant-Mac.command` med `bash`, og vælg den delte **local_apps**-mappe.
5. Vent på **FÆRDIG**. Ved **STOP** skal kopieringsfejlen løses, mens appen forbliver stoppet.
6. Vælg **Kontroller for opdateringer → Opdater → Start** i HA. Behold de eksisterende indstillinger.

Hjælperen kontrollerer kopierede filer og skriver `config.yaml` sidst. Den kopierer ikke databaser. En normal opdatering i samme installation kræver ikke import af backup.

### Skift fra lokal app til repository

HA giver repository-appen en anden identitet end den lokale app. Den får derfor sin egen datamappe. Det er et **engangsskift**, ikke en almindelig opdatering:

1. Eksportér en frisk privat backup fra den fungerende app. Behold backup og den gamle app.
2. Stop den gamle app, før den nye startes på samme port.
3. Installer repository-appen, og vælg adgangskode og privat adresse lokalt.
4. Importér backup gennem den nye app, og gennemgå den viste oversigt før bekræftelse.
5. Google-forbindelsen flyttes ikke med backup og skal tilsluttes igen, hvis den bruges.
6. Behold den gamle installation stoppet, indtil du har sikret dig, at data er overført.

Hvis mål-installationen allerede har delte Google-kort, skal deres offentlige adgang først fjernes. Import blokeres ellers for at undgå efterladte delte billeder. En ny tom installation kræver ikke dette trin.

### Brug mobilen udefra

Forbind telefon eller computer til **VPN på din egen router**. VPN'en skal tillade adgang til netværket med HA-maskinen og TCP-port 8787. Åbn derefter samme private adresse som hjemme, fx `http://DIN_PRIVATE_IP:8787`, og brug appens eget login.

Et VPN-abonnement, der kun ændrer internetplacering, er ikke en forbindelse til dit hjemmenetværk. Hvis lokal Wi-Fi virker, men VPN ikke gør, kontrolleres VPN-ruter og firewall. Brug den faste private IP, hvis `.local`-navnet ikke virker gennem tunnelen.

## Mac

Installer Python 3.9 eller nyere fra [python.org](https://www.python.org/downloads/macos/). Pak hele udgivelses-ZIP'en ud i en almindelig lokal mappe, og åbn `Distrikt-lokal/Start-Distrikt.command`. Fra kildekode hedder programmappen `distrikt`.

Hvis macOS blokerer startfilen, kontrolleres filen, hvorefter Finders **Åbn** kan bruges. Alternativt startes den med `bash` i Terminal. Slå ikke systemets generelle beskyttelse fra. `Stop-Distrikt.command` stopper appen.

Private data bliver i `~/Library/Application Support/Distrikt`. Et nyt produktnavn må ikke flytte eller erstatte denne eksisterende mappe.

## Windows

Installer Python 3.9 eller nyere fra [python.org](https://www.python.org/downloads/windows/) med Python-startfil eller PATH-valg. Pak hele ZIP'en ud, og åbn `Distrikt-lokal/Start-Distrikt.cmd`. Appen stoppes med `Stop-Distrikt.cmd`. Docker og pip-pakker er ikke nødvendige.

Private data ligger normalt i `%LOCALAPPDATA%\Distrikt`.

## Backup, flytning og tilbageførsel

Brug appens private eksport/import ved flytning mellem platforme. Import **erstatter** data og fletter ikke. Adgangskoder, login og Google-forbindelsesfiler følger ikke med.

**HA-backup indeholder ikke appens data.** Tag private sikkerhedskopier inde i appen, også før opdatering, flytning og afinstallation. En almindelig HA-backup alene gendanner ikke distriktsdatabaserne.

Behold tidligere programpakke og tilhørende backup lokalt. Gå ikke tilbage over en fremtidig uforenelig databaseændring uden en passende backup. Den nuværende kode har ingen skemaændring og bevarer de eksisterende elleve databasefiler.

## Kilder og flere guider

- [Home Assistant-repositories](https://developers.home-assistant.io/docs/apps/repository/)
- [Lokale HA-apps](https://developers.home-assistant.io/docs/apps/tutorial/)
- [Google Drive og QR](GOOGLE-DRIVE.md)
- [Privatliv og datastrømme](PRIVACY.md)
