# Adressekilde før januar 2027

Status 17.10.2026: overgangen er implementeret til beta.8. En gemt egen Datafordeler-nøgle aktiverer DAR GraphQL til vej-, postnummer- og grænsehentning. Programkontrollen bruger fiktive svar; levende skema/data med ejerens nøgle og HA/browser kontrolleres særskilt i den lokale installation.

## Kilder og frist

| Del | Aktuel kode og beslutning |
| --- | --- |
| Kortbaggrund | OpenStreetMap er standard. Fliser erstatter ikke strukturerede adresser. Lokale data og reservevisning bevares. |
| Adresseforslag | Adressevælger er stadig en særskilt tjeneste. Dens varslede brugerstyring ultimo 2026/primo 2027 kræver særskilt opfølgning. |
| Vej, postnummer og grænse | Med egen nøgle: DAR GraphQL v3. Uden nøgle: hidtidig Adressevælger/DAR REST. REST er varslet udfaset 15.01.2027. |
| Credentials | Egen nøgle indtastes kun i lokal LTM. Ingen fælles nøgle, credentials i GitHub eller AI-adgang til ejerens konto. |

Se [egen nøgle og brugervejledning](DATAFORDELER.md), [English](DATAFORDELER.en.md) og [betaens testliste](BETA-NOTES.md).

## Implementerede dele

- `address_source.Datafordeler`: fast officiel vært, afviste redirects, timeout og begrænset svarstørrelse. Nøgle gemmes separat fra SQLite/portable backups efter kontrol. Providerfejl gengives ikke råt. HTTP 408/504 og forbindelsestimeout har særskilt type til den eksisterende afgrænsede opdeling af grænseudsnit.
- `dar_paging.collect_pages`: kræver komplette nodes/pageInfo, terminal side, gyldige og forskellige ID'er samt cursors uden cyklusser. Deldata med GraphQL-fejl, grænseoverskridelse og afbrydelse returnerer ikke et halvt resultat.
- `dar_query.DarQuery`: eksplicitte flade projektioner af Adresse, Husnummer, Adressepunkt, NavngivenVej og Postnummer. Alle opslag bruger status 3 og samme registrerings-/virkningstidspunkt. Filterværdier og cursors escapes som strengliteraler. Svar skal svare til forespørgslens scope.
- `collect_many`: op til ti lighedsopslag grupperes med aliases; hver alias beholder egen komplet paginering. 25 enkelt-ID-opslag kræver tre anmodninger i prøven. Manglende aliases/obligatoriske ID'er, dubletter og samlede grænser giver fejl. Der antages ikke udokumenterede IN-filtre.
- `collect_bbox`: afgrænsede rektangler på højst 9 km² i EPSG:25832. Den dokumenterede within-operator bruges med én centimeters udvidelse for at medtage kantpunkter; der filtreres lokalt tilbage til det oprindelige inklusive rektangel. Ukendt CRS, ugyldig dimension/geometri og punkter uden for det forespurgte område afvises.
- `dar_join.join_addresses`: komplette flade lister sammenkobles lokalt via ID'er. Normaliseret adresseformat, `dar:`-ID'er, adgangsadresse-ID, etage/dør og XY/XYZ-punkter bevares. Manglende/inaktive relationer og ugyldige koordinater afviser resultatet før import.
- `dar_adapter.DarAdapter`: finder postnummerets veje via husnumre og vej-ID'er; samler komplette veje og geografiske udsnit. Flere officielle vej-ID'er med samme navn/postnummer behandles som én lokal kontrol af udgåede adresser. Husnumre uden aktuelle adresser får ikke opdigtede boliger.
- `dar_download.DarDownload`: kobler adapteren til eksisterende transaktioner, fremdrift, pause og genstart. Officielle vejlinjer konverteres lokalt i XY/XYZ. En komplet vej/et komplet udsnit og dets checkpoint gemmes samlet.

## Checkpoints og lokale ændringer

Kildemarkøren er `dar-graphql-v3` eller `dar-rest-v3`. Et ældre checkpoint uden markør behandles som REST. Genoptagelse kræver samme kilde og kontrollerede skemafingeraftryk; ellers gives en fejl før ændring af checkpoint eller lokale adresser. Brugeren kan vælge ny opdatering eller gendanne forbindelsen. Skemaændring under et opslag afviser også det igangværende svar.

Færdige veje/udsnit springes over ved genstart; ufærdige dele bruger det gemte tidspunkt. Kilde-/adgangsfejl stopper ved den aktuelle del. Grænsetimeout kan bruge den eksisterende begrænsede opdeling til mindre udsnit. Der foretages ingen lydløs tilbagevenden til REST efter en fejlet GraphQL-hentning.

Postnummeropdateringer og grænseopdateringer bevarer den eksisterende kontrol af nye, ændrede og udgåede adresser. Private kort, udlån, forkyndere og IB berøres ikke af kildeopslagene. Den præcise distriktsgrænse sendes ikke; kun rektangulære udsnit bruges eksternt, og polygonfiltreringen sker lokalt.

GraphQL-fuldstændighed afhænger af kildens korrekte sideoplysninger og reference-ID'er; der er ikke tilføjet et uafhængigt GraphQL-kontroltal svarende til REST-count. Alle efterspurgte nødvendige relationer kontrolleres, før enhedens resultat returneres.

## Verifikation og resterende ejertrin

Fiktive prøver omfatter flere sider, aliases, etage/dør, postnummerkrydsende veje, samme navn med flere vej-ID'er, manglende relationer, ukendte koordinater, delvise fejl, timeout, netfejl, ændret skema, gamle checkpoints, transaktionsfejl, kantpunkter, lokal polygonfiltrering og pause/genstart. REST-normalisering og den nye normalisering sammenlignes med opdigtede adresser.

Nøglen er ikke hentet fra ejerens installation, og der er ikke hentet autentificerede live data gennem AI. Næste særskilte ejertrin er en lille offentlig vej, derefter et postnummer/et lille grænseudsnit, med kontrol af husnumre, bogstaver og etage/dør. HA/browser og reelle servicebegrænsninger testes der. Adressevælgerens særskilte adgangsændring følges fortsat; W07 er derfor ikke markeret fuldt afsluttet alene på grund af kode og fiktive prøver.

## Primære kilder

- [DAR REST: udfases 15. januar 2027](https://confluence.kds.dk/pages/viewpage.action?pageId=16056323).
- [DAR GraphQL og adgang via IT-system/API-key eller OAuth](https://datafordeler.dk/dataoversigt/danmarks-adresseregister-dar/dar-graphql/).
- [DAR GraphQL-felter, geografi og kendte relationer](https://confluence.kds.dk/pages/viewpage.action?pageId=187105632).
- [GraphQL: endepunkter, paging og autentifikation](https://confluence.kds.dk/pages/viewpage.action?pageId=187105434).
- [Adressevælgerens brugerstyring og token](https://confluence.kds.dk/display/ADV/Brugerstyring).
