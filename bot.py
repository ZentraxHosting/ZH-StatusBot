# BonerHost Node Status
# © 2026 BonerHost
# https://status.bigboner.fun

from interactions import (
    Client, Intents, listen, Task, IntervalTrigger, Embed,
    ActionRow, Button, ButtonStyle
)
from datetime import datetime, timezone
import requests, os, colorama, time, urllib3
from dotenv import load_dotenv

load_dot	env()

urllib3.disable_warnings()
colorama.init(autoreset=False)

_log = lambda lvl, col, txt: print(
    f"{colorama.Style.DIM}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{colorama.Style.RESET_ALL} "
    f"{col}[{lvl}]{colorama.Style.RESET_ALL} {txt}"
)
info    = lambda txt: _log("INFO", colorama.Fore.CYAN, txt)
success = lambda txt: _log("OK", colorama.Fore.GREEN, txt)
warn    = lambda txt: _log("WARN", colorama.Fore.YELLOW, txt)
alert   = lambda txt: _log("ALERT", colorama.Fore.RED + colorama.Style.BRIGHT, txt)


STORE = {}

def get_db(db_ignored, key: str, default=None):
    return STORE.get(key, default)

def set_db(db_ignored, key: str, value):
    STORE[key] = value

def ensure_counter(db_ignored, key: str):
    if key not in STORE:
        STORE[key] = 0

ONLINE_EMOJI  = "<:online:1461143135857148015>"
OFFLINE_EMOJI = "<:offline:1461143131151138816>"

TITLE_EMOJI = "<:hi:1461145636274438329>"
FIELD_EMOJI = "<:hi:1461142744759144458>"
TOTAL_EMOJI = "<:hi:1464850186890121321>"
INFO_EMOJI  = "<:hi:1464849047922806875>"

STATUS_PAGE_URL = "https://status.bigboner.fun"
PANEL_URL = "https://panel.bigboner.fun"
DASH_URL  = "https://dash.bigboner.fun"

FEATURED_NODES = ["UK1", "CA1"]     # must match node names in Pterodactyl
SERVERS_REFRESH_SECONDS = 60
CHECK_INTERVAL_SECONDS = 15
MAX_NODE_LINES = 25

def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"""{colorama.Fore.GREEN}
╔════════════════════════════════════════════════════╗
║   BonerHost Node Status                            ║
║   https://status.bigboner.fun                      ║
║   © 2026 BonerHost                                 ║
╚════════════════════════════════════════════════════╝
""")

def add_spacer(embed_obj: Embed):
    embed_obj.add_field(name="\u200b", value="\u200b", inline=True)

def format_duration(seconds: int) -> str:
    seconds = int(max(0, seconds))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days: parts.append(f"{days}d")
    if hours or days: parts.append(f"{hours}h")
    if minutes or hours or days: parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)

def fmt_ts(ts: float) -> str:
    if not ts:
        return "N/A"
    u = int(ts)
    return f"<t:{u}:F>"

def fmt_rel(ts: float) -> str:
    if not ts:
        return "N/A"
    u = int(ts)
    return f"<t:{u}:R>"

def timed_get(url: str, timeout: int = 4, verify: bool = False, allow_redirects: bool = True):
    start = time.perf_counter()
    try:
        r = requests.get(url, timeout=timeout, verify=verify, allow_redirects=allow_redirects)
        ms = int((time.perf_counter() - start) * 1000)
        return True, r.status_code, ms
    except:
        return False, None, None

def check_url_status_latency(url: str, timeout: int = 4):
    ok, code, ms = timed_get(url, timeout=timeout, verify=False, allow_redirects=True)
    if not ok or code is None:
        return "DOWN", None
    return ("UP" if code < 500 else "DOWN"), ms

