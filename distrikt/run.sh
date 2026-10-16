#!/usr/bin/with-contenv bashio
set -euo pipefail
export DISTRIKT_PASSWORD="$(bashio::config 'password')"
DISTRIKT_HOST="$(bashio::config 'access_host')"
exec python3 /opt/distrikt/app/server.py --serve --lan --port 8787 --access-host "$DISTRIKT_HOST" --data-dir /data/distrikt --no-browser
