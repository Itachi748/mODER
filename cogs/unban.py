import disnake
from disnake.ext import commands
from bot import has_allowed_role

class Unban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Снять бан (убрать роль Ban) по ID пользователя, если он на сервере")
    @commands.default_member_permissions(ban_members=True)
    async def unban(self, inter: disnake.AppCmdInter, user_id: str):
        await inter.response.defer(ephemeral=True)
        if not has_allowed_role(inter.author):
            await inter.edit_original_message(content="У вас нет прав для использования этой команды.")
            return
        try:
            uid = int(user_id)
        except ValueError:
            await inter.edit_original_message(content="Неверный ID пользователя.")
            return
        guild = inter.guild
        member = guild.get_member(uid)
        role = disnake.utils.find(lambda r: r.name == "Ban", guild.roles)
        if not role:
            await inter.edit_original_message(content="Роль Ban не найдена.")
            return
        if member and role in member.roles:
            try:
                await member.remove_roles(role, reason=f"Unbanned by {inter.author}")
                await inter.edit_original_message(content=f"{member.mention} был разбанен.")
                logger = self.bot.get_cog('Logger')
                if logger:
                    await logger.log_action(inter.guild, 'Unban', user=member, moderator=inter.author, color=0x00FF00)
            except Exception as e:
                await inter.edit_original_message(content=f"Не удалось разбанить: {e}")
        else:
            await inter.edit_original_message(content=f"Пользователь не найден на сервере или не забанен.")

def setup(bot):
    bot.add_cog(Unban(bot))
