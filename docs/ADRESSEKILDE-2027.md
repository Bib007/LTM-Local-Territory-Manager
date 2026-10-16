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

12 fiktive prøver dækker sidefølge, tomt resultat, deldata med GraphQL-fejl, manglende felter, ugyldige cursors, cyklusser, dubletter, ID’er, grænser, afbrydelse og netfejl efter første side. Næste del er transport/forespørgsler og lokale DAR-joins, derefter integration i vej-, postnummer- og grænsehentning med separate checkpoints. Ingen ny brugerfunktion er aktiveret; beta.7 og dens tag bevares, og næste funktionelle udgivelse er beta.8.

## Primære kilder

- [DAR REST: udfases 15. januar 2027](https://confluence.kds.dk/pages/viewpage.action?pageId=16056323).
- [DAR GraphQL og adgang via IT-system/API-key eller OAuth](https://datafordeler.dk/dataoversigt/danmarks-adresseregister-dar/dar-graphql/).
- [DAR GraphQL-felter, version og kendte relationer](https://confluence.kds.dk/pages/viewpage.action?pageId=187105632).
- [GraphQL: endepunkter, paging og autentifikation](https://confluence.kds.dk/pages/viewpage.action?pageId=187105434).
- [Adressevælgerens brugerstyring og token](https://confluence.kds.dk/display/ADV/Brugerstyring).
