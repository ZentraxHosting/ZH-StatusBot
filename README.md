# 🤖 Setup Guide — Zentrax Hosting Status Bot

### 📌 1. Clone the Repository

```bash
git clone https://github.com/ZentraxHosting/ZH-ProxyBot.git
cd repository
```

Or download the zip file from [here](https://github.com/ZentraxHosting/ZH-ProxyBot/archive/refs/heads/main.zip)

### 📦 2. Install Dependencies

Make sure you have **Python** installed.

```bash
pip install -r requirements.txt
```

### 🔑 3. Discord Developer Setup

1. Go to Discord Developer Portal
2. Create a new application
3. Go to **Bot → Add Bot**
4. Copy your bot token

⚠️ Never share your bot token publicly.

### ⚙️ 4. Environment Configuration

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add:

```env
DISCORD_TOKEN=what_you_got_from_step_3
CHANNEL_ID=channel_you_want_embed
PTERO_TOKEN=application_api_token
PTERO_URL=pterodactyl_url *ex: panel.example.com*
PING_USER_ID=user_you_want_pinged_when_things_go_don
```

### 5. Hardcoded Configuration

Naviage to `bot.py`:

Go to lines 40-55 which have the following

```
ONLINE_EMOJI  = "<:online:1461143135857148015>"
OFFLINE_EMOJI = "<:offline:1461143131151138816>"

TITLE_EMOJI = "<:hi:1461145636274438329>"
FIELD_EMOJI = "<:hi:1461142744759144458>"
TOTAL_EMOJI = "<:hi:1464850186890121321>"
INFO_EMOJI  = "<:hi:1464849047922806875>"

STATUS_PAGE_URL = "https://status.bigboner.fun" - Needs changed 
PANEL_URL = "https://panel.bigboner.fun" - Needs changed
DASH_URL  = "https://dash.bigboner.fun" - Needs changed

FEATURED_NODES = ["UK1", "CA1"]     # must match node names in Pterodactyl
SERVERS_REFRESH_SECONDS = 60
CHECK_INTERVAL_SECONDS = 15
MAX_NODE_LINES = 25
```

and customize them to fit your needs!

### 🚀 6. Run the Bot

```bash
python bot.py
```

### 🔗 7. Invite Bot to Server

Replace `YOUR_CLIENT_ID`:

```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=8&scope=bot%20applications.commands
```

### 🧪 8. Test Bot

* Make sure bot is online
* Try checking the channel you set!
  
### ⚠️ 9. Issues

I currently know of **ZERO** issues with the code, if you find any issues please let me know by going [here](https://github.com/ZentraxHosting/ZH-StatusBot/issues) and creating a new issue or reaching out to me with the following

Email: [owen@puds.lol](mailto:owen@puds.lol)
Discord: ac1q
