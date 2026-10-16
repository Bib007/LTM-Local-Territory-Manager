# Ønskeliste og nye opgaver

Den faste klargøringsplan står fortsat på 20 %. Nye ønsker udvider ikke automatisk dens procenttal. Dansk er hovedsprog, og ændringer udvikles på develop før en stabil udgivelse.

| ID | Ønske | Ejerprioritet | Placering og status | Færdig når |
| --- | --- | --- | --- | --- |
| W23 | Undersøg idéer og feedback uden krav om GitHub-konto | 10 | Registreret fra ejerens dokument; afklar mulige kanaler efter de højere prioriteter | Beskriv en enkel mulighed uden GitHub-login, dens modtager og håndtering af bilag/persondata. Ingen ny offentlig indsendelsestjeneste oprettes automatisk. |
| W20 | Ret opsætningsguidens valgfelter, hvor teksten står ved siden af boksen med knapper | 5 | Udgivet i beta.5 med grønne program/platform/HA-gates; offline layout og guideprøver består | Valg og forklaring holder sig i samme boks ved mobil- og skrivebordsbredder. |
| W21 | Nulstil betadata, så en test kan begynde forfra | 2 | Færdig og udgivet i beta.2; program-, platform- og HA-kontroller består | Tydelig bekræftelse, sikkerhedskopi og ny opstart; stabil installation berøres ikke, og offentlige kort må ikke efterlades uden registrering. |
| W22 | Fast topbar under rulning og logo som link til forsiden | 4 | Udgivet i beta.3, samlet med W04/W03; program/platform/HA-gates består | Topbaren bliver på plads, indhold dækkes ikke, og logoet åbner forsiden med appens sædvanlige kontrol af ugemte ændringer. |
| W19 | Små løbende betaudgivelser, som kan testes i HA efter nye funktioner | -1 · kritisk | Færdig: HA-betaer til og med 1.12.0-beta.7 er udgivet; program-, Mac-, Windows- og HA-betagates består; løbende små betaer er nu fast aftale | Kontrollerede betaer kan installeres/opdateres i HA ved siden af stabil udgave. Hver beta har fast version og kort testliste; main forbliver stabil. |
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
| W03 | Projektets logo tydeligt i appens øverste del | 5 | Udgivet i beta.3 sammen med W04/W22 | Eksisterende mærke gennemgås og suppleres med korrekt logo; lys/mørk baggrund samt mobilbredder er kontrolleret. |
| W04 | Logo og ikon på appens side i Home Assistant | 4 | Udgivet i beta.3: PNG-ikon og logo, med i begge pakker; HA-visning hos ejeren udestår | De relevante HA-billeder findes, følger samme identitet og er med i programpakken; visning på egen HA står særskilt. |
| W05 | Bedre informationstekst ved installation i Home Assistant | 3 | Færdig på develop: beskrivelse og introduktion med funktioner, første start, lokal drift og backup; pakkekontrol består | Kort beskrivelse og dansk introduktion forklarer funktioner, lokal drift, adgang og første start uden intern restliste. |
| W06 | Gennemgå og forbedr HA-appens sikkerhedsvurdering | 6 | Efter HA-præsentation og før næste stabile HA-udgivelse | Officielle krav og faktisk konfiguration er gennemgået. Forbedringer med uændret funktion indføres; større ændringer forelægges ejeren først. |
| W07 | Afklar adressekildens levetid og forenkling til OpenStreetMap-baggrund | 5 | Egen API-nøgle og guidning valgt; lokal forbindelse udgivet i beta.7; selve GraphQL-importen mangler før 15.01.2027 | Kontroller den varslede januarfrist og forskellen på adresser og kortbaggrund. Bevar adressefunktionerne gennem et afprøvet alternativ. OpenStreetMap er den foretrukne synlige baggrund; vurder fjernelse af den lokale reservevisning uden at fjerne lokale data. |
| W08 | Afklar hvornår det tidligere private repository kan arkiveres | 10 | Efter stabil kildekode, pakker og udviklingshistorik er kontrolleret | Giv ejeren en konkret anbefaling, når nødvendig kode og dokumentation er bevaret. Arkivér eller slet ikke noget repository automatisk. |
| W12 | Kontrollér webdemoens direkte link og få den til at åbne korrekt | 5 | Direkte Pages-rodadresse og seks aktiver HTTP 200 uden login; dokumentation rettet; levende browser står særskilt | Verificér det faktiske Pages-link og browserens første åbning; ret eventuelle publicerings- eller linkfejl og brug kun opdigtede demodata. |
| W13 | Gør KTM-rapporten mere nyttig ved besøget | 4 | Opfølgningsliste afvist af ejeren 16.10.2026 og fjernet til beta.6; øvrige rapportforbedringer vurderes særskilt | Undersøg relevante oversigter og gennemgå den eksisterende rapport. Foreslå og tilføj nyttige mål med tydeligt datagrundlag; skeln mellem forslag og eventuelle verificerede krav. |

