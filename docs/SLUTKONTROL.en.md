# Final verification of the fixed development plan

[Dansk](SLUTKONTROL.md)

Verification target: 1.12.0-beta.22 on develop, 17 October 2026. Main remains stable 1.11.1. The fixed plan has ten development tasks; the wishlist is a separate queue. Development verification does not imply testing the owner's physical equipment or accounts.

## Repeatable checks

- Python: `python -m unittest discover -s distrikt/tests -v`, with temporary directories and invented records. The previous private ZIP is not supplied, so its migration test is explicitly skipped.
- JavaScript: every `distrikt/tests/test_*.cjs` with `TZ=Europe/Copenhagen`. Printing tests cover unchanged original content/payloads, bilingual controls, duplicate clicks, blocked popups, changed revisions/forms/navigation, newer dialogs and failed image decoding.
- Browser: `scripts/check_geo_browser.cjs` and `scripts/check_access_browser.cjs`, with isolated Playwright 1.56.1 via `PLAYWRIGHT_MODULE`. No browser dependency is added to the app. Tests cover 320/390/768/1440 pixels, invented login/API, real DOM, focus, front/back printing and complete report PDFs. External services use test responses.
- Packaging: `python scripts/test_build_release.py` and `python -m unittest discover -s scripts -p test_build_beta.py -v`. Checks cover complete forms, packaged guide links, checksums, reproducibility, no runtime data and isolated beta identity.
- Real archives: `python scripts/check_release_smoke.py` verifies reproducibility, all HA checksums and real extracted startup with empty temporary data and a matching version. `python scripts/build_release.py` and `python scripts/build_beta.py --output /tmp/ltm-ha-beta-review`. Verify ZIP integrity, manifest and checksum. Blank originals and the import template are included; private databases, keys and connection files are excluded.
- GitHub additionally runs multiple Python versions, Mac/Windows launcher checks and an HA container check before publishing beta automatically. Stable publication is separate.

## Completed areas

Map overview, addresses/card checks, geographic editing/import, advanced setup/local do-not-call import, Drive/QR with invented responses, errors/save safety, login/keyboard, printing, complete package and final documentation. Original S-12/S-13 files and form placement are preserved. Opening printing never automatically approves a changed card for assignment.

## Local owner checks

Physical printing, the actual HA/phone/VPN, Google consent and access on return/reassignment, the configured Datafordeler account and any screen reader remain separate. Follow the [owner checklist](../Dette-skal-hjaelpes-manuelt.en.md). Automated verification does not mark these as tested.

See [printing](PRINT.en.md), [installation](INSTALL.en.md), [beta](BETA.md), [limitations](LIMITATIONS.en.md) and the [fixed plan](../KOREPLAN.md).
