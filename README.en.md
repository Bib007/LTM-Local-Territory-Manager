<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/brand/logo-dark.svg">
  <img alt="Local Territory Manager – JW" src="assets/brand/logo-light.svg" width="640">
</picture>

[Dansk](README.md)

# Local Territory Manager – JW

**Private territory administration, on your own computer.** An unofficial, community-built tool for Jehovah’s Witnesses. Vibe coded with **OpenAI Codex**, shaped by practical use at the territory desk.

[Dansk](README.md) · [Installation](docs/INSTALL.en.md) · [Privacy](docs/PRIVACY.en.md) · [Roadmap](ROADMAP.md) · [Changelog](CHANGELOG.md) · [Manual help checklist](Dette-skal-hjaelpes-manuelt.md)

## New setup and card import on develop

First launch asks about assignments only or maps, KML, existing card divisions and do-not-call records. Your answers create a personal plan and an optional tour through the real application pages. Reopen it from Settings.

Already divided your addresses into cards? Download the Excel template from **Settings → Advanced → Import existing territory cards**. XLSX and CSV are reviewed locally; every error must be fixed before creating cards together. [Card import guide](docs/KORTIMPORT.en.md).

## Start here

**Development version: 1.12.0-beta.13.** This branch prepares the next version. Use [main](https://github.com/Bib007/LTM-Local-Territory-Manager/tree/main) for stable installations. The ordinary HA link below follows main. [Readiness plan: 30%](https://github.com/Bib007/LTM-Local-Territory-Manager/blob/develop/KOREPLAN.md).

[Add LTM to Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FBib007%2FLTM-Local-Territory-Manager)

The stable baseline is **1.11.0**. The installed application interface is currently Danish. A separate Danish/English browser demo is now in the repository; [publishing instructions](docs/DEMO-HOSTING.en.md) explain the remaining hosting setup. The demo has no public URL yet. Guided onboarding is prepared on a development branch; full app translation remains in progress. Read [the known limitations](docs/LIMITATIONS.en.md) before relying on a feature.

- **Mac / Windows:** download the packaged ZIP from [Releases](https://github.com/Bib007/LTM-Local-Territory-Manager/releases), extract it, install Python 3.9+ once, then open the matching `Start-Distrikt` launcher in `Distrikt-lokal`. No Docker or pip packages needed.
- **From source:** open `distrikt/Start-Distrikt.command` on Mac or `distrikt/Start-Distrikt.cmd` on Windows. Alternatively: `python3 distrikt/app/server.py`. Use a verified release when updating a working installation.
- **Home Assistant OS:** an optional app with its own LAN address and login. [Installation and updates](docs/INSTALL.en.md#home-assistant-os). It does not use Ingress or Nabu Casa.

Home Assistant support exists because I did not have another spare computer available at the time. The desktop versions remain first-class ways to run the same application; data can be moved using a private export/import.

**The everyday advantage of HA hosting:** leave the app running at home and use it on your phone, iPad or computer while away. Connect your device to a **VPN on your own router**, then open the app's private LAN address in the browser. The VPN must allow access to the HA machine's network. This does not require exposing the app to the public internet or using Nabu Casa.

New installation? Start with [your first session](docs/FIRST-STEPS.en.md). Google sharing has its own [optional Drive/QR guide](docs/GOOGLE-DRIVE.en.md).

## What it does

- Check territories out and in; see what is assigned, in the carry folder or in the storage box.
- Add temporary numbered cards first and fill in addresses and boundaries later.
- Manage publishers, assignments, completion history, notes and tasks.
- Draw/import boundaries, select individual addresses, ignore non-visit addresses and propose card divisions.
- Keep do-not-call records locally; print them on the card back.
- Print card fronts/backs, S-13 and reports by service year (1 September–31 August).
- Optionally publish an approved PNG to Google Drive with a stable QR link. Databases and do-not-call lists are never uploaded by this feature.

## Local data, deliberate sharing

SQLite databases stay on the machine running the app. There is no developer account, analytics service or AI endpoint in the application. Online maps, public address lookups and optional Google Drive use outside services; this is **not an entirely offline application**.

Local storage gives you control over data and access. It is **not a guarantee of GDPR compliance**. You remain responsible for retention, backups, access and the instructions applicable to your congregation. See [the actual data flows](docs/PRIVACY.en.md).

## KML from JW HUB

In my experience, you can download a KML file covering the congregation’s entire territory from JW HUB if your account has the appropriate permissions and access. Use the export options available to your own account, then import and review the boundary in LTM. Never post the actual file in GitHub issues or send it to AI.

## Built in the open

This project is vibe coded with Codex. I cannot promise that everything works. Please report bugs and suggest improvements, using **made-up examples only**. Never attach real territory databases, publisher names, addresses marked do-not-call, Google tokens or backups to an issue.

The software is provided as-is. It is not produced, approved or supported by jw.org, JW HUB or Home Assistant. Brand names identify their respective services. Source code is MIT licensed; third-party code and form templates keep their separate rights. [Third-party notices](distrikt/THIRD-PARTY.md).

## Development

```sh
python3 -m unittest discover -s distrikt/tests -v
TZ=Europe/Copenhagen node distrikt/tests/test_frontend.cjs
python3 scripts/build_release.py
```

Python is the only runtime requirement; Node is used for development checks. Tests use isolated fictional data. [Contributing](CONTRIBUTING.en.md).

[Open the fictional web demo](https://bib007.github.io/LTM-Local-Territory-Manager/) without installation or a GitHub account. [Demo details](demo/README.md).
