# Ønskeliste og nye opgaver

**Aktuel aftale 17.10.2026: Den faste udviklingsplan er afsluttet (100 %, 10/10). Ønskelisten behandles efter ejerens prioritet. W35, W34 og W38/W39/W41 er udgivet i beta.25–27. W43 (2) og W42 (3) er udgivet i beta.28. Næste er W44 (4), W36/W40 (5), derefter W31 og W06 (6). Hver beta må højst samle tre ønskepunkter. Små nummererede betaer fortsætter; main er stabil 1.11.1.**

Seneste verificerede beta er 1.12.0-beta.28 fra d753d7a, med grønne program-, Mac-, Windows- og HA-kontroller. Lokale ejerprøver er særskilte og tælles ikke som udført automatisk.

## Arbejdsrækkefølge fra 17.10.2026

Kun udestående arbejde står i denne kø. Nyt prioritet -1 går foran køen. W45 er en løbende regel: højst tre ønskepunkter pr. beta, og færre når en stor ændring bør prøves alene. Næste planlagte kodepakke er punkt 1–3. Rækkefølgen justeres ved nye kritiske ønsker eller nødvendige afhængigheder.

| Nr. | Opgave | Prioritet / placering | Afslutning |
| --- | --- | --- | --- |
| 1 | W44 · Forklar datoen under Dit lokale overblik | 4 · næste | Tydelig periode og opgørelsesdato eller fjernet felt. |
| 2 | W36 · Forklar Adressevælger og særskilt token | 5 | Konkret formål, valgfrihed og forskel fra Datafordeler-nøglen. |
| 3 | W40 · Nedton baggrunden på digitale kort | 5 | Husnumre og røde prikker forbliver tydelige; ingen ændret offentlighedsgrænse. |
| 4 | W31 · Importér to års gennemgange fra CSV og S-13 | 6 · prototype bevaret, ikke udgivet | Lokal kontrol af datoer/kortnumre/dubletter; digital PDF og lokal OCR undersøges og verificeres før godkendt import. |
| 5 | W06 · HA-sikkerhedsprofil og adgang | 6 | Vurder profil og mulige forbedringer; større ændringer forelægges ejeren før implementering. |
| 6 | W16 · Naturlige skel og avancerede vejnet | 7 | Gennemgåelige, redigerbare inddelingsforslag efter reelle skel. |
| 7 | W32 · Sammenlign månedstal med sidste år | 8 · efter historikimport | Samme måned/periode, korrekt håndtering af ufuldstændig historik og indeværende måned. |
| 8 | W28 · Codex Security-gennemgang | 9 · senest blokeret af manglende scanruntime | Kontrollér scanneradgang ved opstart; gennemfør scan og vurder fund, når værktøjerne er tilgængelige. Ingen formel scanning er udført. |
| 9 | W23 · Feedback uden GitHub-konto | 10 · afklaring før endelig demosynkronisering | Anbefal kanal, modtager og håndtering af bilag/persondata; opret ikke automatisk en ny offentlig tjeneste. |
| 10 | W37/W12 · Opdatér webdemo og kontrollér det direkte link | 9/5 · efter appens funktionsvalg | Demo matcher den kontrollerede app; faktiske Pages-link og første åbning prøves med fiktive data. |
| 11 | Ejerprøve · Datafordeler | Egen konto og installation | Egen nøgle, én vej og et lille område; kontrollér husnumre, lejligheder og opdatering. |
| 12 | Ejerprøve · Google Drive og QR | Egen konto og telefon | Samtykke, godkendt kort, adgang under udlån, lukning ved aflevering og genåbning ved genudlevering. |
| 13 | Ejerprøve · HA, telefon, VPN og flytning | Eget udstyr | Opdatering/genstart, login, separat beta/stabil, privat backup og gendannelse; eventuel flytning bekræftes før gammel installation opgives. |
| 14 | Ejerprøve · Fysisk print og betjening | Egen printer/hjælpemidler | A4-prøve, rigtige for-/IB-bagsider, mål/placering/QR samt mobil/tastatur og eventuel skærmlæser. |
| 15 | Samlet slutkontrol og stabil udgivelse, inklusive W10 | Efter relevante kode- og ejerprøver | Gentag program-/platform-/browser-/pakkekontrol, saml dokumentation/versioner, aktivér GitHub-feedbackformular via main og verificér stabil udgivelse. |
| 16 | W08 · Anbefal om gammelt repository kan arkiveres | 10 · efter stabil udgivelse | Kontrollér bevaret kode, historik, vejledninger og pakker; giv anbefaling. Ingen automatisk arkivering eller sletning. |

Punkt 9 afgør eventuelle feedbackvalg før den endelige demo i punkt 10, så demoen ikke straks skal laves om. Arkivanbefalingen afhænger af den stabile udgivelse og ligger derfor sidst. Blokerede punkter forbliver åbne; øvrigt uafhængigt arbejde kan fortsætte. Ejerprøverne kan begynde tidligere, så snart de relevante funktioner er klar, men tælles ikke som automatisk udført.

## Registrerede ønsker og historik

