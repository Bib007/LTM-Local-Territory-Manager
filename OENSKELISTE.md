# Ønskeliste og nye opgaver

Den faste klargøringsplan står fortsat på 20 %. Nye ønsker udvider ikke automatisk dens procenttal. Dansk er hovedsprog, og ændringer udvikles på develop før en stabil udgivelse.

| ID | Ønske | Ejerprioritet | Placering og status | Færdig når |
| --- | --- | --- | --- | --- |
| W19 | Små løbende betaudgivelser, som kan testes i HA efter nye funktioner | -1 · kritisk | Implementeret: isoleret HA-betapakke og udgivelsesflow; lokale program-/pakkeprøver består; første udgivelse afventer CI | Kontrollerede betaer kan installeres/opdateres i HA ved siden af stabil udgave. Hver beta har fast version og kort testliste; main forbliver stabil. |
| W14 | KTM-rapportens distriktskort tilpasses automatisk til geografiens højde/bredde, evt. egen side, og distriktnumre vises på kortet | 3 | Implementeret og afprøvet på develop: læsbare etiketter, forbindelsesstreger, automatisk stående/liggende A4 og visuelt kontrollerede fiktive PDF-rapporter; levende browser/OSM står særskilt | Kortet bruger dynamisk format/udsnit og læsbare distriktnumre ved både smalle og brede distriktsgrænser. |
| W15 | Forbedr autofuldførelse af forkyndere ved udlevering | 6 | Planlagt til betjeningsforbedringer | En tydelig, relevant forslagsliste erstatter browserlignende autofyld; tastatur og mobil fungerer. |
| W16 | Automatisk distriktsinddeling skal følge meningsfulde vej- og områdegrænser, ikke firkanter | 7 | Planlagt til korteditor og automatisk inddeling | Forslag følger veje og naturlige områder og kan kontrolleres/redigeres før gemning. |
| W17 | Fjern tallet 'midlertidige kort' fra KTM-rapportens 'Distriktets oplysninger' | Ikke angivet | Færdig på develop; rapportprøver består | Tallet vises ikke længere i rapporten; underliggende kortdata bevares. |
| W18 | Google Drive-link åbent kun mens kortet er udleveret; vurder forklarende side ved lukket link | 2 | Implementeret på develop: privat klargøring, åbning/lukning, stabil QR og synlige genforsøg; 32 delingsprøver og API-arbejdsgang består; egen Google-konto afventer | Godkendte billeder åbnes ved udlevering og lukkes ved aflevering uden upload af udlånsdata. Genudlevering bevarer QR; gamle linkindehavere kan dermed også åbne igen. Google ejer adgangssiden; en særlig offentlig side er ikke indført. Kontrol med egen Google-konto står særskilt. |
| W11 | Visuel statusoversigt med korte felter og farvekoder | -1 · kritisk | Færdig i ejerens statusdokument | Tre statusfelter, separate færdig-/næste-felter og kompakte tabeller erstatter den lange statusprosa. Den eksporterede visning er kontrolleret visuelt. |
| W09 | Spejl arbejdsplan og fremdrift i ejerens statusdokument | -1 · kritisk | Færdig: statusfanen er oprettet og læst tilbage | Aktuelle opgaver, næste rækkefølge, prioriteter og procenttal er synlige i fanen Hvor langt er vi? og opdateres ved afsluttede opgaver, mens vi arbejder på LTM. |
| W10 | Erstat opfordring til kodebidrag med idéer og feedback, gerne med bilag | 2 | Implementeret på develop: selvstændigt eksternt menupunkt og GitHub-issueformular; frontend- og GitHub-program/platformskontroller består; browserkontrol og aktivering via main udestår | Et selvstændigt menulink åbner GitHubs offentlige idéformular i ny fane. GitHub står for kommentarer og bilag; brugeren advares om persondata. Ingen lokal feedbackdatabase. |
| W01 | Førstegangsopsætning med spørgsmål og guidet rundtur | Ikke angivet | Færdig på develop; program- og platformskontroller består | Valg af enkel udlevering/kort, KML, IB og manuel/automatisk inddeling giver en personlig plan; rundtur kan springes over og genåbnes uden at oprette data. |
| W02 | Importér allerede fordelte distriktskort fra Excel eller CSV | Ikke angivet | Færdig på develop; program- og platformskontroller består | Skabelon med områder, kortnumre/navne og præcise adresser; lokal kontrol af fejl/dubletter; samlet godkendelse; eksisterende kort overskrives ikke. |
| W03 | Projektets logo tydeligt i appens øverste del | 5 | Næste samlet med W04 | Eksisterende mærke gennemgås og suppleres med korrekt logo; lys/mørk baggrund samt mobilbredder er kontrolleret. |
| W04 | Logo og ikon på appens side i Home Assistant | 4 | Sammen med W03 før næste stabile HA-udgivelse | De relevante HA-billeder findes, følger samme identitet og er med i programpakken; visning på egen HA står særskilt. |
| W05 | Bedre informationstekst ved installation i Home Assistant | 3 | Færdig på develop: beskrivelse og introduktion med funktioner, første start, lokal drift og backup; pakkekontrol består | Kort beskrivelse og dansk introduktion forklarer funktioner, lokal drift, adgang og første start uden intern restliste. |
| W06 | Gennemgå og forbedr HA-appens sikkerhedsvurdering | 6 | Efter HA-præsentation og før næste stabile HA-udgivelse | Officielle krav og faktisk konfiguration er gennemgået. Forbedringer med uændret funktion indføres; større ændringer forelægges ejeren først. |
| W07 | Afklar adressekildens levetid og forenkling til OpenStreetMap-baggrund | 5 | Undersøg kilde og frist tidligt; ændr først efter verifikation | Kontroller den varslede januarfrist og forskellen på adresser og kortbaggrund. Bevar adressefunktionerne gennem et afprøvet alternativ. OpenStreetMap er den foretrukne synlige baggrund; vurder fjernelse af den lokale reservevisning uden at fjerne lokale data. |
| W08 | Afklar hvornår det tidligere private repository kan arkiveres | 10 | Efter stabil kildekode, pakker og udviklingshistorik er kontrolleret | Giv ejeren en konkret anbefaling, når nødvendig kode og dokumentation er bevaret. Arkivér eller slet ikke noget repository automatisk. |
| W12 | Kontrollér webdemoens direkte link og få den til at åbne korrekt | 5 | Efter de højere prioriterede præsentationsopgaver | Verificér det faktiske Pages-link og browserens første åbning; ret eventuelle publicerings- eller linkfejl og brug kun opdigtede demodata. |
| W13 | Gør KTM-rapporten mere nyttig ved besøget | 4 | Sammen med rapportarbejdet; før prioritet 5 | Undersøg relevante oversigter og gennemgå den eksisterende rapport. Foreslå og tilføj nyttige mål med tydeligt datagrundlag; skeln mellem forslag og eventuelle verificerede krav. |

