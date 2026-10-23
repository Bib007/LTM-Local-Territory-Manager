# LTM 1.12.2-beta.63 · Små ting, der gør hverdagen lettere

Denne beta samler flere ønsker i én opdatering. Den indeholder også rettelsen fra den stabile 1.12.1, så kort kan redigeres, udleveres og afleveres uden den unødige besked om genindlæsning.

- **Opgaver:** Fremtidige ugentlige opgaver tæller først på den planlagte dag. Udførte gentagelser flyttes til næste dato; historikken bevares.
- **Digitale kort:** Baggrunden er mere hvid, mens prikker, husnumre og grænse står tydeligt.
- **Tekster:** Adressehentning og lokal lagring omtaler dit lokale system frem for at antage, at du bruger en Mac.
- **Gemte visninger:** Findes ved den geografiske kortoversigt.
- **GitHub-forsiden:** Fire løse filer; de øvrige vejledninger og hjælpere er samlet i mapper.

Åbn appen på ny efter opdatering. Prøv en gentagende opgave med en fremtidig dato, markér en forfalden opgave udført, og kontrollér tælleren. Dan en ny forhåndsvisning af et digitalt kort for at se den lysere baggrund. Allerede delte billeder og QR-links ændres ikke ved opdateringen; godkend et nyt billede, når du ønsker at opdatere det.

Hvis flere redigerer samme oplysninger, bliver den senest gemte ændring stående. Samtidig redigering tages op igen med brugerprofiler. Den stabile kanal forbliver 1.12.1.

Denne kandidat skal bestå alle udgivelseskontroller, før den betegnes udgivet. Ønskerne om langsom gemning, samlet import/opfølgning, adressehentning, lys tilstand og ny demo er fortsat åbne.

---

# Beta.62 · Sikkerhedskontrol før stabil

PDF-læseren er opdateret til pypdf 6.21.2. XLSX-import afviser DTD/entiteter i alle understøttede XML-kodninger. API-prøverne dækker beskyttede ruter uden session eller korrekt token, fremmed Origin og forsøg på at hente private filer. Den korte feedbackmenu er med.

Prøv almindelig S-13 PDF-import og kortimport med den lokale forhåndsvisning. Eksisterende data bevares. Google Support/W61 blokerer efter ejerens beslutning ikke stabil; sagen er ikke erklæret afsluttet. W82 om aktivitet og adresseantal er planlagt efter stabil. Se [sikkerhedsgennemgangen](SIKKERHEDSGENNEMGANG-2026-10.md) for fund og afgrænsning.

Denne kandidat skal gennem alle udgivelseskontroller før den betegnes udgivet. Main er fortsat stabil 1.11.1.

---

# LTM 1.12.0-beta.61

W81 · Automatiske forslag til distriktsgrænser og kortinddeling er sat på pause.

Opsæt distrikter og det automatiske valg i førstegangsopsætningen er fjernet. En tidligere plan med automatisk inddeling åbner nu manuel korttegning. Serveren afviser både synkrone og asynkrone forslag, grænsejusteringer og oprettelse fra gamle forslag. Eksisterende kort, adresser, udlån og historik bevares. Adressehentning, kortimport og lokal IB-import fortsætter som før.

Prøv Indstillinger → Avanceret → Åbn lokal IB-import: der skal kun vises IB-import, ingen trin til automatisk inddeling. Åbn korteditoren og kontrollér et eksisterende kort. Koden, algoritmeprøverne og den tidligere vejledning ligger fortsat på GitHub til senere udvikling. Se [arkiv og afgrænsning](ARKIVERET-AUTOFORDELING.md).

Før en stabil udgivelse bruges den konkrete [slutkontrol](SLUTKONTROL.md). W78 kræver stadig ejerens gentagelse af den afbrudte adressehentning. Denne beta ændrer ikke adressekilden eller netforbindelsen.

## Fra beta.60


