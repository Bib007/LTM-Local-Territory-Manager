#!/bin/bash
# Purpose-specific macOS local-app launcher. Data stay outside this program folder.
set -eu
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$APP_DIR/Start-LTM.command" --mode local "$@"
