# Ændringsliste

## 1.12.2-beta.72 · IB-billeder og sikker afslutning

IB fra billeder omfatter nu også kontrolleret afslutning, når selve LTM lukkes under en billedlæsning. Den lokale OCR-proces stoppes og dens midlertidige filer ryddes op, før serveren lukker. Kø, kortvalg, redigerbar tekst, præcise adresser/datoer og godkendelse er som i beta.71. Ingen ekstern AI eller cloud-OCR. S-12-forsider er fortsat ikke med.

## 1.12.2-beta.71 · Lokal IB-import fra billeder

Indstillinger → Import har nu IB fra billeder. Vælg op til 20 PNG-/JPEG-billeder i kø. Hvert billede læses på det lokale LTM-system, får sit eget kortvalg og redigerbar tekst samt forslag. Hver linje skal have en adresse fra det valgte kort og en kontrolleret dato eller springes over ved dit valg. Forhåndsvisningen og IMPORTÉR IB kræves før gemning. Næste billede startes manuelt; tidligere godkendte filer bevares ved lukning eller fejl.

HA-pakken medtager lokal Tesseract med dansk og engelsk. På Mac og Windows kræves en separat lokal Tesseract-installation; appen viser, hvis den mangler. Ingen ekstern AI, cloud-OCR eller automatisk adresseoprettelse bruges. S-12-forsider, automatisk fortolkning af flere spalter og fuld W85 er fortsat åbne. Håndskrift og uklare billeder kan kræve manuel rettelse.

## 1.12.2-beta.70 · Overlappende kortgrænser

Opfølgninger advarer, når to gemte distriktskortgrænser dækker et fælles areal. Hver berørt kombination vises én gang med links til begge kort. Du kan søge på begge kortnumre og navne. Fælles kanter og hjørner udløser ingen advarsel; adresser valgt på flere kort vises fortsat som egne punkter.

Kontrollen bruger de lokalt gemte grænser og ændrer ingen kort eller adresser. Grænser skal rettes manuelt, hvis overlappet er utilsigtet. Dansk/engelsk og telefon/tablet understøttes. Foto- og IB-genkendelse er fortsat under udvikling.

## 1.12.2-beta.69 · Færdig, når ændringen er gemt

- Permanent sletning og almindelige ændringer får den opdaterede oversigt med, når gemningen bekræftes. Du skal derfor ikke vente på en ekstra hentning eller skifte menu for at se resultatet.
- Hvis forbindelsen afbrydes eller svaret ikke kan læses, bliver du stadig bedt om at kontrollere resultatet, før du prøver igen.
- Datafordelerens nøgle og forbindelseskontrol findes nu under Indstillinger → Forbindelser. Hent adresser har en genvej dertil. Din gemte nøgle bevares.
- Udseende, samlet Import og Opfølgninger samt filkøen fra de seneste betaer er med.

## 1.12.2-beta.68 · Vælg dit udseende og prøv det nye overblik

- Vælg Mørkt, Lyst eller Følg enheden nederst i menuen. Valget huskes i din browser og kan skiftes uden at miste åbne formularer.
- Demoen bruger appens fælles designfiler og viser den samme opbygning på forside, genveje og nøgletal. Den har eksempelvisninger for Opfølgninger og Kort og adresser; alle oplysninger er stadig opdigtede.
- Adressevejledningen er gennemgået på dansk og engelsk med aktuelle menuer, hentestatus, genoptagelse og gennemgang af adresseændringer. Gamle beskeder om en manglende afprøvning er fjernet.
- Filkøen fra beta.67 er med. Automatisk genkendelse af billeder er fortsat under planlægning.

## 1.12.2-beta.67 · Flere kortfiler i kø

- Vælg op til 20 Excel-/CSV-filer til kortimport. Hver fil får sin egen forhåndsvisning og godkendelse; næste fil importeres ikke automatisk.
- Se den aktuelle fil, importerede filer og filer, du har sprunget over. Allerede godkendte filer bevares ved lukning eller fejl.
- Grænsen er 2 MB pr. fil og 20 MB samlet. Filerne behandles fortsat på dit eget system.
- Dette er første trin mod lettere masseimport. Fotos og automatisk tekstgenkendelse er endnu ikke med.

## 1.12.2-beta.66 · Import og opfølgninger samlet

- Import af historik, distriktskort og IB findes nu under Indstillinger → Import. Du gennemgår og godkender stadig oplysningerne, før de gemmes.
- Den nye menu Opfølgninger samler kortkontrol, genprint, langvarige udleveringer og adresseændringer. Hvert forhold får sin egen linje og tæller; forside og bagside tæller hver for sig.
- Forsiden åbner det fælles overblik. Genprint og kortkontrol er flyttet fra Kort og adresser, så du har ét sted at følge op.
- Søgning, filtre og dansk/engelsk er med i det nye overblik. Åbning af import eller opfølgninger ændrer ingen registreringer.
- Forbedringerne fra beta.65 med tydelig adressehentning og mindre unødig dataoverførsel er med.

## 1.12.2-beta.65 · Mindre ventetid og tydelig adressehentning

Samler forbedringerne nedenfor og sikrer samtidig, at almindelig kortgemning ikke starter en ekstra hentning af kortdata.

## 1.12.2-beta.64 · Bedre overblik under adressehentning

- Adressehentning viser, hvad den arbejder med, og hvor mange adresser der er modtaget. Antallet tælles uden dubletter ved nye forsøg. Der vises ingen gættet resttid.
- Større adresseområder deles også i mindre udsnit, når ét opslag kræver for mange forespørgsler. Færdige udsnit bevares, hvis hentningen må fortsættes senere.
- Gemning viser tydeligt, når ændringen er gemt, mens oversigten opdateres. Sletning og gendannelse af oplysninger uden kortændringer henter ikke længere alle kortdata igen.
- Rettelsen fra stabil 1.12.1 er bevaret: almindelig gemning og udlevering kræver ikke unødig genindlæsning.

