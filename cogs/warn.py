import disnake
from disnake.ext import commands
import sqlite3
from datetime import datetime
from bot import has_allowed_role, DB_PATH

class Warn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Выдать предупреждение пользователю и сохранить в базу")
    @commands.default_member_permissions(kick_members=True)
    async def warn(self, inter: disnake.AppCmdInter, user: disnake.Member, reason: str = "No reason provided"):
        await inter.response.defer(ephemeral=True)
        if not has_allowed_role(inter.author):
            await inter.edit_original_message(content="У вас нет прав для использования этой команды.")
            return
        date = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO warnings(user_id,guild_id,moderator_id,reason,date) VALUES (?,?,?,?,?)", (user.id, inter.guild.id, inter.author.id, reason, date))
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM warnings WHERE user_id = ? AND guild_id = ?", (user.id, inter.guild.id))
        count = cur.fetchone()[0]
        conn.close()
        await inter.edit_original_message(content=f"{user.mention} получил предупреждение. Причина: {reason}. Всего предупреждений: {count}")
        logger = self.bot.get_cog('Logger')
        if logger:
            await logger.log_action(inter.guild, 'Warn', user=user, moderator=inter.author, reason=reason, extra=f"Всего предупреждений: {count}", color=0xFFFF00)

def setup(bot):
    bot.add_cog(Warn(bot))
