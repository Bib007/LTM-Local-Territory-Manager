# LTM 1.12.6 · Manual Excel fronts and backs, clearer street ranges

This release addresses the priority −1 Drive request.

- Import a card front and a do-not-call back from your own Excel/CSV files without using DAR. Choose columns, use the same card number and review each preview before confirming. Manual IB linking is now the default in the import screen. Both ordinary printed sides work with manual street lines.
- Leave a manual IB entry unlinked, or explicitly link it to an address belonging to that card later. Its record ID and date wording are retained. Changing the linking policy invalidates an existing preview.
- DAR suggestions understand `hele vejen` / `whole street`, including all apartment units. `(kun ulige)` and `(kun lige)` retain their odd/even restriction. Street-side combinations such as `23-25 & 24-26` and `23-29 & 24-26` are interpreted separately, without filling excluded even numbers.

An ordinary unqualified single number range retains its existing meaning. Unknown restrictions are rejected rather than ignored. Review the proposed address list and boundary before saving; the planner never changes a card simply by downloading or previewing.

The familiar Home, roles, assignments, history, original S-12/S-13 forms and separate stable/beta data remain. Update the stable program while preserving its data directory and private backups.
