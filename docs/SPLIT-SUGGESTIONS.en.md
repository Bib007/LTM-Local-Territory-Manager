[Dansk](SPLIT-SUGGESTIONS.md)

# Manual split suggestions and address transfers

Available from LTM 1.12.4. Open **Settings → Congregation and carry folder → Split suggestions**, or the optional setup-checklist item. Choose an approximate visit target and a box-only filter. These preferences are remembered in this browser without storing account or territory data in browser preferences.

Unknown or invalid visit totals are excluded. Visit counts remain estimates, not records of actual house-to-house visits. Exact, unique geographic membership and matching known counts are required for proposed address units. Whole units stay together; no addresses or visit totals are guessed. Receiving alternatives match area, type, street and postcode. This is a numerical alternative, not verified geographic continuity. Review alternatives separately and recalculate after each change.

Both source and receiving cards must be returned and in the box before a transfer can be applied. The box filter hides issued and carry-folder cards. With the filter off, they can be reviewed, but cannot be changed by this workflow. Up to 100 oversized cards and three receiving alternatives per source are shown.

## Split into a new card

**Review split into a new card** opens the existing manual split form with the proposed address boxes selected. Enter a new card number, review the server preview and type the confirmation before anything changes. History stays on the original card. The new card gets no invented completion and needs boundary review and reprinting.

## Move to an existing card

**Move addresses to this card** offers two explicit workflows:

- **Use the latest known date for scheduling:** move the selected units and coupled do-not-call records to the receiver. Its latest known date becomes a scheduling reference for card-age planning. Its actual completion date, completion events and S-13 history are unchanged. The card detail shows the scheduling reference separately.
- **Create an interim card first:** choose a unique interim number. The selected units move to that card while the intended receiver stays unchanged. The interim card can be printed and issued under its own number. Its name and task explain the intended receiver and later reprint. It starts without a completion event.

Every operation requires a current server preview and typed approval. A changed address, card, loan, relevant note or do-not-call record invalidates the earlier confirmation. Unlinked do-not-call text must be reconciled before moving units; it is never guessed or discarded. Ordinary card notes and task responsibility stay with their original card. A failure rolls the whole move back.

## Finalize an interim card

Return the interim card and put both cards in the box. Open **Split suggestions → Interim transfers → Finalize interim transfer**, review the preview and confirm. The receiver then gains the interim units. The interim card is archived with its loan and completion history intact. No completion is copied to the receiving card.

Review the resulting boundaries and print both changed sides. Print the final receiver using its own number; the interim card's task and pending-transfer notice explain this step. Source and receiver tasks remain until explicitly completed. A deleted, changed or issued receiver must be resolved before finalization.

## Dates and records

The scheduling reference uses the latest known source/receiver date, including an actual interim completion when present. It affects card-age planning, not recorded service-year completions or original S-13 output. A later unrelated change to address membership invalidates the inherited reference. Original records and printed forms retain their language. Automatic territory division is not enabled by this workflow.


## Congregation threshold and dismissed proposals (development feature)

The **Territory cards** page shows a live count of cards exceeding the congregation's separate **Settings → Congregation and carry folder → Maximum visits per card for split suggestions** value (1–1,000). This advisory limit does not modify the target used for automatic card creation or block assignments. Existing assignments and completed records are never altered by generating a suggestion.

An administrator may **Dismiss suggestion** with a 1–300-character reason and **Restore suggestion** later. A dismissal is tied to card identity, current estimated visits, address membership, and the threshold; changing any of these makes a changed proposal visible again. Non-administrators do not receive the free-text reason. New mutations are `split.suggestion.ignore` and `split.suggestion.restore`, authorized by `settings.manage`. Existing local SQLite settings and backup retain them without schema changes.

Moves to an existing card and splits to a new card still go through explicit preview/confirmation, preserving loan-history requirements. Same area/type/street name does not by itself prove geographic continuity: an operator must verify the boundaries before applying. Combining selected visits from two source cards into a third card is **not implemented** by this PR. Synthetic tests cover changed limits, stale dismissals, restore and existing split planning; physical platform checks remain outstanding.