| ID | Ønske | Ejerprioritet | Placering og status | Færdig når |
| --- | --- | --- | --- | --- |
| W45 | Saml højst tre ønskepunkter pr. betaudgave | -1 · kritisk | Fast procedure fra nu; erstatter krav om nødvendigvis én beta pr. punkt | En beta kan indeholde 1–3 færdige ønskepunkter efter grønne kontroller. Udgivne versioner overskrives ikke, develop gemmes løbende, og main opdateres ved særskilt stabil udgivelse. |
| W44 | Forklar eller fjern den misvisende dato under Dit lokale overblik | 4 | Næste opgave; før W36/W40 | Datointervallet har en kort, præcis forklaring af, hvilken periode tallene dækker, eller fjernes hvis det ikke giver værdi. Tjenesteårets begyndelse og opgørelsesdato forveksles ikke med installationsdato. Dansk/engelsk og relevante datoeksempler kontrolleres. |
| W43 | Vis menighedsnavnet i topbaren sammen med projektets identitet | 2 | Udgivet i beta.28 med grønne program-, platform- og HA-kontroller | Det lokalt gemte navn vises ved logo/navn og Distrikt, også på mobil. Lange navne kan aflæses uden at dække gemmestatus eller navigation. Der bruges kun fiktive navne i GitHub og prøver. |
| W42 | Gør opgavelisten kompakt, og tilføj genveje til menighed, mappeminimum, print, Google Drive og første forkynder | 3 | Udgivet i beta.28 med grønne program-, platform- og HA-kontroller | Kompakt sammenklappelig liste med udført/overspringning, genveje til navngivning, mappeminimum, fortrykt papir på begge sider, valgfri Drive-forbindelse og oprettelse af første forkynder. Ingen ny spærring af normal brug eller automatisk deling. |
| W41 | Forklar cirkelknappen ved noter og opgaver i appen | 3 | Implementeret og prøvet til beta.27 | Synlig forklaring og tooltip fortæller, at cirklen markerer udført, flueben genåbner, og teksten ikke slettes. Tastatur/skærmlæser og dansk/engelsk bevares. |
| W40 | Gør baggrundskortet på digitale Drive-kort mere afdæmpet, og bevar husnumre og røde adresseprikker tydelige | 5 | Planlagt | Baggrundens ikoner/skel nedtones uden at svække valgte huse, husnumre, grænser eller eksisterende offentlighedskontrol. Fiktive tætte og spredte kort gennemgås visuelt før udgivelse. |
| W34 | Afsluttelig opgaveliste efter guiden med overstregning og spring over | 3 | Implementeret og prøvet til beta.26 | Hvert punkt kan udføres eller springes over. Listen skjules, når alle punkter er afsluttet; genåbning og eksisterende opsætning bevares. |
| W35 | Forklar januarfristen korrekt: kan API-nøgler oprettes bagefter? | 1 | Forklaring rettet til beta.25; officielle kilder kontrolleret | Officielle kilder efterprøves. App og vejledning skelner mellem lukning af gammel REST-adgang og fortsat oprettelse af GraphQL-nøgler. |
| W36 | Forklar Adressevælger og dens særskilte token forståeligt | 5 | Planlagt | Formål, valgfrihed og forskel fra Datafordeler-nøglen beskrives konkret; uklare tekniske menutekster forbedres. |
| W37 | Bring webdemo i overensstemmelse med den udgivne app | 9 | Planlagt til sidst i funktionsforløbet | Demo følger kontrolleret produktudgave med udelukkende fiktive data og tydelige begrænsninger. |
| W38 | Farver efter kortstatus og direkte indlever/udlever i daglig brug | 3 | Implementeret og browserprøvet til beta.27 | Status og primære handlinger får læsbare farver og direkte adgang; eksisterende sidemenu med flere handlinger bevares. |
| W39 | Aflever pr. forkynder med navnesøgning og sortering efter antal kort | 5 | Implementeret og browserprøvet til beta.27 | Alle udleverede kort grupperes tydeligt efter forkynder; flest tildelte først. Søgning og normal aflevering fungerer fra oversigten. |
| W33 | Statusfanen skal kun vise det, der mangler; færdige punkter fjernes | -1 · kritisk | Færdig: statusfanen viser kun udestående punkter | Afsluttede lister og historiske statusreferater fjernes fra ejerens statusfane. Kun udestående udvikling, blokeringer og ejer-/udgivelsestrin vises. Nye ønsker ryddes først efter planlagring. |
| W31 | Importér de seneste to års gennemgange fra en skabelon eller udfyldt S-13 | 6 | Prototype bevaret lokalt; afventer højere prioriteter. Ejer ønsker både digital PDF og scanning/foto hvis muligt | Lokal forhåndsvisning matcher kortnumre, datoer og dubletter før udtrykkelig godkendelse. Ingen eksisterende udlån eller registreringer overskrives. Digital S-13 læses lokalt; lokal OCR undersøges. Eksternt værktøj er kun et frivilligt alternativ med tydelig besked om, at tredjeparts privatlivssikkerhed ikke kan garanteres. |
| W32 | Sammenlign månedlige gennemgange med samme måned sidste år på forsiden | 8 | Planlagt efter højere prioriteter | Graf/tabel viser sammenlignelige månedstal og manglende historik tydeligt; indeværende måned sammenlignes til samme dato. Eksisterende optælling og privatlivsgrænse bevares. |
| W29 | Opdatér develop og beta løbende, og main ved stabil udgivelse | -1 · kritisk | Bekræftet som fast procedure; featureændringer gemmes på develop og udgives som immutable beta efter gates; main ændres først ved stabil udgivelse | Status, udviklingskode og kontrolleret betakanal følger hinanden, uden at en allerede udgivet beta overskrives eller main opdateres ved en beta. |
| W30 | Læsbare navneforslag: lys tekst på en lysere mørk baggrund | 5 | Implementeret og browserprøvet til beta.24 | Navneforslag har læsbar normal/hover/tastaturmarkeret tilstand i appens mørke tema, også på smal skærm. Valg, tastatur og lokale data bevares. |
| W28 | Gennemgå hele programmet med Codex Security og skriv eventuelle vurderede risici i statusdokumentet | 9 | Blokeret i denne session: Codex Security-pakkens nødvendige referencer og preflight-/scannerværktøjer er ikke tilgængelige | En repositorygennemgang med den angivne Codex Security-færdighed er udført, og eventuelle validerede fund får et særskilt felt under Hvor langt er vi? Private data holdes ude af scanning og GitHub. Fund rettes og verificeres efter vurdering. |
| W25 | Én samlet opsætningsguide med information om fordelene ved lokal drift | 2 | Udgivet i beta.23 med grønne program-, platform- og HA-gates | Den normale spørgsmålsguide er den eneste guideindgang. Information om lokal computer/HA, valgfri kort/Drive og privat backup er integreret. Geografi- og importværktøjer bevares som handlinger i den personlige plan; ingen parallel avanceret velkomstguide. |
| W26 | Rundturen er en obligatorisk del af opsætningen, og opsætningen lukkes efter fuldført rundtur | 2 | Udgivet i beta.23 med grønne program-, platform- og HA-gates | Førstegangsforløbet kan ikke markeres fuldført ved kun at gemme svar. Rundturens sidste trin afslutter forløbet og viser appen/den personlige opgaveliste uden at genåbne guiden. Afbrydelse kan genoptages; eksisterende registreringer og tidligere fuldført opsætning bevares. |
| W27 | Følg op på adresseimport, januarfristen og egen API-nøgle | 3 | Officielle kilder genkontrolleret 17.10.2026; direkte nøgletrin og januarfrist til beta.23; egen konto udestår | Genkontrollér aktuelle officielle kilder og den eksisterende GraphQL-import/nøglevejledning. Forklar konkret hvad der er klar, hvad ejeren skal oprette, og hvilke kontoprøver der udestår. Ingen adgangsnøgler indsamles i chat/GitHub. |
| W24 | Redesign af det digitale QR-kort med moderne udseende og lille miniature af kortets printforside | 3 | Udgivet i beta.12; fiktiv visuel SVG/PNG-kontrol og program-/platform-/HA-gates består; egen HA/Drive-prøve udestår | QR-kortet får en tydelig moderne præsentation og en lille visning af det tilsvarende printkort i hjørnet. Vejnavne/layout genbruges fra printforsiden. Ingen IB eller andre private registreringer må indgå. |
| W23 | Undersøg idéer og feedback uden krav om GitHub-konto | 10 | Registreret fra ejerens dokument; afklar mulige kanaler efter de højere prioriteter | Beskriv en enkel mulighed uden GitHub-login, dens modtager og håndtering af bilag/persondata. Ingen ny offentlig indsendelsestjeneste oprettes automatisk. |
| W20 | Ret opsætningsguidens valgfelter, hvor teksten står ved siden af boksen med knapper | 5 | Udgivet i beta.5 med grønne program/platform/HA-gates; offline layout og guideprøver består | Valg og forklaring holder sig i samme boks ved mobil- og skrivebordsbredder. |
| W21 | Nulstil betadata, så en test kan begynde forfra | 2 | Færdig og udgivet i beta.2; program-, platform- og HA-kontroller består | Tydelig bekræftelse, sikkerhedskopi og ny opstart; stabil installation berøres ikke, og offentlige kort må ikke efterlades uden registrering. |
| W22 | Fast topbar under rulning og logo som link til forsiden | 4 | Udgivet i beta.3, samlet med W04/W03; program/platform/HA-gates består | Topbaren bliver på plads, indhold dækkes ikke, og logoet åbner forsiden med appens sædvanlige kontrol af ugemte ændringer. |
| W19 | Små løbende betaudgivelser, som kan testes i HA efter nye funktioner | -1 · kritisk | Færdig: HA-betaer til og med 1.12.0-beta.20 er udgivet; program-, Mac-, Windows- og HA-betagates består; løbende små betaer er nu fast aftale | Kontrollerede betaer kan installeres/opdateres i HA ved siden af stabil udgave. Hver beta har fast version og kort testliste; main forbliver stabil. |
| W14 | KTM-rapportens distriktskort tilpasses automatisk til geografiens højde/bredde, evt. egen side, og distriktnumre vises på kortet | 3 | Implementeret og afprøvet på develop: læsbare etiketter, forbindelsesstreger, automatisk stående/liggende A4 og visuelt kontrollerede fiktive PDF-rapporter; levende browser/OSM står særskilt | Kortet bruger dynamisk format/udsnit og læsbare distriktnumre ved både smalle og brede distriktsgrænser. |
| W15 | Forbedr autofuldførelse af forkyndere ved udlevering | 6 | Udgivet i beta.9; program-/platform-/HA-gates består, visuel mobil-/skærmlæserkontrol udestår | En tydelig, relevant forslagsliste erstatter browserlignende autofyld; tastatur og mobil fungerer. |
| W16 | Automatisk distriktsinddeling skal følge meningsfulde vej- og områdegrænser, ikke firkanter | 7 | Kurvede og sammenhængende vejforløb udgivet i beta.11; naturlige skel og avancerede vejnet udestår | Forslag følger veje og naturlige områder og kan kontrolleres/redigeres før gemning. |
| W17 | Fjern tallet 'midlertidige kort' fra KTM-rapportens 'Distriktets oplysninger' | Ikke angivet | Færdig på develop; rapportprøver består | Tallet vises ikke længere i rapporten; underliggende kortdata bevares. |
| W18 | Google Drive-link åbent kun mens kortet er udleveret; vurder forklarende side ved lukket link | 2 | Implementeret på develop: privat klargøring, åbning/lukning, stabil QR og synlige genforsøg; 32 delingsprøver og API-arbejdsgang består; egen Google-konto afventer | Godkendte billeder åbnes ved udlevering og lukkes ved aflevering uden upload af udlånsdata. Genudlevering bevarer QR; gamle linkindehavere kan dermed også åbne igen. Google ejer adgangssiden; en særlig offentlig side er ikke indført. Kontrol med egen Google-konto står særskilt. |
| W11 | Visuel statusoversigt med korte felter og farvekoder | -1 · kritisk | Færdig i ejerens statusdokument | Tre statusfelter, separate færdig-/næste-felter og kompakte tabeller erstatter den lange statusprosa. Den eksporterede visning er kontrolleret visuelt. |
| W09 | Spejl arbejdsplan og fremdrift i ejerens statusdokument | -1 · kritisk | Færdig: statusfanen er oprettet og læst tilbage | Aktuelle opgaver, næste rækkefølge, prioriteter og procenttal er synlige i fanen Hvor langt er vi? og opdateres ved afsluttede opgaver, mens vi arbejder på LTM. |
| W10 | Erstat opfordring til kodebidrag med idéer og feedback, gerne med bilag | 2 | Implementeret på develop: selvstændigt eksternt menupunkt og GitHub-issueformular; frontend- og GitHub-program/platformskontroller består; browserkontrol og aktivering via main udestår | Et selvstændigt menulink åbner GitHubs offentlige idéformular i ny fane. GitHub står for kommentarer og bilag; brugeren advares om persondata. Ingen lokal feedbackdatabase. |
| W01 | Førstegangsopsætning med spørgsmål og guidet rundtur | Ikke angivet | Færdig på develop; program- og platformskontroller består | Valg af enkel udlevering/kort, KML, IB og manuel/automatisk inddeling giver en personlig plan; rundtur kan springes over og genåbnes uden at oprette data. |
| W02 | Importér allerede fordelte distriktskort fra Excel eller CSV | Ikke angivet | Færdig på develop; program- og platformskontroller består | Skabelon med områder, kortnumre/navne og præcise adresser; lokal kontrol af fejl/dubletter; samlet godkendelse; eksisterende kort overskrives ikke. |
| W03 | Projektets logo tydeligt i appens øverste del | 5 | Udgivet i beta.3 sammen med W04/W22 | Eksisterende mærke gennemgås og suppleres med korrekt logo; lys/mørk baggrund samt mobilbredder er kontrolleret. |
| W04 | Logo og ikon på appens side i Home Assistant | 4 | Udgivet i beta.3: PNG-ikon og logo, med i begge pakker; HA-visning hos ejeren udestår | De relevante HA-billeder findes, følger samme identitet og er med i programpakken; visning på egen HA står særskilt. |
| W05 | Bedre informationstekst ved installation i Home Assistant | 3 | Færdig på develop: beskrivelse og introduktion med funktioner, første start, lokal drift og backup; pakkekontrol består | Kort beskrivelse og dansk introduktion forklarer funktioner, lokal drift, adgang og første start uden intern restliste. |
| W06 | Gennemgå og forbedr HA-appens sikkerhedsvurdering | 6 | Indledende konfigurations-/adgangsgennemgang gemt i docs/HA-SIKKERHED.md; profil og større adgangsændringer udestår | Officielle krav og faktisk konfiguration er gennemgået. Forbedringer med uændret funktion indføres; større ændringer forelægges ejeren først. |
| W07 | Afklar adressekildens levetid og forenkling til OpenStreetMap-baggrund | 5 | GraphQL-import af vej/postnummer/grænse udgivet i beta.8 med grønne gates; egen Datafordeler-/HA-prøve udestår | Kontroller den varslede januarfrist og forskellen på adresser og kortbaggrund. Bevar adressefunktionerne gennem et afprøvet alternativ. OpenStreetMap er den foretrukne synlige baggrund; vurder fjernelse af den lokale reservevisning uden at fjerne lokale data. |
| W08 | Afklar hvornår det tidligere private repository kan arkiveres | 10 | Efter stabil kildekode, pakker og udviklingshistorik er kontrolleret | Giv ejeren en konkret anbefaling, når nødvendig kode og dokumentation er bevaret. Arkivér eller slet ikke noget repository automatisk. |
| W12 | Kontrollér webdemoens direkte link og få den til at åbne korrekt | 5 | Direkte Pages-rodadresse og seks aktiver HTTP 200 uden login; dokumentation rettet; levende browser står særskilt | Verificér det faktiske Pages-link og browserens første åbning; ret eventuelle publicerings- eller linkfejl og brug kun opdigtede demodata. |
| W13 | Gør KTM-rapporten mere nyttig ved besøget | 4 | Opfølgningsliste afvist af ejeren 16.10.2026 og fjernet til beta.6; øvrige rapportforbedringer vurderes særskilt | Undersøg relevante oversigter og gennemgå den eksisterende rapport. Foreslå og tilføj nyttige mål med tydeligt datagrundlag; skeln mellem forslag og eventuelle verificerede krav. |

