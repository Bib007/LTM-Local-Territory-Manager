#!/bin/bash
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
for candidate in /Library/Frameworks/Python.framework/Versions/3.*/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
  if [ -x "$candidate" ] && "$candidate" -c 'import sys; assert sys.version_info >= (3,9)' >/dev/null 2>&1; then
    "$candidate" "$APP_DIR/app/server.py" --stop
    exit
  fi
done
