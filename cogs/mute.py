import disnake
from disnake.ext import commands
import re, sqlite3
from datetime import datetime, timezone, timedelta
from bot import has_allowed_role, DB_PATH

DURATION_RE = re.compile(r"^(\d+)(s|m|h|d)$", re.IGNORECASE)

def parse_duration(s: str):
    m = DURATION_RE.match(s)
    if not m:
        return None
    val = int(m.group(1))
    unit = m.group(2).lower()
    if unit == "s":
        return timedelta(seconds=val)
    if unit == "m":
        return timedelta(minutes=val)
    if unit == "h":
        return timedelta(hours=val)
    if unit == "d":
        return timedelta(days=val)
    return None



class Mute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ensure_muted_role(self, guild: disnake.Guild):
        role = disnake.utils.find(lambda r: r.name == "Muted", guild.roles)
        if role:
            return role
        perms = disnake.Permissions(send_messages=False, speak=False, add_reactions=False)
        role = await guild.create_role(name="Muted", permissions=perms, reason="Create Muted role")
        for ch in guild.channels:
            try:
                await ch.set_permissions(role, send_messages=False, speak=False, add_reactions=False)
            except Exception:
                pass
        return role

    @commands.slash_command(description="Замутить пользователя на время (например 10m, 2h)")
    @commands.default_member_permissions(manage_roles=True, moderate_members=True)
    async def mute(self, inter: disnake.AppCmdInter, user: disnake.Member, duration: str = "10m", reason: str = "No reason provided"):
        await inter.response.defer(ephemeral=True)
        if not has_allowed_role(inter.author):
            await inter.edit_original_message(content="У вас нет прав для использования этой команды.")
            return
        delta = parse_duration(duration)
        if not delta:
            await inter.edit_original_message(content="Недопустимая длительность. Примеры: 30s, 5m, 2h, 1d")
            return
        role = await self.ensure_muted_role(inter.guild)
        try:
            await user.add_roles(role, reason=f"Muted by {inter.author} | {reason}")
        except Exception as e:
            await inter.edit_original_message(content=f"Не удалось выдать роль мута: {e}")
            return
        unmute_at = int((datetime.now(timezone.utc) + delta).timestamp())
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO mutes(user_id,guild_id,unmute_at) VALUES (?,?,?)", (user.id, inter.guild.id, unmute_at))
        conn.commit()
        conn.close()
        await inter.edit_original_message(content=f"{user.mention} был замучен на {duration}. Причина: {reason}")
        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.log_action(inter.guild, 'Mute', user=user, moderator=inter.author, reason=f"{reason} | duration: {duration}", color=0xFFFF00)

def setup(bot):
    bot.add_cog(Mute(bot))
