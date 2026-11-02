# LTM 1.12.4 · Task responsibility and safe manual redistribution

This release completes optional task responsibility and the manual split/transfer workflow, while retaining the familiar home dashboard from 1.12.3.

- Assign a responsible local account to a task or linked follow-up. Readers recognize their own tasks without receiving the account directory. Assignment grants no permissions and sends no notification.
- Review split suggestions using a visit target and a box-only filter. Unknown totals, ambiguous membership and issued cards are excluded from actionable suggestions.
- Move selected address units to an existing card after a server preview and typed approval. Coupled do-not-call records move atomically; original notes, loans and completion events stay with their original cards.
- Choose the latest known date as a scheduling reference, or issue an interim card first. Return the interim card, explicitly finalize its transfer and reprint the receiving card with its own number. Interim history is retained on the archived card.
- English and Danish interface labels, task instructions, maintenance controls and readable conflict fields are covered by the interface catalog check. Original S-12/S-13 forms, stored user content and source diagnostics retain their language.

The scheduling reference affects card-age planning only. It never creates a completion event or rewrites S-13 history. Planning alternatives are independent; review geographic continuity and both print sides before use. Automatic territory division remains paused.

Update the existing stable installation while preserving its data directory. Keep a private data backup and, when profiles are enabled, a separate account backup. The beta installation uses separate data and remains separate from stable.