W78/W79/W80 · Robust adressehentning, enklere kortdata og læsbare fejlforklaringer.

Samlet distriktsgrænse → Fortsæt hentning: Prøv samme afbrudte hentning. Midlertidige GraphQL-netfejl genprøves op til to gange med synlig ventestatus. Pause kan afbryde ventetiden. Færdige udsnit genhentes ikke. Ved fortsat fejl skal kun fejlkoden NET-DNS/NET-RESET/NET-CONNECTION/NET-TLS eller HTTP-koden oplyses; send ikke nøgle, adresser eller private kort. Netårsagen i den konkrete HA-installation er endnu ikke bekræftet rettet.

Kortdata → Hent veje, bygninger, vandløb og jernbaner i det viste udsnit: Postnummerfeltet er væk ved almindelige kortdata og ved Datafordeler-adresser. Kun adresser fra den ældre kilde viser feltet. Kontrollér begge valg og sprogskift. Datafordeleren medtager alle postnumre i udsnittet.

Ved “Ændringen blev afvist” eller anden gemmestatus med en forklaring: Tryk på status øverst. Hele årsagen vises i et panel, som kan rulles og lukkes igen. Prøv på telefon stående/liggende. Ingen ændring sendes ved at åbne forklaringen.

## Fra beta.59

W23 · Idéer og feedback åbner nu ejerens Tally-formular uden konto eller e-mail. Billeder er valgfrie: højst tre JPG/JPEG/PNG/WebP-filer på højst 10 MB hver. Menuen oplyser, at indsendt tekst og billeder gemmes hos Tally. Intet fra installationen vedhæftes eller udfyldes automatisk.

Prøv menupunktet på telefon og computer. Kontrollér at formularen åbner i en ny fane, og at LTM bliver stående. Brug kun fiktive eksempler uden IB, rigtige distriktskort eller personoplysninger. Ejerens private vindue- og billedprøve er bekræftet; faktisk modtagelse af fiktiv tekst er kontrolleret i arbejdsrummet.

## Fra beta.58

W75 · Bedre touchbetjening på telefon og iPad/tablet.

Prøv stående og liggende: åbn menuen, søg efter et kort, åbn udlevering/aflevering, brug forkynderlisten og opgaver, og luk dialoger. Knapper og felter har større trykflader. Dialoger holder sig indenfor skærmens højde, og inputtekst på touchskærme er mindst 16 pixels.

Opsæt distrikter → Lav forslag: På smalle skærme står nummer, navn, område, besøg og advarsler samlet for hvert kort. Du skal kunne læse alle kontroloplysninger uden at rulle sidelæns. Kort oprettes stadig først efter OPRET KORT.

Automatiske touchprøver kører i Chromium og WebKit med fiktive data ved telefon/tablet i begge retninger. Egen iPhone/iPad-prøve med skærmtastatur og browserens værktøjslinjer er fortsat relevant; en simuleret browser er ikke en fysisk enhed.

## Fra beta.57

W76/W77 · Retter adressehentning i kortudsnit og langsomme kortforslag.

Kortdata → Hent vist udsnit → Hent også DAR-adresser i udsnittet: Med Datafordeler-forbindelse hentes alle postnumre direkte indenfor udsnittet, uafhængigt af OSM-vejnavne og den tidligere grænse på 45 vejnavne. Kontrollér meldingen om antal adresser og eventuelle manglende udsnit. Ved fejl bevares færdige dele; gentag samme udsnit. Brug Samlet distriktsgrænse til større hentninger, der skal kunne fortsættes efter genstart. Postnummerfeltet er kun nødvendigt ved den ældre adressekilde.

Opsæt distrikter → Lav forslag: beregningen kører på serveren med løbende statuskald. Store områder må tage over 30 sekunder uden alene at blive meldt som Wi-Fi-/VPN-fejl. Kontrollér og ret forslaget før OPRET KORT. Forladte svar må ikke erstatte nyere redigering. Dette ændrer ingen vejnetalgoritme.

