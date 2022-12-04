import asyncio
import datetime
import json
import random
from tabulate import tabulate
import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get

#from help_d import help_d
#from music_d import music_d
from quotes_d import quotes

bot = commands.Bot(command_prefix='.', intents=discord.Intents.all())#commands.Bot(command_prefix='*')
quote_url = 'https://de.wikiquote.org/wiki/Karl_Marx'
prefix = '.'
l_quote = 0
game_choices = []
config = open('config.json')
data = json.load(config)
config.close()

async def send_daily_quote():
    now = datetime.datetime.now()
    then = now + datetime.timedelta(days=1)
    then.replace(hour=21, minute=0, second=0)
    wait_time = (then - now).total_seconds()
    await asyncio.sleep(wait_time)

    channel = bot.get_channel(751907139425009694)
    await channel.send('**Tägliches Zitat:**\n*\"' + pick_quote() + '\"*')

def pick_quote():
    global l_quote
    quote = random.randint(0, len(quotes) - 1)
    while l_quote == quote:
        quote = random.randint(0, len(quotes) - 1)
    l_quote = quote
    return quotes[quote]

def test_user_or_role(ctx):
    return ctx.author.guild_permissions.administrator or ctx.author.guil

@bot.event
async def on_ready():
    print(f'Bot with id: {bot.application_id} started running')
    i = 0
    while i < len(data['games']):
        game_choices.append(discord.app_commands.Choice(name=data['games'][i]['name'], value=i))
        i += 1
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="workers work"))
    await send_daily_quote()

    #contents = crawl_quotes(quote_url)
    #print(requests.get(quote_url).text)

@bot.tree.command(name='quote', description='Marl Karx quotes Karl Marx')
async def quote(interaction: discord.Interaction):
    await interaction.response.send_message('*\"' + pick_quote() + '\"*')

@bot.tree.command(name='quoteadd', description='Extend Marl Karx\' quote collection')
@app_commands.describe(message='message')
async def quote(interaction: discord.Interaction, message: str):
    quotes.append(message)
    await interaction.response.send_message(f"**{interaction.user.display_name}** added a quote: *\"{message}\"*")

