#!/bin/sh
set -eu
LTM_APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys,sqlite3; assert sys.version_info >= (3,9)' >/dev/null 2>&1; then
  echo 'Installer Python 3.9 eller nyere med sqlite3 fra din Linux-distribution.' >&2
  exit 1
fi
exec python3 "$LTM_APP_DIR/app/launcher.py" "$@"
