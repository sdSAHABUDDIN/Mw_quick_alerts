# Microworkers Job Alert Bot 🤖

Polls Microworkers every 15 seconds and instantly sends new job alerts to your Telegram.

No database needed. No Firebase. Just Python + Telegram.

---

## Files

| File | Purpose |
|---|---|
| `scraper.py` | Main loop — polls Microworkers, detects new jobs |
| `notifier.py` | Sends the Telegram message |
| `parser.py` | Parses the jobs.php HTML into job dicts |
| `auth.py` | Handles the PHPSESSID cookie session |
| `detect_category.py` | Categorizes jobs (Email, YouTube, etc.) |
| `config.py` | All settings — reads from `.env` |
| `.env.example` | Template for your secrets |

---

## Step 1 — Create your Telegram Bot

1. Open Telegram → search **@BotFather**
2. Send `/newbot`
3. Give it a name (e.g. `MW Job Alerts`) and a username (e.g. `mw_jobs_bot`)
4. Copy the **token** it gives you (looks like `123456:ABCdef...`)

---

## Step 2 — Get your Chat ID

**Option A — Personal alerts (messages come to you):**
1. Search **@userinfobot** on Telegram
2. Send `/start`
3. Copy the number next to "Id:" — that's your `TELEGRAM_CHAT_ID`
4. Start a chat with your bot (search its username, press Start)

**Option B — Channel (broadcast to subscribers):**
1. Create a channel in Telegram
2. Add your bot as an **admin** with "Post Messages" permission
3. Send any message to the channel
4. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
5. Find `"chat":{"id":` in the response — copy that number (will be negative, e.g. `-1001234567890`)

---

## Step 3 — Setup locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create your .env file
cp .env.example .env

# 3. Edit .env with your real values
nano .env   # or open in any editor

# 4. Run it
python scraper.py
```

The bot runs the first scan silently (to learn what jobs already exist),
then alerts you only for genuinely new jobs from that point on.

---

## Step 4 — Deploy 24/7

### Option A: Oracle Cloud Free Tier ⭐ (Best — completely free forever)

Oracle gives you a **free ARM Ubuntu VM** with 4 CPUs and 24 GB RAM — more than enough.

1. Sign up at [cloud.oracle.com](https://cloud.oracle.com) (needs a credit card for verification, not charged)
2. Create an instance: Compute → Instances → Create Instance
   - Shape: `VM.Standard.A1.Flex` (ARM, free tier)
   - OS: Ubuntu 22.04
3. SSH into your VM and run:

```bash
sudo apt update && sudo apt install python3-pip python3-venv git -y

# Upload your project files (or git clone if you pushed to GitHub)
scp -r ./MW_Telegram_Bot ubuntu@<your-vm-ip>:~/

cd ~/MW_Telegram_Bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env   # fill in your values
```

4. Create a **systemd service** so it auto-restarts if it crashes:

```bash
sudo nano /etc/systemd/system/mw-bot.service
```

Paste this (replace YOUR_USERNAME):

```ini
[Unit]
Description=Microworkers Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/MW_Telegram_Bot
ExecStart=/home/ubuntu/MW_Telegram_Bot/venv/bin/python scraper.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable mw-bot
sudo systemctl start mw-bot

# Check it's running:
sudo systemctl status mw-bot

# Watch live logs:
sudo journalctl -u mw-bot -f
```

---

### Option B: Railway.app (Easiest — $5 free credit/month)

1. Push your project to a **GitHub repo** (private is fine)
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo
4. Go to **Variables** tab and add:
   - `MW_PHPSESSID` = your cookie value
   - `TELEGRAM_BOT_TOKEN` = your bot token
   - `TELEGRAM_CHAT_ID` = your chat id
5. Add a `Procfile` in your project root:
   ```
   worker: python scraper.py
   ```
6. Deploy — Railway runs it 24/7 automatically

**Note:** Railway's free tier gives $5/month credit. This bot uses barely any compute, so it runs essentially free.

---

### Option C: VPS with screen (Quick & dirty)

If you already have any Ubuntu VPS ($4–6/month from DigitalOcean, Vultr, etc.):

```bash
# Install screen to keep it running after you disconnect
sudo apt install screen -y

screen -S mwbot
source venv/bin/activate
python scraper.py

# Detach with: Ctrl+A then D
# Reattach later with: screen -r mwbot
```

**Downside:** If the VPS reboots, you must manually restart. Use the systemd option instead.

---

## Refreshing the MW Session Cookie

The `PHPSESSID` cookie expires every 1–7 days. When it does, the bot logs:
```
✗ Session expired mid-run! Update PHPSESSID in .env and restart.
```

To fix:
1. Log into microworkers.com in Chrome
2. DevTools (F12) → Application → Cookies → www.microworkers.com
3. Copy the new `PHPSESSID` value
4. Update your `.env` file
5. Restart the bot: `sudo systemctl restart mw-bot`

---

## Adjusting settings

Edit `config.py`:

```python
CHECK_INTERVAL = 15   # How often to scan (seconds). Don't go below 10.
MIN_PAY        = 0.10 # Skip jobs paying less than this (USD)
```

---

## Do I need a database?

**No.** The bot tracks seen jobs in memory (`seen_ids` set). On every startup it does one silent scan to load existing jobs, then only alerts on new ones. No Redis, no SQLite, no Firebase needed.

The only downside: if the server reboots mid-day, the very first scan after restart will silently absorb current jobs (no alerts), then resume normally. This is intentional — it prevents you getting 50 old-job alerts every time the bot restarts.
