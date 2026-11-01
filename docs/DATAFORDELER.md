# Adressehentning med egen Datafordeler-nøgle

[English](DATAFORDELER.en.md)

Opdateret 24.10.2026. Adressehentning med egen nøgle er implementeret. Ejeren har bekræftet, at hentningen virker på Home Assistant; den tidligere generelle afprøvning bestilles derfor ikke igen. En ny installation skal stadig have sin egen forbindelse.

## Opret og gem din nøgle

1. Åbn [Datafordeler Administration](https://portal.datafordeler.dk/), og opret eller log ind på din egen konto.
2. Opret et **IT-system**, fx “LTM lokal”, og en tilhørende **API-key** til offentlige data. LTM bruger DAR og behøver ikke adgang til personregistre. En OAuth Shared Secret er en anden type oplysning og kan ikke bruges som API-key.
3. Gem nøglen sikkert, fx i din adgangskodehåndtering. Send den aldrig i chat, feedback eller til GitHub.
4. Åbn **Indstillinger → Forbindelser → Datafordeleren · egen API-nøgle**. Under **Hent adresser** er der også en genvej til forbindelsen. Indsæt nøglen, og vælg **Kontrollér og gem nøgle**.
5. Feltet tømmes efter indsendelse. Ved en afvist erstatningsnøgle bevares den tidligere gemte nøgle.

LTM kontrollerer adgang og det forventede DAR-skema før gemning. Grøn forbindelse betyder, at forbindelsen er kontrolleret; det er ikke i sig selv et antal hentede adresser.

## Hent og følg arbejdet

Begynd med en vej eller et lille udsnit på en ny installation. Med en gemt nøgle hentes DAR-adresser via Datafordeleren, uafhængigt af om vejforslag fra Adressevælger virker. Skriv det præcise officielle vejnavn og postnummer, hvis forslagene mangler. Kortbaggrund, bygninger og vejgeometri fra OpenStreetMap er en separat kilde.

Ved **Samlet distriktsgrænse → Hent/fortsæt** bruges den gemte grænse. Fra beta.65 vises det aktuelle arbejde og et dubletfrit antal **modtagne adresser**. Modtagne adresser er ikke nødvendigvis det endelige antal inden for din præcise grænse. Slutresultatet angiver antal og om hentningen er komplet. Der vises ingen gættet resttid.

Store opslag deles i mindre udsnit inden for faste grænser. Ved pause, afbrydelse eller midlertidig fejl bevares færdige udsnit. Fortsæt senere fra samme kilde og tidspunkt. En ufuldstændig hentning markeres fortsat som ufuldstændig. En tom hentning er en grund til at kontrollere område og slutbesked; den er ikke dokumentation for, at eksisterende adresser skal fjernes.

## Fortsæt eller start en ny opdatering

En gemt hentning har en kilde, et tidspunkt og et aftryk af det kontrollerede skema. Færdige dele springes over ved genoptagelse. Ved skift mellem den gamle kilde og GraphQL, eller når skemaet er ændret, skal du vælge en ny hentning/opdatering eller gendanne den oprindelige forbindelse. Eksisterende lokale adresser bevares ved afslag.

Gennemgå nye, ændrede og udgåede adresser under **Opfølgninger → Adresseændringer**. Godkendte ændringer i adresseregisteret skal efterfølgende indarbejdes på de relevante kort; kort ændres ikke automatisk. Printkontrol og godkendelse af en fysisk kortside er særskilte handlinger.

## Hvis det ikke virker

- Afvist adgang: kontrollér den rigtige API-key og det rigtige IT-system. Ved en ny nøgle kan du vente og vælge en ny forbindelseskontrol. Brug appens rensede fejlforklaring frem for at dele nøgle eller rå svar.
- Netfejl: færdige dele bevares. Prøv at fortsætte, når forbindelsen virker. En fejl betyder ikke automatisk, at nøglen er forkert.
- Grænsen for et opslag: appen prøver mindre udsnit inden for sine grænser. Hvis slutbeskeden stadig er ufuldstændig, er hentningen ikke færdig.
- Opdatering af nøgle: **Kontrollér gemt forbindelse** kontrollerer igen. **Fjern gemt nøgle** fjerner forbindelsen og bevarer kort og adresser.

De automatiske udviklingsprøver bruger opdigtede svar. De erstatter ikke kontrol af det konkrete område, som en bruger selv vælger at hente.

## Privat lagring og flytning

Nøglen ligger separat i installationens private datamappe og medfølger ikke i en almindelig sikkerhedskopi. Forbind den derfor igen efter flytning til en anden installation. Betaens nulstilling af testdata bevarer forbindelsen.

Datafordeleren modtager nøglen til adgangskontrol og offentlige adresseopslag. Den præcise distriktsgrænse filtreres lokalt. Kort, forkyndere og IB sendes ikke til adressekilden. **Adressevælger** bruges særskilt til vejforslag og benytter normalt den anbefalede standardtoken. Datafordeler-nøglen skal ikke indtastes i Adressevælger-feltet.

## Overgangen i januar 2027

Klimadatastyrelsen angiver fortsat **15. januar 2027** som ophør for de ikke-moderniserede tjenester, herunder den gamle REST-adgang. Det er ikke en sidste frist for at oprette en nøgle. Den moderniserede adgang bruger API-key eller OAuth; GraphQL fortsætter. Nye brugere opretter sig i Datafordeler Administration. Allerede gemte lokale kort og adresser bliver ikke slettet af denne overgang.

Officielle kilder genkontrolleret 24.10.2026:

- [Klimadatastyrelsens meddelelse om 15. januar 2027](https://www.klimadatastyrelsen.dk/om-klimadatastyrelsen/nyheder/nyhedsarkiv/2026/jun/paralleldrift-paa-datafordeleren-ophoerer-den-15-januar-2027)
- [DAR GraphQL og krav om bruger, IT-system og adgang](https://datafordeler.dk/dataoversigt/danmarks-adresseregister-dar/dar-graphql/)
- [Datafordelerens overgangsbeskrivelse](https://datafordeler.dk/vejledning/transitionsnetvaerk/)
