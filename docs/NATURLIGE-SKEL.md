# Forslag langs vandløb og jernbaner

Opsæt distrikter kan bruge lokalt gemte vandløb og jernbaner som skel. Et egnet gennemgående forløb prøves før vejforslagene. Forslagene har fortsat omtrentlige besøgstal og kan rettes, før kortene oprettes.

## Tilføj grundlaget

Åbn kortet og vælg et mindre udsnit. Under Kortdata vælges **Hent veje, bygninger, vandløb og jernbaner i det viste udsnit** og derefter **Hent vist udsnit**. Den eksisterende hentning fra OpenStreetMap medtager nu også disse forløb. Ældre lokale kortdata får først vandløb og jernbaner ved en ny hentning; flere udsnit kan være nødvendige.

Gå derefter til Opsæt distrikter → Områder og numre → Lav forslag. Blå linjer viser gemte vandløb; grå stiplede linjer viser gemte jernbaner. Kontrolteksten forklarer, når et forslag følger et af disse skel. Navne er kortdata, og oversættes ikke ved sprogskift.

Kontrollér broer, adgangsveje og lokale forhold. Ret eventuelt de fælles hjørner med Ret grænser på kortet, og kontrollér ændringen igen. Der oprettes først kort efter den særskilte bekræftelse OPRET KORT. Ændrede lokale skel gør en ældre forhåndsvisning ugyldig.

## Afgrænsning i beta.53

Hentningen omfatter linjer mærket `waterway=river`, `stream` eller `canal` samt `railway=rail`. Andre typer som grøfter, sporvognsspor, kystlinjer og søpolygoner behandles endnu ikke som automatiske skel.

Første beregning bruger kun hele sammenhængende forløb i lag 0 uden bro-/tunnelmærkning. Øvrige hentede stykker vises som kontekst. Samme type og navn kan forbindes ved præcist fælles endepunkt uden forgrening; unavngivne stykker afprøves enkeltvis. Huller, navneskift, forskellige typer og bro-/tunnelstykker forbindes ikke ved gæt. Et forløb skal krydse områdegrænsen to steder og bestå de eksisterende kontroller af geometri og adressefordeling. Beregningen holder stadig lejligheder i samme hus sammen.

Hvis intet egnet lokalt skel findes, prøves de eksisterende vejforslag og derefter geometrisk deling med besked om manuel kontrol. Funktionen vurderer geometri; passage og lokale forhold skal gennemgås på forslaget. W16 om mere komplekse vejnet og yderligere naturlige skel er fortsat delvist åben.

## Datagrundlag

De ekstra offentlige linjer hentes med den eksisterende afgrænsede Overpass-forespørgsel. Lokale adresser, forkyndere, udlån og IB indgår ikke i denne forespørgsel. De gemte linjer følger den almindelige lokale database og sikkerhedskopi. Korteksportens offentlige baggrund kan tegne linjerne; den indeholder ingen af de lokale private registreringer.

Primære beskrivelser læst 21.10.2026:

- [OpenStreetMap: vandløb og deres typer](https://wiki.openstreetmap.org/wiki/Waterways)
- [OpenStreetMap: jernbanetyper](https://wiki.openstreetmap.org/wiki/Railways)
- [Overpass: filtre efter tags](https://dev.overpass-api.de/overpass-doc/en/criteria/per_tag.html)
- [Overpass: kombination af forespørgsler](https://dev.overpass-api.de/overpass-doc/en/criteria/union.html)
