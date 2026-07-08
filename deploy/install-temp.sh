#!/usr/bin/env bash
set -euo pipefail

# Quick deploy with a temporary public URL (no permanent domain needed).
#
# Option A — zero DNS setup (nip.io, HTTP only):
#   sudo bash deploy/install-temp.sh --vps-ip 185.123.45.67 --user YOUR_LINUX_USER
#   Opens at: http://185-123-45-67.nip.io
#
# Option B — free DuckDNS hostname (HTTP, HTTPS optional):
#   1. Create a subdomain at https://www.duckdns.org (e.g. wheelo-greenavenue)
#   2. Point it to your VPS IP
#   3. Run:
#   sudo bash deploy/install-temp.sh --domain wheelo-greenavenue.duckdns.org --user YOUR_LINUX_USER
#   4. Optional HTTPS: sudo certbot --nginx -d wheelo-greenavenue.duckdns.org

APP_DIR="/var/www/wheelo"
APP_PORT="8503"
APP_USER="${SUDO_USER:-$USER}"
VPS_IP=""
APP_DOMAIN=""
APIFY_TOKEN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) APP_DIR="$2"; shift 2 ;;
    --port) APP_PORT="$2"; shift 2 ;;
    --vps-ip) VPS_IP="$2"; shift 2 ;;
    --domain) APP_DOMAIN="$2"; shift 2 ;;
    --apify-token) APIFY_TOKEN="$2"; shift 2 ;;
    --user) APP_USER="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$APP_DOMAIN" && -z "$VPS_IP" ]]; then
  echo "Provide either --vps-ip or --domain"
  echo ""
  echo "Examples:"
  echo "  sudo bash deploy/install-temp.sh --vps-ip 185.123.45.67 --user deploy"
  echo "  sudo bash deploy/install-temp.sh --domain wheelo-greenavenue.duckdns.org --user deploy"
  exit 1
fi

if [[ -z "$APP_DOMAIN" ]]; then
  APP_DOMAIN="${VPS_IP//./-}.nip.io"
  echo "Using nip.io temporary domain: $APP_DOMAIN"
  echo "(No DNS signup required — resolves to $VPS_IP automatically)"
fi

INSTALL_ARGS=(--dir "$APP_DIR" --port "$APP_PORT" --domain "$APP_DOMAIN" --user "$APP_USER")
if [[ -n "$APIFY_TOKEN" ]]; then
  INSTALL_ARGS+=(--apify-token "$APIFY_TOKEN")
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
bash "$SCRIPT_DIR/install.sh" "${INSTALL_ARGS[@]}"

echo ""
echo "=========================================="
echo "  TEMPORARY URL (share this for the draw)"
echo "=========================================="
echo ""
echo "  http://$APP_DOMAIN"
echo ""

if [[ "$APP_DOMAIN" == *".nip.io" ]]; then
  echo "nip.io notes:"
  echo "  - Works immediately over HTTP"
  echo "  - Let's Encrypt SSL on nip.io is unreliable — use HTTP for the event"
  echo "  - Or switch to DuckDNS for HTTPS (see deploy/DEPLOY.md)"
elif [[ "$APP_DOMAIN" == *".duckdns.org" ]]; then
  echo "DuckDNS notes:"
  echo "  - Confirm the subdomain points to your VPS IP in the DuckDNS panel"
  echo "  - For HTTPS before the live draw:"
  echo "      sudo certbot --nginx -d $APP_DOMAIN"
else
  echo "For HTTPS: sudo certbot --nginx -d $APP_DOMAIN"
fi

echo ""
echo "After the event, disable public access:"
echo "  sudo systemctl stop wheelo"
echo "  sudo rm /etc/nginx/sites-enabled/wheelo && sudo systemctl reload nginx"
