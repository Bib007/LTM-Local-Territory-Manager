# Ændringsliste

## 1.12.0-beta.24 · Læsbare lokale navneforslag

- Navneforslag ved udlevering har lys tekst på mørkegrå baggrund. Hover og tastaturmarkering har en lysere mørk tone og tydelig kant.
- Den fejlagtige hvide fallback er fjernet. Lokale navne, søgning, valg og udleveringspayload er uændrede.
- Browserkontrol bruger opdigtede navne, kontrollerer høj kontrast i den normale tilstand, tastaturmarkering/valg og smal/bred visning.


## 1.12.0-beta.23 · Samlet opsætning og obligatorisk rundtur

- Én normal opsætningsguide med introduktion til lokal drift, fælles HA-installation, backup og valgfri deling. Den parallelle detaljerede guide er samlet ind i forløbet.
- Svar gemmes først som uafsluttet. Rundturens sidste trin afslutter opsætningen og åbner forsiden med den personlige plan; guiden genåbnes ikke. Afbrydelse kan genoptages, og tidligere fuldførte installationer bevares.
- Sprogskift i rundturen bevarer trin og fokus. Afvist/sen afslutning og dobbeltklik håndteres uden ekstra skrivning eller lukning af nyere dialoger.
- Kortplanen har en direkte indgang til egen Datafordeler-nøgle. Officiel REST-frist 15.01.2027 er genkontrolleret; den eksisterende GraphQL-import bevares. Egen konto er et ejertrin.


## 1.12.0-beta.22 · Fast punkt 8–10: print, programpakke og slutkontrol

- Dansk/engelsk printdialog og printknapper med bevarede felter, profilværdier og uændrede originalformularer/rapportindhold.
- Printforberedelse beskytter mod dobbeltklik, ændrede felter/data, navigation og nyere dialoger. Fejlet billedafkodning spærrer print; profilgemning godkender ikke genprint.
- Appens versionsvisning følger den kørende server i begge kanaler; gammel API-etiket er rettet efter pakkestartprøven.
- Komplet programpakke med de linkede vejledninger, køreplan, lokal restliste og demovejledning. Pakningen stopper ved manglende original S-12-PDF eller brudte interne vejledningslinks.
- Printguide og slutkontrol på dansk/engelsk. Egen printer, HA/telefon/VPN, Google-/Datafordeler-konto og eventuel skærmlæser står tydeligt som ejerprøver.
- Fiktive JavaScript-, Python-, pakke- og Chromium-prøver kontrollerer både programforløb og faktiske front-/bagside-/rapport-PDF'er ved fire skærmbredder. Main er stabil 1.11.1.


## 1.12.0-beta.21 · Fast punkt 7: login, tastatur og fokus

- Login kan vælges på dansk/engelsk uden at genskabe felter. Indsendelse kræver én bekræftet anmodning, har timeout og blokerer dobbeltklik. Fejl bevarer indtastning og passende fokus; kun sprogvalget gemmes som præference.
- Loginets lille oversættelse ligger i den allerede offentlige loginfil. Generel app-sprogfil, øvrige programfiler og data kræver fortsat login; cookie, adgangskodekontrol, netværks-/oprindelseskontrol og rategrænse er uændrede.
- Dialoger får navngivning fra overskrift, sammenknyttede feltlabels og meningsfuldt startfokus. Tab/Shift+Tab bliver i dialogen, Escape bevarer den eksisterende gemmekontrol, og lukning returnerer til åbneren, også efter genoptegning.
- Fiktive login-/fokusprøver, LAN-grænser og offline Chromium dækker begge loginvarianter ved fire bredder samt appens native dialog- og Escape-forløb. Fast køreplan: 70 % (7/10). Næste er printbetjening med uændrede originalformularer.

## 1.12.0-beta.20 · Fast punkt 6 afsluttet

