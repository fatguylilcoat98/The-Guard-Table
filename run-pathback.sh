#!/usr/bin/env bash
# PathBack launcher for PM2 (bare-metal, no Docker).
#   pm2 start ./run-pathback.sh --name pathback --interpreter bash
# Sources .env, then execs gunicorn serving Flask + the built React frontend.
# Paths derive from this script's location; override via env if needed.
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${PATHBACK_VENV:-$APP_DIR/.venv}"
BIND="${PATHBACK_BIND:-127.0.0.1:8787}"
WORKERS="${PATHBACK_WORKERS:-2}"

cd "$APP_DIR"
if [ -f "$APP_DIR/.env" ]; then
  set -a; source "$APP_DIR/.env"; set +a
fi

exec "$VENV/bin/gunicorn" \
  --chdir "$APP_DIR/backend" \
  -b "$BIND" \
  --workers "$WORKERS" --timeout 120 --keep-alive 75 \
  app:app
