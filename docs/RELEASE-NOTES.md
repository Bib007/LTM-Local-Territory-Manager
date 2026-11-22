# LTM 1.12.40

Afgrænset stable-opdatering af forsiden: korrekte anslåede besøg pr. gennemgang og et fuldt sammenligningsår i søjlediagrammet.

## Beregning af besøg

- For hver registreret gennemgang bruges kortets **aktuelle kendte besøgstal minus antallet af IB på kortet**. Et kort med 35 besøg og 2 IB bidrager med 33 pr. gennemgang, eller 66 ved to gennemgange.
- Tidligere historikposter med ukendt besøgstal kan dermed indgå, når det tilknyttede kort nu har kendt antal. Hvis kortets antal er ukendt, bruges kun et eventuelt kendt historisk tal; ellers udelades posten fra skønnet.
- Skønnet er ikke en optælling af faktiske husbesøg. Ændringer i et korts aktuelle antal eller IB kan ændre skønnet, men **gennemgangshistorikken omskrives ikke**.

## Sammenligning med tidligere tjenesteår

- Hele foregående tjenesteårs registreringer vises, også for måneder, som endnu ikke er begyndt i indeværende tjenesteår.
- Aktuel måned afgrænses fortsat til dags dato og samme dato sidste år. Alle måneders præcise datointervaller findes i tabellen.
- Ingen andre data eller uafsluttede Beta-funktioner følger med denne Stable-rettelse.

## Udgivelse

Udgivelse kræver grønne PR- og Stable-workflowkontroller. Vælg det ønskede spor under **Stable release tracks** på `main`. MacOS-server kræver fortsat separat fysisk godkendelse.

## English

LTM 1.12.40 fixes the dashboard's estimated visits and previous-year comparison. Each completion uses the card's current known visit total less its registered do-not-call entries. Historical records are not modified; estimates can change as a card's current counts change. All twelve months of the previous service year are displayed even when the corresponding current months have not begun. The current month's comparison remains limited to the same calendar date last year. No unfinished Beta work is included.
