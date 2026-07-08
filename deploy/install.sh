#!/usr/bin/env bash
set -euo pipefail

# Wheelo VPS installer
# Run on the server as a user with sudo privileges.
#
# Example:
#   sudo bash deploy/install.sh \
#     --dir /var/www/wheelo \
#     --port 8503 \
#     --domain roulette.yourdomain.com \
#     --apify-token "apify_api_xxx"

APP_DIR="/var/www/wheelo"
APP_PORT="8503"
APP_DOMAIN=""
APIFY_TOKEN=""
APP_USER="${SUDO_USER:-$USER}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) APP_DIR="$2"; shift 2 ;;
    --port) APP_PORT="$2"; shift 2 ;;
    --domain) APP_DOMAIN="$2"; shift 2 ;;
    --apify-token) APIFY_TOKEN="$2"; shift 2 ;;
    --user) APP_USER="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ ! -f "$APP_DIR/app.py" ]]; then
  echo "ERROR: app.py not found in $APP_DIR"
  echo "Upload or git clone the project there first."
  exit 1
fi

echo "==> Installing system packages (python3-venv) if needed..."
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y python3 python3-venv python3-pip
fi

echo "==> Creating virtualenv..."
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "==> Writing Streamlit secrets..."
mkdir -p "$APP_DIR/.streamlit"
if [[ -n "$APIFY_TOKEN" ]]; then
  cat > "$APP_DIR/.streamlit/secrets.toml" <<EOF
APIFY_TOKEN = "$APIFY_TOKEN"
EOF
  chmod 600 "$APP_DIR/.streamlit/secrets.toml"
else
  echo "WARN: No --apify-token provided. Copy secrets manually to $APP_DIR/.streamlit/secrets.toml"
fi

echo "==> Patching Streamlit port to $APP_PORT..."
if grep -q '^port = ' "$APP_DIR/.streamlit/config.toml"; then
  sed -i "s/^port = .*/port = $APP_PORT/" "$APP_DIR/.streamlit/config.toml"
fi
if grep -q '^serverPort = ' "$APP_DIR/.streamlit/config.toml"; then
  sed -i "s/^serverPort = .*/serverPort = $APP_PORT/" "$APP_DIR/.streamlit/config.toml"
fi

echo "==> Installing systemd service..."
sudo tee /etc/systemd/system/wheelo.service > /dev/null <<EOF
[Unit]
Description=Wheelo Green Avenue Roulette (Streamlit)
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$APP_DIR/.venv/bin/python -m streamlit run app.py --server.port $APP_PORT --server.address 127.0.0.1 --server.headless true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable wheelo
sudo systemctl restart wheelo

echo "==> Service status:"
sudo systemctl --no-pager status wheelo || true

if [[ -n "$APP_DOMAIN" ]]; then
  NGINX_SITE="/etc/nginx/sites-available/wheelo"
  echo "==> Writing nginx site for $APP_DOMAIN ..."
  sudo tee "$NGINX_SITE" > /dev/null <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $APP_DOMAIN;

    client_max_body_size 25M;

    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }
}
EOF
  sudo ln -sf "$NGINX_SITE" /etc/nginx/sites-enabled/wheelo
  sudo nginx -t
  sudo systemctl reload nginx
  echo "Nginx configured. Run: sudo certbot --nginx -d $APP_DOMAIN"
else
  echo "No --domain provided. Skipped nginx config."
  echo "App is available locally at http://127.0.0.1:$APP_PORT"
fi

echo ""
echo "Done. Useful commands:"
echo "  sudo systemctl status wheelo"
echo "  sudo systemctl restart wheelo"
echo "  sudo journalctl -u wheelo -f"
