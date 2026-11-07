# LTM 1.12.18 · Responsive print approvals in Home Assistant

Fix a lock conflict between Home Assistant runtime-status sampling and the overview returned after saving. It could leave a print approval showing Saving, time out, and then prevent page reloads until the app was restarted.

Batch approval now reads its validation data once, including for 380 cards / 760 sides. Single and batch approval buttons are disabled while saving and rapid repeat clicks are ignored. Changed print content still requires a new print.

Assignment deletion checks the selected card's actual loan history instead of every change anywhere in the database. Unrelated background saves no longer force a reload; genuine changes to the card's history still require review.

Completed address checks with no pending changes are hidden from the dashboard and have no empty review button. The schedule remains available in settings.

Crowded Drive maps keep every red dot and omit only the house numbers that have no clear position, so an approved PDF/QR map can still be produced. The two-page Drive PDF and canonical print front from 1.12.17 are preserved. After updating, reload the browser so it uses the updated approval controls. If the previous app is already stuck, restart it once in Home Assistant as part of the update.

Mac-server distribution remains deferred under AFK-002.