Ønsker læses ind fra ejerens dokument, når vi arbejder på LTM og mellem afsluttede opgaver. Et punkt fjernes først fra indbakken, efter at ønsket er gemt her. En overførsel betyder planlagt, ikke færdig. Oplyste prioriteter bevares: -1 er kritisk og går før øvrigt arbejde, 1 er snarest, 10 er valgfrit på længere sigt. Arbejdsstatus spejles i ejerens dokument, så arbejdsrækkefølge og fremdrift kan følges uden GitHub. Arbejdsrækkefølge efter den kritiske statusopgave: feedback og udleveringsstyret Drive-adgang (2) afsluttes; derefter HA-information og dynamisk KTM-kort (3), HA-logo og rapportoversigter (4), app-logo, adressekilde og webdemo (5), autofuldførelse og HA-sikkerhed (6), automatisk inddeling (7) og arkivanbefaling (10). Ønsker uden angivet prioritet får ikke et opdigtet prioritetstal. Afhængigheder og en verificeret kildefrist kan ændre rækkefølgen. Private data og eksempler kopieres ikke til denne offentlige plan.

## Aktuel status og næste arbejdssession · 17.10.2026

- Fast plan afsluttet: 100 % (10/10), beta.22 udgivet, main stabil 1.11.1.
- Ejeren har genoptaget ønskelisten. W25/W26 er næste kodeopgave: én normal guide med lokal introduktion og obligatorisk rundtur; bagefter W27 om adressekilde/API-nøgle med prioritet 3.
- W18 kræver fortsat egen Google-kontoprøve. W10's GitHub-issueformular aktiveres i standardbranchen ved en særskilt stabil udgivelse. Disse ejer-/udgivelsestrin er ikke en blokering for de nye guideønsker.
- Nye ønsker nedenfor fjernes først fra Google-dokumentet efter denne plan er gemt på GitHub. Historiske næste-trin i kontroljournalen er ikke den aktuelle rækkefølge.

## W18 · beslutninger og afgrænsning

Ejerens færdige ønske er læst med prioritet 2. Appen bruger den eksisterende Drive-fil og skifter dens offentlige læseadgang efter aktivt udlån. QR kan printes ved privat klargøring og bevares ved genudlevering. Lukning forudsætter kørende app og forbindelse til Google. Afventende/fejlede ændringer vises som ubekræftede; fem forsøg efterfølges af manuel gentagelse. Manuel tilbagetrækning genåbnes ikke automatisk.

Samme QR giver ikke individuel kortholderadgang og forhindrer ikke en tidligere kortholder i at åbne under et nyt udlån. Googles adgangsside ændres ikke; en særlig forklarende offentlig side kræver en ny løsning og er ikke tilføjet. Ingen forkyndernavne, udlån, noter eller IB sendes til Google. Der arbejdes kun med programkode og fiktiv Google-service i prøverne. Egen Google-konto/inkognitotest er et separat ejertrin.

W18-verifikation: 251 Python-prøver (én forventet overspringning), samtlige JavaScript-prøver, 7 programpakkeprøver og arkivbygning består. 32 delingsprøver omfatter netfejl, genstart, delvist udførte Google-anmodninger og køafhængigheder; private HTTP-endpoints er også afprøvet. Ingen rigtige Google-filer eller private databaser er åbnet. Næste udviklingsfokus er W04/W03 (logo og ikon) og W13 (rapportoversigter); W14 har nu bestået nummer- og PDF-kontrollen, mens levende browser/OSM står særskilt. W18-kontrollen med egen konto følger installations-/ejertrinnene.

## W14 · numre og rapportformat kontrolleret

Små kortnumre skjules ikke længere automatisk. Der bruges læsbare etiketter og forbindelsesstreger, placering uden overlap samt et indvendigt anker ved indadbuede grænser. Skærmvisningen bruger mindst 11 px; printet sigter efter ca. 9 pt uafhængigt af skærmens størrelse. Hvis et ekstremt tæt/lille udsnit ikke har plads til alle etiketter, nævnes de resterende numre udtrykkeligt under kortet.

Høje kort bruger stående A4-kortsider, brede kort liggende A4-kortsider. De øvrige rapportsider og den originale S-13 bevarer stående format og 15 mm margener. Tre fiktive rapporter er renderet og kontrolleret visuelt: højt kort (6 sider), bredt kort (6 sider) og 60 tætte distrikter (8 sider, heraf 3 originale S-13-sider). Alle forventede numre er fundet på begge perioders kortsider med 8,98–9,04 pt i kontrollen.

Automatiske prøver dækker også 30 tætte distrikter ved 320 × 260 px, 60 ved 800 × 640 px, kanter, indadbuede grænser, HTML-escaping, reproducerbar placering, overfyldte udsnit og valg af sideformat. PDF-kontrollen er udført offline med WeasyPrint 70 og fiktiv baggrund; den er ikke en påstand om test af levende OSM-fliser eller browserens printdialog. Ingen private kort eller registreringer er brugt.