- Særskilte skrivninger i opsætning, IB-/kortimport, deling og førstegangsopsætning bruger nu samme tydelige faser: usikker kvittering, kendt afvisning eller bekræftet skrivning med behov for genindlæsning. En læsefejl udløser aldrig automatisk gentagelse.
- Nyere opsætningssessioner, imports, formularer og datasnapshots bevares ved sene svar. Delingshandlinger blokerer dobbeltklik og viser mislykket statuslæsning særskilt efter en accepteret handling.
- Supplerende kontroller beskytter lokale billedvalg, geodatahentninger, farve-/Se bort fra-opfølgning og nyere oprydningskontroller mod sene svar.
- Programprøver og offline Chromium dækker gennemført kortoprettelse med efterfølgende læsefejl, bevaret plan og eksplicit kontrol uden dobbeltskrivning. Fast køreplan: 60 % (6/10). Næste er login, tastatur og fokus; ønskelisten venter.

## 1.12.0-beta.19 · Forståelige domænefejl på dansk og engelsk

- Faste fejl fra kort, adresser, udlån, IB, opsætning, administration og backup følger valgt sprog. Ukendte diagnostikker vises fortsat uændret og HTML-escaped.
- Parameteriserede fejl får valgfrie skabelon-/parametermetadata. Den oprindelige danske fejltekst og ValueError-kontrakt bevares. Brugerens navne, kortnumre, interne filnavne og talgrænser ændres ikke.
- Dato-/IB-linjefejl og backupforhåndsvisning bruger samme sikre renderer. Sprogskift bevarer felter og opdaterer beskeden på stedet; ukendte eller ugyldige metadata falder tilbage til originalen.
- JSON-læsning har nu også tidsgrænse efter modtagne HTTP-headere. Nye kildekatalog-, HTTP-, fiktive UI- og Chromium-prøver dækker fejlforløbene. Fast punkt 6 er fortsat i gang; 50 %.

## 1.12.0-beta.18 · Sene svar bevarer nyere arbejde

- Opfølgning efter noter, IB og omstrukturering kan ikke åbne gamle dialoger eller skifte væk fra nyere arbejde. Sene formularfejl overskriver ikke en nyere fejlbesked.
- Omstruktureringens preview bindes til felter, adressevalg, side og revision. Nyeste kontrol vinder; bekræftelse kræver fortsat ÆNDR KORT og blokerer dobbeltklik. Den kontrollerede payload ændres ikke.
- En kvittering for en gammel baggrundsgrænse rydder ikke en nyere tegning. Områdesletning bevarer et nyere filtervalg.
- Fiktive hændelsesprøver og offline Chromium dækker ændrede felter og sen accepteret opdeling ved fire bredder. Fast punkt 6 er fortsat i gang; køreplan 50 %.

## 1.12.0-beta.17 · Gendannelse uden tab af nyere kladder

- Gendannelse og beta-nulstilling sender kun én anmodning ved dobbeltklik. Uændrede samtykke-, kontroltoken-, versions- og beta-begrænsninger bevares.
- En bekræftet import/nulstilling med fejlet genindlæsning markeres som gemt med behov for kontrol, ikke som en import der skal gentages. Nye skrivninger spærres indtil eksplicit genindlæsning.
- Sene svar eller datasnapshots erstatter ikke nyere dialoger eller navigation. Sikkerhedskopien fra en normal gennemført handling kan fortsat hentes lokalt.
- Nye fiktive transferprøver og offline Chromium ved fire bredder dækker sen accepteret import og bevaret nyere kladde. Fast punkt 6 er stadig i gang; 50 % er uændret.

## 1.12.0-beta.16 · Sikker gemmekvittering og bekræftelse

- Fælles dansk/engelsk fejlbeskeder skelner mellem læsefejl, afvist ændring, udløbet login, usikkert resultat og bekræftet gemning med fejlet genindlæsning.
- Usikkert resultat stopper kø og automatisk gemning. Forbindelsestjek gensender aldrig; eksplicit Opdater henter det gemte resultat før videre arbejde. Felterne bevares, indtil brugeren vælger at lukke uden gensendelse.
- Skrivepayload kopieres ved kølægning. Sene svar lukker ikke nyere dialoger. Administrative previews kræver samme formular, værdier og revision; dobbelt bekræftelse blokeres.
- Fiktive request-/bekræftelsesprøver og offline Chromium dækker tabt svar efter faktisk gemning ved fire bredder. Punkt 6 er fortsat i gang; domænefejl og de øvrige bekræftelsesforløb mangler. Fast køreplan uændret 50 %.

## 1.12.0-beta.15 · Google Drive- og QR-betjening

