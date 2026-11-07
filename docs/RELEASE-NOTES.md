# LTM 1.12.18 · Responsive print approvals in Home Assistant

Fix a lock conflict between Home Assistant runtime-status sampling and the overview returned after saving. It could leave a print approval showing Saving, time out, and then prevent page reloads until the app was restarted.

Batch approval now reads its validation data once, including for 380 cards / 760 sides. Single and batch approval buttons are disabled while saving and rapid repeat clicks are ignored. Changed print content still requires a new print.

The accepted red dots, house numbers, two-page Drive PDF and canonical print front from 1.12.17 are preserved. After updating, reload the browser so it uses the updated approval controls. If the previous app is already stuck, restart it once in Home Assistant as part of the update.

Mac-server distribution remains deferred under AFK-002.
