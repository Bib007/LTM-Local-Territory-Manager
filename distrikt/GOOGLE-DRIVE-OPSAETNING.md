# Forbind Google Drive én gang

Brug den nye særskilte Google-konto til distriktskortene. HA kan bagefter uploade og genprøve uden din Mac. Modtagerne skal ikke logge ind for at åbne et delt kortbillede.

Forbindelsen skal sættes op på din egen computer og uploades til din lokale Distrikt-app — aldrig til ChatGPT. Ingen adgangskoder eller Google-forbindelsesfiler skal sendes til AI.

## 1. Opret Google-klienten

1. Log ind med den nye konto på https://console.cloud.google.com/ og opret et projekt, fx Distrikt.
2. Find APIs & Services / API'er og tjenester → Library / Bibliotek. Aktivér Google Drive API.
3. Åbn Google Auth Platform / OAuth consent screen. Opret appens navn og kontaktmail. Brug External som målgruppe, hvis du har en almindelig Google-konto.
4. Opret en OAuth client under Clients / Credentials. Vælg **Desktop app** som type, ikke Web application eller Service account. Kald den fx Distrikt-forbindelse.
5. Hent klientens JSON-fil til din computer.
6. Ved første test kan din konto sættes som testbruger. Før varig brug skal OAuth-appens publiceringsstatus ændres fra Testing til In production i Audience / Målgruppe, og forbindelsesguiden køres igen. Ved Testing udløber denne type refresh-token efter 7 dage.

Publiceringsstatus for OAuth-klienten betyder ikke, at din database eller dit program bliver offentliggjort. Guiden anmoder kun om drive.file: adgang til filer denne app opretter eller får særskilt adgang til. Den anmoder ikke om adgang til hele drevet.

Google kan ændre menunavne eller stille yderligere opsætningskrav på din konto. Hvis din skærm afviger eller Google afviser opsætningen, stop dér og beskriv teksten uden at sende klient-/tokenfilen. Programmet er ikke knyttet til et fælles udviklerprojekt; du ejer selv Google-projektet.

## 2. Kør forbindelsesguiden på Mac eller Windows

Python er det samme, som bruges til desktop-versionen.

- Mac: åbn Forbind-Google-Drive.command.
- Windows: åbn Forbind-Google-Drive.cmd.
- Vælg den hentede JSON-klientfil i filvælgeren.
- Browseren åbner Googles login. Vælg den nye konto og godkend den anmodede filadgang.
- Guiden modtager svaret på en midlertidig 127.0.0.1-adresse på din egen computer. Ingen routerport skal åbnes.
- Filen Distrikt-Google-forbindelse.json gemmes normalt i Downloads/Overførsler.

Der bruges PKCE og en tilfældig state-værdi til loginforløbet. Din Google-adgangskode indtastes kun hos Google, ikke i Distrikt.

## 3. Forbind HA-versionen

Åbn Distrikts lokale webadresse (via VPN, hvis du er ude). Gå til Indstillinger → Deling og QR. Vælg Distrikt-Google-forbindelse.json. Appen kontrollerer forbindelsen og viser kontoen.

Slet forbindelsesfilen fra Downloads bagefter. Google-klientfilen kan hentes igen fra dit eget Cloud-projekt. Forbindelsesfilen indeholder vedvarende adgang og skal behandles som en adgangskode. Serveren gemmer forbindelsen separat fra databaserne og inkluderer den ikke i appens dataeksport eller HA-backup.

## 4. Publicér første kort

1. Åbn et distriktskort med gemt geografi og adresser.
2. I den geografiske visning: vælg Publicér / opdater på Google Drive.
3. Appen indlæser OpenStreetMap, tilpasser udsnittet og viser et preview. Kontroller det.
4. Marker godkendelse, og publicér. HA gemmer billedet i køen og håndterer upload og rettigheder.
5. Under Deling og QR vises kortet som Publiceret. QR-koden vises nu automatisk nederst til højre på kortets forside, også ved print på fortrykte kort. Åbn kortet → Print forside. Du kan desuden hente QR-koden eller printe et særskilt mærke.
6. Test preview-linket i et privat browservindue uden Google-login, og scan QR-koden fra telefonen. Dette er den afsluttende kontrol med din rigtige konto.

Deling sættes til enhver med linket, kun læseadgang, uden offentlig søgbarhed slået til i Drive. Et link kan stadig videresendes, og modtageren kan gemme billedet. Google Drive bruges som billedvisning; det er ikke en interaktiv distriktsapp med vej-dropdown.

Appen opdaterer den eksisterende Google-fil ved næste publicering og beholder dens filnummer/link. Slet ikke filen manuelt i Drive, hvis en trykt QR-kode skal blive ved med at virke. Filerne har genererede navne; find et kort via appens link frem for filnavnet.

## Automatisk upload og ændringer

Billedet dannes og godkendes i browseren. Derefter foregår upload og genforsøg på HA, også når browseren/Mac lukkes. Køen gemmes i den eksisterende kortbilleder.sqlite3, separat fra selve kortregistrene. Højst fem automatiske uploadforsøg; derefter vælger du Prøv upload igen.

Relevante kortændringer, bl.a. adressevalg og IB, gør det publicerede billede forældet. HA fjerner den offentlige adgang til det gamle billede ved næste kontrol, hvis Google kan nås. Der kan gå lidt tid, og downloadede kopier kan ikke trækkes tilbage. Fejl ved fjernelse vises; efter fem mislykkede forsøg skal forbindelsen kontrolleres og fjernelsen prøves manuelt.

Dan og godkend et nyt billede fra kortvisningen. Det genåbner samme fil/link. Automatisk generering af nye OpenStreetMap-billeder uden en åben browser er ikke implementeret. Der foretages ingen skjult massehentning af OSM-kortfliser.

## Afbrydelse, overdragelse og flytning

Fjern offentlig adgang for hvert kort før du afbryder Google, hvis billederne ikke længere må kunne åbnes. Afbryd Google-forbindelsen stopper upload, men fjerner ikke allerede delte filer.

Behold samme Google-konto og samme OAuth-klient, når hovedsystemet flyttes fra HA til Mac/Windows eller til en ny HA-maskine. Importer data, kør forbindelsesguiden igen, og publicér kontrollerede billeder. Filnumrene følger med dataeksporten. Skift til en anden Google-konto kræver først fjernelse af eksisterende deling og vil give nye filer/QR-links. Ved overdragelse af ansvaret er en særskilt konto derfor praktisk.

Officielle tekniske kilder:
https://developers.google.com/identity/protocols/oauth2/native-app
https://developers.google.com/identity/protocols/oauth2#expiration
https://developers.google.com/workspace/drive/api/guides/api-specific-auth
https://developers.google.com/workspace/drive/api/guides/manage-sharing
https://developers.google.com/workspace/drive/api/reference/rest/v3/files/update