## W19 · kritisk betakanal

Ejerens nye prioritet -1 er taget før de øvrige opgaver. Der indføres løbende, mindre HA-betaer efter afsluttede funktioner med kort ændrings-/testliste. Samme repository og én kodebase bevares: develop er kilde, beta er et genereret og kontrolleret HA-snapshot, og main forbliver stabil.

Betakanalen bruger repositoryadressen med #beta, appnavnet Distrikt Beta, slug distrikt_beta, port 8788, egen /data/distrikt-beta og separat login-cookie. Den kan installeres ved siden af stabil på 8787 uden automatisk overførsel af data eller Google-forbindelse. Den starter manuelt. Før publicering kræves program-/pakkeprøver, Mac, Windows og bygning af den faktiske genererede HA-pakke. GitHub-betaen markeres som prerelease og ikke som seneste stabile udgave.

Første beta 1.12.0-beta.1 fokuserer testlisten på adskilt installation, Drive-adgang og KTM-kort/print. Næste små funktioner får nye beta-numre; samme versionsnummer overskrives ikke med ændret kode. Se docs/BETA.md og docs/BETA-NOTES.md.

W19-lokalkontrol: 252 Python-prøver (1 oversprunget), 3 betapakkeprøver, almindelige pakkeprøver og workflow-/shellsyntaks består. Prøven med stabil og beta på samme vært bekræfter forskellige cookies, uafhængige sessioner og separate data. ZIP bygges deterministisk fra samme programmanifest uden brugerfiler. Første publicering er efterfølgende godkendt af hele CI-gaten og gennemført.

W19-udgivelse bekræftet: v1.12.0-beta.1 er en GitHub-prerelease med HA-ZIP og SHA-256. Den kontrollerede kilde er 5b6ec28; den genererede HA-beta er på beta-grenen. Installer via https://github.com/Bib007/LTM-Local-Territory-Manager#beta som Distrikt Beta på 8788. Seneste stabile release er fortsat v1.11.1. Checks, Platformskontrol og HA beta release er grønne. Ejerens HA-test og Google-prøve er endnu ikke udført.

Fremover: afslut én lille funktion eller et sammenhængende sæt, ret relevante prøver, opdater alle versionssteder og BETA-NOTES til beta.2/beta.3 osv., og udgiv efter grønne gates. Flyt ikke beta-grenen direkte fra almindelige develop-commits. Næste udviklingsopgaver er W04/W03 og W13; den faste køreplan står fortsat på 20 %. W14's kode og offline PDF-kontrol er med i beta.1.

## W20–W22 · nye ønsker og beta.2

W21 (prioritet 2) er implementeret først. Kun betakanalen har nulstillingsknappen og API-adgangen. Den kræver teksten NULSTIL BETA, uændret datarevision, afsluttet adressehentning og fjernet offentlig adgang til kort. Alle lokale registreringer erstattes i én transaktion af tom førstegangsopsætning; login, Google-forbindelse og sikkerhedskopier bevares. Ingen Google-filer slettes. Automatisk sikkerhedskopi før nulstilling kan hentes og importeres. Ny opstart fjerner guidens lokale kladde i den aktuelle browser; andre betafaner skal genindlæses.

Lokalt: 256 Python-prøver (1 forventet overspringning), samtlige JavaScript-prøver, 7 almindelige og 3 betapakkeprøver består. Fiktive prøver dækker forkert bekræftelse, ændrede data, disk-/transaktionsfejl, offentlig deling, login/token og beta/stabil på samme vært. Version 1.12.0-beta.2 sendes gennem CI før udgivelse. Næste er W22/W04/W03 (prioritet 4 samlet med branding), derefter W13 (4) og W20 (5). Fast køreplan fortsat 20 %.

## Beta.2 udgivet · beta.3 topbar og identitet

Beta.2 er bekræftet udgivet fra 62b0308 med HA-ZIP og checksum; Checks, Platformskontrol og HA beta release består. Beta.3 samler W22/W04/W03: fast topbar ved begge bredder, afsat plads til indholdet og afgrænsning af Leaflet-kortlag, logo som knap til samme kontrollerede forside-navigation, fuldt ordmærke på computer og kompakt identitet på mobil. Betanavnet bevares synligt. HA får 128 × 128 ikon og 720 × 132 logo; begge temaer er visuelt kontrolleret med de faktiske PNG-filer. Eksisterende SVG-identitet bevares; developer-script kan regenerere PNG-filerne.

HA's officielle fil-/præsentationsvejledning er kontrolleret: https://contributors.home-assistant.io/apps/guides/presentation/. Ikon og logo følger både almindelig programpakke og genereret beta. Lokalt består 256 Python-prøver (1 forventet overspringning), alle JavaScript-prøver, 7 almindelige og 3 betapakkeprøver samt faktisk betaopbygning. Forsideknappen afprøves med afvist ugemt grænseændring. Live-rulning, responsivt browserlayout og visning i egen HA er ikke afprøvet her og står i betaens korte ejer-testliste. Næste prioritet 4 er W13 (rapportoversigter), dernæst W20 (guide-layout, 5). Fast køreplan fortsat 20 %.

## W13 · konkret rapportopfølgning i beta.4

Den eksisterende rapport er gennemgået: månedstal, dækningsgrad, gentagne gennemgange, anslåede besøg og områdeoversigt findes allerede og bevares. Der tilføjes derfor en aktuel opfølgningsliste med tre særskilte tal: ukendt seneste gennemgang, kendt gennemgang ældre end 12 kalendermåneder og aktuel gennemgang udleveret over fire måneder. Hvert aktuelt kort vises én gang med alle relevante årsager, område og datoer. En beholdt kortcyklus regnes fra den nye gennemgang. Ukendt historik sidestilles ikke med aldrig gennemgået; arkiverede kort er udeladt. Ingen nye personnavne, noter eller IB-adresser tilføjes. Tallene er forslag til lokal opfølgning, ikke en påstand om officielle krav.

Listen er dateret med dagens dato og bevarer dette aktuelle grundlag ved valg af et ældre rapportår. Begge rapportperioder og original S-13 bevares i samlet PDF. Kalendergrænser, fremtidige poster, nyeste kendte dato, gentagne årsager, beholdte kort, escaping og privat IB er afprøvet. 256 Python-prøver (1 forventet overspringning), alle JavaScript-prøver og begge pakkekontroller består. Fiktive rapporter har 7, 7 og 10 sider; tæt eksempel med 60 kort og 30 opfølgningsrækker er kontrolleret visuelt, inklusive tabeldeling og gentaget overskrift. Opfølgningslisten bruger 9 pt tabeltekst. Ingen rigtige data eller netkort er brugt.

Beta.3 er udgivet fra 59c0b63 med grøn Checks, Platformskontrol og HA beta release, ZIP og checksum. Beta.4 sendes gennem samme gates. Næste udvikling er W20's opsætningsguide (prioritet 5), efterfulgt af adressekilde/januarfrist og demo. Den faste køreplan er fortsat 20 %.

## W20 · opsætningsguidens valgfelter

Årsagen var dialogens fælles fuldbredde-regel for input, som også ramte radiofelter med højere CSS-specificitet end guidens lokale width:auto. Radiofelter er nu udeladt af tekstfeltreglen og har fast 18 px bredde; tekstkolonnen kan krympe og ombryde inde i valgboksen. Selve valg, plan og gemning er uændrede.

Offline layoutkontrol med produktions-HTML/CSS omfatter 80 valgbokse på tværs af dansk/engelsk, alle guidetrin og bredder 320/390/768/1440 px. Radiofelters og tekstkolonners grænser er kontrolleret programmatisk; en 320 px prøve er også gennemset visuelt. Renderingen bruger WeasyPrint med dialogen gjort synlig til QA, ikke en levende browser; HA-/browserprøven står særskilt. 256 Python-prøver (1 forventet overspringning), alle JavaScript-prøver, 7 normale og 3 betapakkeprøver består.

Beta.4 med W13's opfølgning er udgivet fra 8589264; Checks, Platformskontrol og HA beta release består, og HA-ZIP/checksum er tilgængelige. Beta.5 med W20 sendes nu gennem samme gates. W23 er overført fra ejerens indbakke med prioritet 10, uden at oprette en ny feedbacktjeneste. Næste fokus er W07's dokumenterede kildefrist og dernæst W12. Stabil main 1.11.1 og den faste plans 20 % er bevaret.

## W07 og W12 · kilder og demo undersøgt

