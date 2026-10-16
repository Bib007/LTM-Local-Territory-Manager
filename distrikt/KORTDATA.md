# Kortbaggrunde fra 1.8.5

Kun lokale kortdata og OpenStreetMap-vejkort er tilgængelige. Luftfoto, hybrid og deres API-integration er fjernet. OpenStreetMap kræver ingen personlig kortnøgle. Hentning af adresser fra DAR er bevaret.

# Adressehentning fra 1.8.4

Status viser nu kontroltal eller adresseside samt sekunder med ventetid. For grænsehentning gælder 120 sekunders netværkstimeout uden data. Flere opslag kan være nødvendige for samme udsnit. Sæt på pause stopper mellem opslag og under genprøvningsventetid; det aktuelle netværksopslag skal først afsluttes eller få timeout. Tomme udsnit kræver kun kontroltallet. Mindre udsnit bruges stadig ved timeout, og fremgang gemmes. Den længere timeout er ikke garanti for en tilgængelig kilde.

PNG fra vejkort zoomer selv til hele kortet og beskærer overskydende omgivelser. Skift til Vejkort og vælg Gem PNG · OpenStreetMap. Eksporten venter på fliserne i det viste udsnit; fejl eller huller giver besked. IB, Se bort fra, nedlagte adresser og kortnoter medtages ikke.

# Timeout og mindre udsnit

Fra 1.8.3 opdeles udsnit, der får timeout, automatisk i mindre udsnit. Derfor kan samlet antal udsnit stige, fx fra 28 til 31. Hent / fortsæt alle adresser bruger de gemte checkpoints og genhenter ikke færdige udsnit. Højst to opdelingsniveauer; ved fortsat timeout på mindste udsnit stopper hentningen. De mindre forespørgsler kan hjælpe på tunge opslag, men kan ikke løse en utilgængelig datakilde.

# Ved gentagne kildefejl

Fra 1.8.2 stopper grænsehentningen ved et opslag, der fejler trods automatisk genprøvning. Den viser udsnitsnummer og årsag i slutbeskeden. Andre udsnit forsøges ikke automatisk i samme kørsel. Færdige udsnit er gemt. Brug Hent / fortsæt alle adresser senere for at fortsætte. Sæt på pause afbryder ventetiden mellem forsøg; et igangværende netværksopslag kan først afsluttes eller få timeout.

# Fortsæt en ufuldstændig grænsehentning

Åbn Samlet distriktsgrænse og vælg **Hent / fortsæt alle adresser**. Færdige udsnit hentes ikke igen; de resterende genprøves. Undlad **Opdater hele området**, når du blot vil fortsætte, da den starter en ny fuld opdatering. Hver offentlig DAR-forespørgsel genprøves højst to gange ved midlertidige fejl. En fortsat fejl betyder, at udsnittet stadig mangler — ikke at de allerede gemte adresser slettes. Detaljer findes ved hentestatus på grænsesiden.

# Kortdata i version 1.8.0

**OpenStreetMap-PNG:** Vælg Vejkort i en åben kortvisning, vis det ønskede udsnit, vent på færdig indlæsning, og tryk Gem PNG · OpenStreetMap. PNG'en genbruger allerede viste browserfliser; der køres ingen ekstra kildeanmodninger, zoomrunde, tilearkiv eller masseeksport. Bounds kommer fra netop denne visning, og raster/polygon/adresseprikker bruger samme Mercator-projektion. Synlig attribution og copyright-URL indgår. Ufuldstændige fliser/huller og browserens canvas-sikkerhedsfejl afvises. Lokale vektorer kan fortsat eksporteres uden internet.

## Valgfrie baggrunde

Lokale vektorfigurer er standard. Vejkort henter kun viste fliser fra `https://tile.openstreetmap.org/{z}/{x}/{y}.png` efter et aktivt valg. Browseren følger tjenestens cacheheaders; der er ingen forhentning eller offline-flisepakke. Synlig attribution og en origin-only Referer følger OSM's flisepolitik. OSM modtager IP-adresse, tilekoordinater og appens lokale origin, ikke token eller distriktsoplysninger.



Luftfoto er kontrolleret mod tjenestens dokumentation, men er ikke live-testet med en personlig nøgle. Kortnøglen er uafhængig af den eksisterende adresse-token. Den nye baggrund erstatter ikke DAR REST-adresseintegrationens varslede udfasning.

