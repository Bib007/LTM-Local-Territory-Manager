# Sikkerhedsgennemgang før stabil · 23.10.2026

## Resultat og kodegrundlag

Manuel, kildebaseret gennemgang suppleret med Bandit 1.9.4, pip-audit 2.10.1 og isolerede regressionstests. Dette er ikke en Codex Security-scanning eller en uafhængig penetrationstest. Udgangspunkt: develop `303541e557edc6c0301f8f925d31a94c74d1e0d4`. Rettelserne klargøres som 1.12.0-beta.62; main er fortsat stabil 1.11.1. Den endelige rettelsescommit findes i Git-historikken sammen med denne rapport. Udgivelse kræver grønne kontroller på den præcise kandidat.

To konkrete problemer er håndteret: en forældet PDF-afhængighed med kendte ressourcefejl samt omgåelse af XLSX-importens DTD-afvisning ved UTF-16. Der er ikke fundet en bekræftet høj/kritisk sårbarhed i de gennemgåede programstier. Det er en afgrænset vurdering, ikke en garanti om fravær af fejl.

## Trusselsmodel og dækning

LTM bruger én betroet lokal administrator, LAN/VPN-login på HA og loopback på desktop. Interneteksponering og flere indbyrdes mistroiske brugere er ikke understøttede sikkerhedsmodeller. Importerede filer, providerdata og browserforespørgsler behandles som ubekræftede input. IB, navne, udlån, tokens og API-nøgler må ikke automatisk offentliggøres. Kun et aktivt godkendt kortbillede må sendes til Google Drive.

Gennemgåede grænser:

- `access.py`, `server.py`: login, passwordhash, session, Host/Origin, tokenkrav, ruter og statiske filer. Begge krav (session og request-token) er afprøvet på 24 følsomme GET/POST-ruter. Forkert token og manglende session afvises før sideeffekter. Fremmed Origin afvises også med gyldig session/token; proxyheaders giver ingen adgang.
- `portable.py`, `card_import.py`, `history_import.py`, `s13_reader.py`, `boundary_import.py`: arkivnavne, begrænset ZIP/JSON/XML/base64, parameteriseret dataskrivning, preview-token/revision, transaktion og PDF-underproces. Eksisterende prøver dækker rollback, forældede preview-svar, ukendte arkivfiler og genstart.
- `sharing.py`, `google_connect.py`, `address_source.py`, `geodata.py`, eksportstier: PKCE/state, faste TLS-endpoints, scopes, metadatafiltrering, PNG-format/-størrelse, IB-filtrering, eksplicit billedgodkendelse, adgangslukning og fejl/genforsøg. Ingen rigtige konti eller private nøgler er brugt.
- Udvalgte DOM-/eksportstier i app, korteditor, deling og oversættelse: HTML-escaping, faste destinationslinks, CSP og CSV-formelbeskyttelse. Dette er ikke en linje-for-linje-gennemgang af alle JavaScript-filer eller medleverede bibliotekers kildekode.
- HA-konfiguration, startscript, Dockerfile og Actions-workflows: ingen ekstra HA-API-privilegier/hostnetværk; begrænsede workflowrettigheder, ingen `pull_request_target`, adskilt publicering og genbrugelige udgivelseskrav.
- Sporing af nøglefilnavne og genkendelige nøglemønstre i de aktuelle sporede programfiler; ingen træffere på de kontrollerede nøglemønstre. Dette er ikke en fuld historisk secrets-scanning.

## Fund 1 · PDF-afhængighed · moderat tilgængelighedsrisiko

