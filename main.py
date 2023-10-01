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
    if isinstance(error, app_commands.MissingAnyRole):
        await interaction.response.send_message(
            f"The **DJ** role is required to run this command. Execution failed.")
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
        role = get(member.server.roles, id=191870663718338560)
        await bot.add_roles(member, role)
        await bot.get_channel(976504141587312691).send(f"{member.display_name} joined the server.")
        
        
@bot.event
async def on_member_remove(member: discord.Member):
    if member.guild.id == 170953505610137600:
        await bot.get_channel(751907139425009694).send(f"{member.display_name} left the server.")
    elif member.guild.id == 170953505610137600:
        c = open('config.json', 'w')
        data['users_left'].append({'id': member.id})
        json.dump(data, c)
        c.close()
        await bot.get_channel(976504141587312691).send(f"{member.display_name} left the server.")

@bot.tree.command(name='reload')
async def reload(interaction: discord.Interaction, extension: str):
    await bot.reload_extension(f"cogs.{extension}")
    try:
        synced = await bot.tree.sync()
        for i in synced:
            print(i.name)
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
            print(e)
    await interaction.response.send_message('Reloaded cog');
    
@bot.tree.command(name='unload')
async def unload(interaction: discord.Interaction, extension: str):
    await interaction.response.defer()
    await bot.unload_extension(f"cogs.{extension}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
            print(e)
    await interaction.followup.send('Unloaded cog');
    
@bot.tree.command(name='load')
async def load(interaction: discord.Interaction, extension: str):
    await interaction.response.defer()
    await bot.load_extension(f"cogs.{extension}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
            print(e)
    await interaction.followup.send('Loaded cog');
    
@bot.tree.command(name='sync')
async def sync(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
            print(e)
    await interaction.followup.send('Synced');

    
bot.run(data['token'])  