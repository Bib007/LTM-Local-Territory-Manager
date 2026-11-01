<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/brand/logo-dark.svg">
  <img src="assets/brand/logo-light.svg" alt="LTM — Local Territory Manager" width="420">
</picture>

# Your territory cards. One clear overview.

**Free, self-hosted territory administration for congregations of Jehovah’s Witnesses. Keep your records on your own computer or Home Assistant system.**

[Website](https://localterritorymanager.netlify.app) · [Try the live demo](https://bib007.github.io/LTM-Local-Territory-Manager/) · [Latest stable](https://github.com/Bib007/LTM-Local-Territory-Manager/releases/latest) · [Installation](docs/INSTALL.en.md) · [Dansk](README.da.md)

LTM combines physical territory cards with a searchable overview, assignments, history and practical digital tools. Start with the card numbers you already use; add street lists, addresses or drawn boundaries when you need them. No LTM cloud account or subscription is required.

![Real LTM territory list using fictional example records](assets/screenshots/cards-en.jpg)

## Everyday territory work

- **Cards and assignments:** see cards in the carry folder, storage box or on assignment; record assignments, returns, completions and notes.
- **History and reports:** review recorded work by calendar year, service year or the last 12 months. Print the original S-13, card material and report summaries.
- **Maps and addresses:** draw boundaries, select addresses, retain manual street/number ranges and show an honest unknown count where a visit total is not recorded.
- **Local imports:** preview supported Excel/CSV card, publisher and do-not-call files before confirmation. Card and do-not-call imports support selecting sheets, headers and column mappings. Safe numeric formats, leading zeros and ignored columns are handled deliberately.
- **Profiles and roles:** create accounts and administrator-defined roles. Home and summary-report access can be granted separately from detailed cards, personal records and administration. The personal introduction follows the current account's permissions.
- **Concurrent editing:** independent field edits can be combined; conflicting saved proposals are retained for review. An uncertain save requires checking the result before repeating it.
- **Backups:** keep private territory-data backups and separate account backups. Restore is an explicit, validated operation with a safety copy.
- **Optional QR images:** explicitly approve a public card-front image for Google Drive. Current approved images can retain the same file/QR link, with separately approved date updates. This supports the physical card workflow; it is not a full digital assignment system.

The interface defaults to **English for new users**. Explicit saved language choices are preserved, and Danish is available. Translation remains partial: some screens, errors and original S-12/S-13 forms remain Danish. English printed forms are deferred until after this stable release.

## Try it without installation

[Open the interactive demo](https://bib007.github.io/LTM-Local-Territory-Manager/). It uses fictional records and browser-local state. Select the administrator or territory-desk assistant example to explore their different visible workflows. The assistant can review its allowed overview, assign/return cards and add a return note.

The demo is a simulation, separate from the installed server. Its role switch is not authentication or a substitute for server-enforced permissions. Do not enter real congregation records, names or do-not-call information in a public demo or feedback form.

## Choose an installation

| Option | Start here | Requirements |
| --- | --- | --- |
| Home Assistant | [Install the stable add-on](docs/INSTALL.en.md#home-assistant-os) | Your own Home Assistant system; ordinary stable port 8787 |
| Windows, macOS or Linux | [Computer setup](docs/SELF-HOSTING.en.md) | Python 3.9+ with SQLite; extract the complete release ZIP |
| Separate beta | [Beta installation](docs/BETA.md) and [prereleases](https://github.com/Bib007/LTM-Local-Territory-Manager/releases) | Separate test data/login; HA beta port 8788 |

Use [the latest stable release](https://github.com/Bib007/LTM-Local-Territory-Manager/releases/latest) for ordinary work. GitHub's latest link excludes prereleases; use the release list for betas. Native EXE/DMG installers are not currently supplied.

For a new computer installation, run the platform's **Start-LTM** launcher from the extracted `Distrikt-lokal` directory. Existing installations should follow the update guide and keep using the same data directory. Keep the previous program folder until the new version has been checked. Do not point a separate beta at production data.

## Accounts, access and private records

The installed server enforces each account's current permissions; hiding a button is not its security boundary. The administrator chooses users and roles in the application. See [accounts, roles and introductions](docs/USERS.en.md).

LTM stores its databases in the selected installation's data directory. Restrict server access to your private network and use your own VPN for remote access. Do not expose the application directly to the public internet. [Home Assistant security](docs/HA-SECURITY.en.md) explains its deployment limits.

Map tiles, address services and optional Drive publication contact external providers. Automatic address integrations currently focus on Danish source data; manual cards and core administration do not require Danish automatic address lookup. Read [privacy](docs/PRIVACY.en.md), [current limitations](docs/LIMITATIONS.en.md) and [Google Drive sharing](docs/GOOGLE-DRIVE.en.md) before relying on those features.

## Back up before updating

1. Download a private territory-data backup from the app.
2. If profiles are enabled, also keep a separate account backup. An ordinary data ZIP does not replace account recovery material or connection configuration.
3. Update the program while preserving the installation's data directory.
4. Open the updated app and check the records. Keep backups away from public repositories, the website, feedback forms and public Drive images.

Original printing templates and existing records are preserved by ordinary updates. Imported public-image metadata does not resume external publication automatically; approve a new image after restore.

## Documentation and feedback

[Documentation overview](docs/README.en.md) · [First steps](docs/FIRST-STEPS.en.md) · [Accounts and roles](docs/USERS.en.md) · [Printing](docs/PRINT.en.md) · [Privacy](docs/PRIVACY.en.md) · [Contributing](docs/CONTRIBUTING.en.md)

[Report a bug or suggest an improvement](https://tally.so/r/KpY0ZV). Describe the steps and include invented examples. Never submit real names, do-not-call records, private databases, passwords or connection files. The feedback form is operated separately by Tally.

LTM is an independent, unofficial open-source project. It is not developed, published or endorsed by Jehovah’s Witnesses or their organisation. No official affiliation is implied.