class Pterodactyl:
    def __init__(self, url: str, token: str):
        self.url = url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}"}

    def get_nodes(self):
        r = requests.get(
            f"{self.url}/api/application/nodes",
            headers=self.headers,
            params={"per_page": 100},
            timeout=15
        )
        if r.status_code != 200:
            raise Exception(f"Error getting nodes: {r.status_code} - {r.text[:200]}")
        return r.json().get("data", [])

    def get_servers_page(self, page: int = 1, per_page: int = 100):
        r = requests.get(
            f"{self.url}/api/application/servers",
            headers=self.headers,
            params={"per_page": per_page, "page": page},
            timeout=20
        )
        if r.status_code != 200:
            raise Exception(f"Error getting servers: {r.status_code} - {r.text[:200]}")
        return r.json()

    def count_servers_by_node_ids(self, wanted_node_ids: set, per_page: int = 100, max_pages: int = 50) -> dict:
        counts = {nid: 0 for nid in wanted_node_ids}

        j1 = self.get_servers_page(page=1, per_page=per_page)
        data = j1.get("data", [])

        meta = (j1.get("meta") or {}).get("pagination") or {}
        total_pages = meta.get("total_pages", 1)
        try:
            total_pages = int(total_pages)
        except:
            total_pages = 1
        total_pages = max(1, min(total_pages, max_pages))

        def handle(items):
            for it in items:
                a = it.get("attributes") or {}
                nid = a.get("node")
                if nid in counts:
                    counts[nid] += 1

        handle(data)
        for p in range(2, total_pages + 1):
            jp = self.get_servers_page(page=p, per_page=per_page)
            handle(jp.get("data", []))

        return counts

banner()
time.sleep(1)
info("Initializing...")

db = None

bot = Client(intents=Intents.DEFAULT)
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
PTERO_TOKEN = os.getenv("PTERO_TOKEN")
PTERO_URL = os.getenv("PTERO_URL")
PING_USER_ID = (os.getenv("PING_USER_ID") or "").strip()

if not TOKEN or not CHANNEL_ID or not PTERO_TOKEN or not PTERO_URL:
    alert("Missing env config. Set DISCORD_TOKEN, CHANNEL_ID, PTERO_TOKEN, PTERO_URL in Startup/.env")
    while True:
        time.sleep(60)

if PING_USER_ID and not PING_USER_ID.isdigit():
    warn("PING_USER_ID is not numeric; falling back to @here.")
    PING_USER_ID = ""

set_db(db, "ping_user_id", PING_USER_ID)

ptero = Pterodactyl(PTERO_URL, PTERO_TOKEN)

# Counters
ensure_counter(db, "last_check_ts")
ensure_counter(db, "panel_uptime"); ensure_counter(db, "panel_downtime")
ensure_counter(db, "dash_uptime");  ensure_counter(db, "dash_downtime")
ensure_counter(db, "uk1_uptime");   ensure_counter(db, "uk1_downtime")
ensure_counter(db, "ca1_uptime");   ensure_counter(db, "ca1_downtime")

# Track downtime start for each key (for "down so far" in alert)
ensure_counter(db, "uk1_down_start_ts")
ensure_counter(db, "ca1_down_start_ts")
ensure_counter(db, "panel_down_start_ts")
ensure_counter(db, "dash_down_start_ts")

for k in ["uk1", "ca1", "panel", "dash"]:
    if get_db(db, f"alert_msg_{k}") is None:
        set_db(db, f"alert_msg_{k}", "")

CACHED_NODES = []  # [{name,fqdn,port,status,previous_status,latency_ms}]
SERVICE_STATUS = {"panel": "DOWN", "dash": "DOWN"}
SERVICE_LAT_MS = {"panel": None, "dash": None}

NODE_ID_BY_NAME = {}
WANTED_NODE_IDS = set()
SERVER_COUNTS = {n: 0 for n in FEATURED_NODES}
LAST_SERVERS_REFRESH_TS = 0.0

def make_buttons():
    return [
        ActionRow(
            Button(style=ButtonStyle.LINK, label="Open Status Page", url=STATUS_PAGE_URL),
            Button(style=ButtonStyle.LINK, label="Open Panel", url=PANEL_URL),
            Button(style=ButtonStyle.LINK, label="Open Dash", url=DASH_URL),
        )
    ]

