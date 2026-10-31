# Run LTM on your own computer or server · beta

This is the first W74 step, not a self-contained installer. Install Python 3.9+ with sqlite3, extract **LTM-v1.12.2-beta.78.zip** from [beta.77](https://github.com/Bib007/LTM-Local-Territory-Manager/releases/tag/v1.12.2-beta.78), then open `Start-LTM.cmd` (Windows), `Start-LTM.command` (Mac) or run `sh Start-LTM.sh` (Linux) in the **Distrikt-lokal** folder. The startup menu is currently Danish. No pip packages are downloaded.

Choose **1** for local use in your default browser, listening only on loopback. Stop it using the app's close action. Choose **2** for a private LAN/VPN server, enter a fixed private IPv4 address and port (beta defaults to 8788), and set a 12–1024 character password. Password entry is hidden and only a salted hash is saved. Existing credentials are reused. The server binds only the chosen interface, opens no browser and runs while its terminal stays open. Stop it with **Ctrl+C**. Use `--configure` to select a mode again; stop a running server before changing its address or port.

You configure the router, fixed address, firewall and VPN yourself. Do not forward the app to the public internet. Automatic service startup is not included. Linux has been tried on development Linux; Mac/Windows have automated platform checks, not a physical test on your computer.

Beta local, server and startup settings use separate **Distrikt-beta**, **Distrikt-beta-server**, and **Distrikt-beta-start** folders under the normal application-data parent. Stable **Distrikt** and HA data are unchanged. Use the app's approved backup/restore flow to move records intentionally. Connections and passwords are not transferred. Update by stopping the installation and extracting the new complete ZIP; data stays outside the program folder. The older `Start-Distrikt` files keep their original behavior and data location.

If macOS blocks the launcher, inspect its source, try opening it once, then approve that specific file in **System Settings → Privacy & Security → Open Anyway**. Do not disable system-wide protection. See [Apple's instructions](https://support.apple.com/en-gb/102445). You can also run the file with `bash` in Terminal.

W74 remains open: bundled Python/platform installers, a dedicated app window, and service startup are still missing. OCR/photo-import development remains paused. See the [Danish guide](SELF-HOSTING.md) for the full walkthrough.
