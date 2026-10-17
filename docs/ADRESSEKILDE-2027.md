# Adressekilde før januar 2027

Kontrolleret 16.10.2026. Dette er en konkret overgangsplan. Lokal nøgleopsætning og forbindelseskontrol er implementeret til beta.7; selve adresseimportens overgang er endnu ikke gennemført.

## Hvad rammer LTM?

| Del | Nuværende kode | Fund og beslutning |
| --- | --- | --- |
| Kortbaggrund | `basemaps.js`: OpenStreetMap er standard | Fliser er et baggrundsbillede; de erstatter ikke præcise adresser med ID, etage og dør. OSM bevares som standard. |
| Søgning og enkeltvej | `geodata.py`: Adressevælger; DAR REST som støtte ved store veje | Adressevælger er en særskilt officiel tjeneste. Den anbefalede fælles token er fortsat dokumenteret; fremtidig brugerstyring er varslet ultimo 2026/primo 2027, uden fast dato i den læste vejledning. |
| Hele postnumre og samlet grænse | `postcode.py`, `boundary_download.py`: DAR REST 3.0.0 | Officiel udfasningsdato er 15. januar 2027. Disse forløb kræver en reel erstatning; et skift af baggrund eller værtsnavn er utilstrækkeligt. |
| Lokale adresser og reservekort | SQLite og lokalt tegnede veje/bygninger | Bevares. Fjernelse af reservevisningen ville fjerne muligheden for at orientere sig ved flisefejl og løser ikke kildefristen. |

## Ejerbeslutning og første trin

Ejeren har valgt egen API-nøgle med guidning. Beta.7 tilføjer lokal opsætning, kontrol af DAR v3-skema og GraphQL-forbindelse samt fjernelse/genkontrol af nøglen. Se [trinvis vejledning](DATAFORDELER.md). Nøglen ligger separat fra SQLite, udelades fra portable backups og bevares ved beta-nulstilling. Afviste forbindelser og rå fejltekster med URL/nøgle vises ikke videre.

## Implementeringstrin

1. Ny lokal kildeopsætning til Datafordelerens IT-system/API-key. Hold nøglen ude af browsertilstand, log, offentlige fejl og portable sikkerhedskopier, ligesom eksisterende Google-login. Ingen fælles nøgle indbygges.
2. Indlæs og fastlås det aktuelle DAR v3-skema. Det dokumenterede skema-endpoint gav HTTP 401 uden autentifikation i kontrollen; datakald er derfor ikke afprøvet, og der er ikke søgt efter ejerens credentials.
3. Byg en særskilt GraphQL-adapter med eksplicitte felter og relationer, stabile DAR-ID'er, koordinatkonvertering, statusfilter og ét fast registrerings-/virkningstidspunkt pr. hentning. Vælg flat entitetsopslag og lokale joins, hvor den officielle vejledning oplyser manglende relationer.
4. Erstat postnummer-, vej- og grænsehentning samlet med paginering, kontrol af fuldstændighed, timeout, pause/genoptagelse og eksisterende kontrol før ændringer af lokale kort. Gemte REST-checkpoints må ikke lydløst blandes med en ny kildes svar.
5. Test med fiktive svar: etage/dør, postnummerkrydsende veje, flere sider, manglende join, gentaget cursor, ufuldstændige svar, 401, netfejl og genstart. Sammenlign normaliserede adresser før skift. Egen nøgle og et offentligt ufølsomt prøveområde verificeres som separat lokalt ejertrin.

Denne overgang er endnu ikke færdig. Der er ingen ændring af eksisterende adressehentning i dette dokumentationsarbejde. De næste kodeændringer bør bevare lokale data og en tydelig fejl ved utilgængelig kilde.

## Afsluttet byggesten · komplet sidehentning

`distrikt/app/dar_paging.py` har nu `collect_pages(fetch_page, entity, ...)`, som samler et helt resultat i hukommelsen, før det kan gives videre til en lokal import. Den kontrollerer GraphQL-fejl, nodes/pageInfo, boolsk hasNextPage, endCursor, tomme fortsættelsessider, cursor-cyklusser og dublerede/manglende entitets-ID’er. Grænser for sider og antal resultater giver fejl frem for afkortning. Afbrydelse kontrolleres før og efter hvert opslag. Fejltekster gengiver ikke upstream-svar.

Byggestenen har ingen netværksadgang, credentials eller databaseskrivning og er endnu ikke koblet til Downloads. Den kommende adapter skal levere `fetch_page(after)` med uændrede felter/filtre og samme faste registrerings-/virkningstidspunkt på alle sider samt redigerede transportfejl. Hele resultatet returneres først efter en gyldig slutsides angivelse; fuldstændighed afhænger fortsat af kildens korrekte sideoplysninger. Dette er ikke en kontrol af endnu uimplementerede relationer eller den samlede adresseimport.

12 fiktive prøver dækker sidefølge, tomt resultat, deldata med GraphQL-fejl, manglende felter, ugyldige cursors, cyklusser, dubletter, ID’er, grænser, afbrydelse og netfejl efter første side. Transport/forespørgsler og lokale DAR-joins er nu også implementeret som beskrevet nedenfor. Ingen ny brugerfunktion er aktiveret; beta.7 og dens tag bevares, og næste funktionelle udgivelse er beta.8.