def refresh_server_counts(force=False):
    global LAST_SERVERS_REFRESH_TS, SERVER_COUNTS
    now = time.time()
    if (not force) and ((now - LAST_SERVERS_REFRESH_TS) < SERVERS_REFRESH_SECONDS):
        return

    if not WANTED_NODE_IDS:
        SERVER_COUNTS = {n: 0 for n in FEATURED_NODES}
        LAST_SERVERS_REFRESH_TS = now
        return

    try:
        counts_by_id = ptero.count_servers_by_node_ids(WANTED_NODE_IDS, per_page=100, max_pages=50)
        out = {n: 0 for n in FEATURED_NODES}
        for name in FEATURED_NODES:
            nid = NODE_ID_BY_NAME.get(name)
            if nid in counts_by_id:
                out[name] = counts_by_id[nid]
        SERVER_COUNTS = out
    except Exception as e:
        warn(f"Failed to refresh server counts: {e}")

    LAST_SERVERS_REFRESH_TS = now

def find_cached_node(name: str):
    for n in CACHED_NODES:
        if str(n.get("name", "")).lower() == str(name).lower():
            return n
    return None

def node_status_block(node):
    st = node.get("status", "DOWN")
    em = ONLINE_EMOJI if st == "UP" else OFFLINE_EMOJI
    lat = node.get("latency_ms")
    lat_txt = f"{lat}ms" if isinstance(lat, int) else "N/A"
    return f"{em} **{st}**\n`{node['fqdn']}:{node['port']}`\n**Latency:** {lat_txt}"

def build_main_embed():
    refresh_server_counts(force=False)

    uk1 = find_cached_node("UK1")
    ca1 = find_cached_node("CA1")

    panel_status = SERVICE_STATUS["panel"]
    dash_status = SERVICE_STATUS["dash"]

    other_lines = []
    down_count = 0
    for n in CACHED_NODES:
        if str(n["name"]).lower() in {"uk1", "uk2"}:
            continue
        st = n.get("status", "DOWN")
        em = ONLINE_EMOJI if st == "UP" else OFFLINE_EMOJI
        if st != "UP":
            down_count += 1
        other_lines.append(f"{em} **{n['name']}** (`{n['fqdn']}:{n['port']}`) → **{st}**")
        if len(other_lines) >= MAX_NODE_LINES:
            break

    if (uk1 is None) or uk1.get("status") != "UP": down_count += 1
    if (ca1 is None) or ca1.get("status") != "UP": down_count += 1
    if panel_status != "UP": down_count += 1
    if dash_status != "UP": down_count += 1

    all_ok = (down_count == 0 and len(CACHED_NODES) > 0)
    color = 0x57F287 if all_ok else 0xED4245

    e = Embed(
        title=f"{TITLE_EMOJI} Status",
        description="\n".join(other_lines) if other_lines else "No non-featured nodes found.",
        color=color,
        timestamp=datetime.now(timezone.utc)
    )

    e.add_field(name=f"{FIELD_EMOJI} UK1", value=node_status_block(uk1) if uk1 else f"{OFFLINE_EMOJI} **UNKNOWN**\n`Not found`", inline=True)
    e.add_field(name=f"{FIELD_EMOJI} CA1", value=node_status_block(ca1) if ca1 else f"{OFFLINE_EMOJI} **UNKNOWN**\n`Not found`", inline=True)
    add_spacer(e)

    uk1_up = int(get_db(db, "uk1_uptime", 0) or 0); uk1_down = int(get_db(db, "uk1_downtime", 0) or 0)
    ca1_up = int(get_db(db, "ca1_uptime", 0) or 0); ca1_down = int(get_db(db, "ca1_downtime", 0) or 0)

    e.add_field(
        name=f"{TOTAL_EMOJI} UK1 Total",
        value=f"**Servers:** {SERVER_COUNTS.get('UK1', 0)}\n**Downtime:** {format_duration(uk1_down)}\n**Uptime:** {format_duration(uk1_up)}",
        inline=True
    )

    e.add_field(
        name=f"{TOTAL_EMOJI} CA1 Total",
        value=f"**Servers:** {SERVER_COUNTS.get('CA1', 0)}\n"
              f"**Downtime:** {format_duration(ca1_down)}\n"
              f"**Uptime:** {format_duration(ca1_up)}",
        inline=True
    )

    add_spacer(e)

    panel_em = ONLINE_EMOJI if panel_status == "UP" else OFFLINE_EMOJI
    dash_em = ONLINE_EMOJI if dash_status == "UP" else OFFLINE_EMOJI
    panel_lat = f"{SERVICE_LAT_MS['panel']}ms" if isinstance(SERVICE_LAT_MS["panel"], int) else "N/A"
    dash_lat  = f"{SERVICE_LAT_MS['dash']}ms" if isinstance(SERVICE_LAT_MS["dash"], int) else "N/A"

    e.add_field(name=f"{FIELD_EMOJI} Panel", value=f"{panel_em} **{panel_status}**\n{PANEL_URL}\n**Latency:** {panel_lat}", inline=True)
    e.add_field(name=f"{FIELD_EMOJI} Dash", value=f"{dash_em} **{dash_status}**\n{DASH_URL}\n**Latency:** {dash_lat}", inline=True)
    add_spacer(e)

    panel_up = int(get_db(db, "panel_uptime", 0) or 0); panel_down = int(get_db(db, "panel_downtime", 0) or 0)
    dash_up  = int(get_db(db, "dash_uptime", 0) or 0);  dash_down  = int(get_db(db, "dash_downtime", 0) or 0)

    e.add_field(name=f"{TOTAL_EMOJI} Panel Total", value=f"**Downtime:** {format_duration(panel_down)}\n**Uptime:** {format_duration(panel_up)}", inline=True)
    e.add_field(name=f"{TOTAL_EMOJI} Dash Total", value=f"**Downtime:** {format_duration(dash_down)}\n**Uptime:** {format_duration(dash_up)}", inline=True)
    add_spacer(e)

    e.add_field(name=f"{INFO_EMOJI} For accurate status", value=STATUS_PAGE_URL, inline=False)
    e.set_footer(text=f"BonerHosting Status • {down_count} down")
    return e