## 1.12.2-beta.63 · Flere små forbedringer i daglig brug

- Ugentlige opgaver tæller først fra den dag, de skal udføres. Når de markeres udført, fortsætter de til næste dato med bevaret historik.
- Digitale kort har en lysere baggrund, så røde besøgsprikker og husnumre er tydeligere. Tidligere delte billeder opdateres først, når et nyt billede godkendes.
- Tekster om lokal lagring og adressehentning passer nu også til Home Assistant, Windows og andre enheder.
- Gemte visninger vises ved den geografiske kortoversigt.
- GitHub-forsiden har fire løse filer. Engelsk introduktion, bidragsvejledning og Mac-hjælp ligger i mapper; den gamle danske dublet er fjernet.
- Rettelsen fra 1.12.1 er med: almindelig gemning og udlevering kræver ikke genindlæsning efter ændringer i baggrunden.

## 1.12.1 · Arbejd videre uden unødig genindlæsning

Fjerner den generelle afvisning af ændringer fra andre faner/enheder, indtil brugerprofiler og samtidig redigering bliver udviklet samlet. Kort kan fortsat udleveres og rettes, når Google-delingen skifter status i baggrunden. Kontrol af kort, datoer og dobbelte udleveringer er bevaret. [Læs nyheder og opdateringsråd](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/RELEASE-NOTES.md).


## 1.12.0 · Mere overblik over dine distriktskort

En samlet opstartsguide, import af eksisterende kort og udleveringer, bedre telefon-/tabletbetjening og et tydeligere overblik i det daglige. Arbejd med adresser og kort, gem opgaver, print oversigter, og vælg selv, om du vil dele kortbilleder med QR-koder.

Læs [nyhederne og opdateringsvejledningen](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/RELEASE-NOTES.md). Tag en privat sikkerhedskopi i appen før opdatering.

## 1.12.0-beta.62 · Sikkerhedskontrol før stabil

- Opdatér den lokale PDF-læser fra pypdf 6.10.0 til 6.21.2 med kendte rettelser til ressourceforbrug. Bevar separat importproces, tids-/hukommelsesgrænser og lokal behandling.
- Afvis DTD/XML-entiteter i XLSX-parseren uanset XML-kodning; almindelige UTF-16-ark fungerer fortsat.
- Udvid API-prøver for login, tokens, fremmed Origin og filstier. Tilføj afhængighedskontrol og kontrol af alvorlige statiske Python-fund før beta/stabil publicering.
- Forenkl menupunktet Idéer og feedback. Adressehentning og Drive/gendannelse er ejerbekræftet; løbende adressestatus (W82) ligger efter stabil.

## 1.12.0-beta.61 · Manuel kortinddeling og klargøring til stabil udgivelse

- W81: fjern automatiske grænse- og inddelingsforslag fra aktiv opsætning. Gamle personlige planer peger på manuel korttegning; IB-import og eksisterende data bevares.
- Afvis gamle forslags-/oprettelseskald på serveren. Bevar generator, tidligere vejledninger og isolerede prøver til senere udvikling.
- Opdatér kom-i-gang og begrænsninger, og saml udestående ejerprøver før stabil udgivelse. Overførte Google-ønsker er ryddet efter ejerens bekræftelse.

## 1.12.0-beta.60 · Adressehentning, kortdata og læsbare fejlforklaringer

W78: DAR GraphQL genprøver midlertidige netfejl og HTTP 429/500/502/503 op til to gange på samme forespørgsel og kildetidspunkt. Ventestatus vises, serverens korte Retry-After respekteres, og pause kan afbryde ventetiden. Længere/ukendt cooldown stopper sikkert. Login-/skema-/certifikatfejl genprøves ikke automatisk; tids- og størrelsesgrænser bruger stadig mindre udsnit. NET-DNS, NET-RESET, NET-CONNECTION og NET-TLS skelner sikre fejlkategorier uden nøgler, URL eller leverandørtekst. Færdige udsnit og kontrollen før adresseændringer bevares. Ejerens konkrete hentning skal stadig genprøves.

W79: Hentning af veje, bygninger, vandløb og jernbaner kræver intet postnummer. Feltet vises og kræves kun, når man vælger adresser med den ældre kilde. Med Datafordeleren hentes alle postnumre i udsnittet. Et skjult felt sendes ikke og kan ikke blokere kortdatahentningen.

W80: Gemmestatus med en forklaring kan åbnes med tryk eller tastatur. Hele teksten står i et panel, der tilpasses skærmen og kan rulles. Den tidligere afkortning af årsagen på telefon er erstattet; åbne formularer og gemningskontroller bevares.

## 1.12.0-beta.59 · Feedback uden konto eller e-mail

W23: Menupunktet Idéer og feedback åbner nu den verificerede Tally-formular i en ny fane. Menuen forklarer tjenesten og håndtering af manuelt indsendt tekst/billeder. Ingen lokale data, nøglefiler eller logs overføres automatisk. Ejeren har bekræftet prøven uden login og med billede.

## 1.12.0-beta.58 · Bedre touchbetjening på telefon og tablet

W75: På touchskærme får knapper, formularfelter, menuer og kortets zoom større trykflader. Formulartekst er mindst 16 pixels, så felter på iPhone/iPad ikke alene udløser automatisk zoom på grund af lille tekst. Dialoger tilpasses også skærmens aktuelle højde i liggende visning og holder rulning inde i dialogen.

