#!/bin/bash
set -u
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
DISTRIKT_PYTHON=""
for candidate in /Library/Frameworks/Python.framework/Versions/3.*/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3; do
  if [ -x "$candidate" ] && "$candidate" -c 'import sys,sqlite3; assert sys.version_info >= (3,9)' >/dev/null 2>&1; then
    DISTRIKT_PYTHON="$candidate"
  fi
done
if [ -z "$DISTRIKT_PYTHON" ] && /usr/bin/xcode-select -p >/dev/null 2>&1; then
  if /usr/bin/python3 -c 'import sys,sqlite3; assert sys.version_info >= (3,9)' >/dev/null 2>&1; then DISTRIKT_PYTHON="/usr/bin/python3"; fi
fi
if [ -z "$DISTRIKT_PYTHON" ]; then
  /usr/bin/osascript -e 'display dialog "Distrikt kræver Python 3 én gang. Hent og installer den officielle macOS universal2-version fra python.org. Åbn derefter denne startfil igen. Docker og andre pakker er ikke nødvendige." buttons {"OK"} default button "OK"'
  /usr/bin/open "https://www.python.org/downloads/macos/"
  exit 1
fi
"$DISTRIKT_PYTHON" "$APP_DIR/app/server.py"
if [ "$?" -ne 0 ]; then
  /usr/bin/osascript -e 'display dialog "Distrikt kunne ikke starte. Se start.log i ~/Library/Application Support/Distrikt. Dine data er ikke overskrevet." buttons {"OK"} default button "OK"'
fi