## Afsluttede byggesten · forespørgsler og lokale joins

`address_source.Datafordeler.query` sender interne GraphQL-forespørgsler med den lokalt gemte nøgle gennem den eksisterende begrænsede transport. JSON-fejl, GraphQL-fejl med delresultater og manglende data afvises uden at gengive rå providersvar. Den læser ikke lokale kort eller IB.

`dar_query.DarQuery` fastlåser ét UTC-tidspunkt for registrering og virkning på tværs af de fem flade entiteter og alle sider. De eksplicitte projektioner og lighedsfiltre følger de officielle DAR-eksempler læst 16.10.2026. Status 3 kræves; uafgrænsede landsopslag tillades ikke. Alle værdier og cursors escapes som GraphQL-strengliteraler. Den eksisterende sidehenter kræver en gyldig sidste side, og hvert svar kontrolleres også mod forespørgslens scope.

`dar_join.join_addresses` kræver komplette inputs fra samme snapshot og samler dem lokalt via ID-referencer. Resultatet sammenlignes med det eksisterende normaliserede REST-format i fiktive prøver: `dar:`-ID, adgangsadresse-ID, vej, husnummer/bogstav, postnummer, etage/dør og koordinater. Manglende eller inaktive relationer, dublerede ID'er, manglende etage/dør-felter, ukendt CRS, ugyldig dimension/WKT og ikke-endelige koordinater afviser hele resultatet. Punktgeometri i EPSG:25832 og XY/XYZ behandles; højden bruges ikke. Postnummerfilter anvendes før punktopslag uden for scope, fordi en navngiven vej kan krydse flere postnumre.

14 nye fiktive prøver dækker disse dele, inklusive en samlet transport/side/join-prøve med seks svar. Det er ikke en live skemavalidering, effektiv masseadapter eller aktivering af den nye adressekilde. Den autentificerede skemakontrol med egen lokal nøgle står stadig særskilt.

## Afsluttet byggesten · samlet adapter med aliasbatching

`DarQuery.collect_many` grupperer op til ti uafhængige lighedsopslag i én GraphQL-anmodning med aliases. Hver alias kontrolleres med den samme komplette sidehenter og samme tidspunkt; efterfølgende sider hentes kun for de scopes, der faktisk har flere sider. Dermed kræver 25 enkelt-ID-opslag tre anmodninger i prøven. Der indføres ingen antagelse om IN-filtre i et endnu ikke live-verificeret skema. For mange anmodninger/resultater, manglende aliases, deldata med fejl eller manglende obligatoriske ID'er giver fejl før returnering.

`dar_adapter.DarAdapter.discover_postcode` finder postnummeret, dets husnumre og de nødvendige navngivne veje via ID-opslag. `road` finder husnumre, samtlige adresser samt nødvendige punkter og postnumre og samler dem med den afprøvede normalisering. Et valgfrit postnummer afgrænser husnummeropslaget før adressers og punkters hentning. Den returnerede kilde er `dar-graphql-v3`, og alle dele bruger samme snapshot. Adapteren har ingen forbindelse til databasen. 10 nye fiktive prøver dækker hele forløbet og fejl efter første side.

### Næste konkrete integration

1. Den samlede vej-/postnummeradapter er implementeret med aliasbatching og fuldstændighedskontrol. Næste kildeopslag er afgrænsede geografiske udsnit til den samlede grænse. Det konkrete skema og et ufølsomt prøveområde kontrolleres i ejerens lokale installation; nøglen sendes ikke til AI.
2. Vej-, postnummer- og grænsehentning skal bruge adapteren med samme snapshot, fremdrift, pause/genoptagelse og særskilt GraphQL-kildemarkør i checkpoints. REST-checkpoints må ikke genoptages som GraphQL.
3. Import/retirement skal først ske efter en komplet vej/et komplet udsnit og bevare eksisterende transaktioner. Skemafejl, 401, netfejl eller manglende joins må ikke markere lokale adresser udgået.
4. Afslut fiktive integrationsprøver og program/platform/HA-gates; udgiv først da næste funktionelle beta. Egen lokal nøgle og et offentligt ufølsomt område er separat ejerprøve.

## Primære kilder

- [DAR REST: udfases 15. januar 2027](https://confluence.kds.dk/pages/viewpage.action?pageId=16056323).
- [DAR GraphQL og adgang via IT-system/API-key eller OAuth](https://datafordeler.dk/dataoversigt/danmarks-adresseregister-dar/dar-graphql/).
- [DAR GraphQL-felter, version og kendte relationer](https://confluence.kds.dk/pages/viewpage.action?pageId=187105632).
- [GraphQL: endepunkter, paging og autentifikation](https://confluence.kds.dk/pages/viewpage.action?pageId=187105434).
- [Adressevælgerens brugerstyring og token](https://confluence.kds.dk/display/ADV/Brugerstyring).