På smalle skærme vises hvert kortforslag som en samlet lodret række med nummer, navn, område, besøg og kontrol/advarsler. Alle felter kan gennemgås uden at rulle tabellen sidelæns. Tastatur- og skærmlæseroplysninger samt oprettelsesgodkendelsen bevares. Skrivebordsvisning og print ændres ikke.

## 1.12.0-beta.57 · Komplette adresseudsnit og kortforslag uden kort HTTP-tidsgrænse

W76: Med Datafordeleren hentes adresser nu direkte fra DAR-punkter indenfor det viste udsnit. Alle postnumre i udsnittet medtages, også veje der mangler i OpenStreetMap, og grænsen på 45 OSM-vejnavne bruges ikke til denne hentning. Store udsnit opdeles i små opslag med ét fælles tidspunkt; tids-/størrelsesfejl opdeler videre, og ufuldstændighed vises tydeligt. Færdige udsnit bevares ved fejl. Baggrundens OSM-hentning er særskilt og kan fejle uden at blokere DAR-adresser. Den ældre adressekilde bevarer sine begrænsninger. Samlet distriktsgrænse er fortsat valget til større, vedvarende hentninger.

W77: Forslag til distriktskort og kontrol af rettede grænser kan nu beregnes i baggrunden på den lokale server. Browseren følger med korte statuskald, så en beregning over 30 sekunder ikke alene afbrydes som en Wi-Fi-/VPN-fejl. Kun ét forslag beregnes ad gangen, og forladte eller forældede svar erstatter ikke en nyere redigering. Netfejl og udløbet forespørgsel har hver sin forklaring. Forslag er fortsat læsning; kort oprettes først efter kontrol og OPRET KORT. Det parkerede arbejde med nye vejnetfunktioner genoptages ikke.

## 1.12.0-beta.56 · Natlig adressekontrol på Home Assistant

W73: Under Opgaver kan du nu slå automatisk adressekontrol til, vælge hver 1–30 dage og et klokkeslæt i serverens lokale tid. Kontrollen bruger den gemte samlede distriktsgrænse og din Datafordeler-forbindelse. Appen skal køre i Home Assistant.

Forsiden viser seneste gennemførte kontrol samt antal nye, ændrede og foreslået fjernede adresser. Alle fund venter på gennemgang og udtrykkelig godkendelse. Eksisterende distriktskort ændres ikke automatisk. En ufuldstændig hentning giver aldrig forslag om fjernelser.

Ved fejl gemmes fremdriften, og opgaven prøver automatisk igen efter stigende ventetid. Genstart fortsætter samme udtræk. Manuelle hentninger, grænseændring, nulstilling og gendannelse venter, mens kontrollen arbejder eller afventer genprøve. Slå opgaven fra for at stoppe efter det aktuelle opslag.

## 1.12.0-beta.55 · Lille logo på Drive-kortet

W72: Det digitale distriktskort har nu et lille LTM-logo øverst til højre med “Local Territory Manager” under. Kortets lyse baggrund, husnumre, besøgsprikker og printforside bevares. Logoet dannes lokalt uden ekstra netkald eller persondata.

Eksisterende Drive-billeder ændres først via Opdater Google Drive-upload, ny forhåndsvisning og udtrykkelig godkendelse. Samme fil og QR-link bevares.

## 1.12.0-beta.54 · Enkel topbar og tydeligere Drive-kort

W70: Menighedsnavnet er fjernet fra topbaren. Logo, betamarkering og gemmestatus bevares, og det gemte navn bruges fortsat i indstillinger, sidepanel og rapporter.

W71: Det digitale kort til Google Drive viser nu OSM-baggrunden med 50 % styrke over hvidt. Farvet fyld inden for distriktsgrænsen er fjernet fra dette billede, så det ikke mørkner baggrunden igen. Besøgsprikker er kraftigere røde, og husnumre er mørkerøde med hvid kontur; begge vises uden dæmpning. Grænse, oplysninger og printforside bevares.

Eksisterende Drive-billeder ændres først, når du vælger Opdater Google Drive-upload, kontrollerer det nye billede og godkender publicering. Status viser, når kortbilledet bruger et ældre design. Samme fil og QR-link bevares. Der sker ingen automatisk genpublicering, og private IB, noter og forkyndere indgår fortsat ikke i billedet.

## 1.12.0-beta.53 · Vandløb og jernbaner som skel

W16, delopgave: Hentning af et kortudsnit medtager nu også offentlige vandløb og jernbaner fra OpenStreetMap. Distriktsforslag kan følge egnede gennemgående forløb før vejforslagene. Blå vandløb og grå stiplede jernbaner vises i editoren og i den lokale kortbaggrund; husnumre og besøgsprikker beholder deres styrke. Ældre kortdata skal opdateres ved at hente relevante udsnit igen.

Første beregning bruger sammenhængende forløb i lag 0 uden bro-/tunnelmærkning. Huller, navneskift, forgreninger og bro-/tunnelstykker forbindes ikke ved gæt. Alle adresser og lejligheder kontrolleres med de eksisterende geometriregler, og ændrede skel kræver ny forhåndsvisning. Forslag kan fortsat rettes og kræver OPRET KORT før oprettelse. Kontroltekster om skel følger dansk/engelsk og bevarer kildens navne. W16 er fortsat delvist åben for mere komplekse vejnet og yderligere skeltyper. [Vejledning om naturlige skel](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/develop/docs/NATURLIGE-SKEL.md).

## 1.12.0-beta.52 · Forslag langs enkle vejforgreninger

W16, delopgave: Automatisk distriktsinddeling kan nu også afprøve gennemgående forløb i enkle forgrenede vejnet. Kun lokale vejstykker med samme navn og præcist fælles registrerede punkter forbindes; knæk og kurver bevares. Eksisterende uforgrenede forslag prøves først. Besøgstallet og de hidtidige geometrikontroller vælger mellem mulige faktiske vejforløb, før et geometrisk reserveforslag anvendes.

