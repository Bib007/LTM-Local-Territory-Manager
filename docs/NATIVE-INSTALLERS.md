# Gratis native desktop-installation – udviklingsspor

Målet er en nem installation af LTM til macOS og Windows **uden at installere Python**. Dette udviklingsspor bygger lokale, usignerede prøvepakker. Det ændrer ikke Home Assistant, de eksisterende ZIP-release-spor eller almindelige Stable-udgivelser.

## Windows

GitHub Actions bygger en samlet app med PyInstaller og pakker den med den gratis Inno Setup-installationsmotor som `LTM-Windows-vVERSION-Setup.exe`. Installation sker pr. bruger, uden administratorrettigheder. Den opretter en genvej i Start-menuen. En genvej på skrivebordet kan vælges til.

Windows SmartScreen kan stadig vise en advarsel om en ukendt udgiver, fordi installationsfilen ikke er digitalt signeret. Signering er **ikke** en forudsætning for at bygge eller teste.

## macOS

GitHub Actions bygger en `LTM.app` med en integreret Python-runtime og pakker den som `LTM-macOS-vVERSION-Intel.dmg` og `LTM-macOS-vVERSION-AppleSilicon.dmg`. Man åbner DMG-filen og trækker LTM til Programmer. Buildworkflowet laver særskilte gratis prøvepakker til **Intel** og **Apple Silicon (M-serien)** på hver sin GitHub-runner. Den bruger fysisk Mac-arkitektur under CI; almindelig installation i Finder på en lokal Mac skal stadig afprøves, før vi kalder udgivelsen klar til alle.

Uden betalt Apple Developer ID kan macOS blokere første opstart. Åbn programmet én gang, gå til **Systemindstillinger → Anonymitet & sikkerhed → Åbn alligevel**, hvis du har kontrolleret og stoler på udgivelsen. Herefter husker macOS normalt undtagelsen. Vi slår ikke Gatekeeper fra og beder ikke brugeren fjerne karantæneattributter.

## Fælles adfærd og databeskyttelse

Dobbeltklik starter den lokale LTM-server på `127.0.0.1` og åbner den eksisterende webbaserede brugerflade i standardbrowseren. Den pakkede app har sin egen Python-runtime. Der oprettes ingen LTM-konto i skyen, og ingen offentlige porte åbnes.

Eksisterende private data forbliver i den almindelige LTM-datamappe: `~/Library/Application Support/Distrikt` på Mac og `%LOCALAPPDATA%\\Distrikt` på Windows. De indgår **ikke** i installationspakken. Tag altid backup i LTM før første overgang eller opdatering.

Dette er **lokal app**-sporet; privat LAN/VPN-server og Home Assistant bevarer indtil videre deres eksisterende installationsvej. Ekstern Tesseract/OCR installeres fortsat særskilt, hvis man vil bruge billedbaseret IB-import.

## Afprøvning og frigivelse

Workflowet `Native desktop installers (preview)` bygger på de relevante operativsystemer og tester en midlertidig installation med opdigtede kort. Det publicerer kun PR-/Actions-artifacts til test, **aldrig en Stable-release**. Før offentlig udgivelse kræves vellykket download/installationsprøve på fysisk Mac og Windows, kontrol af gamle data og backup samt en opdateret hjemmesideguide.
