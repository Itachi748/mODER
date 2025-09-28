import disnake
from disnake.ext import commands
import sqlite3
from bot import has_allowed_role, DB_PATH

class WarnRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Удалить предупреждение по его ID")
    @commands.default_member_permissions(kick_members=True)
    async def warnremove(self, inter: disnake.AppCmdInter, warn_id: int):
        await inter.response.defer(ephemeral=True)
        if not has_allowed_role(inter.author):
            await inter.edit_original_message(content="У вас нет прав для использования этой команды.")
            return
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id FROM warnings WHERE id = ? AND guild_id = ?", (warn_id, inter.guild.id))
        row = cur.fetchone()
        if not row:
            await inter.edit_original_message(content=f"Предупреждение с ID {warn_id} не найдено.")
            conn.close()
            return
        cur.execute("DELETE FROM warnings WHERE id = ?", (warn_id,))
        conn.commit()
        conn.close()
        await inter.edit_original_message(content=f"Предупреждение с ID {warn_id} удалено.")
        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.log_action(inter.guild, 'WarnRemove', moderator=inter.author, extra=f'Removed warn id {warn_id}', color=0xAAAAAA)

def setup(bot):
    bot.add_cog(WarnRemove(bot))
