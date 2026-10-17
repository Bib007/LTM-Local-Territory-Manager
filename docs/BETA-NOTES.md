# LTM 1.12.0-beta.20

## Nyt siden beta.19

Fast punkt 6 er afsluttet. Opsætning, IB-/kortimport, deling og førstegangsopsætning skelner mellem afvisning, usikkert svar og bekræftet gemning med fejlet efterfølgende læsning. Der sker ingen automatisk gentagelse. Sene svar erstatter ikke nyere kladder eller opsætningssessioner.

Også lokale billedvalg og geodatahentninger bevarer en nyere dialog. Sene farve-/Se bort fra-svar og oprydningskvitteringer overskriver ikke nyere valg eller kontroller.

## Prøv især

1. Opdater Distrikt Beta, adskilt fra stabil, og brug kun opdigtede prøvedata. Hent først en lokal backup i betaen.
2. Opret et lille sæt prøvekort i opsætningen. Kontrollér normal afslutning, og genåbn kortene.
3. Hvis skrivningen bekræftes, men genindlæsning fejler: kontrollér beskeden **Ændringen er gemt · opdatér data før næste ændring**. Gentag ikke oprettelsen/importen; afslut redigeringen, vælg Opdater og kontrollér de faktiske registreringer.
4. Prøv en opdigtet kort-/IB-import og kontrollér samtykkeord, resultat og genprintmarkeringer. En læsefejl må ikke udløse endnu en import.
5. Kontrollér normal Google-testpublicering med ufølsomme prøvekort og en særskilt testkonto, hvis du ønsker en rigtig kontoafprøvning. Godkendt billede og QR-kontrakt er uændrede. En fejl i statuslæsningen betyder ikke, at uploadanmodningen skal sendes igen.

Fiktive programprøver dækker gennemførte skrivninger, fejlede læsninger, ukendte kvitteringer, nyere sessioner/dialoger, uændrede payloads og spærret gentagelse. Offline Chromium kontrollerer oprettelse med fejlet efterfølgende læsning, bevaret plan og eksplicit genindlæsning ved 320/390/768/1440 pixels. Udviklingsprøver bruger ingen rigtig database, konto eller nøgle.

Fast køreplan: 60 % (6/10). Næste er punkt 7: login, tastatur og fokus. Ønskelisten venter. Egen HA/telefon, kontoforbindelser og fysisk print er fortsat særskilte ejertrin.
