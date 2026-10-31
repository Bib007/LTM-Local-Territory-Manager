# Drift og beskeder i Home Assistant

W110 · frigivet i verificeret beta.78 · [udgivelsesbevis](planning/BETA-78-VERIFICERING.md).

LTM afleverer et lille lokalt livstegn cirka hvert 30. sekund. Beta og stabil har hver sin oplysning: `sensor.ltm_beta_drift` og `sensor.ltm_stable_drift`. Der indgår ingen kort, IB, forkyndernavne, kontonavne, adgangskoder, nøgler, filstier eller fritekst fra adressekilden.

## Opsætning

1. Lad **Driftsstatus til Home Assistant** (`drift_status`) være slået til i HA-appens konfiguration, og start den opdaterede app.
2. Åbn LTM → Indstillinger → Backup og vedligeholdelse → Drift og beskeder.
3. Vælg **Klargør driftsbeskeder i Home Assistant**. Importér opskriften, opret en automation fra den, vælg din LTM-kanal og telefonen med Home Assistant-appen. Tilføj eventuelt en note for hver beskedtype, og gem.
4. Brug **Send én prøvebesked** i LTM. Det sender en særskilt prøvehændelse, uden at fremkalde fejl, overbelastning eller ændringer i distriktsdata.

Opskriften ligger [i projektet](../homeassistant/ltm-status.yaml). Linket i appen peger på samme udgivelsesmærke som den installerede version. Opskriften er klar til import; den bliver ikke automatisk installeret eller tildelt en telefon ved opdatering. Eksisterende automationer ændres ikke. Telefon og noter gemmes i din egen HA-automation. Beskedlevering følger din Home Assistant Companion-opsætning, som kan bruge en ekstern push-tjeneste.

Du kan vise driftsoplysningen på et HA-dashboard. Den oprettes via tilstands-API'et og er ikke en separat integration med enhedsregistrering. Efter en HA-genstart afleverer LTM den igen. Der gemmes ikke en ny LTM-enhedskonto eller en langsigtet HA-nøgle i appens data.

## Hvad måles?

- **Arbejder/venter:** Adressekontrollen kører eller holder en normal pause. Det giver ingen fejlbesked.
- **Gentagne afbrydelser:** En automatisk kontrol er afbrudt mindst fire gange uden nye færdige udsnit. Se årsagen i den private LTM-app. Normale tidsbudget- og ressourcepauser tæller ikke som denne fejl.
- **Vedvarende ressourcepres:** Tilgængelige Linux-PSI-gennemsnit over 60 sekunder ligger over arbejdsgrænserne i mindst to minutter. Det er systemets ventetid på ressourcer, ikke CPU-forbrug i procent. Ukendte målinger angives som utilgængelige.
- **Manglende livstegn:** Opskriften opdager et stoppet LTM eller et livstegn, der er over 150 sekunder gammelt, og venter derefter et minut. HA's tidsopdatering kan give yderligere op til cirka et minut. HA skal selv være i gang for at sende beskeden.

Beskeder udløses ved ændringen, ikke hver gang samme status afleveres. Normal drift sender ingen beskeder. En valgfri besked om ophørt målt fejl/pres kan slås til. Det er ikke en fuld sundhedskontrol af Home Assistant, netværket, backupfiler, Google Drive eller alle LTM-funktioner. Ved utilgængelige ressourcemålinger påstås de ikke at være sunde.

## Adgang og afgrænsning

HA-konfigurationen ændres til `homeassistant_api: true`, mens `hassio_api` forbliver `false`. Home Assistants Core-proxy har administrativ myndighed. LTM's kode bruger kun den faste lokale Supervisor-adresse, sin egen tilstandsoplysning og den faste prøvehændelse. Der findes ingen browserfunktion til vilkårlige HA-kald, værtsvalg eller brugervalgte hændelser. Omdirigering og miljøets webproxy bruges ikke. Tokens og svar fra HA logges ikke.

`drift_status: false` stopper aflevering efter genstart af appen. Det fjerner ikke selve API-rettigheden fra HA-konfigurationen. Slå også den tilhørende automation fra, hvis du vil undgå dens besked om manglende livstegn. Login til LTM, LAN/VPN, privat port og brugerroller fungerer fortsat som før. I profiltilstand kræver driftsvisning og prøve `settings.manage`, også på serveren og ved ændrede rettigheder midt i en session. Prøven begrænses til ét forsøg i minuttet. Et ukendt resultat genudsendes ikke automatisk.

Ressourcegrundlaget læser kun lokale Linux-målinger; det ændrer ingen systemindstillinger. Mac-/Windows-udgaven afleverer ikke til HA. Det er ingen Codex-automation, sikkerhedsscanning eller afprøvning på ejerens installation.

## Primære kilder

- [Home Assistants Core-proxy og rettighed](https://contributors.home-assistant.io/apps/supervisor-api/core/)
- [Blueprints og import](https://www.home-assistant.io/docs/blueprint/tutorial/)
- [Valg af enhed og input](https://www.home-assistant.io/docs/blueprint/selectors/)
- [Companion-beskeder](https://companion.home-assistant.io/docs/notifications/notifications-basic/)
- [Linux PSI](https://cdn.kernel.org/doc/html/latest/accounting/psi.html)

## Udført kontrol af kandidaten

586 Python-prøver, JavaScript-suiten, 16 pakkeprøver og fem HA-betapakkeprøver består lokalt. Det rigtige lokale HTTP-/browserforløb dækker profilrettigheder, øjeblikkelig tilbagekaldelse, prøvebesked, ét minut mellem forsøg og mobilvisning. Home Assistant 2026.10.4 er indlæst i et adskilt midlertidigt miljø: opskrift, input, handlinger, hændelser og besked-/livstegnskabeloner er valideret med begge kanaler og opdigtede noter. Noter bliver almindelig tekst, ikke nye skabeloner. Den valgfrie kameraafhængighed gav en lokal advarsel om manglende turbojpeg-systembibliotek; ingen kamera- eller billedfunktion bruges i denne kontrol. Dette er ikke en leveringsprøve på ejerens telefon. Samme kontrol føjes til udgivelsesporten.
