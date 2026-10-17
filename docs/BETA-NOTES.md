# LTM 1.12.0-beta.8

## Nyt siden beta.7

En gemt Datafordeler-nøgle bruges nu til **vej-, postnummer- og grænsehentning via DAR GraphQL**. Adresse-ID'er, husnumre og etage/dør bevares. Komplette sider og lokale sammenkoblinger kontrolleres før en vej/et udsnit gemmes. Grupperede lighedsopslag giver færre netkald.

Pause og genstart bevarer afsluttede dele og samme tidspunkt. Netfejl stopper ved den aktuelle del. Checkpoints har kilde og skemafingeraftryk, så gamle REST-resultater ikke blandes med GraphQL. Ved skift af kilde eller skema vælges en ny opdatering; færdige lokale adresser bevares. Flere officielle vej-ID'er med samme navn og postnummer behandles samlet.

Uden nøgle bruges den hidtidige kilde. Adresseforslag i søgefeltet kommer stadig fra den særskilte Adressevælger. Nøglen indtastes kun i den lokale app og følger ikke med portable sikkerhedskopier. Præcise distriktsgrænser, kort, forkyndere og IB uploades ikke til Datafordeleren.

## Prøv især

1. Opdater **Distrikt Beta**, og tag først privat backup af dine betadata. Stabil 1.11.1 fortsætter separat.
2. Gem eller kontrollér egen nøgle under Kortdata. Status skal nu oplyse, at nye adressehentninger bruger DAR GraphQL.
3. Hent først en enkelt offentlig vej. Kontrollér bogstaver, etage/dør og adresseantal. Prøv derefter et lille postnummer eller en lille samlet grænse.
4. Sæt en større hentning på pause, genstart appen, og fortsæt. Færdige dele skal springes over. Ved netfejl kan du fortsætte senere.
5. Hvis du har en gammel REST-hentning, skal fortsættelse med GraphQL give en tydelig besked. Vælg en ny opdatering; eksisterende adresser skal bevares og ændringer gennemgås som hidtil.

Programkontrollen bruger fiktive GraphQL-svar og midlertidige databaser. Levende Datafordeler med din egen nøgle og visningen i din HA/browser er særskilte ejerprøver. En grøn forbindelseskontrol er ikke en påstand om, at dit prøveområde allerede er hentet og sammenlignet.

Den ekstra KTM-opfølgningsliste er fortsat fjernet. Den faste køreplan står på 20 %.
