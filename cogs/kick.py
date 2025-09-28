import disnake
from disnake.ext import commands
from bot import has_allowed_role

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Выгнать пользователя")
    @commands.default_member_permissions(kick_members=True)
    async def kick(self, inter: disnake.AppCmdInter, user: disnake.Member, reason: str = "No reason provided"):
        await inter.response.defer(ephemeral=True)
        if not has_allowed_role(inter.author):
            await inter.edit_original_message(content="У вас нет прав для использования этой команды.")
            return
        try:
            await user.kick(reason=f"Kicked by {inter.author} | {reason}")
            await inter.edit_original_message(content=f"{user.mention} был кикнут. Причина: {reason}")
            logger = self.bot.get_cog('Logger')
            if logger:
                await logger.log_action(inter.guild, 'Kick', user=user, moderator=inter.author, reason=reason, color=0xFF4500)
        except Exception as e:
            await inter.edit_original_message(content=f"Не удалось кикнуть {user.mention}. Error: {e}")

def setup(bot):
    bot.add_cog(Kick(bot))