def build_offline_alert_embed(title: str, status: str, endpoint: str, down_since_ts: float, last_check_ts: float, latency_ms):
    em = OFFLINE_EMOJI if status == "DOWN" else ONLINE_EMOJI
    lat_txt = f"{latency_ms}ms" if isinstance(latency_ms, int) else "N/A"
    down_for = format_duration(int(max(0, time.time() - down_since_ts))) if down_since_ts else "N/A"

    e = Embed(
        title=f"{em} {title} is OFFLINE",
        description=f"Endpoint: `{endpoint}`",
        color=0xED4245,
        timestamp=datetime.now(timezone.utc)
    )
    e.add_field(name="Detected At", value=fmt_ts(down_since_ts), inline=True)
    e.add_field(name="Last Check", value=f"{fmt_ts(last_check_ts)}\n({fmt_rel(last_check_ts)})", inline=True)
    add_spacer(e)
    e.add_field(name="Retry Interval", value=f"{CHECK_INTERVAL_SECONDS}s", inline=True)
    e.add_field(name="Down For (so far)", value=down_for, inline=True)
    add_spacer(e)
    e.add_field(name="Latency", value=lat_txt, inline=True)
    e.add_field(name="Auto-clear", value="This alert will be deleted when service is back online.", inline=True)
    return e

