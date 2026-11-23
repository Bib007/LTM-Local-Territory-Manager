# LTM 1.13.0-beta.4

## Nyt siden beta.3

- **To gennemgangsmål:** »Gennemsnitlig gennemgangstid« måler tiden fra udlevering til aflevering, når kortet meldes gennemgået. »Ældste kort i gennemgangskøen« viser alderen på det næste ledige kort efter udleveringsrækkefølgen. Begge bokse har korte forklaringer, og kort uden kendt dato vises særskilt.
- Forsiden går direkte fra »Dit overblik / Velkommen« til de relevante nøgletal. Den ekstra titelblok og den dobbelte tæller for gennemgange er fjernet.
- Fremdriftsboksen viser både dækning af **forskellige aktuelle distriktskort** og **anslåede besøg på de samme kort**. Hvert kort med en gennemgang i tjenesteåret medregnes én gang i begge tal, uanset gentagne gennemgange. Ukendte besøgstal mærkes særskilt. Historiske S-13-rapporter og månedsdiagrammer ændrer ikke optællingsmetode.
- Brugsstatistik har fået sin egen fane under Indstillinger.
- »Aflever til kassen« har nu valgt kort, sidens kortdetaljer, markeringer og hjælp til at åbne næste markerede kort. Hver aflevering gennemføres individuelt med kontrol af dato, gennemgang og IB; markeringerne skriver aldrig data alene.

Denne Beta indeholder forsidefejlrettelserne fra Stable 1.12.40 samt de eksisterende Beta-forbedringer med **brugsstatistik** (beta.1) og **KTM-rapporten** (beta.2). Beta og Stable har fortsat separate data, porte og logins.

## Samlet opdatering

- **Daglig brug og opgaver:** Enklere opgavefiltre, adressekontrol nederst, ulæste opgavesvar og kopierbare påmindelser om for gamle udleveringer under Forkyndere. Udleveringsdialogen er ryddet op, IB-revision er en tydelig fravalgt checkbox, og valgte kort fremhæves ved aflevering pr. forkynder.
- **Kort, historik og indstillinger:** Områdefarver med eksplicit masseoverskrivning og individuelle kortvalg; justerbare månedintervaller; valgfrit antal års historik; husket visning af distriktnumre i rapportkortet; mere læsbar historik på mobil og desktop.
- **Hurtigere og sikrere arbejde:** Genbrug af komplette DAR-veje, tydeligere hentetal og konfliktadresser; geografiske forhåndsvisninger og forbindelsestjek venter ikke bag lange writes. Snapshots bruger mindre arbejde, mens redigeringskonflikter og kvoter bevares. Særskilte rollerettigheder til daglige handlinger og oprydning.
- **Deling og vejledning:** Godkendte Google Drive-PDF'er får en søgbar, grupperet adresseliste fra side 3. Private IB-oplysninger filtreres fortsat. Den personlige guide/nyhedsvisning erstattes af hjemmesideguiden; kun logoets klikflade fører til forsiden. Ufærdige flytteforslag er skjult.
- **Vedligeholdelse og afgrænset import:** Gamle arbejdsnoter ryddes op. Offlineværktøjet til enkelte NW Scheduler-/TH-grænsefiler følger med som forsøgsvis filkonverter; udenlandsk adressehentning eller fuld migrering er ikke tilføjet. Ekstra GitHub-grene arkiveres som tags og fjernes først efter verificeret betaudgivelse.

## Forsiden

- **Fuldstændig nyt layout:** Forsiden starter med en kort tjenesteårsoverskrift, en tydelig fremdriftsbjælke for gennemgåede aktuelle kort, et stort gennemsnit mellem gennemgange samt anslåede besøg. Placering og handlinger står lige nedenunder. Store ringe og det høje tjenesteårs-banner er fjernet.
- **Plads til data:** Grafer og opfølgninger ligger under hovedtallene, mens onboarding, backup, ugentlige opgaver og adressepåmindelser fortsat findes længere nede. Desktop og mobil har egne tilpasninger; begrænsede brugere får samme kompakte fremdriftsvisning uden skjulte oplysninger.
- **Roligere gennemsnit:** Resultatet er større og vises uden antal intervaller eller forklaringer om omregning/prognoser.
- **Anslåede besøg:** Et korts aktuelle, kendte besøgstal minus kortets IB tæller for **hver** gennemgang. Eksempel: 35 besøg, 2 IB og to gennemgange giver 66 anslåede besøg.
- Gennemgange importeret med ukendt antal kan nu medregnes, hvis kortet i dag har et kendt antal. Ukendte tal uden brugbart grundlag forbliver udeladt. De gemte historikposter ændres ikke.
- **Sammenligning med sidste år:** Grafen viser også sidste års gennemgange for de måneder, der ikke er begyndt endnu i det aktuelle tjenesteår. Indeværende måned afgrænses til dags dato og samme dato sidste år.
- De tidligere Stable-korrektioner er også bevaret: historikperioder kan importeres i begge datoordener, importgodkendelsens tekstfelt kan udfyldes ved afviste forhåndsvisninger, og alle S-13-perioder bruger den originale S-13-formular med en tydelig periodeangivelse.
- Nul og manglende registreringer må ikke forveksles. Tabellen viser de præcise perioder, og skønnet er ikke faktiske husbesøg.

## Prøv selv

1. Kontrollér først den nye forside i mørkt og lyst tema på desktop og mobil: progress, gennemsnit, besøg og kortstatus skal være synlige i det øverste overblik, uden vandret rulning.
2. Kontrollér, at dækningsprocenten tæller *forskellige aktuelle* kort, og at gentagne gennemgange fortsat tæller i antal gennemgange, ikke dækningen.
3. Kontrollér, at genvejene til mappe, kasse, opgaver og daglig brug åbner de samme funktioner, og at backup/opfølgninger stadig findes længere nede.

### Eksisterende rettelser

1. Kontrollér **1.13.0-beta.3** på den separate Beta-installation (port 8788).
2. Gennemgå et prøvekort med 35 besøg, registrér 2 IB, og kontrollér at forsidens skøn stiger med 33 for hver gennemgang.
3. Kontrollér, at gentagne gennemgange tæller igen, og at arkiverede kort kun bidrager til besøgsestimatet, når der er kendte tal.
4. Kontrollér 12 måneders sammenligning mod sidste tjenesteår, også for fremtidige måneder i det aktuelle år, samt tabellen under grafen.
5. Kontrollér fortsat brugsstatistikken under Indstillinger og den udvidede KTM-rapport med dækning/mangelliste fra tidligere betaer.

## English

Beta 1.13.0-beta.3 introduces a compact responsive home redesign, a prominent service-year progress bar, larger average completion interval, and key statistics before charts and reminders. It also carries the dashboard corrections from Stable 1.12.40 while preserving usage statistics and the updated KTM reporting. Estimated visits use each territory's current known visit count less linked do-not-call entries for every completion, including formerly unknown historic completions when a current count exists. Previous-year columns remain visible for all twelve months, independently of current-year activity. No stored records are rewritten.