@bot.tree.command(name='echo', description='Marl Karx quotes you')
@app_commands.describe(message='message')
async def echo(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(f'{message}')

@bot.tree.command(name='manifest', description='Get the Manifest of the Communist Party for free!')
async def echo(interaction: discord.Interaction):
    with open('manifest_der_kommunistischen_partei.pdf', 'rb') as fp:
        await interaction.channel.send(file=discord.File(fp, 'manifest_der_kommunistischen_partei.pdf'))
    await interaction.response.send_message("**Das Manifest der Kommunistischen Partei:**")

@bot.tree.command(name='help', description='Get a description of all the commands')
async def help(interaction: discord.Interaction):
    await interaction.response.send_message('```' + tabulate([['/quote', 'Marl Karx quotes Karl Marx.'], ['/echo <message>', 'Marl Karx quotes you.'], ['/manifest', 'Get the Manifest of the Communist Party for free!'], ['/choose <max>', 'Marl Karx chooses a random number from 1 to <max>.'], ['/ping <game>', 'Ping all users who are added to this game ping.'], ['/pingadd <game> <user>', 'Add a user to a specific game ping.'], ['/pingremove <game> <user>', 'Remove a user from a specific game ping.'], ['/pinglist <game>', 'List all users of a game ping.']]) + '```')

@bot.tree.command(name='ping', description='Get the squad together')
@app_commands.describe(game='game')
@app_commands.choices(game=game_choices)
async def ping(interaction: discord.Interaction, game: discord.app_commands.Choice[int]):
    result = f"I hereby request that you come and play some **{game.name}** "
    for player in data['games'][game.value]['players']:
        result += f"<@{player}> "
    await interaction.response.send_message(result)

@bot.tree.command(name='pingadd', description='Add a user to a ping command')
@app_commands.checks.has_role(781223345319706646)
@app_commands.describe(game='game')
@app_commands.choices(game=game_choices)
async def ping_add(interaction: discord.Interaction, game: discord.app_commands.Choice[int], user: discord.User):
    if user.id in data['games'][game.value]['players']:
        await interaction.response.send_message(f"**{user.name}** is already part of the **{game.name}** ping, cannot add user twice")
    else:
        c = open('config.json', 'w')
        data['games'][game.value]['players'].append(user.id)
        json.dump(data, c)
        c.close()
        await interaction.response.send_message(f"**{user.name}** was added to the **{game.name}** ping")

@bot.tree.command(name='pingremove', description='Remove a user from a ping command')
@app_commands.checks.has_role(781223345319706646)
@app_commands.describe(game='game')
@app_commands.choices(game=game_choices)
async def ping_remove(interaction: discord.Interaction, game: discord.app_commands.Choice[int], user: discord.User):
    if user.id in data['games'][game.value]['players']:
        c = open('config.json', 'w')
        data['games'][game.value]['players'].remove(user.id)
        json.dump(data, c)
        c.close()
        await interaction.response.send_message(f"**{user.name}** was removed from the **{game.name}** ping")
    else:
        await interaction.response.send_message(f"**{user.name}** is not part of the **{game.name}** ping, cannot remove user")

@bot.tree.command(name='pinglist', description='List all users of a game ping')
@app_commands.describe(game='game')
@app_commands.choices(game=game_choices)
async def ping_list(interaction: discord.Interaction, game: discord.app_commands.Choice[int]):
    if len(data['games'][game.value]['players']) == 0:
        await interaction.response.send_message(f"No users are pinged by the **{game.name}** ping")
    else:
        result = f"Users pinged by the **{game.name}** ping:\n"
        for userid in data['games'][game.value]['players']:
            u = get(bot.get_all_members(), id=userid)
            result += f"**{u.display_name}**\n"
        await interaction.response.send_message(result)

@bot.tree.error
async def role_error_catch(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message(f"Role **{get(bot.get_guild(170953505610137600).roles, id=781223345319706646)}** is required to run this command. Execution failed.")
    else: raise error

@bot.event
async def on_member_join(member: discord.Member):
    await member.send(f"Welcome to {member.guild.name}, {member.name}!")
    await bot.get_channel(751907139425009694).send(f"{member.display_name} has joined the server.")

@bot.event
async def on_member_remove(member: discord.Member):
   await bot.get_channel(751907139425009694).send(f"{member.display_name} has left the server.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content == prefix + 'quote':
        global l_quote
        quote = random.randint(0, len(quotes) - 1)
        while l_quote == quote:
            quote = random.randint(0, len(quotes) - 1)
        await message.channel.send('*\"' + quotes[quote] + '\"*')
        l_quote = quote

    if message.content.startswith(prefix + 'echo') and message.content[5] == ' ':
        msg = message.content[5:]
        await message.channel.send(msg)

    if message.content == prefix + 'manifest':
        with open('manifest_der_kommunistischen_partei.pdf', 'rb') as fp:
            await message.channel.send(file=discord.File(fp, 'manifest_der_kommunistischen_partei.pdf'))

    if 'communism' in message.content:
        await message.add_reaction('sickle')

    if message.content == prefix + 'help':
        await message.channel.send('```' + tabulate([['.quote', 'Marl Karx quotes Karl Marx.'], ['.echo <message>', 'Marl Karx quotes you.'], ['.manifest', 'Get the Manifest of the Communist Party for free!'], ['.choose <max>', 'Marl Karx chooses a random number from 1 to <max>.']]) + '```')

    if message.content.startswith(prefix + 'choose') and message.content[7] == ' ':
        msg = message.content[8:]
        x = 0
        if (msg.isnumeric()):
            x = random.randint(1, int(msg))
        await message.channel.send(x)

bot.run(data['token'])
#other stuff q

#def crawl_quotes(url):
#    content = requests.get(url).text
 #   result = []
#    boolean = 0
 #   for i in content:
  #      if boolean == 1:
  #      if i == '\"' and boolean == 0:
  #          boolean = 1
  #          boolean = 0