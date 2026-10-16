# Adressekilde før januar 2027

Kontrolleret 16.10.2026. Dette er en konkret overgangsplan, ikke en gennemført kildeændring.

## Hvad rammer LTM?

| Del | Nuværende kode | Fund og beslutning |
| --- | --- | --- |
| Kortbaggrund | `basemaps.js`: OpenStreetMap er standard | Fliser er et baggrundsbillede; de erstatter ikke præcise adresser med ID, etage og dør. OSM bevares som standard. |
| Søgning og enkeltvej | `geodata.py`: Adressevælger; DAR REST som støtte ved store veje | Adressevælger er en særskilt officiel tjeneste. Den anbefalede fælles token er fortsat dokumenteret; fremtidig brugerstyring er varslet ultimo 2026/primo 2027, uden fast dato i den læste vejledning. |
| Hele postnumre og samlet grænse | `postcode.py`, `boundary_download.py`: DAR REST 3.0.0 | Officiel udfasningsdato er 15. januar 2027. Disse forløb kræver en reel erstatning; et skift af baggrund eller værtsnavn er utilstrækkeligt. |
| Lokale adresser og reservekort | SQLite og lokalt tegnede veje/bygninger | Bevares. Fjernelse af reservevisningen ville fjerne muligheden for at orientere sig ved flisefejl og løser ikke kildefristen. |

## Næste implementering

1. Ny lokal kildeopsætning til Datafordelerens IT-system/API-key. Hold nøglen ude af browsertilstand, log, offentlige fejl og portable sikkerhedskopier, ligesom eksisterende Google-login. Ingen fælles nøgle indbygges.
2. Indlæs og fastlås det aktuelle DAR v3-skema. Det dokumenterede skema-endpoint gav HTTP 401 uden autentifikation i kontrollen; datakald er derfor ikke afprøvet, og der er ikke søgt efter ejerens credentials.
3. Byg en særskilt GraphQL-adapter med eksplicitte felter og relationer, stabile DAR-ID'er, koordinatkonvertering, statusfilter og ét fast registrerings-/virkningstidspunkt pr. hentning. Vælg flat entitetsopslag og lokale joins, hvor den officielle vejledning oplyser manglende relationer.
4. Erstat postnummer-, vej- og grænsehentning samlet med paginering, kontrol af fuldstændighed, timeout, pause/genoptagelse og eksisterende kontrol før ændringer af lokale kort. Gemte REST-checkpoints må ikke lydløst blandes med en ny kildes svar.
5. Test med fiktive svar: etage/dør, postnummerkrydsende veje, flere sider, manglende join, gentaget cursor, ufuldstændige svar, 401, netfejl og genstart. Sammenlign normaliserede adresser før skift. Egen nøgle og et offentligt ufølsomt prøveområde verificeres som separat lokalt ejertrin.

Denne overgang er endnu ikke færdig. Der er ingen ændring af eksisterende adressehentning i dette dokumentationsarbejde. De næste kodeændringer bør bevare lokale data og en tydelig fejl ved utilgængelig kilde.

## Primære kilder

- [DAR REST: udfases 15. januar 2027](https://confluence.kds.dk/pages/viewpage.action?pageId=16056323).
- [DAR GraphQL og adgang via IT-system/API-key eller OAuth](https://datafordeler.dk/dataoversigt/danmarks-adresseregister-dar/dar-graphql/).
- [DAR GraphQL-felter, version og kendte relationer](https://confluence.kds.dk/pages/viewpage.action?pageId=187105632).
- [GraphQL: endepunkter, paging og autentifikation](https://confluence.kds.dk/pages/viewpage.action?pageId=187105434).
- [Adressevælgerens brugerstyring og token](https://confluence.kds.dk/display/ADV/Brugerstyring).
