#!/bin/bash
# Run from the unpacked release. Only program files are copied; no database access.
set -euo pipefail
release_version='1.11.0'
script_dir="$(cd "$(dirname "$0")" && pwd)"
source_dir="$script_dir/Home-Assistant/distrikt"
manifest="$script_dir/Home-Assistant/SHA256SUMS.txt"
work_dir=''
cleanup() { if [ -n "$work_dir" ]; then /bin/rm -rf "$work_dir"; fi; }
failed() {
  echo
  echo 'STOP: Opdateringsfilerne blev ikke færdigkopieret.'
  echo 'Lad Distrikt være stoppet. Kør hjælpen igen, eller send fejlteksten ovenfor.'
  echo 'Tryk ikke Opdater i Home Assistant endnu.'
}
trap cleanup EXIT
trap failed ERR

if [ "$(uname -s)" != 'Darwin' ]; then
  echo 'Denne kopieringshjælp er til macOS.'; exit 1
fi
if [ ! -f "$source_dir/app/server.py" ] || [ ! -f "$source_dir/config.yaml" ] || [ ! -f "$manifest" ]; then
  echo 'Pak hele ZIP-filen ud på din Mac, og kør hjælpen derfra.'
  echo 'Hjælpen skal ligge ved siden af mappen Home-Assistant.'; exit 1
fi
work_dir="$(mktemp -d "${TMPDIR:-/tmp}/distrikt-update.XXXXXX")"
echo "Distrikt $release_version — kopi af programfiler til Home Assistant"
echo 'Distrikt skal være stoppet i Home Assistant inden kopieringen.'
echo 'Kontrollerer først alle filer i den udpakkede opdatering…'
if ! (cd "$source_dir" && /usr/bin/shasum -a 256 -c "$manifest") >"$work_dir/source-check.txt" 2>&1; then
  cat "$work_dir/source-check.txt"
  echo 'ZIP-filerne er ufuldstændige eller ændrede. Download og udpak opdateringen igen.'
  exit 1
fi
if ! root_dir=$(/usr/bin/osascript -e 'POSIX path of (choose folder with prompt "Vælg selve local_apps-mappen på Home Assistant. Distrikt skal være stoppet.")'); then
  echo 'Annulleret. Ingen programfiler er kopieret.'; exit 0
fi
root_dir="${root_dir%/}"
case "$root_dir" in
  /Volumes/*) ;;
  *) echo 'STOP: Vælg netværksmappen på Home Assistant under Placeringer.'; exit 1 ;;
esac
case "${root_dir##*/}" in
  local_apps|local_apps-[0-9]*|addons|addons-[0-9]*) ;;
  *) echo 'STOP: Vælg selve local_apps (eller addons), ikke distrikt eller config.'; exit 1 ;;
esac
target_dir="$root_dir/distrikt"
if [ -L "$target_dir" ]; then echo 'STOP: Distrikt-mappen må ikke være et symbolsk link.'; exit 1; fi
/bin/mkdir -p "$target_dir"
echo 'Kopierer programfiler uden Finders midlertidige Mac-filer…'
# __init__.py causes .__init__.py.* temporary names without --inplace.
# Keep config.yaml until all other files have arrived and passed checksums.
/usr/bin/rsync -rvc --inplace --exclude='.DS_Store' --exclude='._*' \
  --exclude='/config.yaml' "$source_dir/" "$target_dir/"
/usr/bin/grep -v '  config.yaml$' "$manifest" >"$work_dir/without-config.txt"
echo 'Kontrollerer de kopierede programfiler…'
if ! (cd "$target_dir" && /usr/bin/shasum -a 256 -c "$work_dir/without-config.txt") >"$work_dir/target-check.txt" 2>&1; then
  cat "$work_dir/target-check.txt"; failed; exit 1
fi
/usr/bin/rsync -vc --inplace "$source_dir/config.yaml" "$target_dir/config.yaml"
if ! (cd "$target_dir" && /usr/bin/shasum -a 256 -c "$manifest") >"$work_dir/final-check.txt" 2>&1; then
  cat "$work_dir/final-check.txt"; failed; exit 1
fi
echo
echo "FÆRDIG: Alle Distrikt $release_version-programfiler er kopieret og SHA-256-kontrolleret."
echo 'Nu: Home Assistant → Appbutik → ⋮ → Kontroller for opdateringer.'
echo "Åbn eksisterende Distrikt → Opdater til $release_version → Start."
echo 'Åbn http://192.168.1.147:8787 og tryk Cmd+Shift+R.'
echo 'Afinstaller ikke appen, og importer ikke en databasebackup ved almindelig opdatering.'
