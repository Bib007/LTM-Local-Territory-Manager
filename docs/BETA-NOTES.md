# LTM 1.12.19-beta.35

- Historikimport opretter ukendte forkyndere i gruppen "Ikke i en tjenestegruppe".
- To forkyndere kan sammenlægges under et valgfrit navn fra forkynderens side. Udleveringer og historik bevares, og tidligere navne genkendes ved senere import.
- Tjenestegruppe, gruppefunktion og pionerstatus bevares fra den forkynder, sammenlægningen åbnes fra. Sammenlægningen kan fortrydes som seneste handling.

- Navigation kan fortsætte under indlevering og andre almindelige gemninger samt kortgemning efter de nødvendige kontroller. Gemmekøen beskytter nyere kladder og profilkonflikter; status er først færdig, når gemning og opdatering er bekræftet.
- Redigeringsværktøjerne står lige under både kortets grænse og den samlede grænse med tekst, ikoner og trykvenlige knapper.
- Intervalvisning udelader (lige)/(ulige), når samme vej på kortet har begge slags husnumre. Rene lige eller ulige veje beholder mærket.
- Home Assistant kan registrere vedvarende svarproblemer uafhængigt af statusafleveringen. Korte interne statuslæsninger udløser ikke fejlalarm. Genimportér det opdaterede driftsblueprint for den nye beskedtype; eksisterende automationer ændres ikke automatisk.

## English

- History import creates unknown publishers in the group "Ikke i en tjenestegruppe" (Not in a service group).
- Merge two publishers under a chosen name from a publisher profile. Assignments and history are preserved, and previous names are recognised in later imports.
- The service group, group role and pioneer status are retained from the publisher whose profile opens the merge. The latest merge can be undone.

- Navigation can continue during returns and ordinary saves, and during geographic saves after the required checks. The ordered queue protects newer drafts and profile conflicts; completion is shown only after the write and synchronization are confirmed.
- Editing tools sit directly below both card and whole-territory boundary maps, with text, icons and touch-friendly buttons.
- Range display omits odd/even labels when the same street on a card contains both parities. Pure odd or even streets retain their label.
- Home Assistant can detect persistent response problems independently of status delivery. Short internal status reads do not cause a false alarm. Reimport the updated runtime blueprint for the new notification type; existing automations are not changed automatically.

## Afprøvning

- Importér historik med et opdigtet nyt navn. Kontrollér den nye tjenestegruppe.
- Åbn en forkynder, vælg Sammenlæg forkyndere, vælg dubletten og skriv det ønskede slutnavn. Kontrollér begge navne, før du gemmer.
- Kontrollér udlån og historik efter sammenlægning. Prøv en senere import med et tidligere navn og den eksisterende Fortryd-handling.

- Gem en indlevering, og skift straks visning. Kontrollér gemmestatus og historik efter svaret. Åbn en ny kladde under en langsom gemning, og kontrollér, at den bliver bevaret.
- Afprøv kortværktøjerne på mobil og desktop samt et DAR-forslag med særskilt godkendelse af nabogrænser.
- Kontrollér intervalvisning for en blandet vej og en ren lige/ulige vej.
- HA-diagnostik dækker serverens svar, ikke alle browser- eller LAN/VPN-fejl. Det opdaterede blueprint skal genimporteres og automationerne genindlæses efter opdatering.
