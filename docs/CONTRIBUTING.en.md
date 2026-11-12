# Contributing to LTM

[Dansk](../.github/CONTRIBUTING.md)

Use the [website feedback form](https://localterritorymanager.netlify.app/en/feedback/), [Issues](https://github.com/Bib007/LTM-Local-Territory-Manager/issues) or a pull request. Describe the changed behaviour and verification using fictional examples. Keep Danish and English controls and guides current. User-entered names, notes and values retain their language.

Use temporary test directories and fictional cards, addresses and accounts. Preserve existing data, file formats, previews and approvals when updating the application.

- Python: `python -m unittest discover -s distrikt/tests -v`
- JavaScript: run `distrikt/tests/test_*.cjs` with `TZ=Europe/Copenhagen`.
- Interface: check the affected workflow on narrow and wide screens. See the browser checks in [GitHub Actions](https://github.com/Bib007/LTM-Local-Territory-Manager/actions/workflows/check.yml).
- Packages: `python scripts/test_build_release.py` and `python scripts/check_release_smoke.py`.
- Versions: update the [Danish changelog](CHANGELOG.md) and [English changelog](CHANGELOG.en.md), copy both into `distrikt/` and run `python scripts/check_changelog.py`.

See [Beta](BETA.md) and [release tracks](RELEASE-TRACKS.md) for publishing.
