# Egen Datafordeler-nøgle i LTM

Dansk vejledning · kontrolleret mod Datafordelerens dokumentation 17.10.2026.

[English](DATAFORDELER.en.md)

## Kort status

Ja: adresseimport via DAR GraphQL er implementeret og kan bruges med din egen nøgle. Fra beta.23 har opsætningsplanen en direkte indgang til nøglevejledningen. Opret en konto, et IT-system og en API-key i Datafordeler Administration, og indsæt nøglen i din lokale LTM. Der er ikke oprettet en fælles nøgle til alle brugere.

Klimadatastyrelsens frist er fortsat **15. januar 2027** for de gamle REST-tjenester. [Officiel meddelelse](https://www.klimadatastyrelsen.dk/om-klimadatastyrelsen/nyheder/nyhedsarkiv/2026/jun/paralleldrift-paa-datafordeleren-ophoerer-den-15-januar-2027) og [DAR GraphQL-adgang](https://datafordeler.dk/dataoversigt/danmarks-adresseregister-dar/dar-graphql/) er genkontrolleret 17.10.2026. Adressevælgerens søgeforslag er en særskilt tjeneste; en fungerende GraphQL-nøgle er ikke i sig selv en prøve af den.

**Kan nøglen oprettes efter 15. januar 2027? Ja.** Datoen er lukningen af den gamle REST-adgang, ikke en sidste frist for at oprette API-nøgler. Den nye adgang med API-key/OAuth og GraphQL fortsætter efter datoen, og nye brugere opretter sig i Datafordeler Administration. Tilslut gerne den nye adgang før lukningen for at undgå en pause i nye adressehentninger. En udløbet eller mistet nøgle kan erstattes via Administration og gemmes i LTM. Se [Datafordelerens overgangsbeskrivelse](https://datafordeler.dk/vejledning/transitionsnetvaerk/).

Lokal administration og gemte adresser kan bruges uden en ny hentning. Det udestående ejertrin er at prøve egen nøgle på én offentlig vej og derefter et lille område på egen HA. Send ikke nøglen i chatten.

## Opret din nøgle

1. Åbn [Datafordeler Administration](https://portal.datafordeler.dk/), og opret eller log ind på din egen konto.
2. Opret et **IT-system**, fx “LTM lokal”.
3. Åbn IT-systemets sektion **API-Keys**, og vælg **Opret**. Giv nøglen et navn, fx “LTM hjemme”. Vælg API-key til offentlige data; LTM bruger DAR og skal ikke have adgang til personregistre.
4. Kopiér den genererede API-key. Datafordeleren viser den kun én gang. Gem den eventuelt i din egen adgangskodehåndtering.
5. Åbn **Kortdata → Datafordeleren · egen API-nøgle** i din lokale LTM. Indsæt nøglen i passwordfeltet, og vælg **Kontrollér og gem nøgle**.
6. LTM kontrollerer DAR v3-skemaet og GraphQL-forbindelsen før gemning. Feltet tømmes efter indsendelse. Ved en afvist erstatningsnøgle bevares den tidligere gemte nøgle.

## Hvad betyder grøn forbindelse?

Fra beta.39 viser afviste opslag en renset GQL-diagnose: skema/filtre, dataadgang, størrelsesgrænse eller anden afvisning. Kun kendte koder og feltnavne vises. Ved genkendte størrelsesfejl prøver appen mindre opslag indenfor faste grænser; andre fejl stoppes. Prøv først én vej, og oplys kun appens GQL-diagnose ved fejl. Beta.38-prøven fejlede på både vej og grænse, så faktisk fungerende hentning er stadig et åbent ejertrin.

Fra beta.38 er en fejl i punktstatus rettet: adressepunkter bruger en anden livscyklus end adresser og husnumre. Fejlen kunne give 0 adresser ved en korrekt gemt nøgle. Efter opdateringen genprøves gamle GraphQL-grænsehentninger automatisk; du kan også vælge **Opdater hele området**. Et tomt resultat advarer nu tydeligt. Kontrollér fortsat en virkelig vej og et område med din egen nøgle, før hentningen godkendes som afprøvet.

Fra beta.8 bruger nye vej-, postnummer- og grænsehentninger **DAR GraphQL**, når en nøgle er gemt. LTM henter komplette sider og sammenkobler adresser, husnumre, vejnavne, postnumre og adgangspunkter lokalt. Adresse-ID'er, etage og dør bevares. Uden en nøgle bruges den hidtidige kilde; den varslede udfasning af DAR REST er fortsat 15.01.2027. Adresseforslag i søgefeltet leveres stadig af den særskilte Adressevælger.

En kontrolleret forbindelse bekræfter adgang og gemt nøgle. Automatisk udviklingskontrol bruger opdigtede svar. Prøv derfor først en enkelt offentlig vej i din egen installation, og kontrollér husnumre og lejligheder, før du vælger et større område. Egen konto og levende Datafordeler/HA er et særskilt ejertrin.

Fra beta.30 er hentning med egen nøgle uafhængig af det gamle systems vejforslag. Hvis forslagstjenesten fejler, kan du skrive det præcise officielle vejnavn og postnummer og vælge **Hent vej**. Forslagene er fortsat en hjælp, ikke et krav for GraphQL. Et lille kortudsnit med bygninger/vejnavne bruger stadig OSM; adresserne til de fundne veje hentes via GraphQL.

## Fortsæt eller opdater en tidligere hentning

En gemt hentning har et fast tidspunkt, en kilde og et skemafingeraftryk. Ved pause/genstart springes færdige veje eller udsnit over, mens manglende dele hentes med det samme tidspunkt. En ufuldstændig vej/et ufuldstændigt udsnit gemmes ikke som komplet. Netfejl stopper ved den aktuelle del; lokale adresser bevares.

En gammel REST-hentning kan ikke fortsættes med GraphQL, og en GraphQL-hentning kan ikke fortsættes uden den gemte forbindelse. Vælg en **ny hentning/opdatering** ved kildeskift, eller gendan forbindelsen for at fortsætte samme kilde. Det samme gælder, hvis det kontrollerede skema er ændret. De allerede hentede lokale adresser slettes ikke ved dette afslag. Postnummeropdatering og opdatering af den samlede grænse bruger den eksisterende kontrol af adresseændringer.

## Lokal lagring og flytning

Nøglen gemmes separat fra registreringerne i installationens private datamappe. Appens status, kortdata og portable sikkerhedskopier indeholder ikke nøglen. Forbindelsen sættes derfor op igen ved flytning til en anden installation. Datafordeleren modtager nøglen som autentifikation. Forbindelseskontrollen sender ingen lokale registreringer. Adressehentning sender kun offentlige opslag med vej-/postnummer-/entitets-ID'er eller rektangulære udsnit. Den præcise distriktsgrænse filtreres lokalt; kort, forkyndere og IB sendes ikke.

**Kontrollér gemt forbindelse** laver en ny kontrol. **Fjern gemt nøgle** fjerner den lokale credential og bevarer dine kort og adresser. Betaens nulstilling af testdata bevarer også forbindelsen.

## Hvis kontrollen fejler

- Ved afvist adgang: kontrollér at du har kopieret en API-key fra det rigtige IT-system. En OAuth Shared Secret er en anden credential og kan ikke sættes ind som API-key.
- En helt ny API-key kan være op til **15 minutter** om at blive aktiv. Det er kun én mulig årsag til afvist adgang, ikke en forklaring på alle fejl. Vent til de 15 minutter er gået, og vælg bevidst **Kontrollér gemt forbindelse** igen. Net- og serverfejl vises fortsat særskilt.
- Ved netfejl: prøv igen senere. En mislykket kontrol erstatter ikke den gemte nøgle.
- Hvis nøglen er udløbet eller deaktiveret: forny eller opret den i Datafordeler Administration og gem erstatningen i LTM.
- Send ikke nøglen i chat, skærmbilleder eller GitHub-feedback. Den indtastes kun i din lokale app.

## Kilder

- [Officiel vejledning: autentifikationsmetoder og oprettelse af API-key](https://confluence.kds.dk/pages/viewpage.action?pageId=187105503).
- [Datafordeler Administration: aktivering af nye API-nøgler](https://datafordeler.dk/media/lggned4a/20260219-datafordeler-administration.pdf).
- [DAR GraphQL](https://datafordeler.dk/dataoversigt/danmarks-adresseregister-dar/dar-graphql/).
- [LTM's overgangsplan](ADRESSEKILDE-2027.md).

## Læsende diagnose i beta.40

Vælg **Kontrollér DAR-opslag** under Datafordeler-forbindelsen. Den sammenligner de aktuelle feltprojektioner og filtre med fiktive søgeværdier i almindelige opslag og aliases. Kontrollen gemmer ingen adresser, ændrer ingen forbindelse eller checkpoints og viser ingen rå leverandørtekst. Den tager op til ét minut. Et accepteret fiktivt opslag er ikke en bekræftet virkelig adressehentning; W62 er fortsat åben.
