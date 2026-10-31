# LTM på din egen computer eller server · beta

Startguiden er første del af W74. Den bruger den samme programpakke på Mac, Windows og Linux. Python 3.9 eller nyere med sqlite3 skal være installeret. Der medfølger endnu ikke en selvstændig app med indbygget Python eller et separat appvindue.

## Hent og start

Hent **LTM-v1.12.2-beta.76.zip** fra [beta.76](https://github.com/Bib007/LTM-Local-Territory-Manager/releases/tag/v1.12.2-beta.76), og pak hele filen ud. HA-installation bruger fortsat sin egen betakanal; desktop-ZIP'en skal ikke kopieres ind i HA.

Åbn filen i **Distrikt-lokal**:

| System | Startfil |
| --- | --- |
| Windows | `Start-LTM.cmd` |
| Mac | `Start-LTM.command` |
| Linux | `sh Start-LTM.sh` fra et terminalvindue i mappen |

Windows/Mac: installer Python fra [python.org](https://www.python.org/downloads/), hvis den mangler. Linux: brug distributionens Python 3-pakke med sqlite3. Startfilen henter ingen pip-pakker.

På Mac: prøv at åbne filen én gang. Hvis macOS blokerer den, og du har kontrolleret kilden, gå til **Systemindstillinger → Anonymitet & sikkerhed → Åbn alligevel**, og bekræft den konkrete fil. Slå ikke den generelle beskyttelse fra. [Apples vejledning](https://support.apple.com/en-gb/102445). Startfilen kan også køres fra Terminal med `bash` efterfulgt af filens sti.

## Vælg, hvordan du vil bruge LTM

**1 · Kun på denne computer:** LTM åbner i din almindelige browser. Serveren lytter kun på denne computers loopback-adresse. Du kan lukke startvinduet efter opstart. Stop gennem LTM's **Luk den lokale app**.

**2 · Server til hjemmenetværk og egen VPN:** Angiv computerens faste private IPv4-adresse og en ledig port. Beta foreslår 8788. Vælg en adgangskode på 12–1024 tegn og gentag den; indtastningen vises ikke. Serveren lytter kun på den valgte netværksadresse. Åbn den viste adresse fra dine andre enheder og log ind. Der åbnes ikke en browser på serveren.

Lad serverens terminalvindue stå åbent. **Ctrl+C** stopper den og rydder op. Automatisk start som systemtjeneste er endnu ikke med. Router, fast IP, firewall og VPN sættes op af dig; opret ikke offentlig portviderestilling. Linux-delen er prøvet på udviklings-Linux, Mac/Windows gennem de automatiske platformprøver; det er ikke en fysisk prøve på din computer.

Næste gang genbruges dit valg. For at vælge igen: kør startfilen med `--configure` i et terminalvindue. Stop en kørende server med Ctrl+C, før du ændrer dens adresse eller port. En eksisterende login-kode genbruges.

## Dine data er adskilt

Beta-startguiden bruger **Distrikt-beta** til lokal brug og **Distrikt-beta-server** til serveren. Startvalget ligger i **Distrikt-beta-start/launcher.json**. De ligger under `~/Library/Application Support` på Mac, `%LOCALAPPDATA%` på Windows og `~/.local/share` på Linux.

Den stabile **Distrikt**-mappe og HA-installationens data flyttes ikke. En ny beta eller et skift mellem lokal/server kan derfor starte tomt. Flyt kun dine registreringer med appens private backup og godkendte gendannelse, hvis du ønsker det. Google-forbindelser og adgangskoder følger ikke med den backup.

Ved opdatering: stop først den relevante installation, pak den nye programpakke ud, og brug samme startguide igen. Dine data ligger uden for programmappen. Tag en privat backup først. De ældre `Start-Distrikt`-filer er bevaret til deres hidtidige lokale installation; bland dem ikke sammen med beta-startguidens separate mapper.

## Det der stadig mangler i W74

- Selvstændige platformspakker med Python med i installationen.
- Et egentligt separat appvindue til lokal brug.
- Automatisk opstart som systemtjeneste og en mere grafisk installationsguide.

W74 er fortsat åbent. OCR/fotoimport er på pause og udvikles ikke som del af dette arbejde.
