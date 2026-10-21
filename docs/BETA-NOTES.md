# LTM 1.12.0-beta.56

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
