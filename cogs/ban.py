import disnake
from disnake.ext import commands
import os
from bot import has_allowed_role
from datetime import datetime, timezone

class Ban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ensure_ban_role(self, guild: disnake.Guild):
        role = disnake.utils.find(lambda r: r.name == "Ban", guild.roles)
        if role:
            return role
        perms = disnake.Permissions(send_messages=False, speak=False)
        role = await guild.create_role(name="Ban", permissions=perms, reason="Create Ban role")
        for ch in guild.channels:
            try:
                await ch.set_permissions(role, send_messages=False, speak=False)
            except Exception:
                pass
        return role

    @commands.slash_command(description="Выдать роль Ban пользователю (запрет писать/говорить)")
    @commands.default_member_permissions(ban_members=True)
    async def ban(self, inter: disnake.AppCmdInter, user: disnake.Member, reason: str = "No reason provided"):
        await inter.response.defer(ephemeral=True)
        if not has_allowed_role(inter.author):
            await inter.edit_original_message(content="У вас нет прав для использования этой команды.")
            return
        role = await self.ensure_ban_role(inter.guild)
        try:
            await user.add_roles(role, reason=f"Banned by {inter.author} | {reason}")
            await inter.edit_original_message(content=f"{user.mention} has been banned. Причина: {reason}")
            # log
            logger = self.bot.get_cog('Logger')
            if logger:
                await logger.log_action(inter.guild, 'Ban', user=user, moderator=inter.author, reason=reason, color=0xFF0000)
        except Exception as e:
            await inter.edit_original_message(content=f"Не удалось забанить: {e}")

def setup(bot):
    bot.add_cog(Ban(bot))
