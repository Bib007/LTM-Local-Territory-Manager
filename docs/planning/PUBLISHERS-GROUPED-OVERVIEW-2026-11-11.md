# Forkyndere: grupperet oversigt

## Afgrænsning
- Tællerne Forkyndere i alt og Forkyndere i visningen adskiller hele det autoriserede register fra det aktive søge- og gruppefilter. Begge følger opdaterede state-snapshots.
- Alle tjenestegrupper viser eksisterende grupper alfabetisk i responsive sektioner; personer uden gruppe vises under Ingen tjenestegruppe til sidst. Hver gruppe viser antal efter søgning.
- En valgt gruppe med nul søgeresultater viser en tom tilstand; et forældet gruppefilter nulstilles som før.
- Den eksisterende alfabetiske sortering, søgning, redigering, import, profil og historik bevares.

## Afhængigheder ved parallelt arbejde
- Base: develop ved cb684ff30f9f51e78f0e419318edb2d48df740eb. Arbejd kun på feature-branchen, ikke direkte på develop/main.
- Database: ingen migration, ny tabel eller semantikændring. Eksisterende publishers.group genbruges. En selvstændig deaktiveringsfunktion er ikke del af denne ændring.
- API: ingen nye endpoints eller kontraktændringer; den eksisterende autoriserede state-projektion og API-adgangskontrol genbruges.
- Delte filer: distrikt/app/app.js, distrikt/app/style.css og distrikt/app/i18n.js. Konfliktkontrollér ved opdatering mod seneste develop, især når andre UI-PR'er berører disse filer. Den nye testfil er distrikt/tests/test_publishers_overview.cjs.
- Persondata: ingen navne eller tilknytninger indlægges i offentligt website/demo, logges, hardkodes eller sendes til andre tjenester. Forkynderrettigheder håndhæves fortsat af backend og eksisterende UI-handlingskontrol.

## Verificering før merge
- Kør JavaScript-syntakscheck, fiktive optællings- og sikkerhedstests, dansk/engelsk og browser-arbejdsgange på mobil/tablet/desktop.
- Kontrollér særskilt tilføjelse, flytning, fjernelse fra et autoriseret snapshot, nul/én/mange, tomme grupper og filtrering.
- Fysiske iPhone/iPad/Android-enheder er ikke afprøvet i denne ændring, medmindre det dokumenteres senere.
- Opret PR mod develop, kontrollér grøn CI og review og opdatér branche uden at overskrive andres commits.
- Merge først efter review og grønne tests. Ingen Stable-release i denne opgave; saml godkendte PR'er på develop, regressionstest helheden og udgiv én separat kontrolleret Stable-release.
