# W101 · QR-adgang med udløb

Undersøgt 24.10.2026. Dette er en vurdering af mulighederne; LTM's nuværende deling er ikke ændret.

En anden tjeneste kan give tidsbegrænset adgang. En almindelig QR-kode kan dog kopieres, ligesom oplysningerne i den kan læses. En hemmelig kode i QR-koden kan beskytte mod at gætte adressen, men giver ikke i sig selv bevis for, at nogen står med det oprindelige papir. Det er vores tekniske vurdering af en almindelig QR-kode med statiske oplysninger, ikke en påvist garanti fra en udbyder.

## To forskellige mål

| Mål | Mulighed | Begrænsning |
| --- | --- | --- |
| Et kortlink virker kun i fx tre timer | Privat billedlager med et signeret link, fx Amazon S3 | AWS dokumenterer både udløb og, at enhver med det gyldige link har adgang. Det kan videresendes inden udløb. |
| Det almindelige sidelink er ikke nok; telefonen skal først have adgang | En særskilt adgangsside kan udstede en kortvarig browsersession efter kontrol af en kode. CloudFront har signerede cookies som byggesten. | Der skal bygges en adgangskontrol. En videresendt QR-kode kan stadig give adgang, medmindre der også er fx login, særskilt godkendelse eller engangsbrug. |

AWS er et dokumenteret eksempel på en anden tjeneste, ikke en valgt leverandør. Ingen konto, betaling, upload eller prøve med rigtige kort er oprettet.

Google Drive understøtter udløb på rettigheder til bestemte brugere og grupper. Den dokumenterede udløbsindstilling gælder ikke offentlig adgang for alle med linket. Den nuværende offentlige PNG-adgang kan derfor ikke få en personlig tre-timers session alene ved at sætte den indstilling.

## Hvad der skal vælges før udvikling

Skal de tre timer begynde ved udlevering af kortet eller ved telefonens første åbning? Skal samme trykte QR-kode kunne bruges igen en anden dag? Skal adgang knyttes til en person, eller er en kortvarig adgang på telefonen tilstrækkelig?

En løsning med en kortvarig browsersession kommer nærmest ønsket om, at det almindelige sidelink ikke er nok. Den må stadig ikke beskrives som umulig at dele. Udløb forhindrer nye hentninger; et billede, der allerede er vist eller gemt, kan ikke trækkes tilbage fra modtageren.

W101 forbliver åben til valg af den ønskede adfærd. En eventuel løsning skal vurderes sammen med fremtidig adgangsstyring og afgrænses til godkendte kortbilleder. IB, forkyndere og den lokale administration skal ikke flyttes til en ny tjeneste.

## Primære kilder

- [DENSO WAVE: QR-kodens egenskaber](https://www.qrcode.com/en/about/).
- [Amazon S3: Signerede links, udløb og adgang for den, der har linket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html).
- [Amazon CloudFront: Adgang med signerede cookies](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-signed-cookies.html).
- [Google Drive: Udløb på delingsrettigheder](https://developers.google.com/workspace/drive/api/guides/manage-sharing#set_an_expiration_date).
