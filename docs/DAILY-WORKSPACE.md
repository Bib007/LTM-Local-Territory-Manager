# Daglig brug

[English](DAILY-WORKSPACE.en.md)

Disse forbedringer er klargjort til næste appversion. En udviklingsbranch er ikke en installationspakke. Følg [installationsvejledningen](INSTALL.md), når en komplet udgave er udgivet.

### Et brugbart udgangspunkt

Forsiden samler tjenesteåret, kortenes placering, gennemgange og opfølgning. Genvejene til mappen, kassen og åbne opgaver åbner de eksisterende lister. Et kort, der gennemgås to gange, tæller som to gennemgange, men kun én gang i dækningen. Anslåede besøg er adresser/enheder på de gennemgåede kort — ikke en registrering af faktiske husbesøg.

Opfølgningslisten regner fire kalendermåneder fra starten af den aktuelle gennemgang. Den er til din egen kontrol og træffer ikke beslutninger eller omfordeler kort automatisk. Ændrede sider er en påmindelse om kontrol og genprint af de fysiske kort. Forsiden ændrer ingen registreringer. Grafens månedstal kan også åbnes som tabel.

### Søgning og mobilmenu

Brug søgningen øverst eller **Ctrl K / Command K**, når du ikke skriver i et tekstfelt. Søg efter kortnummer, kortnavn, vej, område eller forkynder. Søgningen bliver i den lokale app. Navne og noter oversættes aldrig. Ved mange resultater vises en tydelig grænse; afgræns søgningen for at finde flere.

På telefonen kan menuen lukkes ved at trykke uden for den eller med Escape. Menuens åbne/lukkede tilstand følger knappen. Systemets ønske om reduceret bevægelse respekteres.

### Forbindelse er ikke det samme som gemning

- **Alle ændringer er gemt:** Den normale apphandling er gennemført uden fejl.
- **Gemmer…:** En gemning er i gang.
- **Gemning er ikke bekræftet:** Resultatet er usikkert. En afbrudt forespørgsel kan allerede være nået frem. Behold teksten, få forbindelsen tilbage, og kontrollér registreringerne, før du gentager handlingen.
- **Ændringen er gemt · opdatér data før næste ændring:** Skrivningen er bekræftet, men efterfølgende læsning eller visning er ikke afsluttet. Gentag ikke oprettelsen, importen eller delingshandlingen. Afslut redigeringen, vælg Opdater og kontrollér resultatet.
- **Ændringen blev afvist:** Appen har fået en kendt afvisning, fx et eksisterende kortnummer. Ret den angivne fejl; felterne er ikke overskrevet.
- **Forbindelsen svarer igen:** Serveren har besvaret en kontrol. Det beviser ikke, at en tidligere ændring er gemt. Appen sender ikke ændringen igen automatisk og rydder ikke den usikre gemmestatus.

Forbindelseskontrol ændrer ingen data og lader åbne felter stå. Afslut eller luk bevidst en redigering, før du vælger **Opdater**. Opdatering henter serverens tilstand; den gentager ikke en mislykket gemning. Efter en usikker gemning står der **Data opdateret · kontrollér tidligere ændring**, ikke **Alle ændringer er gemt**. Sammenlign registreringerne med det, du ville ændre. Hvis appen slet ikke åbner, viser fejlskærmen en genvej til et nyt forsøg og vejleder om computer/Home Assistant, Wi-Fi og VPN.
