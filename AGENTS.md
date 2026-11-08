# LTM release policy

Develop and test future changes on `develop` / Beta first. Stable (`main`) is the tested baseline; do not use Stable as the normal test channel.

The owner authorized the consolidated 1.12.19 Stable and matching 1.12.19-beta.1 release on 8 November 2026 and confirmed physical Mac/Windows installation and data preservation. Keep Stable/Beta folders, login cookies and native installer identities separate.

Keep generated release assets immutable. Publish from the exact checked commit only after its required checks pass. Mac-server remains gated on its separate physical Apple Silicon LAN/VPN/restart test; desktop approval does not satisfy that test.

Never read or modify a real user's territory data to run tests; use temporary fictional fixtures.