Ønsker læses ind fra ejerens dokument, når vi arbejder på LTM og mellem afsluttede opgaver. Et punkt fjernes først fra indbakken, efter at ønsket er gemt her. En overførsel betyder planlagt, ikke færdig. Oplyste prioriteter bevares: -1 er kritisk og går før øvrigt arbejde, 1 er snarest, 10 er valgfrit på længere sigt. Arbejdsstatus spejles i ejerens dokument, så arbejdsrækkefølge og fremdrift kan følges uden GitHub. Arbejdsrækkefølge efter den kritiske statusopgave: feedback og udleveringsstyret Drive-adgang (2) afsluttes; derefter HA-information og dynamisk KTM-kort (3), HA-logo og rapportoversigter (4), app-logo, adressekilde og webdemo (5), autofuldførelse og HA-sikkerhed (6), automatisk inddeling (7) og arkivanbefaling (10). Ønsker uden angivet prioritet får ikke et opdigtet prioritetstal. Afhængigheder og en verificeret kildefrist kan ændre rækkefølgen. Private data og eksempler kopieres ikke til denne offentlige plan.

## Næste arbejdssession

- Stabil `main`: 1.11.1. `develop`: 1.12.0-beta.1; ingen stabil udgivelse i denne omgang.
- W10: frontendtesten består lokalt; Checks og Platformskontrol for b0b5d42 består på GitHub. Formularen ligger kun på develop og er derfor endnu ikke aktiv som standardgrenens GitHub-formular. Browserkontrol mislykkedes på grund af en utilgængelig browserforbindelse/timeout; ingen test-issues er oprettet.
- W05 er klar i udviklingskoden; præsentationen på en faktisk HA-installation kontrolleres ved udgivelsen.
- W14: formatet følger geografien, tilpasses ved vinduesændring og bruger egne printkort til tjenesteår og rullende periode. Bred/høj geografi, periodernes adskillelse og bevarede originalformularer er afprøvet med opdigtede data. Nummerplacering og offline PDF-layout er efterfølgende implementeret og kontrolleret; se W14-kontrollen nedenfor. Levende browser/OSM er ikke verificeret i dette miljø.
- W17 er løst uden ændring af kortdata; ejerprioritet var ikke angivet og er rettet fra det tidligere tildelte 7-tal.
- Fortsæt først med W10/W14-kontrollen, derefter logo/ikon (W04/W03) og rapportoversigter (W13) efter ejerprioritet. Fortsæt den faste køreplans opgave 3 og 4 efter de højere prioriterede ønsker. Den faste fremdrift er fortsat 20 %.

Seneste kontrol: Checks og Platformskontrol består for b4c5781 (Mac, Windows og HA). 237 Python-prøver (én oversprunget), alle JavaScript-prøver og programpakkekontrol består lokalt. W18 er senere færdigformuleret og prioriteret som 2; se det aktuelle afsnit nedenfor.

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

W19-lokalkontrol: 252 Python-prøver (1 oversprunget), 3 betapakkeprøver, almindelige pakkeprøver og workflow-/shellsyntaks består. Prøven med stabil og beta på samme vært bekræfter forskellige cookies, uafhængige sessioner og separate data. ZIP bygges deterministisk fra samme programmanifest uden brugerfiler. Første publicering afventer CI-gaten.
