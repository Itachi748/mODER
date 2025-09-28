import disnake
from disnake.ext import commands
import sqlite3
from bot import DB_PATH

class WarningsList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Показать предупреждения пользователя")
    async def warnings(self, inter: disnake.AppCmdInter, user: disnake.Member):
        await inter.response.defer(ephemeral=True)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id,reason,moderator_id,date FROM warnings WHERE user_id = ? AND guild_id = ? ORDER BY id ASC", (user.id, inter.guild.id))
        rows = cur.fetchall()
        conn.close()
        if not rows:
            await inter.edit_original_message(content=f"{user.mention} не имеет предупреждений.")
            return
        lines = []
        for r in rows:
            wid, reason, mod_id, date = r
            lines.append(f"{wid}. Причина: {reason} | Выдал <@{mod_id}> | Дата: {date}")
        await inter.edit_original_message(content="\n".join(lines))

def setup(bot):
    bot.add_cog(WarningsList(bot))
