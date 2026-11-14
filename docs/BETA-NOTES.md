# LTM 1.12.19-beta.14 · Valgfri forkortet husnummerlinje på distriktskortet

På et geografisk distriktskort med DAR-adresser kan du under **Rediger forsidens vejlinjer** vælge visning **pr. vejlinje**:

- **Vis de valgte numre (standard):** Bevarer den præcise nuværende oversigt over adresser og huller mellem husnumre.
- **Vis fra første til sidste:** Viser kun laveste og højeste valgte husnummer, fx **3–67** i stedet for **3, 7, 9, 15, 25, 67**.

Det er **udelukkende en tekstindstilling på forsidens vejlinje**. Distriktsgrænse, DAR's faktiske adresse-ID'er, besøgstal, lejligheder, IB og tilknytninger til distriktskortet ændres ikke. Mellemliggende numre regnes **ikke** som valgte, selv om intervallet står på den trykte forside.

Indstillingen kan nulstilles, er uafhængig på hver vejlinje og gemmes på selve kortet med samme robuste kilde-ID-kobling som de eksisterende forsidetekster. Hvis DAR deler en linje i flere veje, flyttes valget ikke automatisk til en forkert vej. Print/PDF, S-12-forhåndsvisning, offentlig PNG, sikkerhedskopi og CSV-læsearkiv følger den valgte visning. Ved ændring markeres forsiden til genprint.

Kun én faktisk valgt adresse på en linje kan ikke omdannes til et første–sidste-interval; valget er da deaktiveret. Manuelle kort uden DAR-grundlag kan allerede få et manuelt nummerinterval i deres vejlinjetekst.

## English

The S-12 street-line editor now offers **Show selected house numbers** or **Show first–last range**, independently for each DAR-backed street line. A selected set such as 3, 7, 9, 15, 25 and 67 can appear as **3–67**. This is display-only: skipped numbers are not assigned to the territory. Actual address IDs, visit counts, boundaries, do-not-call entries and card history stay unchanged. The choice persists per street line through reloading, backups, print/PDF/PNG and readable exports, with existing stale-editor conflict protection. Stable remains unchanged.
