# VPS Deployment Guide (KVM2 + existing projects)

Deploy Wheelo alongside your other apps using **systemd + nginx** on an internal port.

> **Hostinger KVM2?** See [deploy/HOSTINGER.md](HOSTINGER.md) for your server (`72.61.192.84`) and hPanel-specific steps.

## Temporary domain (recommended for the live draw)

Use a **free short-lived URL** — no need to buy a domain.

### Fastest: nip.io (zero DNS setup)

Replace `YOUR_VPS_IP` with your server’s public IP (e.g. `185.123.45.67`):

```bash
cd /var/www/wheelo
chmod +x deploy/*.sh
sudo bash deploy/install-temp.sh --vps-ip YOUR_VPS_IP --user YOUR_LINUX_USER
```

You get a URL like:

```text
http://185-123-45-67.nip.io
```

HTTP only — fine for a one-night event. Share that link for the draw.

### Nicer URL + HTTPS: DuckDNS (free, ~2 minutes)

1. Go to [duckdns.org](https://www.duckdns.org) and sign in (Google/GitHub).
2. Create a subdomain, e.g. `wheelo-greenavenue` → `wheelo-greenavenue.duckdns.org`.
3. Set its IP to your VPS public IP and save.
4. Install:

```bash
sudo bash deploy/install-temp.sh \
  --domain wheelo-greenavenue.duckdns.org \
  --user YOUR_LINUX_USER
```

5. Optional HTTPS before going live:

```bash
sudo certbot --nginx -d wheelo-greenavenue.duckdns.org
```

Then share: `https://wheelo-greenavenue.duckdns.org`

### After the event — turn it off

```bash
sudo systemctl stop wheelo
sudo rm /etc/nginx/sites-enabled/wheelo
sudo systemctl reload nginx
```

You can delete the DuckDNS subdomain or leave it — the app won’t run.

---

## Permanent domain (optional)

If you later want a real subdomain on a domain you own, use the steps below with `--domain roulette.yourdomain.com` instead of `install-temp.sh`.

## Architecture

```text
Internet -> nginx (port 80/443) -> Streamlit wheelo (127.0.0.1:8503)
```

Default port **8503** avoids clashes with other Streamlit apps on 8501/8502.

## 1. Upload project to VPS

```bash
sudo mkdir -p /var/www/wheelo
sudo chown $USER:$USER /var/www/wheelo
```

Option A — git (recommended):

```bash
cd /var/www
git clone https://github.com/davidZakaria/Wheelo.git wheelo
cd wheelo
```

Option B — copy from your PC (PowerShell):
```powershell
scp -r "E:\My Projects\Wheelo\*" user@YOUR_VPS_IP:/var/www/wheelo/
```

Required files on server:
- `app.py`, `roulette.py`, `filtering.py`, `contestants_loader.py`, `apify_fetch.py`
- `winners.csv`, `facebook_raw.csv`, `instagram_raw.csv`
- `requirements.txt`, `.streamlit/config.toml`
- `deploy/install.sh`

## 2. One-command install

SSH into the VPS:

```bash
cd /var/www/wheelo
chmod +x deploy/install.sh deploy/update.sh
sudo bash deploy/install.sh \
  --dir /var/www/wheelo \
  --port 8503 \
  --domain roulette.yourdomain.com \
  --apify-token "apify_api_YOUR_TOKEN" \
  --user YOUR_LINUX_USER
```

Replace:
- `roulette.yourdomain.com` with your subdomain
- `YOUR_LINUX_USER` with the Linux user that owns the app
- `apify_api_YOUR_TOKEN` with your Apify token (optional if you only use pre-loaded winners)

## 3. SSL (recommended)

```bash
sudo certbot --nginx -d roulette.yourdomain.com
```

## 4. Verify

```bash
sudo systemctl status wheelo
curl -I http://127.0.0.1:8503
```

Open in browser: `https://roulette.yourdomain.com`

## 5. Update after changes

```bash
bash /var/www/wheelo/deploy/update.sh /var/www/wheelo
```

## 6. Useful commands

| Command | Purpose |
|---|---|
| `sudo systemctl restart wheelo` | Restart app |
| `sudo journalctl -u wheelo -f` | Live logs |
| `sudo systemctl stop wheelo` | Stop app |

## 7. Firewall

Only expose nginx (80/443), not 8503 publicly:

```bash
sudo ufw allow 80
sudo ufw allow 443
```

## 8. If port 8503 is taken

Pick another free port (e.g. 8504) and pass `--port 8504` to `install.sh`, then update nginx `proxy_pass` to match.

Check used ports:
```bash
sudo ss -tlnp | grep -E '8501|8502|8503|8504'
```

## 9. Production notes

- `winners.csv` must exist before the draw; upload it to `/var/www/wheelo/`
- Apify scraping from the admin panel works if `APIFY_TOKEN` is set in `.streamlit/secrets.toml`
- For a one-time live event, you can skip Apify on the server and only upload `winners.csv`
- Streamlit holds websocket connections — nginx `proxy_read_timeout 86400` is already set

## 10. Minimal deploy (no Apify on server)

If you only need the roulette with existing finalists:

```bash
sudo bash deploy/install.sh --dir /var/www/wheelo --port 8503 --domain roulette.yourdomain.com --user YOUR_LINUX_USER
```

Ensure `winners.csv` is uploaded with all 23 contestants.