async def send_offline_alert(channel, key: str, title: str, endpoint: str, latency_ms):
    ping_id = str(get_db(db, "ping_user_id", "") or "").strip()
    ping_text = f"<@{ping_id}>" if ping_id.isdigit() else "@here"

    down_start_key = f"{key}_down_start_ts"
    if float(get_db(db, down_start_key, 0) or 0) <= 0:
        set_db(db, down_start_key, time.time())

    down_since = float(get_db(db, down_start_key, 0) or 0)
    last_check = float(get_db(db, "last_check_ts", 0) or 0)

    embed = build_offline_alert_embed(
        title=title,
        status="DOWN",
        endpoint=endpoint,
        down_since_ts=down_since,
        last_check_ts=last_check,
        latency_ms=latency_ms
    )

    msg = await channel.send(content=ping_text, embeds=[embed])
    set_db(db, f"alert_msg_{key}", str(msg.id))

async def clear_offline_alert(channel, key: str):
    mid = str(get_db(db, f"alert_msg_{key}", "") or "").strip()
    if not mid:
        return
    try:
        msg = await channel.fetch_message(int(mid))
        await msg.delete()
    except Exception as e:
        warn(f"Couldn't delete alert message for {key}: {e}")

    set_db(db, f"alert_msg_{key}", "")
    set_db(db, f"{key}_down_start_ts", 0)

# ---- NEW: find existing status message on restart ----
async def find_existing_status_message(channel):
    """
    Scan recent messages and find the bot's old status embed message id.
    If this fails (permissions / API differences), we just create a new one once.
    """
    try:
        # interactions.py versions vary; history may or may not exist.
        # Keep this safe.
        async for msg in channel.history(limit=50):
            try:
                if msg.author and msg.author.id != bot.user.id:
                    continue
                if not msg.embeds:
                    continue
                emb = msg.embeds[0]
                if emb and emb.title and "Status" in str(emb.title):
                    return str(msg.id)
            except:
                continue
    except Exception as e:
        warn(f"Couldn't scan history for status message: {e}")
    return None

async def upsert_main_message(channel, embed: Embed):
    msg_id = get_db(db, "status_message_id", None)
    components = make_buttons()

    if msg_id:
        try:
            msg = await channel.fetch_message(int(msg_id))
            await msg.edit(embeds=[embed], components=components)
            return
        except Exception as e:
            warn(f"Couldn't edit stored status message (will recreate): {e}")

    sent = await channel.send(embeds=[embed], components=components)
    set_db(db, "status_message_id", str(sent.id))
    success(f"Created new status message: {sent.id}")

@Task.create(IntervalTrigger(seconds=CHECK_INTERVAL_SECONDS))
async def bg_check():
    now_ts = time.time()
    last_ts = float(get_db(db, "last_check_ts", 0) or 0)
    if last_ts <= 0:
        set_db(db, "last_check_ts", now_ts)
        last_ts = now_ts

    delta = now_ts - last_ts
    if delta < 0 or delta > 120:
        delta = 0
    delta_i = int(delta)

    channel = await bot.fetch_channel(CHANNEL_ID)

    prev_panel = SERVICE_STATUS["panel"]
    prev_dash = SERVICE_STATUS["dash"]

    panel_status, panel_ms = check_url_status_latency(PANEL_URL, timeout=4)
    dash_status, dash_ms = check_url_status_latency(DASH_URL, timeout=4)

    SERVICE_STATUS["panel"] = panel_status
    SERVICE_STATUS["dash"] = dash_status
    SERVICE_LAT_MS["panel"] = panel_ms
    SERVICE_LAT_MS["dash"] = dash_ms

    if delta_i > 0:
        if prev_panel == "UP":
            set_db(db, "panel_uptime", int(get_db(db, "panel_uptime", 0) or 0) + delta_i)
        else:
            set_db(db, "panel_downtime", int(get_db(db, "panel_downtime", 0) or 0) + delta_i)

        if prev_dash == "UP":
            set_db(db, "dash_uptime", int(get_db(db, "dash_uptime", 0) or 0) + delta_i)
        else:
            set_db(db, "dash_downtime", int(get_db(db, "dash_downtime", 0) or 0) + delta_i)

    if panel_status == "DOWN" and prev_panel != "DOWN":
        await send_offline_alert(channel, "panel", "Panel", PANEL_URL, panel_ms)
    if panel_status == "UP" and prev_panel == "DOWN":
        await clear_offline_alert(channel, "panel")

    if dash_status == "DOWN" and prev_dash != "DOWN":
        await send_offline_alert(channel, "dash", "Dash", DASH_URL, dash_ms)
    if dash_status == "UP" and prev_dash == "DOWN":
        await clear_offline_alert(channel, "dash")

    for node in CACHED_NODES:
        name = node["name"]
        prev_status = node.get("status", "DOWN")

        current_status = "DOWN"
        latency_ms = None
        fqdn, port = node["fqdn"], node["port"]

        for scheme in ["https", "http"]:
            ok, code, ms = timed_get(f"{scheme}://{fqdn}:{port}", timeout=3, verify=False, allow_redirects=True)
            if ok and code is not None:
                latency_ms = ms
                current_status = "UP" if code < 500 else "DOWN"
                break

        node["latency_ms"] = latency_ms
        node["status"] = current_status
        node["previous_status"] = prev_status

        lname = str(name).lower()
        if delta_i > 0 and lname in {"uk1", "ca1"}:
            if prev_status == "UP":
                set_db(db, f"{lname}_uptime", int(get_db(db, f"{lname}_uptime", 0) or 0) + delta_i)
            else:
                set_db(db, f"{lname}_downtime", int(get_db(db, f"{lname}_downtime", 0) or 0) + delta_i)

            if current_status == "DOWN" and prev_status != "DOWN":
                await send_offline_alert(channel, lname, lname.upper(), f"{fqdn}:{port}", latency_ms)
            if current_status == "UP" and prev_status == "DOWN":
                await clear_offline_alert(channel, lname)

    set_db(db, "last_check_ts", now_ts)
    refresh_server_counts(force=False)

    await upsert_main_message(channel, build_main_embed())

