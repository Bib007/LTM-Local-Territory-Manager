# LTM 1.13.0-beta.3

Denne Beta indeholder forsidefejlrettelserne fra Stable 1.12.40 samt de eksisterende Beta-forbedringer med **brugsstatistik** (beta.1) og **KTM-rapporten** (beta.2). Beta og Stable har fortsat separate data, porte og logins.

## Forsiden

- **Anslåede besøg:** Et korts aktuelle, kendte besøgstal minus kortets IB tæller for **hver** gennemgang. Eksempel: 35 besøg, 2 IB og to gennemgange giver 66 anslåede besøg.
- Gennemgange importeret med ukendt antal kan nu medregnes, hvis kortet i dag har et kendt antal. Ukendte tal uden brugbart grundlag forbliver udeladt. De gemte historikposter ændres ikke.
- **Sammenligning med sidste år:** Grafen viser også sidste års gennemgange for de måneder, der ikke er begyndt endnu i det aktuelle tjenesteår. Indeværende måned afgrænses til dags dato og samme dato sidste år.
- Nul og manglende registreringer må ikke forveksles. Tabellen viser de præcise perioder, og skønnet er ikke faktiske husbesøg.

## Prøv selv

1. Kontrollér **1.13.0-beta.3** på den separate Beta-installation (port 8788).
2. Gennemgå et prøvekort med 35 besøg, registrér 2 IB, og kontrollér at forsidens skøn stiger med 33 for hver gennemgang.
3. Kontrollér, at gentagne gennemgange tæller igen, og at arkiverede kort kun bidrager til besøgsestimatet, når der er kendte tal.
4. Kontrollér 12 måneders sammenligning mod sidste tjenesteår, også for fremtidige måneder i det aktuelle år, samt tabellen under grafen.
5. Kontrollér fortsat brugsstatistikken under Indstillinger og den udvidede KTM-rapport med dækning/mangelliste fra tidligere betaer.

## English

Beta 1.13.0-beta.3 carries the dashboard corrections from Stable 1.12.40 while preserving usage statistics and the updated KTM reporting. Estimated visits use each territory's current known visit count less linked do-not-call entries for every completion, including formerly unknown historic completions when a current count exists. Previous-year columns remain visible for all twelve months, independently of current-year activity. No stored records are rewritten.