W07: den officielle januarfrist er bekræftet som DAR REST den 15.01.2027. OSM er allerede standardbaggrund og erstatter ikke strukturerede DAR-adresser. Adressevælgerens fremtidige brugerstyring har en særskilt varslet periode ultimo 2026/primo 2027. Konkrete berørte kodeveje, overgangstrin, credential-håndtering og prøver er samlet i docs/ADRESSEKILDE-2027.md. Skemaet til DAR v3 svarer 401 uden autentifikation. En kontrolleret GraphQL-erstatning er endnu ikke implementeret; opgaven er ikke markeret færdig. Lokale data og reservevisning er bevaret.

W12: den rigtige adresse er https://bib007.github.io/LTM-Local-Territory-Manager/ . Roden og alle seks JS/CSS/logo-aktiver svarer 200 uden login og matcher den kontrollerede demokode; /demo/ svarer 404. Direkte links er nu indført i de danske/engelske introduktioner og demovejledninger på develop. Ingen genudgivelse eller ændring af hosting var nødvendig for at få det rigtige link til at svare. Model-/UI-prøver og allowlist-bygning køres igen. Levende browsers første åbning, OSM-fliser, mobil og print står fortsat særskilt. Main er bevaret som stabil 1.11.1; dokumentationsrettelsen ligger på develop.

## Seneste udgivelse og dokumentationskontrol

Beta.5 er verificeret udgivet fra 7e5739b med HA-ZIP og SHA-256. Alle tre CI-workflows er grønne. Stabil main står fortsat på 842541a / 1.11.1. W12's fiktive model- og UI-prøver, allowlist-bygning samt 7 programpakkeprøver består efter linkrettelserne. Næste beta efter en ny kodeopgave skal være beta.6; beta.5 må ikke overskrives. Der er ingen ny betapublicering nødvendig for denne status-/link-/kilderapport alene.

## Ejerrettelse · ingen opfølgningsliste i KTM-rapport

16.10.2026: Ejeren ønsker ikke den foreslåede opfølgningsliste. Den fjernes helt fra skærmrapport, samlet PDF, beregningshjælpere og tilhørende særlige printregler i beta.6. Eksisterende rapporttal, kort og original S-13 bevares. W13's generelle ønske er ikke en tilladelse til at genindføre denne liste. Historikken ovenfor beskriver den tidligere beta.4, ikke den aktuelle ønskede rapport.

Næste arbejde efter fjernelsen er fortsat W07's adressekildeovergang. Main 1.11.1 og den faste plans 20 % bevares.

## W07 · ejerbeslutning og lokal nøgleopsætning til beta.7

Ejeren har valgt “Egen api-nøgle og guidning dertil”. Første fuldførte del er lokal Datafordeler-opsætning under Kortdata: guide til konto, IT-system og API-key; kontrol af det officielle DAR v3-skema og en minimal GraphQL-forbindelse før gemning; genkontrol og fjernelse. Credential gemmes separat fra SQLite og vises ikke i status, kortdata eller portable backups. Beta-nulstilling bevarer forbindelsen. Den faste officielle vært bruges med afviste redirects, begrænset svarstørrelse, timeout og redigerede fejl, som ikke indeholder nøgle eller URL. En afvist erstatningsnøgle efterlader den hidtidige nøgle. Se docs/DATAFORDELER.md.

Beta.6's fjernelse af den uønskede rapportliste er udgivet fra 1b503f8; alle tre gates er grønne. Beta.7 klargør kun forbindelsen og lader den eksisterende adresseimport fortsætte; dette står tydeligt i både UI og testlisten. Fiktive prøver omfatter gemning/genstart, nøgleskiftfejl, rå providerfejl, redirects, credential-fri backup, beta-nulstilling, HTTP-tokenkontrol og frontendens dobbelklik/forladte dialoger. Ingen reel konto, nøgle, private data eller autentificerede DAR-opslag er brugt her. 263 Python-prøver (1 forventet overspringning), alle JavaScript-prøver og begge pakkekontroller består lokalt.

Næste del er den egentlige GraphQL-adapter til vej-, postnummer- og grænsehentning med komplette sider, lokale joins, stabile DAR-ID'er og adskilte checkpoints. W07 er fortsat i gang, ikke færdig. Main 1.11.1 og den faste plans 20 % bevares. Ejerens afvisning af rapportopfølgningslisten gælder fortsat.

## Beta.7 udgivet · aktuel status efter ejerrettelsen

Beta.7 er bekræftet udgivet fra dd5d934 med HA-ZIP og checksum. Checks, Platformskontrol og HA beta release er grønne; både Mac, Windows og den genererede HA-pakke består. Beta.6 og senere har ingen ekstra rapportopfølgningsliste. Egen API-key og guidning er nu tilgængelig under Kort og adresser → Hent adresser → Datafordeleren · egen API-nøgle. Gemt forbindelse er forberedelse; importen bruger fortsat den hidtidige kilde. Dette står også i produktets status.

Næste kildeændring kræver paginering og kontrollerede lokale joins mellem DAR_Adressepunkt, DAR_Husnummer, DAR_Adresse, DAR_NavngivenVej og DAR_Postnummer. Officielle kendte fejl i relationerne er undersøgt; den kommende adapter skal bruge flade entitetsopslag med fuldstændighedskontrol, ikke antage at alle joinrelationer er tilgængelige. Egen nøgle indtastes kun i ejerens lokale app; ingen nøgle eller private registreringer skal sendes til AI. Næste funktionelle beta er beta.8, og betatagget beta.7 bevares uændret.

En efterfølgende testrettelse afgrænser POSIX-filmoduskontrollen til POSIX-systemer; Windows bruger ikke de samme modebits. Runtime-koden i den udgivne beta.7 er uændret. 263 Python-prøver (1 forventet overspringning), alle JavaScript-prøver og begge pakkekontroller består for udgivelsen; den berørte credential-prøve køres igen efter testrettelsen.

## W07 · kort delopgave før de planlagte kørsler

16.10.2026: `dar_paging.collect_pages` er implementeret med fuldstændig sidekontrol før returnering, afvisning af delvise GraphQL-fejl, cursor-cyklusser, dubletter og ugyldige ID’er samt grænser og afbrydelse. 12 nye fiktive prøver består. Funktionen har ingen database-/netværksadgang og er endnu ikke koblet til den aktive import. Hele Python-suiten består med 275 prøver (én forventet overspringning); 7 almindelige og 3 betapakkeprøver består.

Næste session starter med transport/forespørgsler og de lokale DAR-joins og bruger den nye sidehenter. Importovergangen er stadig uafsluttet. Ingen ny brugerfunktion eller beta er udgivet for denne isolerede byggesten. Beta.7, stabil main og fast køreplan 20 % bevares.

## W07 · query-transport og lokale joins

16.10.2026: `Datafordeler.query` genbruger fast officiel vært, redirect-afvisning, timeout, svargrænse og redigerede fejl. `DarQuery` bruger eksplicitte projektioner for de fem DAR-entiteter, afgrænsede lighedsfiltre, status 3 og ét fast UTC-tidspunkt for både registrering og virkning på tværs af opslag/sider. Filterværdier og cursors escapes som strengliteraler; afvigende svar afvises. Ingen nye afhængigheder.

`join_addresses` samler komplette flade entitetslister lokalt: Adresse → Husnummer → Adressepunkt/NavngivenVej/Postnummer. Den bevarer stabile DAR-ID'er, etage/dør og det eksisterende normaliserede adresseformat. Dubletter, manglende/inaktive relationer, ugyldige koordinater og ukendte koordinatsystemer afviser hele resultatet før nogen import. En vej kan krydse postnumre uden at kræve koordinater uden for det valgte postnummer.

14 nye fiktive prøver omfatter også transport → flere sider → joins i sammenhæng samt sammenligning med den eksisterende REST-normalisering. Den samlede adapter og aktive import mangler stadig; funktionerne skriver ikke til databaser og er ikke koblet til Downloads. Ingen ejercredentials eller private data er åbnet. Aktuel beta.7 og main 1.11.1 bevares; næste funktionelle beta er beta.8. Den faste køreplan står fortsat på 20 %.

## W07 · samlet vej-/postnummeradapter og færre netkald

17.10.2026: Foregående byggesten er gemt i c2166c5; Checks, Platformskontrol og HA beta release er grønne for dette commit. `DarQuery.collect_many` grupperer op til ti dokumenterede lighedsopslag i én GraphQL-anmodning med separate aliases. Hvert opslag har egen fuldt kontrolleret paginering; der antages ikke udokumenteret IN-filtrering. 25 entitets-ID'er kræver tre anmodninger i den fiktive prøve. Manglende aliases, delvise fejl, forkerte scopes, dubletter, manglende obligatoriske ID'er og overskredne samlede grænser afviser hele kaldet.

