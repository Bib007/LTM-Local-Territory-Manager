#!/bin/bash
# Purpose-specific macOS private-server launcher. It prompts for a private LAN address.
set -eu
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$APP_DIR/Start-LTM.command" --mode server "$@"