Lokal S-13-import indlæste pypdf 6.10.0. pip-audit gav 57 rå advisory-poster med 39 forskellige IDs; nogle IDs/aliases overlapper. Det betyder ikke, at alle er udnyttelige gennem LTM. Relevante upstream-eksempler er [CVE-2026-113790](https://github.com/py-pdf/pypdf/security/advisories/GHSA-f54x-cmq8-qg57), hukommelsesforbrug ved PDF-arrays/dictionaries, og [CVE-2026-82398](https://github.com/py-pdf/pypdf/security/advisories/GHSA-fc8x-2rww-xw9m), lange køretider ved læsning uden whitespace.

Angrebsvej: En administrator importerer en manipuleret PDF. Den lokale parser kan bruge mange ressourcer eller fejle; preview holder under behandlingen appens datalås. Linux/macOS-processen har allerede CPU-/hukommelsesgrænser og alle platforme har 15 sekunders procestimeout. Windows har ikke samme POSIX-hukommelsesgrænse. Der er ikke dokumenteret kodeudførelse eller datalæk. De enkelte upstream-PoC'er er ikke kørt; pakkens berørthed er verificeret mod versionsintervaller og kaldestien til PdfReader.

Rettet ved at medlevere uændrede pypdf 6.21.2-kilder fra den officielle wheel. Wheel-SHA256 er verificeret mod PyPI: `1d44d1a3a200f25062adff0085b02040e4646431ac2ccac22e42679e91466084`. Den deterministiske ZIP har SHA256 `6249fae430aae6af33ef92ea894309e6a2f1062de6cd445fb8bf6d2fd34b6a70`. Kilde-/pakkereferencer og licens/proveniens er opdateret. Python 3.9-understøttelsen og den separate, begrænsede underproces bevares. S-13-prøverne består med den nye parser.

## Fund 2 · XLSX DTD-kontrol kunne omgås · lav/moderat robusthedsrisiko

`card_import.py:xlsx_rows.xml` søgte efter ASCII-bytes for DOCTYPE/ENTITY før ElementTree. En gyldig UTF-16-workbook kunne indeholde interne XML-entiteter uden at ramme kontrollen. En ufarlig, komplet XLSX-prøve med en intern testentitet blev accepteret før rettelsen (fire rækker). Dette dokumenterer omgåelsen, ikke filudlæsning eller en gennemført hukommelsesudmattelse. Eksisterende ZIP-grænse og Expat-beskyttelse begrænser risikoen.

Rettet ved en TreeBuilder, der afviser DOCTYPE i selve XML-parseren, før entiteter behandles. Regressionstesten afviser UTF-8, UTF-16 og UTF-16 big-endian med DTD. En almindelig UTF-16-workbook uden DTD importeres fortsat. Makroer, eksterne arklinks, formler og størrelsesgrænser er fortsat kontrolleret.

## Yderligere forebyggelse

Pakkebygningen afviser nu `drive-auth.json`, `datafordeler-auth.json`, `access.json` og `run.json` i programtræet, også i undermapper. Det er en forebyggende forbedring; der er ikke fundet sådanne filer i den aktuelle sporede kode. En ny prøve bekræfter, at de ikke kan medleveres ved et uheld.

Den fælles Security checks-workflow auditerer de eksplicit medleverede Python-versioner og blokerer højt klassificerede Bandit-fund. Checks (og dermed stabil publicering) samt beta-publicering afhænger af kontrollen. Hele Bandit-resultatet er desuden vurderet manuelt ved denne gennemgang: 36 signaler, ingen high. SQL-signaler bruger faste modulnavne og bundne værdier; netkald har faste hosts; subprocess-kald har faste argumentlister uden shell; LAN-binding er tilsigtet. XML-signaler er vurderet sammen med parsernes grænser og rettelsen ovenfor. En høj-only CI-gate erstatter ikke denne vurdering af lavere signaler.

## Validering

- 479 Python-prøver består; én dokumenteret prøve af en ikke-medleveret privat backup er sprunget over.
- Nye prøver: 24 API-ruter uden session og med forkert token, fremmed Origin uden dataskrivning, private/encoded filstier, DTD i flere XML-kodninger samt normal UTF-16-import.
- pip-audit efter rettelse: ingen kendte advisories for pypdf 6.21.2, qrcode 8.2 og typing_extensions 4.16.0 på kontroltidspunktet. Kun disse medleverede Python-biblioteker er omfattet; ikke hele containerens pakker eller Python-fortolkeren.
- Bandit på appens egen Python-kode, eksklusive vendor_py: ingen fund med severity high. Lavere signaler er gennemgået som ovenfor.
- JavaScript-, pakke-, arkivstart-, browser- og platformkontroller registreres i CI på kandidaten. De må ikke betegnes bestået ud fra ældre betaer.

## Afgrænsning før main

GitHub Support/W61 er efter ejerens udtrykkelige beslutning ikke en udgivelsesblokering; historisk oprydning er ikke dermed afsluttet. Ejeren har godkendt Drive/gendannelse, generel HA-drift og API-adressehentning. Der bruges ingen private data i denne gennemgang.

Den dokumenterede HTTP/LAN/VPN-model, manglende særskilt AppArmor-profil og containerens nuværende procesbruger er uændret. HTTP er ikke transportkrypteret på det lokale net; VPN beskytter VPN-strækningen. De arkitekturforbedringer i W06 og separat krypteret nøglebackup i W56 anbefales behandlet særskilt, ikke præsenteret som implementeret. Serveren har ikke fået en komplet ressource-/belastningstest. Der er ikke kørt container-OS-scanner, omfattende fuzzing, fuld afhængighedskildeaudit eller uafhængig penetrationstest.

Anbefaling: Hold rettelserne på develop/beta, indtil alle kandidatens CI-/platformkontroller er grønne. Derefter er der ikke identificeret en yderligere konkret sikkerhedsblokering i de gennemgåede stier for den dokumenterede lokale LAN/VPN-brug. Main skal fortsat promoveres som et særskilt udgivelsestrin. Codex Security må ikke markeres som kørt; denne manuelle gennemgang er den aftalte alternative kontrol.
