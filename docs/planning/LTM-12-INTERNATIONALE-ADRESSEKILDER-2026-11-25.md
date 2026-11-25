# LTM #12 / W128 – International adressehentning, kildeafprøvning (2026-11-25)

Opfølgning på [W128](INTERNATIONALE-ADRESSER-OG-MIGRERING-2026-11.md). Research og lokal syntetisk prototype, ikke produktionsintegration, leverandørkontakt eller release.

## Kilder og anbefaling

| Kilde | Områdeudtræk, aktualitet, dækning | Vilkår og begrænsninger |
|---|---|---|
| [US DOT NAD](https://www.transportation.gov/gis/national-address-database) | [Officiel FeatureServer/0](https://services.arcgis.com/xOi1kZaI0eWDREZv/ArcGIS/rest/services/Address_Points_from_National_Address_Database_view/FeatureServer/0), punktdata, enkelte underenheder; senest dokumenteret datasæt 30. september 2026, max 2.000 poster/svar. Periodisk, ikke alle delstater fuldt dækket. | [Officielle vilkår](https://www.transportation.gov/mission/open/gis/national-address-database/national-address-database-nad-disclaimer): public domain, ingen dækningsgaranti, særlige regler ved brug som mailingliste. Afklar anvendelse inden drift. |
| [Overture Maps Addresses](https://docs.overturemaps.org/guides/addresses/) | Gratis offentlige GeoParquet-filer på AWS/Azure; officiel CLI med bbox, DuckDB med geografisk filter. Månedlige releases, stadig alpha. [18. november 2026](https://docs.overturemaps.org/blog/2026/11/18/release-notes/): 475.239.461 poster; vejnavn 98,52 %, husnummer 92,83 %, postnummer 78,69 % (feltudfyldning, ikke dækningsprocent). | [Licenser](https://docs.overturemaps.org/attribution/) pr. oprindelig kilde; attribution og specialvilkår. [Schema](https://docs.overturemaps.org/schema/reference/addresses/address/) har unit, land, kilde-ID m.m. ID kan ændres; ingen automatisk sletning ved genhentning. |
| [OpenAddresses](https://openaddresses.io/) | Globale, normaliserede kildefiler, forskellig aktualitet og dækning. Gratis GeoJSON, [specialeksport er en backer-funktion](https://github.com/openaddresses/batch/blob/master/api/API.md); programmatisk batch-API dokumenterer token. | [Originale licenser](https://github.com/openaddresses/openaddresses) bevares. Download kildefiler og filtrér lokalt, ingen afhængighed af betaling. |
| [Frankrig BAN](https://adresse.data.gouv.fr/outils/telechargements) | Daglige nationale/departementale CSV-filer, WFS opdateret to gange ugentligt, én position pr. adresse; ikke bevis for lejlighedsdækning. | [Licence Ouverte 2.0](https://www.data.gouv.fr/datasets/base-adresse-nationale). |
| [Norge Kartverket/Matrikkelen](https://www.kartverket.no/api-og-data/eiendomsdata/apent-tilgjengelige-data-og-tjenester) | Officielle adresseudtræk via Geonorge, valg af geografisk område, GML/SOSI; normalt daglige opdateringer. | Åbne data; verificér specifikt datasæts licens/attribution og enhedsdækning. |
| [Nederlandene BAG](https://api.pdok.nl/kadaster/bag/ogc/v2?f=html&lang=en) | Officiel OGC API med bygninger, opholdsobjekter og adresseoplysninger; verificér aktuelle samlinger, bbox/sidegrænser, opdatering og komplette enheder. | PDOK-tjenesten angiver Public Domain Mark 1.0. |
| [OSM/Geofabrik](https://download.geofabrik.de/) | Regionale PBF-udtræk normalt dagligt; offline filtrering. Ufuldstændige addr-tags; bygning er ikke adresse. | [ODbL](https://www.openstreetmap.org/copyright), attribution/share-alike afklares før kombination/eksport. [Nominatim](https://operations.osmfoundation.org/policies/nominatim/) må ikke bruges til systematisk adresselistehentning. |

Anbefaling (ikke endeligt kildevalg): pilotér NAD for USA, Overture som fælles international adapter for lande uden godkendt bedre officiel kilde. Tilføj BAN, Norge og BAG efter behov. OpenAddresses til supplerende offline import efter licenskontrol; undgå at tælle samme oprindelige kilde to gange. DAR for DK og manuel supplering uændret. Gratis data betyder ikke garanteret gratis hosting, storage, trafik eller drift. Ingen betalt API som automatisk fallback.

## Foreslået integration

- Bevar eksisterende DAR-rute/flow. Ny adaptergrænseflade fetch(area, snapshot, checkpoint) med WGS84 (lon, lat), kildestatus, side-/filidentitet, dokumenteret total og afslutningssignal. Adressemodel: country, locality/region, postcode (tekst), street, number (tekst), unit (tekst eller null), coordinates, provider/dataset/record_id, version, source_date, license, attribution. Lokalt LTM-ID uafhængigt af kilde-ID. Undersøg eksisterende dansk koordinat-/postnummer-validering før international integration.
- NAD: envelope + inSR/outSR=4326; hent count og objekt-ID'er, hvis tjenesten bekræfter støtte, opdel deterministisk i batches <= 2000, kontroller alle ID'er og transfer-limit. Hvis ID-liste ikke kan verificeres, del bbox rekursivt med kontrolleret overlap, stop ved uafklaret truncering. Bekræft faktisk API-kapabilitet og snapshot/ændringer under hentning før implementering. Overture: pin release 2026-11-18.0 i pilot, filtrér GeoParquet bbox ved overlap (ikke strikt containment af lagret bbox), derefter punkt i polygon; undgå globalt download. OpenAddresses: licensgodkendte kildefiler med versionsmetadata.
- For alle: indre punkter foreslås, ydre udelades, præcis grænse til manuel afgørelse (forslag, ikke ejerbeslutning). Afvis ugyldig geometri, koordinater, forkert land og manglende nødvendig identitet; vis uklare poster til gennemgang. Håndtér huller/multipolygon, datolinje og grænser mellem lande eksplicit eller afvis med forklaring før forespørgsel. Forskellige unit-værdier må aldrig slås sammen; match samme kilde-ID først, derefter normaliseret land/lokalitet/postnummer/vej/nummer/enhed og geografisk plausibilitet; usikre match og baseadresse vs. enhed til gennemgang. Bevar provenance.
- Checkpoint knyttet til polygonfingeraftryk lokalt, kilde, release, side/ID. Genoptag kun samme snapshot; ved ændring genstart efter godkendelse. Ufuldstændig/afbrudt hentning må ikke markeres komplet eller slette adresser. Vis teknisk status separat fra kilde-dækning, dato, licens, mangler, nye, dubletter og grænseposter. Gem først efter godkendelse, med versions-/konfliktkontrol og bevarelse af IB, manuelle poster, historik og udlån. Ingen automatisk genafsendelse af uafklaret skrivning.
- Databeskyttelse: hent helst offentlige regionfiler eller groft bbox direkte på lokal LTM-server og filtrér præcist lokalt. Ingen privat polygon, distriktsnavn/-ID, IB, bruger-, forkynder- eller udlånsdata i eksterne requests/logs. Eksterne udbydere ser stadig IP og evt. geografiske parametre; beskriv dette, minimér logs, ingen tredjepartstelemetri, begræns retention. Adskil offentlig cache fra privat database, behold kildeattribution ved visning/eksport. Licensvurdering inden sammenblanding, især ODbL.

## Lokal fiktiv prøve – gennemført 25. november

Python med Shapely 2.1.2, ingen netværkskald. Følgende er den udførte, selvstændige prototype (ikke en test af LTM-koden og ikke en live-kildetest). Alle rækker/ID'er og grænsen er opdigtede, koordinater bruges kun lokalt.

```python
from shapely.geometry import Polygon, Point
p = Polygon([(-100,40),(-99.99,40),(-99.99,40.004),
             (-99.996,40.004),(-99.996,40.01),(-100,40.01)])
rows = [('a','1','',-99.998,40.002),
        ('b','2','A',-99.998,40.006),
        ('c','2','B',-99.998,40.006),
        ('b','2','A',-99.998,40.006),
        ('d','3','',-99.992,40.008),
        ('e','4','',-100,40.003),
        ('f','5','',-99.98,40.002),
        ('g','6','',-99.996,40.007)]
x1,y1,x2,y2 = p.bounds
candidates = [r for r in rows if x1<=r[3]<=x2 and y1<=r[4]<=y2]
inside = {}; boundary = {}; outside = []
for r in candidates:
    pt = Point(r[3:])
    target = inside if p.contains(pt) else boundary if p.touches(pt) else None
    if target is None:
        outside.append(r[0]); continue
    target.setdefault(r[0],r)
assert len(candidates)==7 and set(inside)=={'a','b','c'}
assert set(boundary)=={'e','g'} and outside==['d']
assert len({(r[1],r[2]) for r in inside.values()})==3
assert p.is_valid
```

PASS: 8 inputrækker, 7 bbox-kandidater, 3 unikke indre, 2 på grænsen til manuel afgørelse, 1 uden for polygon, 1 uden for bbox, 1 dublet. To enheder på samme punkt bevaret. Kun dublet med samme ID afprøvet. Ingen rigtig adressehentning, data, API-ydeevne eller app-regression er verificeret.

## Næste testgate inden integration

1. Verificér NAD metadata/områdequery, ID/count, paging/transfer-limit og 0-resultat mod offentlig tjeneste med syntetisk valgt område, kun aggregerede tal og ingen private data. Overture pin-release bbox og lokal polygon: sammenlign med et godkendt officielt register, registrér dækning af husnumre/enheder og kildedato; verificér licens og drift/ressourcebehov. Ingen live-test i denne opgave.
2. Mock flere sider, overlap, timeout, 429/5xx, manglende side, ugyldige felter, snapshot-skift, genoptagelse, totalmismatch og tomt/ufuldstændigt svar. Afvis falsk succes.
3. Test konkav polygon, huller, præcis kant, selvskæring, forkert CRS/land, koordinatorden, evt. datolinje, internationale postnumre (førende nul, alfanumerisk), unit og husnumre med bogstav. Test dubletter på tværs af kilder/ændrede ID'er, kolliderende unit, manuelle poster.
4. Test udenlandsk kort i UI: preview, status, afbrydelse, manuel supplering, godkendelse, samtidige ændringer, uafklaret gemning og eksport/backup med kildeangivelse; afvis ukendt licens til produktionsimport.
5. Dansk regression: DAR GraphQL, adressevælger, eksisterende checkpoints, redigering og manuel supplering, bevar IB/udlån/historik/backup. Netværksmock skal vise at kun offentlige geografiske parametre og nødvendige tekniske parametre sendes.
6. Ingen merge eller release. Før integration kræves målrettede app-tests med fiktive data, verificeret live-kildeadgang, licens-/privatlivsvurdering og fuld relevant DAR-regression. Før udgivelse gælder repoets normale release-gates.
