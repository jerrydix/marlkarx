import discord
from discord.ext import commands
from discord import app_commands


class HLTV(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

async def setup(client: commands.Bot) -> None:
    await client.add_cog(HLTV(client))