Navneskift, huller, sløjfer og uklare kryds gættes ikke, og søgningen har faste arbejdsgrænser. Lejligheder i samme hus holdes sammen; adresser, besøgstal og eksisterende kort bevares. Forslaget kan fortsat rettes og skal godkendes med OPRET KORT. Ingen nye netkald eller automatisk kortoprettelse. Dansk/engelsk vejledning forklarer begrænsningerne. W16 er ikke samlet afsluttet: vandløb, jernbaner og mere komplekse vejnet kræver fortsat manuelt arbejde.

## 1.12.0-beta.51 · Topbar og roligere digitale kort

W66: Menighedsnavnet i topbaren står nu ved logoets hovedtekst i stedet for midt mellem hovedtekst og undertekst. Tom plads i logoets højre side udnyttes, uden at ændre logoets 360 × 66 pixels. Lange navne afkortes fortsat visuelt med den fulde tekst i hjælpeteksten; mobilens kompakte identitet, betamarkering og gemmestatus bevares. Den private reference er ikke medtaget i kode eller kontrolbilleder.

W40: På digitale Drive-kort nedtones kun baggrundens vejkort, ikoner/skel og lokale vej-/bygningslag. Valgte husnumre, røde besøgsprikker, distriktsgrænse, miniature og kildeangivelse beholder deres styrke. Almindelige lokale korteksporter ændres ikke. Eksisterende Drive-filer, links og QR bevares; layoutopfølgning beder om ny lokal forhåndsvisning og udtrykkelig godkendelse, ikke automatisk upload eller genpublicering. Fiktive tætte/spredte kort og topbarer i stabil-/betavisning ved 320/390/768/1440 pixels indgår nu i browserkontrollen.

## 1.12.0-beta.50 · S-13 med navne og udleveringer

W69: Den lokale historikimport aflæser nu også forkyndernavne, udleveringer og indleveringer i understøttet digital S-13. Efter ejerens afklaring bliver en udlevering uden indleveringsdato et aktivt udlån; en indlevering afslutter udlånet og registrerer kortet som gennemgået. Forhåndsvisningen viser navnematch, nye forkyndere, aktive/afsluttede udlån og konflikter før udtrykkelig godkendelse. En ekstra femkolonners CSV-skabelon understøtter manuel overførsel fra scanninger og fotos; den eksisterende skabelon med kortnummer/dato bevares.

Entydigt ens navne genbruges. Dubletter og allerede kendte kortcyklusser springes over; overlappende udlån, uklare navne, ugyldige datoer og gendannelige poster skal rettes før lagring. En kendt gennemgang uden udlån kan kobles til den importerede udlevering uden at tælle igen eller ændre dato/besøgstal. Eksisterende udlån overskrives ikke. Aktive udlån med ældre udleveringsdato medtages; afsluttet historik følger toårsgrænsen. Hele importen gemmes atomisk. Historiske besøgstal gættes ikke, og filer/navne videresendes ikke automatisk.

## 1.12.0-beta.49 · Forstå Adressevælger og token

W36: Kortdata forklarer nu Adressevælgerens online vejforslag, valgfriheden og forskellen fra Datafordelerens DAR GraphQL-forbindelse og API-key. Det fremgår, hvilke søgefelter der sendes ved online forslag, og hvordan forslag kan begrænses til lokalt gemte veje. Status viser standardtoken eller gemt egen token uden at vise værdien. Det valgfrie tokenfelt er flyttet under Avanceret, og det forklares, at et tomt felt og Gem tokenvalg gendanner standardtoken uden at ændre Datafordeler-nøglen. Dansk/engelsk vejledning og link til KDS’ officielle tokenvejledning følger med. Opslag, forbindelser og gemmehandlinger fungerer som før.

## 1.12.0-beta.48 · Sammenlign månedstal med sidste år

W32: Forsidens månedsgraf viser nu parvise søjler for det valgte tjenesteår og samme måneder sidste år. Tabellen viser de præcise datoperioder og registrerede antal. Indeværende måned tælles til i dag og til samme kalenderdato sidste år; afsluttede måneder sammenlignes som hele måneder, og skuddag tilpasses kalenderen. Fremtidige måneder er ikke begyndt. Manglende registreringer fra sidste år vises som ? / Ingen registreringer frem for et bekræftet nul. Der vises ingen misvisende procentændring ved ukendt historik. Gentagne gennemgange og arkiverede kort tælles fortsat med; personnavne og IB indgår ikke.

W31-opfølgning: Den manglende typing_extensions-afhængighed til pypdf på Python 3.9/3.10 følger nu med lokalt og med licens. PDF-processen bruger isoleret Python uden installerede tredjepartspakker, så aflæsningen afhænger af programmets egne filer. Beta.47’s Python 3.9-kontrol identificerede manglen. Udgivelsen kræver nu også fulde Python 3.9-/3.13-prøver direkte i betaforløbet. Historikimporten kræver fortsat grønne kontroller før afslutning.

## 1.12.0-beta.47 · Lokal historikimport

W31: Indstillinger → Data kan importere de seneste to års gennemgange fra CSV og understøttede digitale S-13-filer: den originale udfyldelige formular og LTM’s egen PDF-eksport. Filen aflæses lokalt; kortnummer og gennemgangsdato vises i en redigerbar kladde før udtrykkelig godkendelse. Navne og udleveringsdatoer importeres ikke. Dubletter og ældre datoer vises som fravalgte; ukendte/uklare kort, fremtidige datoer og gendannelige poster skal rettes før hele importen kan gemmes. Eksisterende udlån og historiske registreringer overskrives ikke. Aktuelle og arkiverede kort understøttes. En ændret database eller udløbet forhåndsvisning kræver ny kontrol.

