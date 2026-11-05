#!/usr/bin/env bash
# Called only by the manually dispatched GitHub workflow after common and one
# selected platform's controls pass. It never replaces an existing asset.
set -euo pipefail

track="${1:?Choose one release track}"
python scripts/build_tracks.py --track "$track" --output dist
version="$(python -c "import sys; sys.path.insert(0,'scripts'); import build_release; print(build_release.version())")"
if [[ "$version" == *-* ]]; then
  echo "Pre-release version: stable track publication is disabled."
  exit 1
fi
tag="v$version"
asset="$(python -c "import sys; sys.path.insert(0,'scripts'); import build_tracks; print('dist/'+build_tracks.TRACKS['$track'][1]+'-v'+__import__('build_release').version()+'.zip')")"
title="$(head -n 1 docs/RELEASE-NOTES.md | sed 's/^# //')"
notes="$RUNNER_TEMP/ltm-release-notes.md"
tail -n +3 docs/RELEASE-NOTES.md > "$notes"

if gh release view "$tag" >/dev/null 2>&1; then
  # No --clobber: an existing file is immutable and must be investigated.
  gh release upload "$tag" "$asset" "$asset.sha256"
else
  gh release create "$tag" "$asset" "$asset.sha256" --target "$GITHUB_SHA" --title "$title" --notes-file "$notes"
fi
