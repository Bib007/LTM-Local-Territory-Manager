# Import existing territory cards

[Dansk](KORTIMPORT.md)

Use this when addresses are already divided into numbered cards and named areas. Open the first-use guide or **Settings → Advanced → Import existing territory cards**. Maps are optional.

1. Download the Excel template. Fill in the **Distriktskort** sheet; **Vejledning** contains Danish instructions and fictional examples. Keep the Danish column headings.
2. Use one row per exact address or apartment. Repeat the card number. Area, card name and territory type can be given on the first row for each card; repeated values must agree.
3. Save as `.xlsx`, or use CSV with commas or semicolons. Convert old `.xls` files to `.xlsx`. Paste values instead of formulas.
4. Choose the file and review all cards, areas, addresses and visit counts. Fix every error and duplicate, then choose the file again.
5. Type **IMPORTÉR KORT** and approve. All cards are created together in the storage box and flagged for print review. Any error blocks the whole import.

Required columns are **Kortnummer** (card number), **Vejnavn** (road), **Husnummer** (one house number, e.g. 12A) and **Postnummer** (four digits). Optional columns are **Område** (area), **Kortnavn** (card name), **Distriktstype** (By/Land/Ukendt), **Etage** (floor), **Dør** (door), **Adressetype** (template type) and **Besøg** (integer visits, default 1). Blank territory type becomes Ukendt and blank address type becomes Hus. Keep identifiers as text to preserve leading zeros. Expand house-number ranges into individual addresses before importing.

Limits: 2 MB, 10,000 addresses, 500 cards and 300 addresses per card. No online address service receives the file. Add coordinates and boundaries later. Existing cards and history are never overwritten; deleted numbers reserved for recovery remain unavailable.

Exact apartments are included in private backups and can be matched by local do-not-call import. Editing a road list keeps exact address selections for retained rows. Card import creates no do-not-call entries, and those entries do not reduce visit totals. Keep real files private; use fictional examples in bug reports.