`DarAdapter` finder postnummerets officielle veje via flade husnumre og vej-ID'er og henter en samlet vejs adresser, adgangspunkter og postnumre ved samme faste tidspunkt. Veje på tværs af postnumre kan hentes samlet eller afgrænset. Kun punkter til faktiske adresser hentes; tomme husnumre får ikke opdigtede boliger. Adapteren returnerer komplette resultater i hukommelsen med kildemarkøren `dar-graphql-v3`; ingen database eller checkpoint ændres.

10 yderligere fiktive prøver dækker aliasbatching, individuelle fortsættelsessider, transportfejl efter første side, pause, grænser, komplette veje/postnummeropslag, etage/dør og manglende relationer. Næste er aktivering i Downloads og vej/postnummer/grænse med separate kildecheckpoints, fremdrift og uændret kontrol før lokale ændringer. GraphQL-grænseopslag og live skemakontrol er endnu ikke implementeret/verificeret. Ingen ny brugerfunktion eller beta er udgivet for disse interne byggesten; beta.7 og den faste køreplans 20 % bevares.

## W07 · aktiv import og beta.8

17.10.2026: Grænseadapteren henter komplette rektangulære udsnit og sammenkobler alle nødvendige entiteter. Within-forespørgslen udvides én centimeter og filtreres lokalt, så fælles kantpunkter bevares. Præcise distriktsgrænser, kort og IB sendes ikke til datakilden.

Med en gemt nøgle bruger nye vej-, postnummer- og grænsehentninger nu GraphQL. Uden nøgle bevares den hidtidige kilde. Checkpoints fastlåser kilde, skemafingeraftryk og tidspunkt; skift af kilde/skema kræver ny opdatering og ændrer ikke de lokale adresser ved afslag. Netfejl stopper ved den aktuelle del, og genstart springer færdige dele over. Eksisterende kontrol af adresseændringer samt samlet transaktion for adresser/checkpoint bevares. Flere officielle vej-ID'er med samme navn/postnummer behandles samlet for at undgå falske forslag om udgåede adresser.

Beta.8 har opdateret dansk/engelsk nøglevejledning og kort ejer-testliste. Den sendes gennem program-, Mac-, Windows- og faktisk HA-pakkekontrol før offentliggørelse. Egen Datafordeler med offentlig prøvevej og HA/browser afventer separat. REST-kildens deadline 15.01.2027 og Adressevælgerens særskilte adgangsændring følges fortsat. Næste prioriteter efter udgivelseskontrollen er W06's HA-sikkerhedsvurdering og W15's forkynderforslag (6). Større sikkerhedsændringer aftales fortsat med ejeren. Stabil main 1.11.1, rapportens afviste opfølgningsliste og den faste køreplans 20 % bevares.

## Beta.8 udgivet · W06 indledende gennemgang

17.10.2026: Beta.8 er verificeret udgivet fra c0528c9 med HA-ZIP og SHA-256 som prerelease. Checks (Python 3.9/3.12/3.13, JavaScript og pakker), Platformskontrol (Mac, Windows og HA) samt HA beta release er grønne. Betagrenens konfiguration er 1.12.0-beta.8, Distrikt Beta, port 8788 og manuel start. Lokal kontrol: 319 Python-prøver (én forventet overspringning), samtlige JavaScript-prøver, 7 almindelige og 3 betapakkeprøver samt faktisk betapakkeopbygning består. Main er fortsat 842541a / 1.11.1.

W07's kodeovergang er dermed tilgængelig til lokal ejerprøve. Levende Datafordeler, ejerens nøgle, HA/browser og Adressevælgerens fremtidige adgangsændring er fortsat særskilte. Der er ikke åbnet private databaser eller credentials.

W06 er påbegyndt med en afgrænset offentlig kode-/konfigurationsgennemgang og officielle HA-kilder: docs/HA-SIKKERHED.md samt engelsk udgave. En egen AppArmor-profil er næste afgrænsede kandidat, men er ikke aktiveret uden profil-/HA-prøve. Ingress/HA-auth, procesrettigheder og en eventuel datamigrering er større ændringer, som aftales før implementering. Faktisk installeret HA-vurdering er ikke aflæst. Ingen ekstra privilegier eller ændret adgangsarkitektur er indført. W15's forkynderforslag (6) kan fortsætte uafhængigt; den faste køreplan er stadig 20 %.

## W15 · lokal forkyndersøgning

17.10.2026: Browserens indbyggede datalist er erstattet af en eksplicit lokal combobox ved udlevering. Søgning på flere navneled prioriterer præcise navne og begyndelsen af navne; højst otte forslag vises. Piletaster/Enter, Escape/Tab, mus og berøring har separate hændelsesprøver; IME afbrydes ikke. Nye navne bevares som fri tekst og oprettes først af den eksisterende udleveringshandling. Ingen API-kald, persondataupload, ekstra lagring eller ændrede databaser.

Dansk/engelsk bevarer indtastning og formularnøgler. Komponentens liste ligger i dokumentflowet med rullegrænse, 44-pixel knapper og ombrydning til smalle skærme. Automatiske hændelses-/kontraktprøver er ikke en påstand om visuel mobil- eller skærmlæserkontrol. Browserdownload fejlede i udviklingsmiljøet; egen HA/browserprøve står på beta.9's testliste. Beta.9 afventer grønne program-, platform- og HA-gates før offentliggørelse. Næste kodeopgave er W16 (7), meningsfuld automatisk inddeling; større W06-ændringer afventer fortsat aftale. Den faste køreplan forbliver 20 %.

## Beta.9 udgivet · W16 første vejbaserede del

17.10.2026: Beta.9 er verificeret som prerelease fra 7c631df med HA-ZIP/SHA-256. Checks, Platformskontrol og HA beta release er grønne. 319 Python-prøver (én forventet overspringning), alle JavaScript-prøver, 7 almindelige og 3 betapakkeprøver samt faktisk betapakkeopbygning består. W15 er tilgængelig; visuel mobil-/skærmlæserkontrol står særskilt.

W16 er derefter fortsat med en generel skæring langs skrå linjer, som også bevarer adskilte konkave komponenter. Automatisk forslag bruger nu egnede lokale lige vejsegmenter før geometrisk deling. Kandidater er begrænset til 256 lokale segmenter og 32 afprøvninger pr. deling. Kun faktisk dækkede gennemgående vejstykker accepteres; korte fragmenter forlænges ikke, og grupper af lejligheder kontrolleres med alle deres koordinater. Forslag markerer vejnavnet eller manglende egnet vejskel. Ingen netkald eller automatisk oprettelse tilføjes. Lokale vejændringer ugyldiggør en gammel forhåndsvisning.

Beta.10 klargøres til de krævede gates med konkret prøvevejledning. W16 er fortsat i gang: kurvede veje, sammenhængende flersegmentsforløb og naturlige skel mangler. Eksisterende manuelle rettelser og eksplicit godkendelse bevares. Næste kodeopgave er den fortsættelse, før lavere prioriterede W08/W23. Stabil main og den faste køreplans 20 % bevares.

## Beta.10 verificeret udgivet

17.10.2026: Prerelease 1.12.0-beta.10 fra 1586b59 har HA-ZIP og SHA-256. Checks (Python 3.9/3.12/3.13, JavaScript og pakker), Platformskontrol (Mac/Windows/HA) samt HA beta release består. Betakanalen er kontrolleret som Distrikt Beta, manuel start og port 8788. Tidligere betaer er bevaret. Lokal kontrol: 325 Python-prøver (én forventet overspringning), alle JavaScript-prøver, 7 almindelige og 3 betapakkeprøver samt programopbygning. Yderligere 120 fiktive skrå skæringer består areal-, overlap- og adressepunktskontrol.

W15's nye lokale forkynderforslag er i beta.9 og senere. W16's lige vejsegmenter er i beta.10; W16 er ikke afsluttet. Kurvede/flersegments vejforløb og naturlige skel er næste kodearbejde. Visuel mobil-/skærmlæser-/HA-kontrol, egen Datafordeler og egen Google-konto står særskilt. Browserdownload til denne kørsels visuelle prøve fejlede; hændelsesprøver er ikke angivet som visuel godkendelse. Ingen private databaser eller credentials er åbnet. Main er stadig 842541a / 1.11.1; den faste køreplan er stadig 20 %.

## W16 · kurvede vejforløb og præcise forbindelser

17.10.2026: Beta.11 klargøres. En ny lokal skæring følger vejforløbets faktiske punkter gennem området; enkeltstående vejfragmenter forbindes kun ved præcist fælles endepunkt, samme navn og uden forgrening. Inputrækkefølge og vejretning ændrer ikke resultatet. Huller, løkker, selvberøring, tvetydige hjørneskæringer og komplekse genindtrædninger gættes ikke. Algoritmen har grænser for punkter, kandidater og geometrisk arbejde; den eksisterende lige deling kan fortsat bruges, og geometrisk deling uden egnet vej markeres til manuel rettelse.