Historiske besøgstal gættes ikke fra nutidens adresser: importerede gennemgange markeres med ukendt besøgstal, og rapporten forklarer deres udeladelse fra besøgsskønnet. Scanninger/fotos og andre PDF-layouts indtastes i CSV-skabelonen. Ekstern OCR er kun et frivilligt alternativ med tydelig oplysning om usikker privatlivssikkerhed; ingen fil videresendes automatisk. PDF-læsning sker i en tidsbegrænset lokal proces med medfølgende pypdf og licens.

Eksportforbedringerne fra den ikke udgivne beta.46-kandidat følger med. Dens pakkekontrol stoppede korrekt, fordi server- og HA-versionen var forskellige; begge versionsfelter er nu beta.47. Ingen offentliggjort beta overskrives.

## 1.12.0-beta.46 · Hurtigere læsearkiv

W57-opfølgning: PDF-dannelse holder ikke længere databaselåsen under hele arbejdet. Appen kan fortsat bruges, og dataversionen kontrolleres igen før download; ændrede data giver ingen delvis fil. Kortfiltreringen bruger ét frosset datasnapshot frem for gentagne databaseopslag pr. kort. Kortbilleder dannes med en uigennemsigtig baggrund for mindre billedbehandling. Ingen ændring af gemte data eller arkivets indhold.

407 Python-prøver består (én forventet overspringning), herunder ændring under eksport og optælling af databaseopslag. Eksisterende browser- og platformskontroller kræves før udgivelse.

## 1.12.0-beta.45 · Læsearkiv og forenklet forside

Tre sammenhængende ønskepunkter: W57, W68 og W48. Det fulde lokale læsearkiv fra eksportarbejdet i beta.44 følger med her: fire PDF'er, CSV og S-13 for hele historikken med indlejrede digitale OpenStreetMap-kort. Hvert kort vises og medtages af brugeren; ingen automatisk massehentning eller Google-upload.

W68: Ejerens nye feedback erstatter W44-løsningen: både datointervallet og den forklarende tekst under Dit lokale overblik er fjernet helt. Tjenesteårets overskrift og rapporternes egne perioder bevares.

W48: Forsidens gennemsnit viser hele måneder og dage i stedet for et decimaltal i måneder. Samme kendte intervaller for aktuelle og arkiverede kort anvendes. Gennemsnittet afrundes én gang til nærmeste hele dag og omregnes med 30 dage pr. måned, som oplyses ved tallet. Ental/flertal, 30-/60-dagesgrænser og manglende historik er kontrolleret på dansk/engelsk. Ingen datoer eller historik ændres.

## 1.12.0-beta.44 · Læsearkiv med PDF, CSV og fuld S-13

W57: Indstillinger → Data tilbyder en lokal ZIP, der kan læses uden LTM. Fire PDF'er indeholder alle forsider på den originale blanke formular, IB-bagsider pr. kort, digitale kort og alle opgaver. S-13 følger for hvert tjenesteår i den gemte historik. CSV dækker kort, præcise adresser og eksisterende vejlinjer, IB, udleveringer med forkyndere, gennemgange, områder, forkyndere, opgaver, besøg og menighed. Aktive og arkiverede registreringer bevares. Ingen nøgler, adgangskoder eller rå forbindelses-/indstillingsfiler kopieres.

Digitale kort bruger appens offentligt afgrænsede kortindhold og OpenStreetMap-baggrund. Hvert kort vises og medtages af brugeren før næste kort hentes; der er ingen automatisk massehentning. Den færdige PDF har indlejrede billeder og kræver ikke internet. Kort uden geografi fremgår af forsider og CSV. OSM-attribution bevares.

Eksporten bindes til én dataversion. Manglende billeder, ændrede data, udløbet forløb, annullering eller fejl giver ingen delvis download. ZIP'en har kontrolsummer og læsevejledning og ændrer hverken data, genprintgodkendelser, backupdato eller Google-adgang. CSV bevarer Unicode og beskytter mod fortolkning af brugerdata som regnearksformler; tegn uden for PDF-standardfonten vises med deres Unicode-kode i læse-PDF. Den eksisterende gendannelsesbackup er uændret.

## 1.12.0-beta.43 · Fælles rapportoversigt og forklaret datoperiode

W51: Rapporten samler tjenesteåret og de seneste 12 måneder med hver sin periode, gennemgange, anslåede besøg, dækning og månedsgraf på én fælles oversigt. Oversigten findes både digitalt og på den første printside. Kortene følger fortsat på to særskilte sider med tydelige periodeoverskrifter; original S-13 og distriktets oplysninger bevares. Rapportens to første faner vælger, hvilket periodekort der vises under oversigten. Målinger, historiske år og aktuelle kortbestande beregnes som før. Ingen IB-adresser indgår i oversigten.

W44: Datoerne under Dit lokale overblik forklarer nu udtrykkeligt perioden for gennemgange og anslåede besøg. Kort og opgaver viser aktuel status; datoerne er ikke en installationsdato. Hjælpen følger dansk/engelsk.

## 1.12.0-beta.42 · Ændringslog i Home Assistant

W64: Home Assistant-pakkens ændringslog var stoppet ved beta.29, selv om projektets ændringslog var opdateret. Appmappens CHANGELOG.md indeholder nu også beta.30–42 i samme rækkefølge som projektets ændringslog. Tidligere versionsnoter bevares; ældre udgivelser og tags ændres ikke.

Pakning af både komplet program og HA-beta afvises fremover, hvis de to ændringslogfiler er forskellige, eller den aktuelle version ikke står først. Prøver dækker den tidligere fejl, bevaret historik og den faktiske ZIP-fils ændringslog/kontrolsum. Der ændres ingen lokale data eller adressefunktioner. Visning på ejerens egen HA kontrolleres efter næste opdatering.

