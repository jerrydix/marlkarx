import datetime
import json
import random
import openai
from bot import config
from tabulate import tabulate
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from discord.utils import get
import webcrawler

quote_url = 'https://de.wikiquote.org/wiki/Karl_Marx'
quotes = webcrawler.crawl_quotes(quote_url)
prefix = '.'
l_quote = 0
game_choices = []
settings = open('config.json')
data = json.load(settings)
openai.api_key = data['openai_key']
settings.close()

config.load()

class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='.', intents=discord.Intents.all())
        
    async def on_ready(self):
        print(f'We have logged in as {bot.user}')
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="workers work"))
        print(f'Bot with id: {bot.application_id} started running')
        try:
            synced = await self.tree.sync()
            # for i in synced:
                # print(i.name)
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)
    
    async def setup_hook(self):
        await self.load_extension('cogs.core')
        await self.load_extension('cogs.music')
        
        
bot = Client()
        
@bot.tree.error
async def role_error_catch(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message(
            f"Role **{get(bot.get_guild(170953505610137600).roles, id=781223345319706646)}** is required to run this command. Execution failed.")
    elif isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"Not so fast, comrade. Wait for another {int(error.retry_after)} seconds before executing the command again.",
            ephemeral=True)
    else:
        raise error
    
    
@bot.event
async def on_member_join(member: discord.Member):
    await member.send(f"Welcome to {member.guild.name}, {member.name}!")
    if member.guild.id == 170953505610137600:
        await bot.get_channel(751907139425009694).send(f"{member.display_name} joined the server.")
    elif member.guild.id == 170953505610137600:
        await bot.get_channel(976504141587312691).send(f"{member.display_name} joined the server.")
        
        
@bot.event
async def on_member_remove(member: discord.Member):
    if member.guild.id == 170953505610137600:
        await bot.get_channel(751907139425009694).send(f"{member.display_name} left the server.")
    elif member.guild.id == 170953505610137600:
        await bot.get_channel(976504141587312691).send(f"{member.display_name} left the server.")
     
bot.run(data['token'])  


        
        
