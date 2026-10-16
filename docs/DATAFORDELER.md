# Egen Datafordeler-nøgle i LTM

Dansk vejledning · kontrolleret mod Datafordelerens dokumentation 16.10.2026.

## Opret din nøgle

1. Åbn [Datafordeler Administration](https://portal.datafordeler.dk/), og opret eller log ind på din egen konto.
2. Opret et **IT-system**, fx “LTM lokal”.
3. Åbn IT-systemets sektion **API-Keys**, og vælg **Opret**. Giv nøglen et navn, fx “LTM hjemme”. Vælg API-key til offentlige data; LTM bruger DAR og skal ikke have adgang til personregistre.
4. Kopiér den genererede API-key. Datafordeleren viser den kun én gang. Gem den eventuelt i din egen adgangskodehåndtering.
5. Åbn **Kortdata → Datafordeleren · egen API-nøgle** i din lokale LTM. Indsæt nøglen i passwordfeltet, og vælg **Kontrollér og gem nøgle**.
6. LTM kontrollerer DAR v3-skemaet og GraphQL-forbindelsen før gemning. Feltet tømmes efter indsendelse. Ved en afvist erstatningsnøgle bevares den tidligere gemte nøgle.

## Hvad betyder grøn forbindelse?

I beta.7 betyder det, at din nøgle er gemt og forbindelsen til DAR v3 er kontrolleret. **Adresseimporten bruger fortsat den hidtidige kilde.** Dette er første del af den planlagte overgang før udfasningen af DAR REST. Et skift af adressekilde kommer i et efterfølgende, særskilt kontrolleret trin.

## Lokal lagring og flytning

Nøglen gemmes separat fra registreringerne i installationens private datamappe. Appens status, kortdata og portable sikkerhedskopier indeholder ikke nøglen. Forbindelsen sættes derfor op igen ved flytning til en anden installation. Datafordeleren modtager nøglen som autentifikation; denne kontrol sender ingen lokale adresser, distriktsgrænser, kort, forkyndere eller IB.

**Kontrollér gemt forbindelse** laver en ny kontrol. **Fjern gemt nøgle** fjerner den lokale credential og bevarer dine kort og adresser. Betaens nulstilling af testdata bevarer også forbindelsen.

## Hvis kontrollen fejler

- Ved afvist adgang: kontrollér at du har kopieret en API-key fra det rigtige IT-system. En OAuth Shared Secret er en anden credential og kan ikke sættes ind som API-key.
- Ved netfejl: prøv igen senere. En mislykket kontrol erstatter ikke den gemte nøgle.
- Hvis nøglen er udløbet eller deaktiveret: forny eller opret den i Datafordeler Administration og gem erstatningen i LTM.
- Send ikke nøglen i chat, skærmbilleder eller GitHub-feedback. Den indtastes kun i din lokale app.

## Kilder

- [Officiel vejledning: autentifikationsmetoder og oprettelse af API-key](https://confluence.kds.dk/pages/viewpage.action?pageId=187105503).
- [DAR GraphQL](https://datafordeler.dk/dataoversigt/danmarks-adresseregister-dar/dar-graphql/).
- [LTM's overgangsplan](ADRESSEKILDE-2027.md).
