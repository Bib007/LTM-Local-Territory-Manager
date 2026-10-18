# Daglig brug

[English](DAILY-WORKSPACE.en.md)

Disse forbedringer er klargjort til næste appversion. En udviklingsbranch er ikke en installationspakke. Følg [installationsvejledningen](INSTALL.md), når en komplet udgave er udgivet.

### Et brugbart udgangspunkt

Fra beta.34 afsluttes relevante opsætningstrin automatisk, når indstillinger eller data faktisk gemmes. Det gælder fx menighed, begge printprofiler, forkyndere og kort. Åbning og forhåndsvisning tæller ikke. Nye installationer starter med mappeminimum 0; vælg og gem det ønskede tal, også hvis det skal være 0. Eksisterende minimum og fremdrift bevares. **Spring over** og **Fortryd** kan stadig bruges. Forbindelser og samlet gennemgang af udleveringer bekræftes med **Udført**, fordi appen ikke kan kontrollere, om hele arbejdet er færdigt.

Fra beta.33 kan **Hurtig oprettelse → Interval** danne kortnumre fra start til slut inklusive. Vælg eventuelt antal cifre til nuludfyldning og ét foranstillet bogstav. 0–300 med fire cifre giver 0000–0300, i alt 301 kort; et bogstav foran bliver bevaret. Der er fortsat højst 500 kort pr. oprettelse. Kontrollér hele nummerlisten, antal og eventuelle dubletter før Bekræft og gem. Intet oprettes ved forhåndsvisning. **Egen liste** virker som før, hvor fx 1–10 er ét kortnummer, ikke et interval.

Fra beta.32 bruges **Opgaver** til al opfølgning. Tidligere noter bliver opgaver med samme tekst, datoer, kortreference og udført-status. Det sker også, når en gammel sikkerhedskopi importeres; forhåndsvisningen ændrer intet. Teksten oversættes ikke. Den interne datafil og gamle API-navne bevares for kompatibilitet, så eksisterende backups kan bruges.

Navigationens tæller viser kun åbne opgaver. Kort med åbne opgaver markeres i kortlisten/mappen, og udleveringsformularen viser en tydelig advarsel med opgaveteksten. En opgave opretter ikke IB automatisk og spærrer ikke udlevering. Brug fx opgaver til at tilføje IB, kontrollere numre eller fjerne et hus, der ikke findes. **○** markerer udført; **✓** genåbner. Udførte opgaver kan findes og redigeres under Udførte uden at miste indhold eller tilknytning.

Forsiden samler tjenesteåret, kortenes placering, gennemgange og opfølgning. Genvejene til mappen, kassen og åbne opgaver åbner de eksisterende lister. Et kort, der gennemgås to gange, tæller som to gennemgange, men kun én gang i dækningen. Anslåede besøg er adresser/enheder på de gennemgåede kort — ikke en registrering af faktiske husbesøg.

Opfølgningslisten regner fire kalendermåneder fra starten af den aktuelle gennemgang. Den er til din egen kontrol og træffer ikke beslutninger eller omfordeler kort automatisk. Ændrede sider er en påmindelse om kontrol og genprint af de fysiske kort. Forsiden ændrer ingen registreringer. Grafens månedstal kan også åbnes som tabel.

### Søgning og mobilmenu

Brug søgningen øverst eller **Ctrl K / Command K**, når du ikke skriver i et tekstfelt. Søg efter kortnummer, kortnavn, vej, område eller forkynder. Søgningen bliver i den lokale app. Navne og noter oversættes aldrig. Ved mange resultater vises en tydelig grænse; afgræns søgningen for at finde flere.

På telefonen kan menuen lukkes ved at trykke uden for den eller med Escape. Menuens åbne/lukkede tilstand følger knappen. Systemets ønske om reduceret bevægelse respekteres.

### Login og tastatur

Login kan vælges på dansk/engelsk. Sprogskift bevarer feltet og ændrer ikke adgangskoden. Kun sprogvalget gemmes som præference; indtast koden i din lokale app, aldrig i chat eller feedback. En loginfejl vises i formularen, og en afbrudt anmodning gentages ikke automatisk.

I dialoger flytter Tab og Shift+Tab mellem tilgængelige kontroller. Escape følger den normale gemme-/lukningskontrol; afvis lukning for at beholde felter ved usikker gemning. Efter lukning returneres fokus til kontrollen, der åbnede dialogen, når den stadig findes.

### Forbindelse er ikke det samme som gemning

- **Alle ændringer er gemt:** Den normale apphandling er gennemført uden fejl.
- **Gemmer…:** En gemning er i gang.
- **Gemning er ikke bekræftet:** Resultatet er usikkert. En afbrudt forespørgsel kan allerede være nået frem. Behold teksten, få forbindelsen tilbage, og kontrollér registreringerne, før du gentager handlingen.
- **Ændringen er gemt · opdatér data før næste ændring:** Skrivningen er bekræftet, men efterfølgende læsning eller visning er ikke afsluttet. Gentag ikke oprettelsen, importen eller delingshandlingen. Afslut redigeringen, vælg Opdater og kontrollér resultatet.
- **Ændringen blev afvist:** Appen har fået en kendt afvisning, fx et eksisterende kortnummer. Ret den angivne fejl; felterne er ikke overskrevet.
- **Forbindelsen svarer igen:** Serveren har besvaret en kontrol. Det beviser ikke, at en tidligere ændring er gemt. Appen sender ikke ændringen igen automatisk og rydder ikke den usikre gemmestatus.

Forbindelseskontrol ændrer ingen data og lader åbne felter stå. Afslut eller luk bevidst en redigering, før du vælger **Opdater**. Opdatering henter serverens tilstand; den gentager ikke en mislykket gemning. Efter en usikker gemning står der **Data opdateret · kontrollér tidligere ændring**, ikke **Alle ændringer er gemt**. Sammenlign registreringerne med det, du ville ændre. Hvis appen slet ikke åbner, viser fejlskærmen en genvej til et nyt forsøg og vejleder om computer/Home Assistant, Wi-Fi og VPN.