**Samlet grænse:** Hent / fortsæt alle adresser læser DAR REST gennem et omgivende rektangel i EPSG:25832, opdelt i 3 km udsnit. Præcis polygonfiltrering sker lokalt. Alle postnumre og kendte lejligheder i formen medtages. Hvert udsnit kontrolleres mod kildens antal; mangler/fejl vises, og færdige udsnit kan genoptages efter genstart. Officielle vejlinjer til de fundne adresser medtages. Helt færdige opdateringer markerer bortfaldne offentlige DAR-adresser indenfor som nedlagte; manuelle adresser og private kort/IB/historik bevares.

Forslaget fra fotoet er manuelt aftegnet og omtrentlig placeret med bymærker. Det er ikke en officiel grænse eller landmåling. Kontrollér før gemning og adressehentning. Upload af andre grænser kræver én GeoJSON Polygon i WGS84; billeder uden koordinater kan ikke importeres som en geografisk polygon.

Kun rektangelkoordinater og kildens tids-/sideparametre sendes ved grænsehentning, ikke selve polygonen. Den varslede DAR REST-lukning nedenfor gælder også denne nye hentning.

Kortmotoren er Leaflet 1.9.4, lokalt inkluderet med licens. Der bruges vektorfigurer for veje og bygninger samt husnummer-/adressepunkter. Eksterne kortbaggrunde er valgfrie; CDN, Google Maps-nøgle eller ny Python-afhængighed er ikke nødvendig. Hentede figurer og punkter kan bruges uden internet. Hentning af nye data kræver internet.

## Kilder og adgang

- **Hele postnummeret og lange veje:** DAR REST på Datafordeleren. Først hentes postnummerets officielle vejliste og vejlinjer, derefter gældende adresser for hver vej med sideopdeling. En vej kan krydse postnumre; adresser fra andre postnumre filtreres fra lokalt. Hver færdig vej gemmes sammen med et kontrolpunkt. Pause/fortsæt bevarer samme kildetidspunkt, mens Opdater alle starter et nyt udtræk. Fejl vises pr. vej.
- **Vejforslag og almindelige vejopslag:** Klimadatastyrelsens Adressevælger, inklusive opslag af adresser med id og alle adresser til et husnummer. Gældende selvstændige adresser med etage/dør tælles som hver sit besøg. Positionen fra EPSG:25832 omregnes lokalt til WGS84.
- **Veje og bygningsomrids:** OpenStreetMap via Overpass. Ét lille udsnit ad gangen, hentning ved brugerens handling, højst omtrent 20 km² og højst 45 vejnavne ved kombineret adressehentning. Der køres ikke parallelle områdedownloads i appen. Kilden er en gratis fællesskabstjeneste uden driftsgaranti.
- **Egne data:** Manuel lokal adresse, CSV eller GeoJSON. Importen går kun til den lokale server. Den uploades ikke til en ekstern tjeneste.

Pr. **6. oktober 2026** anbefaler KDS den offentlige standardtoken `adressevaelger123`; den anvendes i programmet. KDS har varslet brugerstyring senere. Et felt under Hent / importer kortdata kan gemme en ny egen token lokalt, hvis det senere bliver nødvendigt. Token returneres ikke i appens normale datarespons. Den kan findes i din egen private sikkerhedskopi og må ikke deles med AI.

**DAR REST udfases 15. januar 2027** ifølge KDS. Hele-postnummer-hentning og lange-veje-reserven i denne version kræver derfor senere en ny kildeintegration. GraphQL-efterfølgeren kræver autentifikation; den er ikke implementeret eller udgivet som anonym erstatning. Allerede hentede data virker fortsat lokalt. Adressevælgerens vejforslag er en separat tjeneste.

DAWA anvendes ikke: den lukkede 1. oktober 2026. Der bruges ikke private DAWA-erstatninger med ukendte abonnementer.

## Privatliv

Online vejforslag sender det skrevne offentlige vejnavn og postnummer under indtastning; de kan slås fra. Selve adresse-/kort-hentningen starter ved Hent eller ved Vis og vælg adresserne for en endnu ikke hentet vej. En vejhentning sender hele det offentlige vejnavn og postnummer til den officielle adressekilde; dit nummerinterval filtreres derefter lokalt. Hentning af vej-/bygningsdata sender et offentligt geografisk kortudsnit til OSM-kilden. Der sendes aldrig kortnummer, det gemte adressevalg, distriktsgrænser, forkyndere, IB eller gennemgangshistorik.

Der sendes også offentlige vej-id’er ved samlet postnummerhentning.

Alle resultatdata, adressevalg, tegning, dubletkontrol og vejlistesummering ligger på din Mac. Appen har ingen AI-forbindelse eller offentlig app-server. ZIP-udgivelserne indeholder kun program, skabeloner, dokumentation og fiktive tests.

