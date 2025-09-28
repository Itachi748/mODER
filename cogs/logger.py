import disnake
from disnake.ext import commands
from bot import log_embed

class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_action(self, guild, action, user=None, moderator=None, reason=None, extra=None, color=0x3498db):
        embed = disnake.Embed(title=action, color=color)
        if user is not None:
            embed.add_field(name="Пользователь", value=f"{getattr(user, 'mention', str(user))} ({getattr(user, 'id', '')})", inline=False)
        if moderator is not None:
            embed.add_field(name="Модератор", value=f"{moderator.mention} ({moderator.id})", inline=False)
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
        if extra:
            embed.add_field(name="Детали", value=extra, inline=False)
        embed.add_field(name="Время (UTC)", value=disnake.utils.utcnow().isoformat(), inline=False)
        await log_embed(guild, embed)

def setup(bot):
    bot.add_cog(Logger(bot))
