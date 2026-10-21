# Final verification of the fixed development plan

[Dansk](SLUTKONTROL.md)

Verification baseline: beta.60 passed program, platform, package and browser checks. Beta.61 implements W81 in source commit cd95b1b130bebe07c9ffc3d2c5fe380ca5058253. Program, browser, Windows, HA and package checks passed; the Mac job remains queued on GitHub and gates automatic release. Beta.61 is not yet recorded as published. Main remains stable 1.11.1. The fixed development plan is complete; the entire wishlist is not required for the next stable release.

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

## Next stable release gates

1. Verify the W81 beta: no automatic proposals, working manual maps/local do-not-call import and preserved cards. Require successful program, browser, platform and HA package checks on the exact release code.
2. Repeat W78's interrupted address download on the owner's HA. Check resume, completed tiles and any failure code before declaring that workflow stable.
3. Owner smoke check: private backup, beta update, restart, phone login, assignment/return and restore to a separate test installation. Check printing/QR when used and overnight address checks when enabled.
4. Resolve or explicitly scope W61 GitHub cleanup and open security items W06/W28/W56 with the owner. A full security scan and encrypted key backup have not been documented. The existing LAN/VPN access model is unchanged.
5. Finalize limitations, version, changelog, upgrade/backup instructions and package checksums. Promote verified code to main and publish stable as a separate step.

Automatic division/W16 is paused and removed from the active app. Multiuser W65 is not ordered. Hosting W74 and old-repository archiving W08 follow stable. The unverified live web demo is separate from local/HA release. Full English completion W58 remains open; do not claim complete translation before verification.
