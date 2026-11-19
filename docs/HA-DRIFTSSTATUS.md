# Drift og beskeder i Home Assistant

Den oprindelige W110-status er frigivet i [verificeret beta.78](planning/BETA-78-VERIFICERING.md). Udvidelsen med HTTP-prøve og svarproblemer nedenfor er en udviklingskandidat; den er ikke udgivet endnu.

LTM afleverer et lille lokalt livstegn cirka hvert 30. sekund. Beta og stabil har hver sin oplysning: `sensor.ltm_beta_drift` og `sensor.ltm_stable_drift`. Der indgår ingen kort, IB, forkyndernavne, kontonavne, adgangskoder, nøgler, filstier eller fritekst fra adressekilden.

## Opsætning

1. Lad **Driftsstatus til Home Assistant** (`drift_status`) være slået til i HA-appens konfiguration, og start den opdaterede app.
2. Åbn LTM → Indstillinger → Backup og vedligeholdelse → Drift og beskeder.
3. Vælg **Klargør driftsbeskeder i Home Assistant**. Importér opskriften, opret en automation fra den, vælg din LTM-kanal og telefonen med Home Assistant-appen. Tilføj eventuelt en note for hver beskedtype, og gem.
4. Brug **Send én prøvebesked** i LTM. Det sender en særskilt prøvehændelse, uden at fremkalde fejl, overbelastning eller ændringer i distriktsdata.

Opskriften ligger [i projektet](../homeassistant/ltm-status.yaml). Linket i appen peger på samme udgivelsesmærke som den installerede version. Opskriften er klar til import; den bliver ikke automatisk installeret eller tildelt en telefon ved opdatering. Eksisterende automationer ændres ikke. Når HTTP-overvågningen er udgivet, skal du genimportere den opdaterede opskrift og genindlæse automationerne for at få den nye beskedtype **Vedvarende svarproblemer**. Bevar dit kanalvalg, din telefon og dine noter, og send en ny prøve. Den eksisterende besked om manglende livstegn virker også med den gamle opskrift. Telefon og noter gemmes i din egen HA-automation. Beskedlevering følger din Home Assistant Companion-opsætning, som kan bruge en ekstern push-tjeneste.

Du kan vise driftsoplysningen på et HA-dashboard. Den oprettes via tilstands-API'et og er ikke en separat integration med enhedsregistrering. Efter en HA-genstart afleverer LTM den igen. Der gemmes ikke en ny LTM-enhedskonto eller en langsigtet HA-nøgle i appens data.

## Hvad måles?

- **Arbejder/venter:** Adressekontrollen kører eller holder en normal pause. Det giver ingen fejlbesked.
- **Gentagne afbrydelser:** En automatisk kontrol er afbrudt mindst fire gange uden nye færdige udsnit. Se årsagen i den private LTM-app. Normale tidsbudget- og ressourcepauser tæller ikke som denne fejl.
- **Vedvarende ressourcepres:** Tilgængelige Linux-PSI-gennemsnit over 60 sekunder ligger over arbejdsgrænserne i mindst to minutter. Det er systemets ventetid på ressourcer, ikke CPU-forbrug i procent. Ukendte målinger angives som utilgængelige.
- **Vedvarende svarproblemer:** LTM foretager en lokal HTTP-prøve og en separat intern statusmåling cirka hvert 30. sekund. En samlet svarfrist på fem sekunder vurderes af afleveringstråden, også hvis prøven aldrig returnerer eller kun sender enkelte bytes. Fejlen skal være observeret vedvarende i mindst 120 sekunder før tilstanden bliver `unresponsive`. Med måleintervallet kan beskeden typisk komme efter cirka 2–3 minutter. Kortvarige gemninger giver ikke denne besked.
- **Manglende livstegn:** Opskriften opdager et stoppet LTM eller et livstegn, der er over 150 sekunder gammelt, og venter derefter et minut. HA's tidsopdatering kan give yderligere op til cirka et minut. HA skal selv være i gang for at sende beskeden.