## 1.12.0-beta.41 · DAR-opslag uden aliaser

Ejerens læsende beta.40-kontrol accepterede almindelige opslag for alle fem DAR-entiteter, men afviste både ét alias og flere rodfelter. Adressehentningen bruger nu ét almindeligt opslag ad gangen, også ved mange ID'er. Samme tidspunkt, filtre, separate cursors, afbrydelse og fælles resultat-/anmodningsgrænser bevares. Ingen delvise svar frigives til import. Fiktive leverandørprøver afviser nu aliaser og flere rodfelter; vej- og grænseforløbet fejlede før rettelsen og består efter. En rigtig hentning efter opdateringen udestår; W62 er fortsat åben.

## 1.12.0-beta.40 · Læsende DAR-kontraktkontrol

W62 er fortsat åben. En ny kontrol i Kortdata → Datafordeleren prøver de samme projektioner og filtre som adressehentningen med fiktive søgeværdier. Den sammenligner enkeltopslag, ét alias og ti aliases uden at oprette hentningsjob, gemme adresser eller ændre checkpoints og forbindelsen. Kun faste fejlkategorier, genkendte fejlkoder og en afgrænset liste diagnoseord vises; ingen rå leverandørtekst, data, stier eller nøgler. Prøven er tidsbegrænset. Den eksisterende grønne forbindelseskontrol er ikke en prøve af de faktiske dataopslag. Der er endnu ikke dokumenteret en årsagsrettelse eller en vellykket livehentning.

## 1.12.0-beta.39 · Sikker GraphQL-diagnose og mindre opslag ved størrelsesfejl

W62: Beta.38-prøven fejlede både på grænsen og på en enkelt vej med en generisk GraphQL-afvisning. Den bagvedliggende afvisningsårsag er endnu ikke bekræftet. Fejlteksten viser nu en sikker kategori: GQL-SCHEMA, GQL-ACCESS, GQL-LIMIT, GQL-RESULT eller GQL-REJECTED, opslagets entitet og genkendte fejlkoder/feltnavne. Rå leverandørbeskeder, søgeværdier, URL'er, nøgler og fejlstier vises ikke. Dansk/engelsk bevarer de samme diagnostikkoder.

Kun genkendte størrelsesfejl udløser tilpasning: færre poster pr. side, enkeltopslag i stedet for alias-batches og derefter mindre grænseudsnit. Tidspunkt, filter, cursor og fuldstændighedskontrol bevares; vedvarende fejl stopper begrænset. Andre afvisninger genprøves ikke som størrelsesfejl. HTTP 400/422 med struktureret GraphQL-fejl behandles også. Ingen delvise resultater importeres. Ny faktisk ejerprøve er nødvendig; dette er ikke en færdigmelding af W62.

## 1.12.0-beta.38 · Ret tomme GraphQL-adressehentninger

W62: Punktstatus var fejlagtigt behandlet som adresse-/husnummerstatus 3. DAR-adressepunkter har en særskilt livscyklus med 8 = i brug, og tjenester kan udelade punktstatus. Punktopslag bruger nu entitets-ID/geometri og det fælles faste tidspunkt; husnumre, adresser, veje og postnumre kræver fortsat status 3. Punktsvar uden status og med status 8 accepteres; eksplicit ugyldige punktstatusser og brudte koordinater/relationer afvises. Hentning af vej, postnummer og grænse er dækket af realistiske, fiktive tests.

Gamle GraphQL-grænsecheckpoints genhentes automatisk med rettelsen, så et tidligere tomt udsnit ikke springes over som færdigt. Et reelt tomt resultat får en tydelig advarsel; et tomt GraphQL-svar kan ikke udgå områdets eksisterende lokale adresser. Ejerens prøve i beta.37 bekræftede fejlen; ny faktisk hentning i beta.38 mangler fortsat. Forbindelseskontrol alene er ikke bevis for adressehentning.

