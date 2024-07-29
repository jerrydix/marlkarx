import datetime
from datetime import datetime

import discord
import json
from discord.ext import commands
from discord.ext import tasks
from discord import app_commands

from javascript import require

from pagination import MatchView

h = require('../hltv-api-parser.js')

from cogs.core import data


class HLTV(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if data["major_id"] == -1:
            c = open('config.json', 'w')
            currentMajorID = h.getCurrentMajorID()
            data["major_id"] = currentMajorID
            json.dump(data, c)
            c.close()
        self.send_daily_results.start()

    @tasks.loop(seconds=1)
    async def send_daily_results(self):
        if datetime.now().time().hour == 20 and datetime.now().time().second == 0:
            matches = h.getTodaysResults()
            channel = self.bot.get_channel(1222557631726620692)

            if not matches:
                return

            m_data = []
            for i in range(matches.length):
                m_data.append(matches[i])

            view = MatchView()
            view.data = m_data
            await view.send(channel=channel)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(HLTV(client))
