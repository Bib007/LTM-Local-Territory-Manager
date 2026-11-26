# Dual territory identifiers — feature branch contract

Status: feature under review, **not** merged into `develop` or released in Stable.

## Invariants and migration

- `cards.id` remains the immutable UUID-like technical key. Existing relations (`card_id`) in loans, completion history, IB, addresses, maps, QR/share and exports are untouched.
- `cards.number` is the legacy **public printed territory number**, including original S-12/S-13, card front/back and public map labels. Previous imports/backup files and older installations can still use it.
- `cards.internal_number` is an **optional** uppercase A–Z/0–9 code (up to 30 characters), such as `T0025`, `M0101`, `D0201`. It is unique case-insensitively across live and recoverable/deleted cards. Leading zeros are retained. Legacy cards read as `internal_number: ""` until explicitly populated.
- Existing SQLite `records` JSON fields and `PRAGMA user_version=1` are unchanged. No destructive schema migration and no start-up renumbering. Old backup archives import normally. App-version rollback preserves unknown JSON keys where code updates records with `dict(old)`; always take a normal full backup before deploying to a real installation.
- Area settings gain `numbering: {prefix,start,end,width}` only after explicit configuration. Range endpoints inclusive. The configuration alone never changes cards.
- CSV import still accepts previous headers. New optional `internt_nummer` column is validated; omit it to keep codes unset. The readable `kort.csv` export appends `internt_nummer`, leaving all old columns and indexes intact. Exports keep `kort_id` stable and print labels public.
- Existing browser/desktop clients should refresh after deploying this change. Old clients can save public card numbers while preserving unknown internal fields; coordinate upgrades for concurrent administrators.

## Numbering operations

The new Distrikter controls distinguish public and internal codes. `card.save` can edit a single internal code with collision validation, while bulk operations require two explicit phases:

1. Configure a per-area prefix/range without modifying cards (`area.numbering.preview` + `area.numbering.save`, confirmation `GEM INTERVAL`).
2. Preview a single card, one area, or all cards, including archived cards (`card.numbering.preview`, `scope: card|area|all`, `mode: swap|assign`). `swap` exchanges the two label values on each selected card; `assign` allocates unused codes only to blank internal numbers from their area's configured range.
3. Review complete final-state namespace conflicts, including numbers reserved by deleted/recoverable cards. Confirm with exact `BYT NUMRE` or `TILDEL NUMRE`, then call `card.numbering.apply` with the preview's opaque `expected` digest. A changed card, area, newly imported card, deletion, restore, or concurrent operation invalidates the preview.
4. The server writes all card edits plus a **durable, local before/after recovery record** (`entity: territory-numbering-batch` in settings records) under a single `BEGIN IMMEDIATE` transaction. If any write fails, all changes roll back. Public-number changes set *both* print revisions; users must review physical cards/QR/publication assets for reprinting.
5. `card.numbering.undo.preview` / `card.numbering.undo` require exact `FORTRYD NUMRE`. Undo is allowed only if every affected card still carries the post-change identifiers and restoring all original values would be collision-free. Other changes to cards are preserved. Records survive restart and regular database backup. Undo is never automatic.

No global renumbering, issue, merge, or Stable release is triggered by range configuration or opening previews.

## API, authorization and concurrency dependencies

- `Store.guarded_mutate` is the transaction boundary; `territory_numbers.TerritoryNumbering` is mixed into `Store` and handles the new domain actions.
- Profile permissions: `cards.view + cards.edit` for preview/apply/undo, `settings.manage` for area range configuration. `profile_policy.CARD_FIELDS` and profile edit snapshot/reconciliation expose `internal_number`; area snapshots expose `numbering`.
- Shared files touched: `store.py`, `profile_policy.py`, `profile_edits.py`, `app.js`, `index.html`, `card_import.py`, `readable_export.py`. Coordinate merges especially with other history, dashboard, print, address import and mobile UI PRs.
- New files: `territory_numbers.py`, `territory-numbering-ui.js`, `test_territory_numbers.py`. The specialized UI script avoids editing unrelated `admin.js` controls.
- The existing `number` property is deliberately not renamed in HTTP or print APIs; external consumers that inspect the public number remain compatible. Consumers can optionally read `internal_number`. Existing QR links use the technical `card_id`.
- There is no new external storage service; number history is in the existing local settings database. The audit records contain card labels but no personal information.

## Verification and release gate

All test fixtures use fictional areas, publishers and cards. New unit tests cover legacy records, natural sorting, area ranges, missing codes, swaps, namespace collision, stale previews, concurrent writes, durable undo after restart, print-revision invalidation, retained loan relationships, CSV technical IDs and transaction rollback. The existing CI suite is the release gate for S-12/S-13 templates, PDF/A4 layouts, QR, offline browser, language, map render and profile-related regression coverage.

**Not a substitute for manual tests:** verify physical printed cards, real-device responsive UI and a full backup/restore on a copy of an existing installation before using the feature on production. Do not import live territory data as test fixtures.

### Parallel development / merge sequence

1. Keep this branch independent from `develop` and any other feature work. Avoid rewriting, rebasing or force-pushing other people's branches.
2. Update this branch against current `develop`; resolve overlapping schema/API/UI edits, then rerun full CI.
3. Obtain review and passing CI before merging this PR into `develop`.
4. Integrate the other approved PRs on `develop`, regression-test the combined changes with fictional datasets, and only then plan one separately approved Stable release.