Egen prøve: Hent det tidligere problemudsnit igen og sammenlign adresser midt i kortet. Prøv samme inddeling som gav forbindelsesfejl. Brug sikkerhedskopi; del ingen private kort, IB eller API-nøgler i fejlrapporter.

## Fra beta.56

W73 · Natlig adressekontrol på Home Assistant. Gem først den samlede distriktsgrænse, og forbind Datafordeleren. Gå til Opgaver → Automatisk adressekontrol → Indstil opgave. Vælg hyppighed (1–30 dage), tidspunkt og aktivér. Tiden følger serverens lokale tidszone; næste tidspunkt vises på opgaven. Slået fra som udgangspunkt.

Forsiden viser seneste gennemførte kontrol og antal nye, ændrede og foreslået fjernede adresser. Gennemgå adresseændringer, og godkend dem enkeltvis. Ingen lokale adresser eller kort ændres automatisk. Ved net-/kildefejl vises ventestatus og næste genforsøg; fremdriften bevares også ved genstart. Slå opgaven fra for at stoppe efter det aktuelle opslag. Manuelle hentninger, grænseændring, nulstilling og gendannelse venter, mens kontrollen arbejder eller venter på genprøve.

Egen HA-prøve: vælg en nært forestående tid, kontrollér resultat på forsiden, prøv midlertidigt netudfald/genstart, og kontrollér at genforsøg sker uden manuel start. Brug sikkerhedskopi og fiktive data. Rigtig Datafordeler-forbindelse og en faktisk natlig HA-kørsel er særskilte ejerprøver.

## Fra beta.55

W72 · Lille LTM-logo med “Local Territory Manager” under er tilføjet øverst til højre på det digitale Drive-kort.

Prøv med fiktive data: Åbn forhåndsvisningen af Drive-kortet, og kontrollér logo, tekst og læsbarhed. Eksisterende billeder opdateres via Opdater Google Drive-upload efter ny godkendelse. Samme fil/QR-link bevares. Opgradering alene ændrer ikke godkendte billeder.

## Fra beta.54

W70/W71 · Menighedsnavnet er fjernet fra topbaren. Det digitale Drive-kort har nu 50 % OSM-baggrund over hvidt, kraftige røde besøgsprikker og tydelige mørkerøde husnumre uden dæmpning.

For allerede uploadede billeder: Indstillinger → Google Drive → Opdater Google Drive-upload ved kortet. Kontrollér det nye billede, og godkend derefter publicering. Det opdaterer samme fil/QR-link. Opgradering alene erstatter ikke tidligere godkendte billeder. Prøv også topbaren på mobil og med et langt gemt menighedsnavn; indstillinger, sidepanel og rapporter bevarer navnet.

## Fra beta.53

W16, delopgave · Vandløb og jernbaner kan nu bruges som skel ved distriktsforslag. Hent først relevante udsnit igen under Kortdata → Hent veje, bygninger, vandløb og jernbaner i det viste udsnit. Ældre lokale kortdata indeholder ikke automatisk de nye forløb.

Prøv med fiktive data og sikkerhedskopi: Opsæt distrikter → Områder og numre → Lav forslag. Blå linjer viser vandløb, og grå stiplede linjer viser jernbaner. Kontrollér skel, besøgstal og passage; prøv Ret grænser på kortet. Kontrolteksten følger dansk/engelsk. Ændrede skel kræver ny forhåndsvisning. Kort oprettes først efter OPRET KORT.

Huller, navneskift, sløjfer og bro-/tunnelstykker gættes ikke. Første beregning bruger forløb i lag 0 uden bro-/tunnelmærkning; øvrige hentede stykker er kontekst. Mere komplekse vejnet og yderligere skeltyper står tilbage i W16. [Læs vejledningen om naturlige skel](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/develop/docs/NATURLIGE-SKEL.md). Main er stabil 1.11.1.