Prøver bruger kun fiktive data og midlertidige databaser. Både polygonareal/overlap og hvert adressepunkt kontrolleres, husenes lejligheder holdes sammen, og de kurvede fælles grænser kan stadig rettes, kontrolleres og oprettes gennem den eksisterende transaktion. Ingen nye netkald, afhængigheder eller databaseændringer indføres. Dansk/engelsk vejledning er tilføjet. Naturlige skel og avancerede vejnet er fortsat næste del af W16; fast køreplan er stadig 20 %.

## W24 · digitalt QR-kort

17.10.2026: Ejerens nye ønske med prioritet 3 er overført til den offentlige plan før rydning af ønskelistefeltet. Det digitale kort, der åbnes fra QR-koden, ønskes moderniseret. En lille miniature i hjørnet skal genbruge det respektive korts printforside, herunder den allerede eksisterende vejoversigt. Ingen IB må indgå. Opgaven går foran resterende W16, når den igangværende, afprøvede beta.11-ændring er gemt og kontrolleret. Den nuværende Drive-/QR-arbejdsgang og dens offentlige billedformat gennemgås før implementering, så layoutet kan forbedres med samme privatlivsgrænse og adgangscyklus.

## Beta.11 udgivet · W24 implementeret til beta.12

17.10.2026: Beta.11 er verificeret udgivet fra 3a987f5 med HA-ZIP og SHA-256. Checks, Platformskontrol og HA beta release er grønne. Lokal kontrol: 338 Python-prøver (én forventet overspringning), alle JavaScript-prøver samt almindelig/betapakke og faktisk opbygning består. W24 (3) blev derefter overført til GitHub, før ønskets tekst blev fjernet fra dokumentets ønskeliste; tabeller og faner blev bevaret.

W24 har nu nyt SVG/PNG-layout med stor kortflade, overskrift, statusfelter og printminiature i hjørnet. Miniaturen bruger den eksisterende blanke S-12 og samme vejlinjeformatering som printforsiden, men kun offentligt godkendte kortdata. Private kortfelter og IB-lister anvendes ikke. Standard, langt navn/nummer, tæt og tomt kort er renderet og visuelt kontrolleret. Billederne er fiktive, ikke fra en privat database eller levende korttjeneste.

Layoutrevision følger godkendt upload. Eksisterende links/adgang og gamle billeder bevares, indtil et nyt preview er godkendt. Ukendte ældre layoutfelter bevares og giver en kontrolmarkering; ny ukendt uploadrevision afvises. Ingen ny offentlig webtjeneste, nye runtime-afhængigheder eller upload af private data. Beta.12 afventer de krævede gates. Virkelig HA/browser/telefon og egen Google-konto er særskilte prøver. Resterende W16 (7) er næste kodeopgave efter W24; den faste køreplan forbliver 20 %.

## Beta.12 verificeret udgivet

17.10.2026: Beta.12 fra 00e7f06 er en verificeret prerelease med HA-ZIP og SHA-256. Checks (Python 3.9/3.12/3.13, JavaScript og pakker), Platformskontrol (Mac/Windows/HA) og HA beta release består. Betagrenen er kontrolleret som Distrikt Beta 1.12.0-beta.12 med manuel start og port 8788. Beta.11 fra 3a987f5 og tidligere betaer er bevaret. Lokal kontrol: 341 Python-prøver (én forventet overspringning), alle JavaScript-prøver, 7 almindelige og 3 betapakkeprøver samt faktisk betapakkeopbygning. Tre fiktive SVG/PNG-varianter er visuelt gennemgået; de fulde PNG-billeder består den rigtige uploadvalidering.

W24's nye prioritet 3 blev fulgt før yderligere W16. Moderne kortlayout og offentlig printforside-miniature er udgivet; nye preview kræver stadig godkendelse. Egen HA/browser/telefon og egen Google-konto står særskilt. Ingen private databaser eller credentials er åbnet, og intet er uploadet til ejerens Drive. Næste kodearbejde er igen W16: naturlige skel og avancerede vejnet. Main er fortsat 842541a / 1.11.1; fast køreplan er fortsat 20 %.

## Fast køreplan prioriteret · punkt 3 færdig · beta.13

17.10.2026: Efter ejerens nye aftale er ønskelisten sat på pause. Korteditor, samlet grænse, KML/GeoJSON-import, kortdata-/nøgleguide og vejforslag har dansk/engelsk betjening med uændrede kanoniske dataværdier. Sprogskift bevarer kortinstans, zoom, fokus, indtastninger, valgte adresser og ugemt tegning. Importen bevarer fil, grænsevalg og kort.

Sene eller ombyttede adresse-/oprydnings-/importsvar erstatter ikke nyere tegninger eller dialoger. Gemning bruger kopierede data, blokerer dobbeltgemning og afbrydes før skrivning ved ændret/annulleret valg. Ændringer under en accepteret skrivning bevares som ugemt kladde; skrivninger genafspilles ikke. Åbning af en adresse deler ikke den gemte polygons koordinatlister. Afsluttet baggrundshentning genopbygger ikke korteditorens formular; et ældre afventende nummerinterval anvendes kun på uændret kladde.

Lokalt: 341 Python-prøver (én forventet overspringning), alle JavaScript-prøver, 7 almindelige og 3 betapakkeprøver. Offline Chromium bruger rigtige app-/Leaflet-filer og kun opdigtede API-svar ved 320/390/768/1440 pixels; skærmbilleder er visuelt gennemgået. Browserprøven følger kodebasen og HA-beta-gaten. Beta.13 afventer grønne GitHub-program-, platform- og HA-kontroller før udgivelse. Fast køreplan: 30 % (3/10). Næste er punkt 4; W16 og øvrige ønskefunktioner venter. Egen HA/telefon, Datafordeler-nøgle, Google og fysisk print er fortsat særskilte ejerprøver.

## Fast punkt 4 færdig · beta.13 udgivet · beta.14

17.10.2026: Beta.13 fra 1f31286 er udgivet efter grøn Checks (inklusive offline Chromium), Platformskontrol og HA beta release med fast ZIP/checksum. Den genererede betakanal er kontrolleret som version 13, port 8788 og manuel start. Main er uændret 842541a / 1.11.1.

Avanceret opsætning har nu dansk/engelsk i alle fire trin, område-/nummerstandarder, forslag, manuel grænsekontrol, kortoprettelse og lokal IB-import. Sprogskift ændrer ikke kortinstans, indtastede navne/numre, geometri eller IB-kontrol. Kanoniske typer/nummerering, CSV-skabelon og bekræftelsesord OPRET KORT / IMPORTÉR IB bevares. Statiske valg er markeret på option-elementet, så sprogskift også virker i den native vælger.

Forsinkede forslag accepteres kun til uændret opsætning/revision. Ombyttede lokale filindlæsninger bruger kun den nyeste fil. Ny fil, ændret dato, navigation eller fejl ugyldiggør ældre IB-kontrol; en forkert/for stor fil efterlader ikke et gammelt skjult CSV-indhold til import. Under oprettelse er opsætningsfelter spærret. Forhåndsvisninger opretter intet; eksplicit bekræftelse og serverens transaktions-/tokenkontrol bevares.

Lokale program-, JavaScript-, pakke- og Chromium-prøver med fiktive data består; browserkontrol dækker 320/390/768/1440 pixels med rigtig app/Leaflet. Beta.14 afventer GitHub-gates. Fast køreplan er 40 % (4/10); næste er punkt 5, Google Drive og QR med opdigtede svar. Ønskelisten venter, og egne konti/HA/telefon/print er fortsat særskilte ejertrin.

## Fast punkt 5 færdig · beta.14 udgivet · beta.15

Den samlede kontrol fandt, at API-håndteringen ændrer klientens revision efter en vellykket mutation. Korteditorens kladdesammenligning tog det for en ny redigering og afsluttede derfor ikke en ellers gemt tegning eller et nyt kort korrekt. Beta.15 sammenligner kladden uden den forventede revisionsændring efter skrivning; kontrollen før skrivning bruger stadig revisionen. Nye positive prøver bruger den rigtige API-wrapper til kortoprettelse og grænsegemning. Chromium prøver begge grænsegemninger med revisionssvar. Nyere redigeringer under skrivning bevares fortsat.

17.10.2026: Beta.14 fra 540cb6a er udgivet efter grøn Checks, Platformskontrol og HA beta release med fast HA-ZIP/checksum. Beta.13 og tidligere versioner er bevaret; main er stabil 1.11.1.

Google Drive-/QR-betjening har dansk/engelsk med bevaret preview, checkbox, offentlig opskrift, URL og QR ved sprogskift. Billedets offentlige indhold og originale printformularer er uændrede. Adgangsstatus beskriver fortsat åbning/lukning og usikker adgang korrekt. Sene/ombyttede statusbeskeder kan ikke gendanne ældre adgangsstatus.

