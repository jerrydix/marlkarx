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
        #await self.load_extension('cogs.hltv')


bot = Client()


@bot.tree.error
async def role_error_catch(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingRole) and error.missing_role == "DJ":
        await interaction.response.send_message(
            f"The **DJ** role is required to run this command. Execution failed.")
    elif isinstance(error, app_commands.MissingRole) and error.missing_role == "Jailor":
        await interaction.response.send_message(
            f"The **Jailor** role is required to run this command. Execution failed.")
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
async def on_message(message: discord.Message):
    number, measure, jm = "", "", ""
    if message.author == bot.user:
        return

    if "cm" in message.content:
        number, measure, jm = calculate_jerrimeter("cm", message)
    elif "km" in message.content:
        number, measure, jm = calculate_jerrimeter("km", message)
    elif "dm" in message.content:
        number, measure, jm = calculate_jerrimeter("dm", message)
    elif "mm" in message.content:
        number, measure, jm = calculate_jerrimeter("mm", message)
    elif "µm" in message.content:
        number, measure, jm = calculate_jerrimeter("µm", message)
    elif "nm" in message.content:
        number, measure, jm = calculate_jerrimeter("nm", message)
    elif "pm" in message.content:
        number, measure, jm = calculate_jerrimeter("pm", message)
    elif "fm" in message.content:
        number, measure, jm = calculate_jerrimeter("fm", message)
    elif "am" in message.content:
        number, measure, jm = calculate_jerrimeter("am", message)
    elif "zm" in message.content:
        number, measure, jm = calculate_jerrimeter("zm", message)
    elif "ym" in message.content:
        number, measure, jm = calculate_jerrimeter("ym", message)
    elif "m" in message.content and "cm" not in message.content:
        number, measure, jm = calculate_jerrimeter("[]m", message)

    if jm != "" and number != "":
        number = "%g" % number
        jm_measure = "Jerrimeter" if jm == 1 else "Jerrimeters"
        await message.channel.send(f"{number} {measure} correspond to {jm} {jm_measure}.")


def calculate_jerrimeter(measure: str, message: discord.Message):
    index = message.content.index(measure)
    while index > 0 and message.content[index - 1].isdigit() or message.content[index - 1] == "." or message.content[
        index - 1] == "," or message.content[index - 1] == " ":
        index -= 1
    if index < 0:
        index = 0
    try:
        number = float(message.content[index:message.content.index(measure)].replace(",", "."))
    except ValueError:
        return "", "", ""

    if measure == "cm":
        jm = number / 23
    elif measure == "m":
        jm = number / 0.023
    elif measure == "km":
        jm = number / 0.000023
    elif measure == "dm":
        jm = number / 2.3
    elif measure == "mm":
        jm = number / 230
    elif measure == "µm":
        jm = number / 230000
    elif measure == "nm":
        jm = number / 230000000
    elif measure == "pm":
        jm = number / 230000000000
    elif measure == "fm":
        jm = number / 230000000000000
    elif measure == "am":
        jm = number / 230000000000000000
    elif measure == "zm":
        jm = number / 230000000000000000000
    elif measure == "ym":
        jm = number / 230000000000000000000000

    else:
        return "", measure, ""

    return number, measure, jm


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


@bot.event
async def on_voice_state_update(member, before, after):
    channel = after.channel
    sets = open('config.json')
    current_data = json.load(sets)
    if channel is not None and channel.id != current_data["jail"]:
        for inmate in current_data["jailed"]:
            if inmate["user"] == member.id:
                channel = bot.get_channel(current_data["jail"])
                await member.move_to(channel)
                return


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