Grundlag: [DAR-livscyklus](https://danmarksadresser.dk/adressedata/kodelister/livscyklus) og [DAR GraphQL](https://confluence.kds.dk/pages/viewpage.action?pageId=187105632). Ingen lokale adresser eller nøgler er brugt som testdata.

## 1.12.0-beta.37 · Backuppåmindelse følger serverens kalender

W52-opfølgning: Sidste backupdato og appens i dag regnes nu i samme lokale serverkalender, også når UTC-datoen er dagen før. Dermed kommer 14-dagespåmindelsen ikke en dag for tidligt omkring midnat. Sommer-/vintertid dækkes af syntetiske tests. Det er en ren beregning ved læsning; tidsstempler, backupfiler, historik og udsættelser ændres ikke.

## 1.12.0-beta.36 · Ugentlige opgaver på forsiden

W53: En opgave kan gentages ugentligt på en valgt ugedag. Første forekomst er den valgte dag fra og med i dag. Forfaldne opgaver vises på forsiden og kan markeres udført derfra. Tekst, korttilknytning, opgaven og afslutningshistorikken bevares. Næste forekomst lægges på den valgte ugedag strengt efter udførelsesdagen. Forsinkede uger opretter ikke kopier eller opdigtede gennemførelser.

For tidlig eller gentagen udførelse af samme forekomst afvises; historik og næste dato gemmes atomisk og kan fortrydes sammen. Redigering bevarer historikken. Ingen gentagelse stopper fremtidige forekomster uden at slette opgaven/historikken. Ældre klienters almindelige tekstredigering fjerner ikke gentagelsen. Datoer/historik bevares ved genstart og gendannelse. Ingen automatisk kortflytning, upload eller ekstern påmindelse; dansk/engelsk skifter uden at miste formularens valg og tekst.

## 1.12.0-beta.35 · Lokal backuphistorik og påmindelse

W52: De seneste 100 manuelle backupforsøg vises under Indstillinger → Data med særskilt status for oprettet ZIP, startet browserdownload og afsluttet filskrivning via filvælgeren. Annullering registrerer ingen backup. Fejlet filskrivning beholder kun ZIP-oprettelsen; den udskyder ikke påmindelsen. Filstier, filnavne, nøgler og forbindelsesoplysninger gemmes ikke i denne historik. Eksisterende backupregistreringer bevares uden at blive omtalt som bekræftet filskrivning.

Forsiden påminder, hvis ingen overførsel er registreret, eller der er gået mindst 14 kalenderdage. Udsæt skjuler feltet til næste kalenderdag, ikke i 24 timer. Browserdownload betyder kun, at overførslen er startet; kontrollér filen i browseren. Historikken følger dataene ved gendannelse og indeholder kun registreringer fra før ZIP'ens oprettelse. Ingen automatisk backup, upload eller ekstern besked.

## 1.12.0-beta.34 · Opsætning følger gemte handlinger

W47: Relevante opsætningstrin afsluttes automatisk efter en gennemført gemning: menighed, mappeminimum, begge printprofiler, forkynder, kort, ydergrænse, IB-import og registreret backup. Fremdriften gemmes i samme transaktion som handlingen og følger med ved Fortryd. Åbning, forhåndsvisning og afvist gemning tæller ikke. Spring over og eksisterende fremdrift bevares. Forbindelser og den samlede gennemgang af udleveringer bekræftes fortsat manuelt; én registrering beviser ikke, at hele gennemgangen er færdig.

Nye installationer og en udtrykkeligt godkendt beta-nulstilling starter med mappeminimum 0, også for land. Eksisterende valg ændres ikke. Mappetrinnet afsluttes ved et ændret minimum eller et eksplicit indtastet og gemt 0; en uvedkommende indstillingsgemning godkender ikke standardværdien.

## 1.12.0-beta.33 · Hurtig oprettelse med inklusivt interval

W54: Hurtig oprettelse har et særskilt intervalvalg med start/slut inklusive, valgfrit antal cifre/nuludfyldning og ét valgfrit foranstillet bogstav. 0–300 med fire cifre giver 0000–0300, i alt 301 kort. Bogstavet og nuludfyldningen indgår i den synlige forhåndsvisning. Højst 500 kort oprettes ad gangen, og den eksisterende egen liste er uændret; her betyder 1–10 stadig ét bogstaveligt kortnummer.

Antal og alle endelige numre vises før godkendelse. Serveren efterprøver interval, længder og dubletter igen ved oprettelsen. Eksisterende, arkiverede og gendannelige kortnumre reserveres som før, uanset store/små bogstaver. Et ugyldigt interval eller én dublet stopper hele oprettelsen. Eksisterende kort overskrives ikke.

## 1.12.0-beta.32 · Én samlet opgavefunktion

W50: Noter og opgaver er samlet under Opgaver. Gamle noter bliver opgaver med uændret tekst, kortreference, datoer og udført-status, også efter import af ældre backup. Aktive og gendannelige poster konverteres i en transaktion; aktivitetshistorik ændres ikke til opgaver. Gamle data-/API-navne bevares for kompatibilitet. Redigering af udførte opgaver og tilknytning til arkiverede kort bevarer status og reference.

Navigationen tæller kun åbne opgaver. Kortlisten/mappen viser et tydeligt opgavemærke. Udleveringsformularen viser en stærkere advarsel med de åbne opgaver og opdaterer den ved kortvalg. Der er ingen ny obligatorisk spærring eller automatisk IB-ændring. Separate notefiltre, noteoprettelse og valg af note/opgave er fjernet fra opgavefunktionen. En valgfri opgave kan stadig tilføjes ved aflevering/gennemgang. KTM-besøgets selvstændige tekstfelt kaldes Bemærkning.

## 1.12.0-beta.31 · Logo i fuld størrelse og bevidst kortbetjening

W49: Det eksisterende desktoplogo bevarer 360 × 66 px, mens menighedsnavnet står på samme vandrette linje efter en tankestreg. Mobilikonet bevarer 34 × 34 px. Lange navne afkortes visuelt med hele titlen tilgængelig; beta-markering, navigation og gemmestatus er bevaret.

W59: Kortets interaktive detaljevisning kræver Ctrl/Command til panorering og hjulzoom, eller eksplicit aktivering til touch/tastatur. Normal rulning går til dialogen. Kortet kan låses igen uden at nulstille udsnittet. Lyttere fjernes ved lukning, og nyt kort starter låst. Medlemskab, gemte grænser, eksport og publiceringsgodkendelse ændres ikke.

Disse to ønskepunkter er afgrænset fra beta.30. Rigtig API-hentning og ekstern GitHub-cache/PR-oprydning er fortsat åbne ejer-/Support-trin. Main er stabil 1.11.1.

## 1.12.0-beta.30 · API-hentning og sikkerhedskopi

W62: Hentning af en vej med egen Datafordeler-nøgle afhænger ikke længere af det gamle systems vejforslag. Det gælder også vejene i et lille OSM-kortudsnit. Den nye kilde bruger det præcise officielle vejnavn og postnummer; der vælges ikke en tilfældig nabovej. Regler for komplette adresser, lejligheder, opdateringer og bevarelse af lokale data er uændrede. Rettelsen er testet med fiktive svar; ejerens rigtige API-hentning skal fortsat bekræftes.

W55: Ved HTTP 401/403 forklares på dansk/engelsk, at en ny nøgle kan være op til 15 minutter om at blive aktiv. Afvist adgang og nøglekontrol beskrives fortsat; andre net-/serverfejl forklares ikke som aktiveringstid. Prøv forbindelse er fortsat en bevidst handling.

W46: Indstillinger tilbyder Gem sikkerhedskopi som… i sikre browserkontekster med understøttet filvælger. Filnavn og placering vælges før hentningen. Annullering henter intet og registrerer ikke en backup. Først en afsluttet filskrivning registreres som gemt. Almindelig download og hjælp til browserens placering er bevaret, også i desktopudgaven; ingen automatisk upload.

W61: Udgivelsespakker og grene/tags er renset; GitHub-cache, gamle PR-henvisninger og resterende udgivelsesmetadata afventer ekstern oprydning. W63: Det brede eftersyn af faste eksempler er afsluttet med en ny test af tomme hentefelter. Main er fortsat stabil 1.11.1.

## 1.12.0-beta.29 · Neutrale felter i adressehentning

Faste vej-, postnummer- og husnummereksempler er fjernet fra Hent en vej og adressevalget. Felterne beskriver nu kun deres formål på dansk/engelsk. Den tidligere stedtekst er også fjernet fra oversættelser og erstattet med opdigtede testdata i prøverne. Gemte lokale adresser og den eksisterende vejnavnesøgning bevares.

W61 er fortsat kritisk og åben: rettelsen i denne beta er ikke en færdigmelding af oprydningen i tidligere udgivelser, betaer eller Git-historik. W62 om fejlslagen faktisk API-hentning er en særskilt, endnu ikke rettet fejl.

## 1.12.0-beta.28 · Kompakt opsætning og menighed i topbaren

Menighedsnavnet vises ved projektets logo i topbaren. Lange navne afkortes visuelt og kan læses i feltets titel; navn og gemmestatus holder sig inden for topbaren, også på mobil og i HA-betaen. Navnet gemmes fortsat kun lokalt.

Opgavelisten på forsiden fylder nu én sammenklappet linje med antal resterende trin. Listen har kompakte handlinger og genveje til menighedsnavn, mappeminimum, printvalg, valgfri Google Drive og første forkynder. Udført/overspringning og eksisterende fremdrift bevares. Listen spærrer ikke normal brug.

Indstillinger → Printprofiler kan nu gemme valg af blankt eller fortrykt papir særskilt for forside og IB-bagside, også før første kort. Eksisterende mål bevares. Gemning åbner ikke print og godkender ingen ændret kortside.

## 1.12.0-beta.27 · Daglig aflevering og tydelig opgavestatus

Kortstatus har nu tydelige farver for udleveret, i mappen og i kassen. Direkte udleverings-/afleveringsknapper åbner de normale kontrollerede formularer; den valgte kortmenu bevares. Ændrede kort kan fortsat være spærret for udlevering.

Daglig brug har fanen Aflever pr. forkynder: alle aktive udlån grupperes efter forkynder, flest kort først, med navnesøgning og aflevering fra hver kortlinje. Ens navne med forskellige registreringer holdes adskilt. Listen og sidemenuen fungerer på smalle skærme og på dansk/engelsk. Ingen udlåns- eller delingsregler ændres.

Cirkelknappen ved opgaver og noter er forklaret med synlig hjælp og tooltip: markér udført eller genåbn uden at slette teksten.

## 1.12.0-beta.26 · Opgavelisten kan afsluttes

Planen på forsiden er nu en liste med Udført, Spring over og Fortryd. Afsluttede trin streges ud. Listen forsvinder, når alle trin er udført eller sprunget over; gemt status huskes på installationen efter genindlæsning. At åbne et trin afslutter det ikke automatisk. Opsætningsplanen kan stadig åbnes fra Indstillinger. Dansk/engelsk og smalle skærme er kontrolleret med fiktive data.

## 1.12.0-beta.25 · Præcis forklaring af adressefristen

Januarfristen gælder lukningen af gammel DAR REST-adgang. API-nøgler til DAR GraphQL kan også oprettes bagefter. Nøglevejledningen og opsætningsplanen forklarer nu forskellen og anbefaler overgang i god tid for at undgå pause i nye hentninger. Gemte adresser bevares. Officielle kilder er kontrolleret 17.10.2026.

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

## 1.12.0-beta.7

- Kortdata får trinvis vejledning til egen Datafordeler-konto og API-key, lokal lagring og eksplicit forbindelseskontrol. Nøglen udelades fra portable sikkerhedskopier.
- Dette klargør DAR v3-forbindelsen; selve adresseimporten flyttes i et efterfølgende trin.

## 1.12.0-beta.6

- Den ekstra opfølgningsliste er fjernet fra KTM-rapporten og samlet PDF efter ejerens ønske. De øvrige rapportoversigter og original S-13 bevares.

## 1.12.0-beta.5

- Opsætningsguidens radioknapper arver ikke længere tekstfelters fulde bredde. Valgtekst og forklaring holdes inden for deres boks på smalle skærme.

## 1.12.0-beta.4

- Rapporten får en aktuel opfølgningsliste med manglende historik, gennemgange over 12 måneder og aktuelle udlån over fire måneder.
- Kort vises én gang med datoer og årsager; arkiverede kort udelades. Ingen personnavne, noter eller IB-adresser føjes til listen. Samme liste følger samlet PDF.

## 1.12.0-beta.3

- Fast topbar ved rulning på computer og mobil; logoet åbner forsiden med kontrol af ugemte ændringer.
- Fuldt projektlogo i topbaren på computer, kompakt mærke på mobil og tydelig beta-identitet.
- HA-ikon og logo følger nu både normal programpakke og betapakke.

## 1.12.0-beta.2

- Betaen kan nulstille testdata med bekræftelse, automatisk lokal sikkerhedskopi og kontrol af delte kort. Login og forbindelser bevares.

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
