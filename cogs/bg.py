"""
Dredd, discord bot
Copyright (C) 2020 Moksej
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord
import time
from discord.ext import commands, tasks
from db import emotes


class Background(commands.Cog, name="BG"):
    def __init__(self, bot):
        self.bot = bot
        self.temp_mute.start()
        self.help_icon = ""
        self.big_icon = ""
    
    async def log_temp_unmute(self, guild=None, mod=None, member=None, reason=None):
        check = await self.bot.db.fetchval("SELECT * FROM moderation WHERE guild_id = $1", guild.id)

        if check is None:
            return
        elif check is not None:
            channel = await self.bot.db.fetchval("SELECT channel_id FROM moderation WHERE guild_id = $1", guild.id)
            case = await self.bot.db.fetchval("SELECT case_num FROM modlog WHERE guild_id = $1", guild.id)
            chan = self.bot.get_channel(channel)

            if case is None:
                await self.bot.db.execute("INSERT INTO modlog(guild_id, case_num) VALUES ($1, $2)", guild.id, 1)

            casenum = await self.bot.db.fetchval("SELECT case_num FROM modlog WHERE guild_id = $1", guild.id)

            e = discord.Embed(color=self.bot.logging_color, description=f"{emotes.log_memberedit} **{member}** unmuted `[#{casenum}]`")
            e.add_field(name="Previously muted by:", value=f"{mod} ({mod.id})", inline=False)
            e.add_field(name="Reason:", value=f"{reason}", inline=False)
            e.set_thumbnail(url=member.avatar_url_as(format='png'))
            e.set_footer(text=f"Member ID: {member.id}")

            await chan.send(embed=e)
            await self.bot.db.execute("UPDATE modlog SET case_num = case_num + 1 WHERE guild_id = $1", guild.id)

    def cog_unload(self):
        self.temp_mute.cancel()

    @tasks.loop(seconds=1)
    async def temp_mute(self):
        for guild, user, mod, reason, timed, roleid in self.bot.temp_timer:
            if timed and timed - time.time() <= 0:
                try:
                    g = self.bot.get_guild(guild)
                    m = g.get_member(user)
                    r = g.get_role(roleid)
                    mm = g.get_member(mod)
                    reasons = "Auto unmute"
                    try:
                        await m.remove_roles(r, reason=reasons)
                        await self.log_temp_unmute(guild=g, mod=mm, member=m, reason=reasons)
                    except Exception as e:
                        print(e)
                        pass
                except Exception as e:
                    print(e)
                    pass
                await self.bot.db.execute("DELETE FROM moddata WHERE user_id = $1 AND guild_id = $2", user, guild)
                self.bot.temp_timer.remove((guild, user, mod, reason, timed, roleid))

    @temp_mute.before_loop
    async def before_change_lmao(self):

        await self.bot.wait_until_ready()
        print('\n[BACKGROUND] Started temp punishments task.')

def setup(bot):
    bot.add_cog(Background(bot))