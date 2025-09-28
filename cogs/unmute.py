import disnake
from disnake.ext import commands
import sqlite3
from bot import has_allowed_role, DB_PATH

class Unmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Снять мут с пользователя (убрать роль Muted)")
    @commands.default_member_permissions(manage_roles=True)
    async def unmute(self, inter: disnake.AppCmdInter, user: disnake.Member):
        await inter.response.defer(ephemeral=True)
        if not has_allowed_role(inter.author):
            await inter.edit_original_message(content="У вас нет прав для использования этой команды.")
            return
        role = disnake.utils.find(lambda r: r.name == "Muted", inter.guild.roles)
        if not role:
            await inter.edit_original_message(content=f"{user.mention} не в муте (роль не найдена).")
            return
        if role not in user.roles:
            await inter.edit_original_message(content=f"{user.mention} не в муте.")
            return
        try:
            await user.remove_roles(role, reason=f"Unmuted by {inter.author}")
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("DELETE FROM mutes WHERE user_id = ? AND guild_id = ?", (user.id, inter.guild.id))
            conn.commit()
            conn.close()
            await inter.edit_original_message(content=f"{user.mention} был размучен.")
            logger = self.bot.get_cog('Logger')
            if logger:
                await logger.log_action(inter.guild, 'Unmute', user=user, moderator=inter.author, color=0x00FF00)
        except Exception as e:
            await inter.edit_original_message(content=f"Не удалось размутить: {e}")

def setup(bot):
    bot.add_cog(Unmute(bot))
