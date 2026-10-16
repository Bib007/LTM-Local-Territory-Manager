# Valgfri Google Drive og QR

[English](GOOGLE-DRIVE.en.md) · [Detaljeret dansk kontoguide](../distrikt/GOOGLE-DRIVE-OPSAETNING.md)

LTM fungerer uden Google. Forbindelsen er kun nødvendig, hvis gennemgåede PNG-kort skal deles med et stabilt QR-link. Alle med linket kan se billedet uden Google-login.

Databaser, forkyndere, udleveringer, noter og IB-liste uploades ikke af funktionen. Kortets synlige geografi og tilladte besøgspunkter er en del af billedet. Gennemgå derfor hele previewet.

## 1. Opret egen Google-klient

Brug [Google Cloud Console](https://console.cloud.google.com/) med den ønskede konto. Opret et projekt, aktivér **Google Drive API**, og opret en OAuth-klient af typen **Desktop app**. Hent klientens JSON-fil. En webklient eller servicekonto er ikke den forbindelse, LTM bruger.

Gennemgå samtykkeskærm, målgruppe, testbrugere og publiceringsstatus efter Googles aktuelle krav. Eksterne OAuth-apps i testtilstand kan have refresh-tokens med syv dages levetid for dette scope. Følg den detaljerede kontoguide og Googles egne oplysninger; klient- og tokenfiler skal ikke i GitHub.

Forbindelsen bruger **drive.file** til filer, som appen opretter eller får adgang til. Den beder ikke om at læse alle kontoens filer. Projektets OAuth-status offentliggør ikke appens lokale databaser.

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
