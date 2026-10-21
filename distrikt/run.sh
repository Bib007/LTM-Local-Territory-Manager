#!/usr/bin/with-contenv bashio
set -euo pipefail
export LTM_CHANNEL=beta
export DISTRIKT_HOME_ASSISTANT=1
export DISTRIKT_PASSWORD="$(bashio::config 'password')"
DISTRIKT_HOST="$(bashio::config 'access_host')"
exec python3 /opt/distrikt/app/server.py --serve --lan --port 8788 --access-host "$DISTRIKT_HOST" --data-dir /data/distrikt-beta --no-browser
