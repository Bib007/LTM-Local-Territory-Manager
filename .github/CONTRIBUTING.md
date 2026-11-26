# Bidrag til LTM

[English](../docs/CONTRIBUTING.en.md)

Brug [hjemmesidens feedbackformular](https://localterritorymanager.netlify.app/da/feedback/), [Issues](https://github.com/Bib007/LTM-Local-Territory-Manager/issues) eller en pull request. Beskriv den ændrede adfærd og kontrollen med fiktive eksempler. Hold dansk og engelsk betjening og vejledning ajour. Navne, noter og andre brugerindtastninger bevarer deres sprog.

Test i en midlertidig mappe. Brug fiktive kort, adresser og konti. Bevar eksisterende data, filformater, forhåndsvisninger og godkendelser ved opdatering.

## Kontrol

- Python: `python -m unittest discover -s distrikt/tests -v`
- JavaScript: kør `distrikt/tests/test_*.cjs` med `TZ=Europe/Copenhagen`.
- Brugerflade: gennemgå den ændrede arbejdsgang på smal og bred skærm. De relevante browserprøver står i [GitHub Actions](https://github.com/Bib007/LTM-Local-Territory-Manager/actions/workflows/check.yml).
- Pakker: `python scripts/test_build_release.py` og `python scripts/check_release_smoke.py`.
- Versioner: opdatér [dansk ændringslog](../docs/CHANGELOG.md) og [engelsk changelog](../docs/CHANGELOG.en.md), kopiér begge til `distrikt/` og kør `python scripts/check_changelog.py`.

Se [Beta](../docs/BETA.md) og [udgivelsesspor](../docs/RELEASE-TRACKS.md) for publicering.
