import os, json, sqlite3, asyncio, traceback
from datetime import datetime, timezone
import disnake
from disnake.ext import commands, tasks
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("aiohttp.client").setLevel(logging.DEBUG)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

TOKEN = CONFIG.get("token")
LOG_CHANNEL_ID = CONFIG.get("log_channel_id", "")
ALLOWED_ROLES = CONFIG.get("allowed_roles", [])

INTENTS = disnake.Intents.default()
INTENTS.members = True
INTENTS.guilds = True
INTENTS.messages = True
INTENTS.voice_states = True

bot = commands.InteractionBot(intents=INTENTS)

DB_PATH = os.path.join(os.path.dirname(__file__), "база", "warnings.db")

def ensure_db():
    os.makedirs(os.path.join(os.path.dirname(__file__), "база"), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            moderator_id INTEGER NOT NULL,
            reason TEXT,
            date TEXT
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS mutes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            unmute_at INTEGER NOT NULL
        )"""
    )
    conn.commit()
    conn.close()

ensure_db()

async def save_config():
    # write back global CONFIG (careful: this will write the same file for all guilds)
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(CONFIG, f, ensure_ascii=False, indent=2)
    except Exception:
        traceback.print_exc()

async def ensure_mod_logs(guild: disnake.Guild):
    """Ensure a mod-logs channel exists in this guild. If not, create it and update CONFIG['log_channel_id'] with its id as string."""
    global LOG_CHANNEL_ID, CONFIG
    # Try configured channel id first (global). If exists in this guild, prefer it.
    if LOG_CHANNEL_ID:
        try:
            chan = guild.get_channel(int(LOG_CHANNEL_ID))
            if chan and isinstance(chan, disnake.TextChannel):
                return chan
        except Exception:
            pass
    # search for channel named mod-logs or mod_logs or logs
    for name in ("mod-logs", "mod_logs", "logs", "mod-logs-logs"):
        ch = disnake.utils.get(guild.text_channels, name=name)
        if ch:
            LOG_CHANNEL_ID = str(ch.id)
            CONFIG['log_channel_id'] = LOG_CHANNEL_ID
            await save_config()
            return ch
    # not found -> create one
    overwrites = {guild.default_role: disnake.PermissionOverwrite(send_messages=False)}
    try:
        ch = await guild.create_text_channel("mod-logs", overwrites=overwrites, reason="Mod logs channel for moderation bot")
    except disnake.Forbidden:
        # cannot create; fallback to first text channel
        ch = guild.text_channels[0] if guild.text_channels else None
    if ch:
        LOG_CHANNEL_ID = str(ch.id)
        CONFIG['log_channel_id'] = LOG_CHANNEL_ID
        await save_config()
    return ch

async def log_embed(guild: disnake.Guild, embed: disnake.Embed):
    """Send embed to mod logs in given guild."""
    ch = await ensure_mod_logs(guild)
    if ch:
        try:
            await ch.send(embed=embed)
        except Exception:
            try:
                # fallback: send to system channel if available
                if guild.system_channel:
                    await guild.system_channel.send(embed=embed)
            except Exception:
                pass

def has_allowed_role(member: disnake.Member):
    # if ALLOWED_ROLES empty, rely on discord perms that are set per-command via decorators
    if not ALLOWED_ROLES:
        return True
    return any(r.id in ALLOWED_ROLES for r in member.roles)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    # load cogs
    for fname in ("logger","ban","unban","kick","mute","unmute","warn","warnings","clearwarnings","warnremove"):
        try:
            bot.load_extension(f"cogs.{fname}")
        except Exception as e:
            print(f"Failed to load {fname}:", e)
    # start background task
    if not check_mutes.is_running():
        check_mutes.start()

@tasks.loop(seconds=10)
async def check_mutes():
    # unmute users whose time expired
    now = int(datetime.now(timezone.utc).timestamp())
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, guild_id, unmute_at FROM mutes WHERE unmute_at <= ?", (now,))
    rows = cur.fetchall()
    for row in rows:
        mid, user_id, guild_id, unmute_at = row
        guild = bot.get_guild(guild_id)
        if not guild:
            # remove record if guild missing
            cur.execute("DELETE FROM mutes WHERE id = ?", (mid,))
            continue
        member = guild.get_member(user_id)
        role = disnake.utils.find(lambda r: r.name == "Muted", guild.roles)
        if role and member and role in member.roles:
            try:
                await member.remove_roles(role, reason="Automatic unmute (expired)")
                # log auto unmute
                embed = disnake.Embed(title="Auto-Unmute", color=0x00FF00)
                embed.add_field(name="User", value=f"{member.mention} ({member.id})", inline=False)
                embed.add_field(name="Reason", value="Mute duration expired", inline=False)
                embed.add_field(name="Time (UTC)", value=datetime.now(timezone.utc).isoformat(), inline=False)
                await log_embed(guild, embed)
            except Exception:
                pass
        cur.execute("DELETE FROM mutes WHERE id = ?", (mid,))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    if not TOKEN or TOKEN == "YOUR_BOT_TOKEN" or TOKEN.strip() == "":
        print("Please put your bot token into config.json (key 'token') before running.")
    else:
        bot.run(TOKEN)
