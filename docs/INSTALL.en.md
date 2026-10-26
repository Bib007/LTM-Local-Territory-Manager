# Installation and updates / installation og opdatering

## New beta startup guide for local/server use

See [Self-hosting](SELF-HOSTING.en.md) for the shared Windows/Mac/Linux launcher, separate local/server data and private server login. Python is still required; this is the first W74 step.

[Dansk](INSTALL.md)

## Mac

Install Python 3.9+ from [python.org](https://www.python.org/downloads/macos/). Extract the full release ZIP to a normal local folder, then open `Distrikt-lokal/Start-Distrikt.command`. From source, the folder is `distrikt` instead.

If macOS blocks the launcher, inspect the file and open it through Finder's Open action, or run `bash` followed by the dragged launcher path in Terminal. Do not disable system-wide security. The launcher opens your default browser; `Stop-Distrikt.command` stops this app.

Private data: `~/Library/Application Support/Distrikt`. Keep this existing location when updating; changing the product title does not move your databases.

## Windows

Install Python 3.9+ from [python.org](https://www.python.org/downloads/windows/) with its launcher or PATH option. Extract the ZIP, then open `Distrikt-lokal/Start-Distrikt.cmd`. Use `Stop-Distrikt.cmd` to stop it. No pip packages or Docker required.

Private data: `%LOCALAPPDATA%\Distrikt` in the usual configuration. Physical Windows installation remains to be verified; automated tests are not a substitute for a hardware test.

## Home Assistant OS

The app binds its own port, normally **8787**, with its own password. Access is intended for your LAN and router VPN, not public port forwarding or Nabu Casa/Ingress.

### Use your phone away from home / brug mobilen udefra

The benefit of the HA installation is that it can keep running at home while you access the same up-to-date data from your phone, iPad or computer.

1. Set up a VPN server on **your own router** (for example your existing UniFi VPN), and install the corresponding VPN profile/app on the device.
2. Allow that VPN connection to reach the private LAN/VLAN containing the HA machine and TCP port 8787. A VPN that only changes internet location is not a connection to your home network.
3. Away from home, turn on that VPN and open the **same private IP address** used at home: `http://YOUR_PRIVATE_IP:8787`.
4. Sign in using LTM's own password. Use the mobile interface with the same records as at home; do not import a second database onto the phone.

På dansk: Slå router-VPN'en til på telefonen, og åbn appens lokale adresse. Du kan nu finde distrikter og arbejde i appen på farten. Appen er fortsat på dit private netværk, og Nabu Casa bruges ikke. VPN og netværksregler konfigureres på routeren; appen opretter ikke selv VPN'en.

If home Wi-Fi works but VPN does not, check the VPN's LAN routes/firewall and use the fixed private IP rather than assuming `.local` names work across the tunnel. Do not solve this by forwarding port 8787 to the public internet.

### Existing local app: safe update

1. In the running app, download a private backup from **Indstillinger → Backup og gendannelse**. Keep it outside shared cloud folders.
2. Stop **only Distrikt** in Home Assistant. Do not uninstall it.
3. Extract the new release ZIP locally on your Mac. Mount HA's `local_apps` Samba share in Finder.
4. In Terminal, type `bash ` and drag `Opdater-Home-Assistant-Mac.command` into the same line. Find it in the ZIP’s `scripts` folder, or in the main folder in version 1.12.1 and earlier. Press Enter.
5. Choose the mounted **local_apps** folder, not the app's nested folder. The helper checks source files, copies with `rsync --inplace`, verifies copied bytes and updates `config.yaml` last. This avoids Samba's `._*` temporary-file restriction. It does not delete extra files or copy databases.
6. Wait for **FÆRDIG**. On **STOP**, leave the app stopped and resolve the reported copy error before updating.
7. In HA's app store, select **⋮ → Kontroller for opdateringer**, open the existing Distrikt app, choose **Opdater**, then **Start**.
8. Keep the current options: `access_host` is your HA machine's fixed private IP, without `http://`, port or slash; `password` stays your existing app password.
9. Open `http://YOUR_PRIVATE_IP:8787` and refresh the browser. Confirm your cards and assignments remain.

Regular updates do **not** require importing a backup. Never replace or remove `/data/distrikt`.

### New local app

Copy the complete `Home-Assistant/distrikt` release folder into the mounted `local_apps` share using the helper. Refresh the HA app store, install Distrikt, set the fixed private `access_host` and a unique password of at least 12 characters, then start it. Use `http://YOUR_PRIVATE_IP:8787`.

### Repository installation

Add `https://github.com/Bib007/LTM-Local-Territory-Manager` in HA **Settings → Apps / Add-ons → Store → ⋮ → Repositories**, then choose **Distrikt → Install**. HA fetches the program itself. Set the fixed private `access_host`, the app's own password of at least 12 characters and port 8787, then start it. Future updates are installed through HA without Samba file copying. The default branch is stable; do not use `#develop` as a normal update source.

 Do not switch an existing local installation blindly: HA identifies repository-installed apps differently and may give the new instance a separate data folder. Export from the old instance, stop it, install the new one, import privately, reconnect Google and verify data before retiring the old instance. Never run competing copies as the authoritative database.

## Backups and moving between platforms

Use the application's private backup export, then import on the destination after reviewing record counts. Import replaces rather than merges. Passwords, Google credentials and login sessions do not travel in the backup. Existing public files require the documented account/republication checks.

**HA app data is excluded from HA backups**, including local HA backups. The app's own private backup is essential before updates, movement or uninstalling. An HA backup alone does not restore the territory databases.

Keep the previous program ZIP for rollback. Do not downgrade after a future incompatible data migration without using the matching private backup. This baseline uses the existing eleven database files and no schema migration.

## Sources

- [Home Assistant app repositories](https://developers.home-assistant.io/docs/apps/repository/)
- [Home Assistant local apps/tutorial](https://developers.home-assistant.io/docs/apps/tutorial/)
- [Google Drive and QR setup — English](GOOGLE-DRIVE.en.md)
- [Google Drive — dansk](../distrikt/GOOGLE-DRIVE-OPSAETNING.md)
- [First session with LTM](FIRST-STEPS.en.md)

### Local do-not-call photo import (beta)

The beta's **Settings → Import → Do-not-call entries from photos** reads PNG/JPEG images on your own LTM server. Review the recognized text, choose the card, select an exact local card address and a date for every line (or explicitly skip it), then review the preview and type `IMPORTÉR IB`. Choosing an image does not write records. Previously approved images remain imported if you close the queue. Handwriting and complex layouts may require manual editing. S-12 fronts are not supported yet.

The HA beta includes Tesseract with Danish and English data in its container image. On Mac/Windows, install Tesseract and its `dan`/`eng` language data on the machine running LTM; a phone using HA needs no OCR installation. See the [official installation guide](https://tesseract-ocr.github.io/tessdoc/Installation.html). Homebrew users can install `tesseract tesseract-lang`; Windows users can follow the installations linked by that guide and enable PATH or the standard Program Files/Tesseract-OCR location. LTM does not automatically install software on desktop. The import shows when the engine or Danish data is missing.

Images and text are not sent to an external AI or OCR service. Temporary files are removed after local recognition; unapproved OCR results are RAM-only and expire after five minutes. Only explicit approval adds do-not-call entries to the local database. Only addresses already on the chosen card can be imported. HEIC/PDF must first be converted to PNG/JPEG. Limits: 20 images, 12 MB per original and 60 MB total.
