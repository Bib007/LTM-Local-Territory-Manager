# Næste stabile LTM · under udvikling

Målet er de allerede udgivne betafunktioner plus brugerprofiler, administratorstyrede roller/rettigheder, samtidig redigering og konfliktgennemgang. W106 tilføjer seneste gennemgangsdato og udleveringsdato til det digitale kort; det er registreret til samme stabile udgave og endnu ikke leveret. W107 om importerede vejintervaller og gradvis overgang til geografisk kortlægning skal også med. W108 tilføjer tjenestegrupper, gruppetilsynsmand/assistent/pioner og lokal import af gruppeliste.

Profilintegration er prøvet lokalt i den almindelige app, men kandidatens samlede platform-/udgivelseskontrol og de resterende afslutninger mangler. **Stabil 1.12.1 og beta.75 er fortsat de udgivne udgaver.** Ny stabil publicering kræver særskilt ejerbesked; denne plan er ikke en udgivelsesgodkendelse.

Aktuel status står i [udviklingsplanen](planning/OENSKELISTE.md) og [profilnotatet](planning/BRUGERE-SAMTIDIG.md). W85/OCR og automatisk kortinddeling genoptages ikke. Drive, gendannelse og den generelle HA-prøve er allerede ejerbekræftet og bestilles ikke igen. Codex Security er ikke kørt.

## Historik · stabil 1.12.0

Ejeren har godkendt udgivelse 23.10.2026. De færdige, brugerrettede nyheder og opdateringsråd står i [udgivelsesnoterne](RELEASE-NOTES.md). Dette dokument bevarer beslutningsgrundlaget for udgivelsen.

Udgangspunktet er den verificerede beta.62 med sikkerhedsrettelser, forenklet feedbackmenu og bevarede lokale arbejdsgange. Home Assistant, API-adressehentning samt Drive og gendannelse er ejerbekræftet. Den offentlige demo er en særskilt udgave med opdigtede data.

Den aftalte [manuelle sikkerhedsgennemgang](SIKKERHEDSGENNEMGANG-2026-10.md) er gennemført med de beskrevne afgrænsninger. Codex Security og en uafhængig penetrationstest er ikke kørt. Adgangsmodellen for lokalt netværk og egen VPN er uændret. Krypteret nøglebackup, større HA-adgangsændringer og flerbrugerredigering er fortsat fremtidige ønsker. W61's eksterne GitHub-oprydning er efter ejerens beslutning ikke en udgivelsesblokering.

Automatisk kortinddeling er sat på pause; manuel korttegning og eksisterende data bevares. Fuld engelsk oversættelse er endnu ikke færdig. Nye installationsprodukter i W74 og løbende status under adressehentning i W82 venter til efter stabil udgivelse.

Den stabile publicering kræver de fulde program-, browser-, pakke-, Mac-, Windows- og Home Assistant-kontroller på den præcise kode. Kun den kontrollerede main-version må publiceres. Eksisterende udgivelser overskrives ikke. [Slutkontrollen](SLUTKONTROL.md) beskriver kontrollerne; aktuelle resultater og pakkeidentitet registreres i Google-planen og ønskelisten efter publicering.
