# Import existing territory cards

[Dansk](KORTIMPORT.md)

Import card numbers, manual street lines or exact addresses. Open the first-use guide or **Settings → Import → Open card import**. Maps are optional.

1. Download the Excel template. Fill in the **Distriktskort** sheet; **Vejledning** contains Danish instructions and fictional examples. Keep the Danish column headings.
2. Use one row per address or manual street line. A card number alone is also accepted; leave every address field blank in that case. Repeat the card number. Area, card name and territory type can be given on the first row for each card; repeated values must agree.
3. Save as `.xlsx`, or use CSV with commas or semicolons. Convert old `.xls` files to `.xlsx`. Paste values instead of formulas.
4. Choose the file and review all cards, areas, addresses and visit counts. Fix every error and duplicate, then choose the file again.
5. Type **IMPORTÉR KORT** and approve. All cards are created together in the storage box. Cards with street lines are flagged for print review; register-only cards do not require printing. Any error blocks the whole import.

**Kortnummer** (card number) is required. Enter both **Vejnavn** (road) and **Husnummer** (number or literal range such as 1–19), or leave all address fields blank. **Postnummer** is four digits for an exact address and optional for manual lines. Other columns are **Område**, **Kortnavn**, **Distriktstype**, **Etage**, **Dør**, **Adressetype** and **Besøg**. Visit counts must be integers from 1 to 10,000. A blank count means unknown for a manual line and defaults to one for an exact address. Ranges are never expanded or counted automatically. Blank territory type becomes Ukendt and blank address type becomes Hus. Keep identifiers as text to preserve leading zeros.

Limits: 2 MB, 10,000 lines, 500 cards and 300 street lines or addresses per card. No online address service receives the file. Select geographic addresses and boundaries later, one card at a time. The card number, assignments, do-not-call entries and history remain. The street list then follows the selected addresses and needs another print review. Existing cards and history are never overwritten; deleted numbers reserved for recovery remain unavailable.

Exact apartments are included in private backups and can be matched by local do-not-call import. Editing a road list keeps exact address selections for retained rows. Card import creates no do-not-call entries, and those entries do not reduce visit totals. Keep real files private; use fictional examples in bug reports.

Unknown counts remain visible on cards, printouts and current totals. They may be filled in through normal card editing. Completions with unknown counts still count as completions but are excluded from visit estimates. Later card edits do not change those historical records.

## Multiple files

Choose up to 20 Excel/CSV files, up to 2 MB each and 20 MB in total. Approve each file separately, then choose **Review next file**. You can skip a file. Previously approved files remain saved after closing or an error. The queue currently supports card files, not images or do-not-call files.
