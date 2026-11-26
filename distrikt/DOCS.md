# Install LTM on Home Assistant

[Website](https://localterritorymanager.netlify.app) · [Full English guide](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/INSTALL.en.md) · [Dansk](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/INSTALL.md)

## Install the stable repository

1. Add `https://github.com/Bib007/LTM-Local-Territory-Manager` under Home Assistant → Settings → Apps / Add-ons → Store → Repositories.
2. Choose **Distrikt → Install**. Home Assistant downloads the program and builds the installation; do not copy program files with Samba.
3. Set `access_host` to the Home Assistant machine's private IP address or local hostname, without a scheme, port or slash.
4. Choose an app password of at least 12 characters. This is the app's login, separate from your Home Assistant account.
5. Keep **8787 → 8787**, start the app and open `http://YOUR_PRIVATE_HOST:8787`.
6. Complete the setup guide. If you enable individual profiles, the administrator chooses accounts and roles in the application.

Use your own VPN for remote access. Do not publish this application directly on the internet. The beta repository ending in `#beta` is a separate test installation with port 8788 and its own data/login.

## Move an older local add-on

A different add-on identity has its own data directory. Moving to it requires a private data backup and a deliberate restore. Stop the older app before starting a replacement on the same port, keep the old installation and backups, review the import preview, then confirm replacement. An ordinary repository update of the same installation does not require re-importing its data. Do not uninstall a working app merely to update it.

Connections are configured separately. A normal data ZIP does not include Google/account login configuration, and restored public-image metadata cannot resume sharing without new approval.

## Backups and recovery

The stable app stores its records in persistent `/data/distrikt`. Original blank printing forms are included; your records stay in the data directory.

**App records are excluded from Home Assistant backups.** Use the app's private backup function before updates, moves or uninstalling. Profile account backups are separate from territory-data ZIPs; keep both when profiles are in use. Do not send any of these files to the public website, demo, feedback form or repository.

## Home Assistant status integration

The add-on declares `homeassistant_api: true` for local health/status reporting and the supported notification blueprint. This is a Core API grant, independent of an LTM user's role. Disabling the optional status feature stops those calls; it does not remove the add-on's declared grant. The implementation uses fixed status/event paths and excludes private territory records from those payloads.

See [Home Assistant security](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/HA-SECURITY.en.md) for the current boundaries and [account administration](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/main/docs/USERS.en.md) for installed profile permissions.

## Language and limitations

English is primary for new browser users, and Danish remains available. Saved language preferences are preserved. Some screens/errors and the original printed S-12/S-13 forms remain Danish. Native EXE/DMG packages, OCR development and automatic card division are not part of this release.