- Kortgemning skelner mellem serverens nye revisionsnummer og en ændret tegning. En vellykket gemning afsluttes korrekt, også ved oprettelse af et nyt kort; nyere kladder bevares. Prøvet gennem den rigtige API-håndtering.
- Dansk/engelsk i delingsstatus, Google-guide, preview/godkendelse og QR. Sprogskift bevarer billede, checkbox, URL og godkendelsesdata. Offentlige billeder og originale printformularer ændres ikke.
- Nyeste polling vinder. Sene preview-/QR-svar erstatter ikke nyere dialoger. Publicering blokerer dobbeltklik, kræver en uændret kontrolleret revision og bevarer nyere navigation efter svar.
- Forbindelsesfilens indlæsning beskyttes mod navigation og genopbygning under polling. Ugyldig JSON vises uden at citere filindhold. Program-/browserprøver bruger fiktive svar, et genereret prøve-PNG og ingen Google-konto. Fast køreplan: 50 %.

## 1.12.0-beta.14 · Opsætning og lokal IB-import

- Dansk/engelsk i opsætningens fire trin, områder, nummerering, kortforslag og lokal IB-import. Sprogskift bevarer kortinstans, kladdenavne/-numre, geometri og IB-kontrol. Dataværdier, CSV-kolonner og bekræftelsesord er uændrede.
- Ændret opsætning, dato, fil, revision eller navigation beskytter mod forældede forslag. Ombyttede filindlæsninger bruger kun den nyeste fil; fejlede filer kan ikke godkende et gammelt IB-token. Felter spærres under oprettelse.
- Nye kontrakt-/hændelsesprøver og udvidet offline Chromium ved fire skærmbredder. Den faste køreplans punkt 4 er afsluttet: 40 %.

## 1.12.0-beta.13 · Korteditor og grænser

- Dansk/engelsk betjening i geografisk korteditor, samlet grænse og KML/GeoJSON-import. Sprogskift bevarer kort, zoom, fokus, valgte adresser, tegning, formularer og importfil. Gemte typer og API-værdier ændres ikke.
- Forsinkede forhåndsvisninger, oprydning og import kan ikke erstatte nyere kladder/dialoger. Gemning bruger en fast kopi, afviser ændret/annulleret valg før skrivning og bevarer en nyere tegning under gemning. Dobbeltgemning og reference-deling af kortgrænser er rettet.
- Gentagelige fiktive Chromium-prøver ved 320/390/768/1440 pixels kræves før HA-betaudgivelse. Kortvælgeren holder sig inden for en smal skærm. Fast køreplans punkt 3 er afsluttet; planen er 30 %, og ønskelisten venter.

## 1.12.0-beta.12 · Digitalt QR-kort

- Delt kortbillede får et nyt blåt layout med stor kortflade, tydeligt kortnummer/navn og miniature af printforsiden i hjørnet. Den blanke S-12-forside og printets vejlinjeformatering genbruges.
- Miniaturen bygges kun af den offentlige opskrift, ikke af private kortdata. IB, noter og kortholdere indgår ikke. Lange navne og tætte/tomme kort er afprøvet i fiktive SVG/PNG-billeder.
- Eksisterende QR-links og adgangscyklus bevares. Ældre layout markeres til manuel opdatering; nyt billede kræver fortsat preview og udtrykkelig godkendelse.

## 1.12.0-beta.11 · Kurvede og sammenhængende vejskel

- Automatisk inddeling kan følge vejens faktiske knæk og kurver. Samme-navn-vejstykker forbindes kun ved præcist fælles endepunkt uden forgrening; huller lukkes ikke ved gæt.
- Tvetydige skæringer, løkker, selvkrydsning og komplekse grænsekrydsninger afvises. Areal, overlap, hvert adressepunkt og hele huse kontrolleres. Manuelle rettelser og eksplicit samlet oprettelse bevares.
- Dansk/engelsk inddelingsvejledning beskriver lokale vejdata, kontrol og begrænsninger. Naturlige skel er næste del af W16; ønsket er ikke markeret afsluttet.

## 1.12.0-beta.10 · Første vejbaserede skel

