# Service groups and local list import

[Dansk](TJENESTEGRUPPER.md)

Open **Publishers** to add or edit a service group, group function and pioneer flag. Known group names are suggested. Filter the publisher overview by group and see the same information in each publisher's card/history view.

Each group may have one overseer and one assistant. Pioneer is a separate flag and may be combined with either function. These records do not create accounts or grant app permissions. The administrator controls user accounts and permissions separately. Publishers may already hold multiple different cards; each card still has only one active assignment.

Choose **Import service group list** and download the blank Excel or CSV template. Keep the headings **navn**, **tjenestegruppe**, **gruppefunktion**, **pioner**. The Excel input sheet is **Forkyndere**. Use one row per publisher, with values instead of formulas.

The name is required. Group is optional. Function values are **Gruppetilsynsmand**, **Assistent**, or blank. Pioneer accepts **Ja/Nej** (also Yes/No). Existing names must match uniquely without case or repeated-space differences. Ambiguous names and duplicate rows must be corrected first.

Review new, changed and unchanged rows, especially before/after values for existing names. A present blank cell clears a value; an omitted column preserves it. Type **IMPORTÉR GRUPPER** to approve the whole file. No publisher is saved just by reading or reviewing the file. A valid import may swap group functions atomically.

Limits: 2 MB and 5,000 rows. XLSX and CSV with commas or semicolons are supported. Processing stays on the local server; no OCR or external name lookup is used. Card assignments, completions, identities and unlisted publishers are preserved.

Ordinary concurrent edits retain their observed basis and conflicting values. A publisher-list change after preview requires a fresh import review; unrelated card edits do not block the import. Group fields are included in private data backups and readable publisher CSV exports. Account backup remains separate. Keep real name lists private and use fictional examples in public feedback.