Et forsinket preview/QR-svar erstatter ikke en nyere dialog eller side. Godkendt publicering er låst mod dobbeltklik og sender kun det samme offentlige PNG/fingeraftryk/layoutversion. Ændret revision kræver et nyt kontrolleret preview. Et sent publiceringssvar tvinger ikke navigation eller lukker en nyere dialog. Forbindelsesfilen læses kun til den aktuelle kontekst; polling genopbygger ikke inputtet under indlæsning. Ugyldig JSON giver en neutral fejl uden filindhold. Alle program-/browserprøver bruger opdigtede svar og forbindelsesfixture; ingen rigtig nøgle, Google-konto eller privat fil er åbnet eller uploadet.

Nye kontrakt-/hændelsesprøver dækker ens godkendelses-payload på begge sprog, sene svar, annullering og fejl. Chromium ved 320/390/768/1440 pixels dækker app/Leaflet, opsætning/IB samt samtykke og QR med et genereret prøve-PNG; selve billedgeneratoren kontrolleres særskilt i billedprøverne. Beta.15 afventer GitHub-gates. Fast køreplan er 50 % (5/10); næste er punkt 6. Ønskelisten venter fortsat, og virkeligt HA/telefon/Google/Datafordeler/print er særskilte ejerprøver.

## W25–W27 · ønskelisten genoptaget

17.10.2026: Ejeren ønsker nu videre arbejde efter afsluttet fast plan. Samlet guide, obligatorisk rundtur med afslutning og opfølgning på adresseimport er registreret med de oplyste prioriteter. Der åbnes ikke private data eller credentials. W25/W26 implementeres som ét sammenhængende førstegangsforløb; administrationsværktøjer og eksplicit import-/oprettelsesgodkendelse bevares.

## W25/W26/W27 · beta.23

Den normale guide indeholder nu lokal introduktion, spørgsmål, personlig plan og obligatorisk afsluttende rundtur. Den tidligere parallelle detaljerede velkomstguide er fjernet; dens indgange går til den samme guide. Kortinddeling og import er bevaret som værktøjer, ikke som en ekstra velkomstguide. Svar gemmes som version 2 med uafsluttet status, og afslutning gemmes først ved sidste turtrin. Afbrydelse kan genoptages; tidligere fuldført opsætning og ukendte indstillinger bevares. Rundturen lukker til forsiden med planens handlingsknapper uden at åbne dialogen igen. Sene/afviste svar og dobbeltklik dækkes af kontroller.

W27: Den officielle DAR REST-frist er genbekræftet som 15.01.2027. Egen API-key/IT-system er fortsat den understøttede adgang til den implementerede DAR GraphQL-import. Guideplanen har en direkte nøgleindgang, og den lokale nøglevejledning viser fristen. Egen live konto/prøvehentning er fortsat et ejertrin. Se docs/DATAFORDELER.md. W28 er registreret med ejerprioritet 9; der er ikke påstået en gennemført sikkerhedsscanning eller registreret hypotetiske fund.

## W29/W30 · opdateringsprocedure og navneforslag

W29 er bekræftet som fast kritisk procedure: develop gemmes, hver færdig kodeopgave får en ny kontrolleret beta, og main opdateres først ved særskilt stabil udgivelse. Udgivne betaer overskrives ikke. W30 retter den hvide CSS-fallback i de lokale navneforslag til mørkegrå med lys tekst og tydelig hover/tastaturmarkering. Prøven bruger kun fiktive navne og rigtig produktions-CSS; normal kontrast er mindst 7:1 ved fire bredder. Ingen søge-/gemmekontrakt ændres.

## W28 · scanneropstart blokeret

17.10.2026: Den udtrykkeligt ønskede Codex Security-standardfærdighed er indlæst. Den kræver de medfølgende scan-prologue/core-scan-referencer og en gennemført security_scan-preflight med resultatet ready, før kildegennemgang/scannerarbejdere starter. Referencefilerne kan ikke læses fra den tilgængelige pakke, og ingen af de nødvendige preflight-/scanværktøjer eller lokale hjælpescripts er eksponeret i denne session. Der er derfor ikke startet en formel Codex Security-scanning og ikke oprettet eller afvist sikkerhedsfund. Opgaven skal genoptages, når pakkens runtime er tilgængelig. Denne tekniske blokering erstattes ikke af en påstået manuel godkendelse.

## W31–W33 · næste ønsker

17.10.2026: Ejerens kritiske statusoprydning udføres før ny kode. Historikimport (6) og månedssammenligning (8) er gemt inden rydning af deres indbakkefelter. Ejeren har afklaret S-13: helst digitale PDF'er samt scanning/foto; ved for kompliceret billedaflæsning kan der henvises til et frivilligt eksternt værktøj med udtrykkelig besked om, at dets privatlivssikkerhed ikke kan garanteres. Der uploades aldrig ejerfiler automatisk. Prioritet 11 betyder fremover altid sidst; -1 forbliver kritisk.

## W34–W39 · nye ønsker gemt før rydning

17.10.2026: Opgaveliste efter guiden (3), præcis forklaring af API-fristen (1), Adressevælger-vejledning (5), demo-opdatering (9), farver/direkte udlånsknapper (3) og aflevering pr. forkynder (5) er registreret fra ejerens ønskefane. W35 behandles først. W31 er bevaret som igangværende arbejde. W33 er udført og statusfanen læst tilbage. Ingen private registreringer indgår i planen.

## W35 · fristen gælder gammel adgang

17.10.2026: Datafordelerens officielle overgangsbeskrivelse fastslår API-key/OAuth-adgang og registrering af nye anvendere efter 15.01.2027. Fristen gælder gammel REST/Webbruger/Tjenestebruger-adgang. Appens danske og engelske nøglevejledning, guideplan og dokumentation skelner nu tydeligt mellem de to. Ingen ændring af autentifikation eller adressehentning. Kilder: https://datafordeler.dk/vejledning/transitionsnetvaerk/ og https://confluence.kds.dk/pages/viewpage.action?pageId=187105503 .

## W34 · opgavelisten kan afsluttes · beta.26

Trin markeres eksplicit som udført eller sprunget over, streges ud og kan fortrydes, mens listen vises. Når alle trin er afsluttet, skjules listen. Status gemmes i installationens indstillinger og deles ved normal genindlæsning på andre enheder. Guidens indgange og arbejdsdata bevares. Serveren validerer valgte trin, status, afsluttet guide og normal datarevision. Sene svar genopbygger ikke en nyere dialog. Program- og browserprøver bruger kun fiktive data; genindlæsning, sprog, afvisning og dobbeltklik er dækket. W31-kladden er bevaret, mens højere prioriteter behandles.

## W38/W39 · kontrolleret daglig brug · beta.27

Statusfarver, direkte udlånsformularer og forkyndergrupperet aflevering er implementeret samlet. Grupper tæller alle aktive kort pr. registreret forkynder, sorterer efter antal/navn og bevarer ens navne som særskilte personer. Navnesøgning ændrer ikke lagrede data; valgt kort har fortsat sin sidemenu. Aflevering opdaterer visningen gennem den normale udlåns- og revisionskontrol. Ingen nye eksterne tjenester eller ændringer i Google-adgangen. Fiktive programprøver og rigtig Chromium dækker farvekontrast, spærret udlevering, aktive udlåns-ID’er, søgning, sprog, tastatur og en eksplicit aflevering uden gennemgang.

## W42 · yderligere opsætningstrin registreret

Ejerens ønske om mindre felter på forsiden og flere enkle opsætningsgenveje er gemt. Ejerens efterfølgende prioritet er 3, og genvej til første forkynder er tilføjet. Ingen ny spærring af appens almindelige brug indføres på baggrund af formuleringen om opsætning; handlinger som deling og printopsætning forbliver eksplicitte.

## W42/W43 · kompakte opsætningsgenveje og lokalt navn · beta.28

Ejerens prioritet 2 for menighedsnavnet og 3 for den kompakte liste er gemt. Lokalt navnefelt vises ved den eksisterende logoidentitet og slettes fra visningen ved tomt navn. Ingen navn hardcodes eller sendes videre. Sammenklappet liste med antal resterende trin åbner de eksisterende indstillinger/formularer; gennemført/oversprunget status består. Fem nye valgfrie trin kan markeres, uden at de spærrer almindelig brug. Printvalget anvender eksisterende valideret profilgemning og bevarer mål samt anden sides profil. Ingen printåbning, genprintgodkendelse, forkynderoprettelse eller Drive-publicering sker ved blot at åbne genvejene. Fiktive Chromium-prøver dækker smalle skærme, lange navne, stabil/betamarkering, sprog, genveje og begge printvalg før første kort.