Beskeder udløses ved ændringen, ikke hver gang samme status afleveres. Normal drift sender ingen beskeder. En valgfri besked om ophørt målt fejl, svarproblemer eller pres kan slås til. Den udløses først ved en ny normal tilstand (`idle`, `working` eller `waiting`); manglende ressourcemålinger (`unknown`) udløser ingen raskmelding. Der er ingen særskilt raskmelding efter et forældet livstegn alene. Det er ikke en fuld sundhedskontrol af Home Assistant, netværket, backupfiler, Google Drive eller alle LTM-funktioner. Ved utilgængelige ressourcemålinger påstås de ikke at være sunde.

## Hvad kan HTTP-prøven fortælle?

Den eksisterende Supervisor TCP-watchdog kontrollerer kun, om porten accepterer en forbindelse. Den bevares uændret. En åben port er ikke bevis for et færdigt HTTP-svar.

LTM bruger nu samme HTTP-lytter til en lille intern prøve før den normale profiladgang. Prøven forsøger data- og kontolåsene uden ventetid og læser ingen brugerdata. HTTP-prøve, intern statusmåling og aflevering til HA kører adskilt. Der findes højst én igangværende arbejder for hver måling; en fastlåst måling skaber ikke flere og flere tråde eller HTTP-forespørgsler. Afleveringen venter aldrig på disse arbejdere eller på data-/kontolåsene. En sen succes, som overskred svarfristen, tæller stadig som timeout; en ny rettidig prøve kræves til raskmelding.

| Fast diagnose i HA-attributten `diagnostic` | Hvad er faktisk observeret? |
| --- | --- |
| `none` | De seneste prøver gennemførte normalt. |
| `starting` | De første målinger afventes. |
| `http_timeout` | HTTP-prøven overskred sin samlede svarfrist. |
| `http_error` | Forbindelsen eller læsning af svaret mislykkedes. Ingen rå fejltekst sendes. |
| `http_invalid_response` | Uventet, for stort eller forældet svar; prøvens engangsværdi matchede ikke. |
| `runtime_busy` | HTTP-prøven svarede, men data- eller kontolåsen var optaget. Det kan være en gemning. |
| `status_timeout` | Den separate interne statusmåling overskred svarfristen. |
| `status_error` | Den interne statusmåling mislykkedes. |

Derudover vises de begrænsede attributter `http_status`, `status_sample` og `problem_seconds` (højst 86400). Det er målinger, ikke beviser for årsagen. Beskeden oversætter kun kendte diagnoser til faste tekster; ukendte værdier videresendes ikke.

Hvis hele processen, Python-afviklingen eller forbindelsen til HA fryser, kan LTM ikke selv offentliggøre en ny diagnose. **Den eksisterende HA-blueprint opdager i stedet det forældede livstegn udefra.** Det kræver, at HA Core og automationen stadig kører. Appen skal ikke kunne håndtere en HTTP-forespørgsel for at HA kan opdage dette. Ingen ekstra REST-sensor, åbent status-endpoint eller nye HA-rettigheder er nødvendige.

Prøven beviser ikke, at en bestemt browser, Wi-Fi/VPN-forbindelse, proxy, statisk fil eller alle API-funktioner virker. En fastfrysning kun i browserens JavaScript kan være usynlig, når serveren fortsat svarer. Ved næste rigtige fastfrysning er der derfor brug for:

- Klokkeslæt, hvilken skærm og handling der var i gang, samt om en gemning ventede. Brug fiktive eksempler.
- Om en anden browser/enhed på samme net kunne åbne LTM, og om HA Core stadig reagerede.
- Kanal/version, driftsensorens faste tilstand og diagnoser samt hvor gammelt `updated_at` var før genstart. Eventuelle HTTP-statuskoder eller ventetider kan beskrives uden URL-parametre, cookies eller tokens.

Ingen automatisk genstart er tilføjet. En optaget lås eller et langsomt svar kan skyldes en igangværende gemning; beskeden giver ikke grønt lys til at afbryde den. Vi har ikke ændret ejerens HA-installation eller genskabt den præcise årsag til den rapporterede fastfrysning.

## Adgang og afgrænsning

