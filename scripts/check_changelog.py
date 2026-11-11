#!/usr/bin/env python3
"""Fail closed if Danish/English release histories or the HA copies drift.

Translations are reviewed and authored alongside their source notes. A release
must not silently publish an English-only update in Home Assistant.
"""
from pathlib import Path
import re

SECTION = re.compile(r"^##[ \t]+(\d+\.\d+\.\d+(?:-beta\.\d+)?)(?:[^\n]*)$", re.M)


def _versions(raw: bytes, name: str) -> list[str]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{name}: changelog must use UTF-8") from exc
    matches = list(SECTION.finditer(text))
    versions = [match.group(1) for match in matches]
    if not matches or len(set(versions)) != len(versions):
        raise ValueError(f"{name}: missing or duplicate changelog versions")
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        if not text[match.end():end].strip():
            raise ValueError(f"{name}: empty release notes for {match.group(1)}")
    return versions


def validate(da: bytes, en: bytes, ha_da: bytes, ha_en: bytes, current: str) -> None:
    if da != ha_da:
        raise ValueError("Project and HA changelogs differ. Sync distrikt/CHANGELOG.md from docs/CHANGELOG.md.")
    if en != ha_en:
        raise ValueError("Project and HA English changelogs differ.")
    if not da.startswith("# Ændringslog\n"):
        raise ValueError("Danish changelog must remain the default.")
    if not en.startswith("# Changelog"):
        raise ValueError("English changelog must have its own language heading.")
    da_versions = _versions(da, "Danish")
    en_versions = _versions(en, "English")
    if da_versions[0] != current:
        raise ValueError("Changelog must list the current version first.")
    if en_versions != da_versions:
        raise ValueError("Danish and English changelog versions differ; update both languages in the same PR.")


def main() -> None:
    import build_release
    root = Path(__file__).resolve().parents[1]
    validate(
        (root / "docs/CHANGELOG.md").read_bytes(),
        (root / "docs/CHANGELOG.en.md").read_bytes(),
        (root / "distrikt/CHANGELOG.md").read_bytes(),
        (root / "distrikt/CHANGELOG.en.md").read_bytes(),
        build_release.version(),
    )
    print("Danish/English changelogs and Home Assistant copies match the current version.")


if __name__ == "__main__":
    main()
