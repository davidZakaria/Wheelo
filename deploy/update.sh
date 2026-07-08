#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:-/var/www/wheelo}"

cd "$APP_DIR"
git pull || true
./.venv/bin/pip install -r requirements.txt
sudo systemctl restart wheelo
sudo systemctl --no-pager status wheelo