Ønsker læses ind fra ejerens dokument, når vi arbejder på LTM og mellem afsluttede opgaver. Et punkt fjernes først fra indbakken, efter at ønsket er gemt her. En overførsel betyder planlagt, ikke færdig. Oplyste prioriteter bevares: -1 er kritisk og går før øvrigt arbejde, 1 er snarest, 10 er valgfrit på længere sigt. Arbejdsstatus spejles i ejerens dokument, så arbejdsrækkefølge og fremdrift kan følges uden GitHub. Arbejdsrækkefølge efter den kritiske statusopgave: feedback og udleveringsstyret Drive-adgang (2) afsluttes; derefter HA-information og dynamisk KTM-kort (3), HA-logo og rapportoversigter (4), app-logo, adressekilde og webdemo (5), autofuldførelse og HA-sikkerhed (6), automatisk inddeling (7) og arkivanbefaling (10). Ønsker uden angivet prioritet får ikke et opdigtet prioritetstal. Afhængigheder og en verificeret kildefrist kan ændre rækkefølgen. Private data og eksempler kopieres ikke til denne offentlige plan.

## Aktuel status og næste arbejdssession · 16.10.2026

- Stabil main og seneste stabile release: 1.11.1. Seneste nummererede HA-beta: 1.12.0-beta.7. Checks, Platformskontrol og HA beta release består for kilde dd5d934. Alle betaer .2–.7 har separate ZIP/checksum og er prereleases.
- Udgivet: betanulstilling (W21, beta.2), topbar/forsidelink/logo/HA-billeder (W22/W03/W04, beta.3) og guide-layout (W20, beta.5). Rapportopfølgningslisten fra beta.4 er efterfølgende afvist af ejeren og fjernet i beta.6 og senere. Testlisten følger docs/BETA-NOTES.md. Virkelig HA, browserrulning, OSM, printdialog og Google-konto er fortsat ejerprøver.
- W07 (5): officiel DAR REST-frist 15.01.2027 er verificeret. Lokal nøgleopsætning og vejledning er udgivet i beta.7. Byggestenen til komplet GraphQL-sidehentning er nu implementeret og afprøvet på develop; den er endnu ikke aktiveret i importen. Næste kodeopgave er transport/forespørgsler og lokale DAR-joins efter docs/ADRESSEKILDE-2027.md. Dokumenteret skema kræver autentifikation; intet skema eller live data er hentet med ejercredentials. Bevar lokale data og reservevisning. Adressevælgerens varslede brugerstyring er en særskilt ændring.
- W12 (5): det rigtige direkte demo-link og alle statiske JS/CSS/logo-aktiver svarer 200 uden login og matcher kontrolleret kilde. Links er rettet i develop-dokumentationen. Browserens første åbning/mobil/print står særskilt.
- Efter prioritet 5: W06 HA-sikkerhedsvurdering og W15 forkynderforslag (6), W16 meningsfuld indeling (7), W08 arkivanbefaling og W23 kontofri feedback (10). Større HA-sikkerhedsændringer aftales med ejeren. Arkivér ikke automatisk.
- W10-formularen er fortsat kun på develop og aktiveres først som GitHubs standardformular via main. Ingen test-issues er oprettet. W18's egen Google-/inkognitotest udestår.
- Den faste køreplans opgave 3 og 4 fortsætter efter de højere prioriterede ønsker; procenten forbliver 20 % (2/10). Brug denne oversigt frem for de historiske næste-trin i kontroljournalen nedenfor.

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