## Lokal CSV

UTF-8, komma eller semikolon som separator. Felter:

| Felt | Betydning |
| --- | --- |
| road | Vejnavn, påkrævet |
| number | Husnummer, fx 42 eller 42B, påkrævet |
| postcode | Firecifret postnummer, påkrævet |
| lng | Længdegrad i WGS84, påkrævet |
| lat | Breddegrad i WGS84, påkrævet |
| floor | Etage, valgfrit |
| door | Dør, valgfrit |
| count | Antal besøg, normalt 1; valgfrit |
| type | Hus, Lejlighed, Lejlighedskompleks, Butik, Kontor, Virksomhed eller Andet; valgfrit |
| id | Stabil egen identitet; valgfrit |

Vejnavn/husnr/postnr/latitude/longitude og etage/doer accepteres også som alternative kolonnenavne. Brug ét punkt pr. selvstændig adresse/lejlighed. Hvis filen allerede har en samlet hus-række med count, må du ikke samtidig indlæse lejlighedsrækker for samme hus, som ville tælle dem to gange. Appen kan ikke udlede, om en samlet række også omfatter andre rækker.

GeoJSON skal være en FeatureCollection med Point-geometri `[lng,lat]` i WGS84 og samme felter under properties. Filgrænse: 12 MB, højst 20.000 poster pr. import. Importen valideres samlet; en ugyldig post ruller hele importen tilbage. En rå relationsopdelt DAR-fildownload med flere entitetsfiler er ikke dette format og kræver forbehandling.

## Kvalitet og grænser

Et adressepunkt på kanten af en grænse er medtaget. Hvis bygninger ligger hen over kanten, er det deres adressepunkter, der afgør valget. Et klik ved en bygningsfigur viser adresser inde i eller højst ca. 9 meter fra figurens hjørner; kontrollér selv den rigtige indgang. Der gøres ikke krav på officiel bygnings-/adressekobling fra GeoDanmark/BBR.

En automatisk grænse fra et adressevalg er en konveks omslutning med ca. 12 meters luft. Den er et forslag, der kan omfatte andre adresser og veje. Den beregner ikke matrikelskel, fortove eller terrængrænser. Du kan flytte hjørnerne eller tegne den igen.

Et områdedownload via navngivne OSM-veje kan mangle veje, adresser eller bygninger. “Auto huse” vælger kun de hentede adressepunkter; den gætter ikke manglende huse eller lejligheder. Ufuldstændige eller tvetydige vejopslag accepteres ikke som komplet vej. Ved fejl bevares eksisterende data. En delvis områdedownload kan stadig have gemt vektorer og de veje, der blev hentet uden fejl; manglende veje oplyses.

Vejteksten viser første–sidste husnummer, eventuelt lige/ulige, også hvis der er huller. Den udvider aldrig kortets medlemsliste. Besøgsantallet bygger udelukkende på de præcist valgte selvstændige adresser. Bogstavendelser er bevaret.

Mangler på kort omfatter hentede gældende adresser uden kort eller Se bort fra. Inden for kortgrænse filtrerer desuden til gemte polygoner. Et kort uden registreret adressevalg tæller ikke som adressernes ejer.

Gamle kort og deres besøgsantal ændres ikke automatisk ved nyt datadownload. Gem et nyt adressevalg på det samme kort for at anvende ændringer. IB og udleveringshistorik bevares. Der kan ikke gemmes en adresse, som allerede er på et andet kort eller et slettet kort i 48-timers gendannelse.

## Dokumentation

- OSM-flisepolitik: https://operations.osmfoundation.org/policies/tiles/

- Leaflet: https://leafletjs.com/reference og https://leafletjs.com/download.html
- DAWA-lukning: https://www.klimadatastyrelsen.dk/om-klimadatastyrelsen/nyheder/nyhedsarkiv/2026/jul/dawa-lukker-d-1-oktober-2026
- DAR REST og udfasning: https://confluence.kds.dk/pages/viewpage.action?pageId=16056323
- Adressevælger: https://confluence.kds.dk/pages/viewpage.action?pageId=234782998
- Adresseopslag: https://confluence.kds.dk/pages/viewpage.action?pageId=246743156
- Token/brugerstyring: https://confluence.kds.dk/display/ADV/Brugerstyring
- OSM/Overpass: https://wiki.openstreetmap.org/wiki/Overpass_API
- OSM-licens og attribution: https://www.openstreetmap.org/copyright
