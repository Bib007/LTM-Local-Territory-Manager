# Privatliv og datastrømme

[English](PRIVACY.en.md)

Maskinen, som kører Python-appen, opbevarer de private SQLite-filer. Desktopversionen bruger en lokal forbindelse. HA-versionen bruger den valgte private adresse, appens eget login og LAN/VPN. Appregistreringer sendes ikke til udvikleren, telemetri eller en AI-tjeneste.

| Handling | Hvad forlader maskinen | Modtager |
| --- | --- | --- |
| Almindelig redigering af kort, forkyndere, IB og udleveringer | Intet til udvikleren | Kun den lokale server |
| Visning af OpenStreetMap | Kortflisernes koordinater og almindelige forbindelsesoplysninger, som viser det betragtede område | OpenStreetMap |
| Online vejforslag | De offentlige vej-/postnummerdele, der søges efter | Adressetjenesten |
| Hentning af adresser og bygninger | Vej/postnummer eller et geografisk rektangel | Officielle danske adressetjenester / OSM |
| Valgfri Google-forbindelse | OAuth-godkendelse og API-kald | Google |
| Godkendt offentligt kort | Et gennemgået PNG-billede med kortnummer/navn, grænse og tilladte besøgspunkter | Den valgte Google Drive-konto |
| Privat backup | En fil, der hentes til browser/enhed | Det sted, hvor operatøren efterfølgende gemmer den |

Offentlige PNG-billeder indeholder ikke IB-liste, forkyndernavne, udlånsdata, noter eller databasefiler. IB-punkter, ignorerede og nedlagte adresser udelades. **Synlige besøgspunkter og grænser kan stadig være følsomme.** Gennemgå hele billedet, før det godkendes. Enhver med det offentlige link kan se, kopiere og videresende billedet.

IB-ændringer kræver et nyt billede dannet i browseren og en ny godkendelse. Serveren kan uploade et godkendt billede, men danner ikke selv nye OSM-billeder. Fjernelse af forældet offentlig adgang kræver kontakt til Google. Følg delingsstatus og løs eventuelle fejl.

Webdemoen har opdigtede data og gemmer ændringer i den enkelte browser. Den har ingen privat import, rigtig Google-publicering eller forbindelse til en installeret app. Webværten modtager almindelige webforespørgsler; browserens demotilstand er ikke en delt serverdatabase.

Offentlig kildekode og installationspakker indeholder programfiler og tomme formularer. Lokale databaser, rigtige geografiske filer, private kortbilleder, adgangskoder og forbindelsesfiler skal blive på eget system. Den offentlige programudgave bygger på en gennemgået filsamling med en selvstændig historik.

Lokal drift kan begrænse deling og give kontrol. Den dokumenterer ikke i sig selv lovmæssig overholdelse. Følg gældende regler, lokale instruktioner og passende praksis for adgang, opbevaring og sletning. Dette dokument beskriver programmet og er ikke juridisk rådgivning.

Private sikkerhedskopier kan indeholde data længere end appens 48 timers gendannelsesvindue. Gamle kopier skal håndteres særskilt. Del aldrig rigtige registreringer i fejlmeldinger eller AI-samtaler.
