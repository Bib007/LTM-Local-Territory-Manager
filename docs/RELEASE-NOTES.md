# LTM 1.12.3 · The familiar home dashboard is back

This patch corrects a regression in 1.12.2: profile users were shown a report-style summary instead of their familiar home dashboard.

- Users with the existing detailed overview permissions again see the original home dashboard: card-location and service-year coverage rings, shortcuts, metrics, monthly comparison and follow-ups.
- Summary-only accounts get the familiar home presentation using permitted aggregate totals. Private cards, names, notes and histories remain protected.
- The three-period report stays on the Reports page. Existing roles, guides, imports and saved language choices are preserved.

Update the existing installation while preserving its data directory. Keep a private data backup and, when profiles are enabled, a separate account backup. Original printed forms are unchanged.
