# Valgfri Google Drive og QR

[English](GOOGLE-DRIVE.en.md) · [Detaljeret dansk kontoguide](../distrikt/GOOGLE-DRIVE-OPSAETNING.md)

LTM fungerer uden Google. Forbindelsen er kun nødvendig, hvis gennemgåede PNG-kort skal deles med et stabilt QR-link. Alle med linket kan se billedet uden Google-login.

Databaser, forkyndere, udleveringer, noter og IB-liste uploades ikke af funktionen. Kortets synlige geografi og tilladte besøgspunkter er en del af billedet. Gennemgå derfor hele previewet.

## Digitalt kort i beta.12

Fra beta.12 har kortbilledet et nyt layout med tydeligt kortnummer/navn, stor kortflade og en lille miniature af printforsiden i hjørnet. Miniaturen bruger den samme blanke S-12-forside og samme vejlinjeformatering som printet, men bygges kun af de offentligt godkendte adresser. Den kopierer ikke et billede af dit private kort. IB-oplysninger, noter og kortholderdata indgår ikke.

Eksisterende QR-links og adgangscyklus bevares. Et ældre layout markeres under Deling og QR; vælg **Opdater Google Drive-upload**, kontrollér hele billedet og miniaturen, og godkend publicering. Layoutopdateringen starter ikke upload af sig selv. QR-linket åbner fortsat et PNG-billede på Google Drive; der oprettes ingen ny offentlig hjemmeside.

## 1. Opret egen Google-klient

Brug [Google Cloud Console](https://console.cloud.google.com/) med den ønskede konto. Opret et projekt, aktivér **Google Drive API**, og opret en OAuth-klient af typen **Desktop app**. Hent klientens JSON-fil. En webklient eller servicekonto er ikke den forbindelse, LTM bruger.

Gennemgå samtykkeskærm, målgruppe, testbrugere og publiceringsstatus efter Googles aktuelle krav. Eksterne OAuth-apps i testtilstand kan have refresh-tokens med syv dages levetid for dette scope. Følg den detaljerede kontoguide og Googles egne oplysninger; klient- og tokenfiler skal ikke i GitHub.

Forbindelsen bruger **drive.file** til filer, som appen opretter eller får adgang til. Den beder ikke om at læse alle kontoens filer. Projektets OAuth-status offentliggør ikke appens lokale databaser.

## Adgang følger udleveringen

Et godkendt kortbillede kan uploades og få en trykbar QR-kode, før kortet udleveres. Billedet opbevares da privat på din valgte Drive-konto. Når kortet udleveres i LTM, åbner appen offentlig læseadgang. Ved aflevering lukkes den igen. Gennemgået med **behold kort** holder adgangen åben. Ved genudlevering genåbnes samme godkendte fil uden nyt upload, så den trykte QR-kode bevares. Hvis Google ændrer selve visningslinket, markeres forsiden til genprint; kontrollér derfor QR efter første åbning.

Styringen sender kun anmodninger om filrettigheder til Google; den uploader ikke udlånsregistre eller kortholderens navn. Forældede billeder genåbnes ikke, før et nyt preview er godkendt. **Fjern offentlig adgang** er et manuelt stop, som forbliver aktivt indtil ny publicering.

Appen skal køre og kunne nå Google for at ændre adgangen. Kontrollen foregår i baggrunden, og netfejl eller afbrudt Google-forbindelse kan forsinke ændringen. Status viser afventende lukning og mislykkede forsøg; efter fem fejl bruges **Prøv adgangsændring igen**. En forsinket upload af et nyt billede udsætter ikke forsøget på at lukke det gamle billede ved aflevering. Lukninger prioriteres før genåbninger.

**Samme link gælder for alle, der har det.** Det virker også for en tidligere kortholder, når kortet genudleveres. Funktionen lukker mellem udlån; den giver ikke personlig adgang til kun den aktuelle kortholder. Allerede gemte billeder kan ikke trækkes tilbage. Kontoens ejer og personer med særskilt Google-adgang kan fortsat have adgang; læg ikke filen i en offentligt delt mappe eller giv adgang manuelt, hvis den skal følge LTM-styringen.

Når linket er lukket, vises Googles egen adgangsside. Modtageren kan muligvis anmode om adgang via Google. LTM ændrer ikke denne side eller dens tekst og godkender ikke anmodninger. En særlig side med beskeden om et ikke-udleveret kort kræver et særskilt offentligt indgangspunkt og er ikke indført her.

Afprøv med egen konto: klargør kortet, kontrollér QR før udlevering, udlever og kontrollér adgang i privat browser, aflever og kontrollér lukning, og genudlever med samme QR. Testen bruger kun et ufølsomt prøvebillede.


## 2. Forbind fra Mac eller Windows

Start `Forbind-Google-Drive.command` på Mac eller `Forbind-Google-Drive.cmd` på Windows fra programpakken. Vælg klientfilen. Log ind hos Google, vælg den rigtige konto, og godkend filadgangen. Google-adgangskoden indtastes kun hos Google.

Guiden bruger en midlertidig lokal adresse på **127.0.0.1**, PKCE og en tilfældig state-værdi. Der skal ikke åbnes en routerport. Resultatet gemmes normalt som `Distrikt-Google-forbindelse.json` i Downloads.

## 3. Importér forbindelsen privat

Åbn **Indstillinger → Deling og QR** i den installerede app, og vælg forbindelsesfilen. Kontrollér den viste konto, og slet filen fra Downloads bagefter.

Filen giver fortsat adgang og skal behandles som en adgangskode. Den må ikke sendes til AI eller uploades i GitHub. Forbindelsen ligger adskilt fra databaserne og følger ikke med appens eksport eller HA-backup. Ved flytning skal kontoen derfor forbindes igen.

## 4. Publicér ét gennemgået kort

1. Åbn et kort med gemt geografi og besøgspunkter.
2. Vælg publicering/opdatering til Google Drive.
3. Vent på preview, og kontrollér hele billedet, kortnummer/navn og IB-påmindelsen.
4. Godkend publicering udtrykkeligt. Serveren uploader det godkendte billede.
5. Følg status under **Deling og QR**, og brug kortets QR-kode.
6. Inden kort udleveres, bør linket åbnes uden Google-login, og den trykte QR afprøves.

Det er læseadgang til et billede, ikke en interaktiv distriktsapp. Billedet kan gemmes og videresendes.

## Opdatering og flytning

Næste godkendte publicering opdaterer samme Drive-fil og bevarer linket. Slet ikke filen manuelt, hvis de trykte QR-koder skal virke.

Relevante adresse-/IB-ændringer gør billedet forældet. Appen forsøger at fjerne gammel offentlig adgang, når Google kan nås. Det sker ikke nødvendigvis straks og kan ikke tilbagekalde downloadede kopier. Dan og godkend et nyt billede i browseren. Efter fem mislykkede uploadforsøg kræves den viste handling til nyt forsøg.

Afbrydelse af Google stopper uploads, men fjerner ikke allerede offentliggjorte filer. Fjern først deres offentlige adgang, hvis de skal trækkes tilbage.

Ved flytning beholdes samme Google-konto og klient, hvis QR-links skal bevares. Dataeksporten indeholder filnumre, men ikke login. En anden konto kræver en bevidst fjernelse og ny publicering med nye links.

## Officielle kilder

- [OAuth til installerede programmer](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Udløb af refresh-tokens](https://developers.google.com/identity/protocols/oauth2#expiration)
- [Drive-scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)
- [Fildeling](https://developers.google.com/workspace/drive/api/guides/manage-sharing)
