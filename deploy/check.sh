#!/usr/bin/env bash
# Run from project root on VPS after upload to verify files before install.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

missing=0
for f in app.py roulette.py filtering.py contestants_loader.py apify_fetch.py \
         winners.csv requirements.txt .streamlit/config.toml deploy/install.sh; do
  if [[ ! -f "$f" ]]; then
    echo "MISSING: $f"
    missing=1
  else
    echo "OK: $f"
  fi
done

if [[ $missing -eq 1 ]]; then
  echo ""
  echo "Fix missing files before running deploy/install.sh"
  exit 1
fi

echo ""
echo "All required files present. Run:"
echo "  sudo bash deploy/install.sh --dir $ROOT --port 8503 --domain YOUR_DOMAIN --user \$USER"
