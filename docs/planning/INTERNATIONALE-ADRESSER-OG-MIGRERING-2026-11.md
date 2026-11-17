# W128 · Internationale adressekilder og begrænset migrering

**Undersøgt 17. november 2026. Status: kildebeslutning og eksperimentel, lokal formatadapter — ikke verificeret integration med andre platforme.** Leverandørkontakt er udtrykkeligt sat på vent. Der er ikke brugt private menighedsdata.

## Internationale, gratis adressekilder

| Førstepartskilde | Formater/adgang | Vurdering |
| --- | --- | --- |
| [OpenAddresses](https://openaddresses.io/) ([GitHub](https://github.com/openaddresses/openaddresses)) | Global samling af åbne adresselister; download af normaliserede data, koordinater og adressefelter. | Mulig fremtidig **lokal batchimport**. Vurder tilgængelighed, dubletter, datadækning og licens pr. oprindelig kilde; ikke garanteret komplet. |
| [Overture Maps Addresses](https://docs.overturemaps.org/guides/addresses/) ([dataadgang](https://docs.overturemaps.org/getting-data/), [licenser](https://docs.overturemaps.org/attribution/)) | **Alpha**-adressetema; cloud-GeoParquet og udtræk til GeoJSON via officiel klient. | Mange lande, men delvis dækning, varierende felter og kildeafhængige licenser. Ingen live-API i LTM. |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) ([Geofabrik](https://download.geofabrik.de/)) | Land-/regionudtræk som bl.a. .osm.pbf med eventuelle addr:-felter. ODbL. | Kan behandles offline, men adresser er ikke komplette alle steder. Fliser er **ikke** en adresseliste. Attribution/share-alike vurderes før brug. |
| [Officiel dansk DAR GraphQL](https://datafordeler.dk/dataoversigt/danmarks-adresseregister-dar/dar-graphql/) | Datafordeler med egen API-nøgle; se [LTM's eksisterende dokumentation](../ADRESSEKILDE-2027.md). | **Uændret**. Dansk adressehentning, checkpoints og adgang skal bestå regression før enhver fremtidig international implementering. |

[OSMF's offentlige Nominatim-politik](https://operations.osmfoundation.org/policies/nominatim/) forbyder personlige/fortrolige data og bl.a. autocomplete og systematisk scraping. **Ingen personoplysninger til OSM.** Denne PR læser kun lokale filer; ingen søgning, upload, eksternt kortopslag eller adresseimport til produktion.

## Førsteparternes dokumenterede migreringsformater

| Retning | Dokumenteret af platformen | Afgrænsning |
| --- | --- | --- |
| Territory Helper → LTM | TH [eksporterer distrikter som KML](https://www.territoryhelper.com/Help/TerritoryExport). LTM har allerede lokal KML-import med forhåndsvisning og efterfølgende manuel gemning. | Den eksisterende funktion bevares; adapterens **th-to-ltm** oversætter kun én simpel KML-polygon til GeoJSON uden fritekst. |
| LTM → Territory Helper | TH [importerer KML/KMZ-grænser](https://www.territoryhelper.com/Help/TerritoryImport). | **ltm-to-th** eksporterer almindelig KML 2.2 med én polygon, ikke TH-native data eller hele historikken. Målsystemets import er ikke faktisk afprøvet. |
| NW Scheduler → LTM | NW's [Territories CSV](https://nwscheduler.com/how-to/import-territories-from-csv/) kræver engelske kolonner og dokumenterer Number, CategoryCode, Suffix og Boundary med kommaseparerede par [longitude,latitude] og én form. | **nws-to-ltm** accepterer kun disse felter og præcis én CSV-række; øvrige felter afvises. |
| LTM → NW Scheduler | Samme officielle CSV-felter. Number skal være numerisk; kategori + nummer kan ramme et **eksisterende** distrikt, der så opdateres. | **ltm-to-nws** genererer kun Territory CSV-polygon; kontrollér identiteter og tag backup **før** import i NW. |
| Territory Helper → NW Scheduler direkte | NW's [særlige TH-guide](https://nwscheduler.com/how-to/import-export/import-territories-from-territory-helper/) kræver **TH JSON, ikke KML** til distrikter. TH's Locations/Assignments Excel gemmes som **CSV UTF-8** til særskilte TH-importvalg. | JSON-filschema, semantik og en tabsfri returvej er **ikke verificeret**; ingen JSON-konverter er implementeret. |
| Adresser/historik begge veje | TH [Locations-import](https://www.territoryhelper.com/Help/LocationsImport) anvender Excel-skabelon med bl.a. krævede Latitude, Longitude, Address, Number, Street Name. NW's [generelle CSV-guide](https://nwscheduler.com/how-to/import-territories-from-csv/) oplister særskilt adresser (TerritoryAddressID, Type, Status, Latitude, Longitude, Street, PostalCode, Phone, Notes) og assignments. | **Ikke implementeret.** Manglende dokumenteret tabsfri mapping af personfelter, IB, gennemgange, tildelinger, ID'er og konflikter; NW advarer om, at ikke alle eksportfelter kan genimporteres. |

### Officielle eksempler kontra syntetiske testdata

* NW's [officielle Boundary-eksempel](https://nwscheduler.com/how-to/import-territories-from-csv/) indeholder en lukket kæde af koordinatpar og henviser til eksport fra NW for en CSV-prøve. Det eksempel er ikke vores fiktive prøve.
* TH [tilbyder en Excel-sample i selve importvisningen](https://www.territoryhelper.com/Help/LocationsImport), men den kunne ikke verificeres offentligt uden konto. Ingen udokumenterede kolonner er antaget i kode.
* Overtures [officielle Quickstart](https://docs.overturemaps.org/getting-data/) demonstrerer geografiske GeoJSON-udtræk. Det beviser ikke en import til LTM.
* **Egen opdigtet fixture, ikke en officiel eksportfil**: Number=17, CategoryCode=C, Suffix=A, polygon [[10,55],[10.01,55],[10.01,55.01],[10,55.01],[10,55]]. Se distrikt/tests/test_territory_boundary_adapter.py.

## Lokal, aktivt godkendt formatadapter

scripts/territory_boundary_adapter.py behandler kun **én** grænse inden for **LTM's aktuelle danske koordinatvalidering**. International adresseimport er *ikke* tilføjet. Den genbruger den faktiske boundary_import.preview_boundary til WGS84, antal hjørner og polygonvalidering og afviser ekstra data frem for at miste oplysninger lydløst. Maks. 2 MB kildefil. KML-fritekst/navne kopieres ikke; kun offentlige, korte distrikts-ID'er fra NW kan bevares. Programmet har **ingen netværkskald**.

Kør eksempelvis først en forhåndsvisning — den skriver **ingen fil**:

    python3 scripts/territory_boundary_adapter.py nws-to-ltm fiktiv.csv graense.geojson
    python3 scripts/territory_boundary_adapter.py th-to-ltm fiktiv.kml graense.geojson
    python3 scripts/territory_boundary_adapter.py ltm-to-th graense.geojson graense.kml
    python3 scripts/territory_boundary_adapter.py ltm-to-nws graense.geojson graense.csv --number 17 --category-code C --suffix A

Kontrollér retning, distriktsnummer og antal hjørner. Gentag derefter **præcis den samme kommando med** --approve KODEN-FRA-FORHAANDSVISNING. Koden er bundet til retning og outputindhold. Ingen eksisterende målfil eller kildefil overskrives. Kontrollér resultatet igen i målprogrammets **egen** forhåndsvisning/import og godkend eksplicit. LTM's egen KML/GeoJSON-import kræver separat valg af grænse og gemning. TH og NW's faktiske indlæsning er ikke testet med konto.

## Test og release-stop

    python3 -m unittest discover -s distrikt/tests -p 'test_territory_boundary_adapter.py' -v
    python3 -m unittest discover -s distrikt/tests -p 'test_boundary_import.py' -v

Fiktive regressionstests dækker NW CSV ⇄ GeoJSON, KML ⇄ GeoJSON, præcist medlemskab/geometri, ukendte/fortrolige kolonner, flere rækker, ugyldig/åben polygon, udenlandske koordinater, størrelsesloft, ingen netværk, visning før skrivning, forkert godkendelseskode og ingen overskrivning.

**Gate:** Koordinatoren må ikke frigive funktionaliteten som *verificeret migration*, før relevante tests er grønne på den eksakte PR-commit, import/eksport er prøvet manuelt med fiktive data på aktuelle versioner af begge målplatforme, identitetsmatch/backup er kontrolleret, og DAR-flow er regressionsgodkendt. Indtil da er dette alene en **dokumenteret filformatkonverter**. Ingen merge, release, brugerdata, leverandørkontakt eller ny produktionsintegration i denne PR.
