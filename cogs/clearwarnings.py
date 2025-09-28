import disnake
from disnake.ext import commands
import sqlite3
from bot import has_allowed_role, DB_PATH

class ClearWarnings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Очистить все предупреждения пользователя")
    @commands.default_member_permissions(kick_members=True)
    async def clearwarnings(self, inter: disnake.AppCmdInter, user: disnake.Member):
        await inter.response.defer(ephemeral=True)
        if not has_allowed_role(inter.author):
            await inter.edit_original_message(content="У вас нет прав для использования этой команды.")
            return
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM warnings WHERE user_id = ? AND guild_id = ?", (user.id, inter.guild.id))
        conn.commit()
        conn.close()
        await inter.edit_original_message(content=f"Все предупреждения для {user.mention} были очищены.")
        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.log_action(inter.guild, 'ClearWarnings', user=user, moderator=inter.author, extra='All warnings removed', color=0xAAAAAA)

def setup(bot):
    bot.add_cog(ClearWarnings(bot))