@listen()
async def on_ready():
    info(f"{colorama.Fore.GREEN}Logged in!{colorama.Style.RESET_ALL}")

    try:
        nd_data = ptero.get_nodes()
    except Exception as e:
        alert(f"Failed to fetch nodes from Pterodactyl: {e}")
        return

    CACHED_NODES.clear()
    NODE_ID_BY_NAME.clear()

    for item in nd_data:
        attrs = item.get("attributes") or {}
        node_id = attrs.get("id")
        node_name = attrs.get("name", "Unknown")
        NODE_ID_BY_NAME[node_name] = node_id

        CACHED_NODES.append({
            "name": node_name,
            "fqdn": attrs.get("fqdn", "localhost"),
            "port": attrs.get("daemon_listen", 8080),
            "status": "DOWN",
            "previous_status": "DOWN",
            "latency_ms": None,
        })

    WANTED_NODE_IDS.clear()
    for name in FEATURED_NODES:
        nid = NODE_ID_BY_NAME.get(name)
        if nid is not None:
            WANTED_NODE_IDS.add(nid)
        else:
            warn(f"Featured node name not found in Pterodactyl nodes list: {name}")

    SERVICE_STATUS["panel"], SERVICE_LAT_MS["panel"] = check_url_status_latency(PANEL_URL, timeout=4)
    SERVICE_STATUS["dash"], SERVICE_LAT_MS["dash"] = check_url_status_latency(DASH_URL, timeout=4)

    refresh_server_counts(force=True)

    if float(get_db(db, "last_check_ts", 0) or 0) <= 0:
        set_db(db, "last_check_ts", time.time())

    try:
        channel = await bot.fetch_channel(CHANNEL_ID)

        # NEW: after restart, try to reuse existing status message id
        existing_id = await find_existing_status_message(channel)
        if existing_id:
            set_db(db, "status_message_id", existing_id)
            success(f"Reusing status message: {existing_id}")

        await upsert_main_message(channel, build_main_embed())
    except Exception as e:
        warn(f"Couldn't create initial status message: {e}")

    bg_check.start()

info("Connecting to Discord...")
try:
    # interactions.py uses start(), not run()
    bot.start(TOKEN)
except Exception as e:
    alert(f"Error connecting to Discord: {e}")
    time.sleep(2)
    raise
