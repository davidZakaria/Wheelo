# Live Green Avenue Property Drawing

A Streamlit app that fetches Facebook and Instagram comments via Apify, filters correct score guesses, and runs a random winner draw.

## Setup

1. Install Python 3.10+ from [python.org](https://www.python.org/downloads/) (check "Add to PATH").

2. Install dependencies:

```powershell
cd "E:\My Projects\Wheelo"
py -m pip install -r requirements.txt
```

3. Configure your Apify API token:

```powershell
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Edit `.streamlit/secrets.toml` and replace the placeholder with your token from [Apify Integrations](https://console.apify.com/account/integrations).

Alternatively, set the `APIFY_TOKEN` environment variable.

## Run

```powershell
py -m streamlit run app.py
```

The app opens on a cinematic **live roulette** experience:
1. Review the 23 finalists with Facebook / Instagram avatars
2. Click **Launch Suspense Roulette**
3. Press **Spin the Wheel** inside the arena for a 7-second suspenseful spin
4. Watch the winner reveal with confetti and profile link

Admin scraping tools are tucked inside **Admin · Scrape & Filter Comments**.

## Usage

1. Enter the Egypt and Argentina scores (defaults: 2 and 1).
2. Paste Facebook and/or Instagram post URLs, or upload a CSV/Excel file with `username` and `comment` columns.
3. Click **Download & Process Comments** — Apify scrapes can take 3–7 minutes for large posts (~27k comments). Do not refresh the tab while scraping.
4. Click **SPIN THE WHEEL** to pick a random winner from correct entries.

## CSV Upload Format

Your file must have `username` and `comment` columns. Common aliases are also accepted:

| Accepted aliases | Maps to |
|---|---|
| `text`, `comment_text` | `comment` |
| `profileName`, `ownerUsername`, `user` | `username` |

## Apify Cost

Large scrapes (~27k comments) cost roughly $0.50–$1.00 in Apify compute credits. New accounts receive $5/month free.

## Smoke Test

Before a full scrape, test with a small limit by temporarily lowering `max_comments` in the URL inputs section, or use CSV upload only to verify filtering and the wheel.

## VPS Deployment (KVM2)

See [deploy/DEPLOY.md](deploy/DEPLOY.md) for full instructions.

### Temporary domain (for the live draw)

**Repo:** https://github.com/davidZakaria/Wheelo

On your Hostinger VPS:

```bash
git clone https://github.com/davidZakaria/Wheelo.git /var/www/wheelo
cd /var/www/wheelo
chmod +x deploy/install-temp.sh

sudo bash deploy/install-temp.sh --vps-ip 72.61.192.84 --user root
# → http://72-61-192-84.nip.io
```

See [deploy/HOSTINGER.md](deploy/HOSTINGER.md) for full Hostinger steps.
