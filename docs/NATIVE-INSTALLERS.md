# Gratis native desktop-installation – udviklingsspor

Målet er en nem installation af LTM til macOS og Windows **uden at installere Python**. Pakkerne er lokale og usignerede. Ejeren har 8. november 2026 bekræftet første installation og bevarelse af eksisterende data på både Mac og Windows. Det ændrer ikke Home Assistant, de eksisterende ZIP-release-spor eller almindelige Stable-udgivelser.

## Windows

GitHub Actions bygger en samlet app med PyInstaller og pakker den med den gratis Inno Setup-installationsmotor som `LTM-Windows-vVERSION-Setup.exe`. Installation sker pr. bruger, uden administratorrettigheder. Den opretter en genvej i Start-menuen. En genvej på skrivebordet kan vælges til.

Windows SmartScreen kan stadig vise en advarsel om en ukendt udgiver, fordi installationsfilen ikke er digitalt signeret. Signering er **ikke** en forudsætning for at bygge eller teste.

## macOS

GitHub Actions bygger en `LTM.app` med en integreret Python-runtime og pakker den som `LTM-macOS-vVERSION-Intel.dmg` og `LTM-macOS-vVERSION-AppleSilicon.dmg`. Man åbner DMG-filen og trækker LTM til Programmer. Buildworkflowet laver særskilte gratis prøvepakker til **Intel** og **Apple Silicon (M-serien)** på hver sin GitHub-runner. Den bruger fysisk Mac-arkitektur under CI; almindelig installation i Finder på en lokal Mac skal stadig afprøves, ved ændringer i installationsforløbet.

Uden betalt Apple Developer ID kan macOS blokere første opstart. Åbn programmet én gang, gå til **Systemindstillinger → Anonymitet & sikkerhed → Åbn alligevel**, hvis du har kontrolleret og stoler på udgivelsen. Herefter husker macOS normalt undtagelsen. Vi slår ikke Gatekeeper fra og beder ikke brugeren fjerne karantæneattributter.

## Fælles adfærd og databeskyttelse

Dobbeltklik starter den lokale LTM-server på `127.0.0.1` og åbner den eksisterende webbaserede brugerflade i standardbrowseren. Den pakkede app har sin egen Python-runtime. Der oprettes ingen LTM-konto i skyen, og ingen offentlige porte åbnes.

Eksisterende private data forbliver i den almindelige LTM-datamappe: `~/Library/Application Support/Distrikt` på Mac og `%LOCALAPPDATA%\\Distrikt` på Windows. De indgår **ikke** i installationspakken. Tag altid backup i LTM før første overgang eller opdatering.

Dette er **lokal app**-sporet; privat LAN/VPN-server og Home Assistant bevarer indtil videre deres eksisterende installationsvej. Ekstern Tesseract/OCR installeres fortsat særskilt, hvis man vil bruge billedbaseret IB-import.

## Afprøvning og frigivelse

Workflowet `Native desktop installers (preview)` bygger på de relevante operativsystemer og tester en midlertidig installation med opdigtede kort. Det publicerer kun PR-/Actions-artifacts til test, **aldrig en Stable-release**. Ejeren har bekræftet den fysiske Mac-/Windows-prøve; automatiske prøver gentages på den endelige kildekode.

## LTM installationer og opdateringer

**Mac:** Åbn den nye DMG og træk LTM over i Programmer igen. Finder tilbyder at erstatte den eksisterende app. Luk den tidligere LTM-instans før udskiftning. DMG'en har en grafisk installationsbaggrund med træk-pil og et klikbart link til [første åbning på LTM-hjemmesiden](https://localterritorymanager.netlify.app/da/guide/#mac-first-open).

**Windows:** Kør den nye Setup.exe med samme AppId og installationsmappe. Den opdaterer programfilerne uden at afinstallere brugerdata. Når man vælger dansk eller engelsk i installationsguiden, bruges dette sprog ved den første åbning i en browser uden gemt LTM-sprogvalg. Et senere manuelt valg i appen vinder altid over installationssproget.

**Ingen automatisk opdatering endnu:** Vi viser ikke en falsk auto-update-knap. Før native installer-releases bliver Stable, skal de udgives som individuelle `.dmg`- og `.exe`-assets under GitHub Releases, uden ekstra ZIP-indpakning. GitHub Actions pakker sine midlertidige preview-artifacts i ZIP; det er ikke det endelige downloadformat. Når installationspakkerne er fysisk testet og kildekoden er merged på main (Stable) eller develop (Beta), kan `Native desktop installers (preview)` startes manuelt med `publish_direct_assets=true` og bekræftelsen `INSTALLERS-VERIFIED`. Workflowet kræver alle fælles tests, bygger på de tre rigtige operativsystemer og vedhæfter `.dmg` og `.exe` **direkte** som separate assets i den allerede eksisterende versionsudgivelse, med SHA-256-kontrolfiler. Det overskriver aldrig eksisterende assets. Almindelige PR- og main-builds publicerer intet.

Husk at eksportere backup inden en versionsopgradering, og undlad at slette LTM's datamappe ved afinstallation.

Beta-installationen har egen Windows AppId, genveje og programmappe; på Mac hedder programmet LTM Beta.app og har eget bundle-id. Beta bruger Distrikt-beta som datafolder og særskilte sessionscookies. Opdatering af Beta må aldrig erstatte Stable-data.
