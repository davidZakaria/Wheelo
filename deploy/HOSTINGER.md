# Hostinger KVM2 — Wheelo deploy

Your server: **root@72.61.192.84** (KVM2, 2 existing projects)

Wheelo becomes a **third nginx site** on port 80 — it does not replace your other apps.

## Temporary URL (no DNS changes in Hostinger)

After install, share:

```text
http://72-61-192-84.nip.io
```

nip.io resolves to your VPS IP automatically. No hPanel DNS setup.

---

## Option A — Use a subdomain on a domain you already have on Hostinger

If your other two projects use a domain managed in Hostinger:

1. **hPanel** → **Domains** → your domain → **DNS / DNS Zone**
2. Add an **A record**:
   - **Name:** `wheelo` (or `draw`, `roulette`)
   - **Points to:** `72.61.192.84`
   - **TTL:** 300 (or default)
3. Wait 5–15 minutes, then install with that hostname:

```bash
sudo bash deploy/install-temp.sh --domain wheelo.yourdomain.com --user root
sudo certbot --nginx -d wheelo.yourdomain.com
```

This is often the best option on Hostinger — HTTPS works and the link looks professional.

---

## Option B — DuckDNS (free, not in Hostinger)

1. [duckdns.org](https://www.duckdns.org) → create `wheelo-greenavenue`
2. IP: `72.61.192.84`
3. On VPS:

```bash
sudo bash deploy/install-temp.sh --domain wheelo-greenavenue.duckdns.org --user root
sudo certbot --nginx -d wheelo-greenavenue.duckdns.org
```

---

## Full install (from your Windows PC)

### 1. Clone from GitHub (recommended)

```bash
ssh root@72.61.192.84
sudo mkdir -p /var/www
cd /var/www
git clone https://github.com/davidZakaria/Wheelo.git wheelo
cd wheelo
```

Or re-pull on an existing clone:

```bash
cd /var/www/wheelo
git pull
```

### 1b. Upload files manually (alternative)

```powershell
ssh root@72.61.192.84 "mkdir -p /var/www/wheelo"
scp -r "E:\My Projects\Wheelo\*" root@72.61.192.84:/var/www/wheelo/
```

Or use **Hostinger hPanel → VPS → Browser terminal** if SCP is awkward.

### 2. SSH in

```powershell
ssh root@72.61.192.84
```

Or: **hPanel → VPS → SSH access / Browser terminal**

### 3. Install (nip.io temp URL)

```bash
cd /var/www/wheelo
chmod +x deploy/*.sh
bash deploy/check.sh

bash deploy/install-temp.sh --vps-ip 72.61.192.84 --user root
```

### 4. Firewall (Hostinger KVM — UFW on the server)

```bash
sudo ufw status
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
# or: sudo ufw allow 80 && sudo ufw allow 443
```

Do **not** expose port 8503 publicly — only nginx (80/443).

### 5. Verify

```bash
sudo systemctl status wheelo
sudo nginx -t
curl -I http://127.0.0.1:8503
```

Browser: **http://72-61-192-84.nip.io**

---

## Coexisting with your 2 other projects

| Item | Wheelo | Your other sites |
|---|---|---|
| nginx config | `/etc/nginx/sites-available/wheelo` | unchanged |
| App port | `127.0.0.1:8503` | their own ports |
| systemd service | `wheelo` | their own services |
| Public URL | nip.io / subdomain / DuckDNS | existing domains |

Check ports in use before install:

```bash
sudo ss -tlnp | grep -E '8501|8502|8503|80|443'
```

If 8503 is taken:

```bash
bash deploy/install-temp.sh --vps-ip 72.61.192.84 --port 8504 --user root
```

---

## Troubleshooting on Hostinger

**502 Bad Gateway**
```bash
sudo systemctl restart wheelo
sudo journalctl -u wheelo -n 50
```

**Site not loading externally**
- UFW: `sudo ufw allow 80`
- nginx: `sudo nginx -t && sudo systemctl reload nginx`
- Confirm IP in hPanel VPS overview is still `72.61.192.84`

**Certbot fails**
- DNS A record must point to `72.61.192.84` first
- nip.io + Let's Encrypt is unreliable — use a real subdomain or DuckDNS for HTTPS

**After the draw — disable Wheelo only**
```bash
sudo systemctl stop wheelo
sudo rm /etc/nginx/sites-enabled/wheelo
sudo systemctl reload nginx
```

Your other two projects keep running.

---

## Apify token (optional)

Only needed if you scrape from the server admin panel. For the live draw with existing `winners.csv`, skip it:

```bash
bash deploy/install-temp.sh --vps-ip 72.61.192.84 --user root
```

To add scraping later, edit `/var/www/wheelo/.streamlit/secrets.toml`:

```toml
APIFY_TOKEN = "apify_api_xxx"
```

Then: `sudo systemctl restart wheelo`
