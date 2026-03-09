# 🕵 OSINT Telegram Bot

Real OSINT intelligence gathering bot for Telegram.
Uses **only public open-source data** — no hacking, no illegal activity.

---

## ✅ What This Bot Does

| Command | Description | Sources |
|---|---|---|
| `/nick <username>` | Username search | WhatsMyName (500+ sites) + Sherlock DB |
| `/email <email>` | Email OSINT | EmailRep.io, Gravatar, HaveIBeenPwned, Hunter.io |
| `/domain <domain>` | Domain intelligence | WHOIS, DNS, crt.sh, HackerTarget, URLScan.io |
| `/ip <ip>` | IP geolocation & threats | ipinfo.io, ip-api.com, BGPView, AlienVault OTX, Shodan |
| `/social <username>` | Social network analysis | GitHub API, Reddit API, Twitter/X, Instagram, TikTok, Telegram, VK, Steam, YouTube |

---

## 🚀 Installation on VPS (Ubuntu/Debian)

### 1. System setup

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git -y
```

### 2. Clone / upload bot files

```bash
mkdir -p /opt/osint_bot
cd /opt/osint_bot
# Upload all bot files here
```

### 3. Virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
nano .env
# Set BOT_TOKEN=your_token_here
# Add optional API keys for more sources
```

### 5. Create bot with @BotFather

1. Open Telegram → search `@BotFather`
2. Send `/newbot`
3. Set name and username
4. Copy the token → paste into `.env`

### 6. Test run

```bash
source venv/bin/activate
python bot.py
```

### 7. Run as system service (always-on)

```bash
# Create dedicated user
sudo useradd -r -s /bin/false osintbot
sudo chown -R osintbot:osintbot /opt/osint_bot

# Install service
sudo cp osint_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable osint_bot
sudo systemctl start osint_bot

# Check status
sudo systemctl status osint_bot
sudo journalctl -u osint_bot -f
```

---

## 🔑 API Keys (All Optional)

Free sources work without any keys. Keys unlock additional data:

| Service | Free Tier | Link |
|---|---|---|
| HaveIBeenPwned | $3.50/month | https://haveibeenpwned.com/API/Key |
| Hunter.io | 25 req/month free | https://hunter.io |
| Shodan | Free + $49 lifetime | https://shodan.io |
| ipinfo.io | 50,000 req/month free | https://ipinfo.io |
| IntelX | Free tier | https://intelx.io |

---

## 🌐 Data Sources Used

### Free (No Key Required)
- **WhatsMyName** — 500+ site username database (GitHub: WebBreacher/WhatsMyName)
- **Sherlock** — Username enumeration DB (GitHub: sherlock-project/sherlock)
- **EmailRep.io** — Email reputation, breach info, profile detection
- **Gravatar** — Email → avatar/profile lookup (MD5 hash)
- **crt.sh** — Certificate Transparency logs, subdomain discovery
- **HackerTarget API** — WHOIS, DNS, subdomain scan, port scan, traceroute
- **ipinfo.io** — IP geolocation (50k/month free)
- **ip-api.com** — IP geo + ASN + proxy detection (free)
- **BGPView.io** — ASN/BGP routing data (free)
- **AlienVault OTX** — Threat intelligence (free)
- **URLScan.io** — Domain/URL scanning history (free)
- **Google DNS-over-HTTPS** — DNS record resolution (free)
- **GitHub API** — Public profile data (free, 60 req/hour unauthenticated)
- **Reddit API** — Public user profiles (free)
- **BreachDirectory** — Breach data lookup (free)
- **Telegram** — Public channel/user pages
- **VK** — Public profiles
- **Steam Community** — Public profiles

### Premium (Key Required)
- **HaveIBeenPwned** — Email breach database ($3.50/month)
- **Hunter.io** — Email verification + company data
- **Shodan** — Device/port/vulnerability scanning
- **IntelX** — Deep web + OSINT database

---

## ➕ Adding New OSINT Sources

### Add a new username check site

Edit `modules/sites_db.py`, add to `FALLBACK_SITES`:

```python
{"name": "NewSite", "uri_check": "https://newsite.com/user/{}", "e_code": 200, "e_string": ""},
```

### Add a new email check

In `modules/email_osint.py`, add a new method to `EmailOSINT` class:

```python
async def check_new_source(self, session, email) -> Dict:
    try:
        url = f"https://api.newsource.com/check?email={email}"
        async with session.get(url) as resp:
            data = await resp.json(content_type=None)
            return {"source": "NewSource", "status": "ok", "data": data}
    except Exception as e:
        return {"source": "NewSource", "status": "error", "error": str(e)}
```

Then add it to the `scan()` method's tasks list.

### Add a new social platform

In `modules/social_osint.py`, add a method:

```python
async def check_newplatform(self, session, username) -> Dict:
    url = f"https://newplatform.com/{username}"
    async with session.get(url) as resp:
        if resp.status == 200:
            return {"platform": "NewPlatform", "found": True, "url": url}
        return {"platform": "NewPlatform", "found": False}
```

---

## 🛡️ Legal & Ethical Notice

This bot:
- ✅ Uses only **public** OSINT sources
- ✅ Queries only **publicly accessible** data
- ✅ Does NOT access private accounts or databases
- ✅ Does NOT perform any unauthorized access
- ✅ Does NOT store or log target data
- ✅ Complies with OSINT community ethics

Intended for: security researchers, journalists, investigators, and personal privacy checks.

---

## 📁 Project Structure

```
osint_bot/
├── bot.py                    # Main entry point
├── config.py                 # Configuration & API keys
├── handlers.py               # Command router
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── osint_bot.service         # Systemd service file
├── commands/
│   ├── nick.py               # /nick handler
│   ├── email_cmd.py          # /email handler
│   ├── domain.py             # /domain handler
│   ├── ip_cmd.py             # /ip handler
│   ├── social.py             # /social handler
│   └── help_cmd.py           # /start /help handlers
├── modules/
│   ├── http_client.py        # Async HTTP client
│   ├── sites_db.py           # WhatsMyName + Sherlock DB fetcher
│   ├── username_scanner.py   # 500+ site username scanner
│   ├── email_osint.py        # Email intelligence
│   ├── domain_osint.py       # Domain intelligence
│   ├── ip_osint.py           # IP intelligence
│   ├── social_osint.py       # Social network checks
│   └── formatter.py          # Result formatting
├── data/
│   └── sites_cache.json      # Cached sites list (auto-generated)
└── logs/
    └── bot.log               # Log file (auto-generated)
```

---

## ⚙️ Configuration Options

In `config.py`:

```python
REQUEST_DELAY = 0.3      # Seconds between requests (lower = faster but more bans)
MAX_CONCURRENT = 30      # Parallel requests (increase for faster scanning)
REQUEST_TIMEOUT = 10     # Per-request timeout in seconds
```

### Proxy Support

Set in `.env`:
```
PROXY_URL=socks5://user:pass@proxy-host:1080
```

Supports: SOCKS4, SOCKS5, HTTP proxies.

---

## 📊 Performance

- Username scan: ~500 sites in 60-120 seconds (depends on network)
- Email scan: ~10-15 seconds
- Domain scan: ~20-30 seconds  
- IP scan: ~10-15 seconds
- Social scan: ~10-15 seconds

To increase speed: raise `MAX_CONCURRENT` and lower `REQUEST_DELAY`.
