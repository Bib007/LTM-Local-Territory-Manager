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

## Fjern forkynder med bekræftelse
- Oversigt og profil har knappen Slet forkynder, som åbner en bekræftelsesdialog med navnet og konsekvenserne.
- Backend tillader kun sletning af forkyndere uden aktive, afsluttede eller stadig gendannelige udleveringer. Dette sikrer, at S-13, rapporter og historik ikke får manglende forkynderrelationer. Tilknyttede poster blokeres med en forklaring.
- Sletning kræver publishers.view, publishers.manage og loans.view samt eksplicit bekræftelse og det nøjagtige observerede forkyndersnapshot (navn, gruppe, funktion, pioner); ændringer fra andre brugere imellem åbning og bekræftelse afvises.
- Benytter den eksisterende delete/recovery-mekanisme: fjernet fra listen og tælleren straks efter serverbekræftelse, mulighed for at gendanne inden for 48 timer via Gendan ved fejl. Gendannelse forhindres, hvis samme navn allerede findes som en anden aktiv forkynder.
- Ingen ny databasekolonne eller API-route. Den eksisterende delete-kontrakt udvides med module=publishers, confirmation og expected; capability-kataloget opdateres. Delte filer nu også distrikt/app/store.py og distrikt/app/profile_policy.py.
- Regression: fiktive cases for ingen relationer, aktiv/afsluttet/gendannelig udlevering, samtidige navne-/gruppeændringer, rettigheder, gendannelse og navnekollision samt browserbekræftelse/annullering.

## Verificering før merge
- Kør JavaScript-syntakscheck, fiktive optællings- og sikkerhedstests, dansk/engelsk og browser-arbejdsgange på mobil/tablet/desktop.
- Kontrollér særskilt tilføjelse, flytning, fjernelse fra et autoriseret snapshot, nul/én/mange, tomme grupper og filtrering.
- Fysiske iPhone/iPad/Android-enheder er ikke afprøvet i denne ændring, medmindre det dokumenteres senere.
- Opret PR mod develop, kontrollér grøn CI og review og opdatér branche uden at overskrive andres commits.
- Merge først efter review og grønne tests. Ingen Stable-release i denne opgave; saml godkendte PR'er på develop, regressionstest helheden og udgiv én separat kontrolleret Stable-release.