HA-konfigurationen ændres til `homeassistant_api: true`, mens `hassio_api` forbliver `false`. Home Assistants Core-proxy har administrativ myndighed. LTM's kode bruger kun den faste lokale Supervisor-adresse, sin egen tilstandsoplysning og den faste prøvehændelse. Der findes ingen browserfunktion til vilkårlige HA-kald, værtsvalg eller brugervalgte hændelser. Omdirigering og miljøets webproxy bruges ikke. Tokens og svar fra HA logges ikke.

`drift_status: false` stopper aflevering efter genstart af appen. Det fjerner ikke selve API-rettigheden fra HA-konfigurationen. Slå også den tilhørende automation fra, hvis du vil undgå dens besked om manglende livstegn. Den interne `/api/runtime/probe` kræver en særskilt tilfældig nøgle, som kun findes i processen, en loopback-forbindelse, godkendt Host og ingen browser-Origin. Den sædvanlige app-/CSRF-nøgle giver ikke adgang. Nøglen sendes aldrig til browseren eller HA, og prøven læser eller ændrer ingen poster. Svar kan ikke caches eller genbruges som nye succeser. Login til LTM, LAN/VPN, privat port og brugerroller fungerer fortsat som før. I profiltilstand kræver driftsvisning og prøve `settings.manage`, også på serveren og ved ændrede rettigheder midt i en session. Prøven begrænses til ét forsøg i minuttet. Et ukendt resultat genudsendes ikke automatisk.

Ressourcegrundlaget læser kun lokale Linux-målinger; det ændrer ingen systemindstillinger. Mac-/Windows-udgaven afleverer ikke til HA. Det er ingen Codex-automation, sikkerhedsscanning eller afprøvning på ejerens installation.

## Primære kilder

- [Home Assistants Core-proxy og rettighed](https://contributors.home-assistant.io/apps/supervisor-api/core/)
- [Blueprints og import](https://www.home-assistant.io/docs/blueprint/tutorial/)
- [Valg af enhed og input](https://www.home-assistant.io/docs/blueprint/selectors/)
- [Companion-beskeder](https://companion.home-assistant.io/docs/notifications/notifications-basic/)
- [HA-skabeloner og tidsopdatering](https://www.home-assistant.io/triggers/template/)
- [Linux PSI](https://cdn.kernel.org/doc/html/latest/accounting/psi.html)

## Kontrol af HTTP-kandidaten

Midlertidige fiktive SQLite-data og lokale HTTP-servere dækker blokerede HTTP-svar, langsom levering af svarindhold, afvist forbindelse, forældet/uventet svar, optagne data- og kontolåse samt en fastlåst intern statusmåling. Den uafhængige aflevering fortsætter, femsekundersfristen og to minutters vedvarende fejl afprøves med fiktivt monotont ur, kun én arbejder tillades per måling, og raskmelding kræver nye rettidige målinger. Adgang, uændret dataversion, ingen hemmeligheder i status og bevaret kørende server kontrolleres. Ingen rigtig HA eller telefon kontaktes.

Den eksisterende kontrol i `scripts/check_ha_status_blueprint.py` er udvidet med den nye beskedtype og alle faste diagnoser for begge kanaler. PR-CI kører Home Assistant 2026.10.4's faktiske skemaer og skabeloner samt den brede suite. Ejerens telefonlevering og en virkelig fastfrysning er fortsat ikke afprøvet.

## Historisk kontrol af den oprindelige W110-udgave

586 Python-prøver, JavaScript-suiten, 16 pakkeprøver og fem HA-betapakkeprøver består lokalt. Det rigtige lokale HTTP-/browserforløb dækker profilrettigheder, øjeblikkelig tilbagekaldelse, prøvebesked, ét minut mellem forsøg og mobilvisning. Home Assistant 2026.10.4 er indlæst i et adskilt midlertidigt miljø: opskrift, input, handlinger, hændelser og besked-/livstegnskabeloner er valideret med begge kanaler og opdigtede noter. Noter bliver almindelig tekst, ikke nye skabeloner. Den valgfrie kameraafhængighed gav en lokal advarsel om manglende turbojpeg-systembibliotek; ingen kamera- eller billedfunktion bruges i denne kontrol. Dette er ikke en leveringsprøve på ejerens telefon. Samme kontrol føjes til udgivelsesporten.
