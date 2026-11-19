# Navigation during saves (beta.35)

The client queue owns immutable submitted payloads and the originating editor's
profile edit base. Navigation does not cancel that queue. Status remains pending
until the server receipt and the required state/geographic synchronization finish.
Closing/reloading the browser is still protected while writes are pending.

| Save path | Navigation behavior | Remaining gate |
| --- | --- | --- |
| Issue/return/retained completion, manual completion | The submitted form becomes nonmodal; navigation and Close remain available. | Duplicate submits coalesce; commands execute in queue order. The displayed records update only after acknowledgement. |
| Card create/edit and existing-card autosave | Same; leaving a valid existing-card editor captures the latest draft in the queue without waiting. | Invalid fields stay in the editor. Newer values are separate writes. A stale/uncertain write still stops dependent writes. |
| Publisher, area, note, visit, IB and saved-view forms | Same nonmodal behavior once the immutable command is queued. | Newer form signatures and dialog generations cannot be closed or marked saved by an older receipt. Profile bases remain independently owned. |
| Geographic assignment (addresses, street list and polygon) | Navigation is available after the unchanged-draft, DAR/conflict/ignore and neighbour-approval checks have passed and the command is queued. | Preview still waits and validates the exact draft. New edits still require the normal discard decision. A late response cannot clear a new geographic session/draft. |
| Individual/whole boundary save | The exact queued drawing may leave. | A boundary-only save does **not** cover a changed address selection: that selection retains its discard warning. Geographic saves remain mutually exclusive. |
| Settings and ordinary nonmodal row actions | Existing navigation remains available; late mutation refreshes preserve dirty/busy page forms and geographic drafts. | Same queue; no modal behavior is relaxed for other actions. |
| Merge/restructure, imports/setup, destructive/recovery, print approval, security/admin, sharing | Existing approval/session guards and modal workflows are retained. `confirmedWrite` joins the common queue and captures its original profile snapshot. | Their follow-up work depends on the reviewed preview, current permissions, exported file or confirmed result. They are not opted into background modal behavior. |
| Explicit Refresh and shutdown | Wait for the current queue before reading/reviewing or stopping. | Refresh also rejects navigation, new editors/drafts or new writes appearing while it waits/reads; it cannot clear an uncertain-write guard using a pre-write read. |

All `mutate` callers were examined, including the save/approval/import helpers in
workspace, geography, profiles, setup/import, IB, printing, sharing and numbering.
Direct transport/job polling and profile edit-base/read endpoints retain their
existing controls. No server, runtime, HA, map-tool layout, interval formatting,
version or release file changes are part of this work.

Tests use temporary fictional data only. `test_w124_save_queue.cjs` covers queue
progress/coalescing, owned and chained bases, blocked dependent commands, and
newer drafts. `check_save_navigation_browser.cjs` uses the real temporary server
with held receipts, clickable navigation, returns, newest card autosaves, settings
and geographic drafts, independently conflicting profile edits, rejection and
lost/malformed receipts, with shared login and enabled profiles. The broad suite
and this browser proof run in PR CI.