- Automatisk kortinddeling foretrækker nu egnede, lokalt hentede gennemgående lige vejstykker som skel, også på skrå. Ingen nye netkald og ingen automatisk kortoprettelse.
- Korte vejfragmenter forlænges ikke kunstigt. Husenes lejligheder og faktiske adressepunkter bevares samlet. Manglende egnede vejstykker giver en tydelig markering af geometrisk deling til manuel rettelse.
- Vejdata indgår i kontrollen af forældede forhåndsvisninger. Kurvede veje, sammensatte vejforløb og naturlige skel er fortsat udestående under W16.

## 1.12.0-beta.9 · Forkynderforslag

- Udlevering får en lokal søge- og forslagsliste med fornavn/efternavn, højst otte forslag, tastaturvalg og berøring. Søgetekst og navne forlader ikke appen.
- Nye navne kan fortsat skrives frit og oprettes først ved registrering. Escape/Tab vælger ikke et navn; Enter i en åben liste gemmer ikke ved et uheld. Dansk/engelsk og formularens data bevares.
- Programprøver dækker hændelser og gemmekontrakt; visuel mobil-/skærmlæserkontrol står særskilt.

## 1.12.0-beta.8 · DAR GraphQL

- Egen lokalt gemte Datafordeler-nøgle bruges til komplette vej-, postnummer- og grænsehentninger. Flade opslag sammenkobles lokalt med stabile adresse-ID'er og bevarede etage-/døroplysninger.
- Grupperede opslag reducerer antal netkald. Kilde og skemafingeraftryk følger checkpoints; ufuldstændige svar gemmes ikke som komplette veje/udsnit. Genstart fortsætter kun ufærdige dele af samme hentning.
- Uden nøgle fortsætter den hidtidige kilde. Ved kildeskift kræves en ny opdatering. Adresseforslag fra Adressevælger er fortsat en særskilt tjeneste. Egen Datafordeler-/HA-prøve står særskilt fra fiktiv programkontrol.

## 1.12.0-beta.1 · HA-beta under klargøring

- Separat HA-betakanal med port 8788, egne data og egen login-cookie. Små nummererede prereleases udgives først efter program-, Mac-, Windows- og HA-kontrol.

- Google Drive-billeder er private mellem udlån og åbnes automatisk ved udlevering. QR-linket bevares; afventende/fejlede adgangsændringer og nyt forsøg vises. Ingen udlåns- eller personoplysninger uploades.

- Selvstændigt link til idéer og feedback via GitHub med valgfrie bilag og tydelig oplysning om offentligt indhold; aktiveres med næste stabile udgivelse.
- HA-installationssiden forklarer funktioner, første start, lokal adgang og backup.
- KTM-kort får læsbare distriktnumre med forbindelsesstreger, når der er trangt. Kortets egen printside bliver automatisk stående eller liggende efter geografien; fiktive PDF-rapporter er kontrolleret visuelt.
- Det overflødige tal for midlertidige kort er fjernet fra distriktets oplysninger.

- Spørgsmål ved første start med personlig opsætningsplan og en valgfri rundtur i de rigtige sider.
- Lokal Excel-/CSV-import af allerede fordelte kort, områder, kortnavne og adresser med kontrol før oprettelse.
- Præcise importerede lejligheder kan bruges til lokal IB-import; besøgstal bevares.
- Regnearksskabelon med dansk vejledning og udfyldningsfelter.


- Blå identitet og valgfri velkomstguide.
- Dansk/engelsk navigation, centrale kort-/udleveringsformularer, forkyndere, opgaver, indstillinger, rapportskærme, kortoversigt og adresselister.
- Kladder bevares ved sprogskift og flere forsinkede forhåndsvisninger.
- Forbindelseskontrol bekræfter ikke en usikker gemning.
- Backupoversigten sammenligner synlige kort og noter korrekt og bevarer arkiverede poster.
- Originalt dansk print, gemte værdier og datastier bevares.

## 1.11.0 · første offentlige kildekodeudgave

- Lokal distriktsadministration til Mac, Windows og Home Assistant OS.
- Opstart på en fast lokal IP kræver ikke reverse DNS; det undgår forsinket Mac-start uden netværksopslag.
- Kort, forkyndere, udleveringer, gennemgange, IB, lokale backups og dansk print.
- Gennemgået programkode og tomme S-12/S-13-formularer; ingen brugerregistreringer eller private kørselsfiler.
- Dansk README og opsætningsguider med engelsk som ekstra valg.
- Installation og senere programopdateringer via HA-repository uden manuel kopiering af programfiler.
