import datetime
import json
import random
import openai
from tabulate import tabulate
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from discord.utils import get
import webcrawler

#from help_d import help_d
#from music_d import music_d

bot = commands.Bot(command_prefix='.', intents=discord.Intents.all())
quote_url = 'https://de.wikiquote.org/wiki/Karl_Marx'
quotes = webcrawler.crawl_quotes(quote_url)
prefix = '.'
l_quote = 0
game_choices = []
config = open('config.json')
data = json.load(config)
openai.api_key = data['openai_key']
config.close()

@tasks.loop(minutes=1)
async def send_daily_quote():
    if (datetime.datetime.now().time().hour == 19 and datetime.datetime.now().time().minute == 0):
        channel = bot.get_channel(779824836498948118)
        await channel.send('**Tägliches Zitat:**\n*\"' + pick_quote() + '\"*')

def pick_quote():
    global l_quote
    quote = random.randint(0, len(quotes) - 1)
    while l_quote == quote:
        quote = random.randint(0, len(quotes) - 1)
    l_quote = quote
    return quotes[quote]

def test_user_or_role(ctx):
    return ctx.author.guild_permissions.administrator or ctx.author.guild

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
    send_daily_quote.start()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="workers work"))

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
    await interaction.response.send_message('```' + tabulate([['/quote', 'Marl Karx quotes Karl Marx.'], ['/quoteadd <quote>', 'Add a quote to Marl Karx\' quote collection.'], ['/echo <message>', 'Marl Karx quotes you.'], ['/manifest', 'Get the Manifest of the Communist Party for free!'], ['/choose <max>', 'Marl Karx chooses a random number from 1 to <max>.'], ['/ping <game>', 'Ping all users who are added to this game ping.'], ['/pingadd <game> <user>', 'Add a user to a specific game ping.'], ['/pingremove <game> <user>', 'Remove a user from a specific game ping.'], ['/pinglist <game>', 'List all users of a game ping.'], ['/pingaddgame <name>', 'Add a game to the ping system.'], ['/pingremovegame <game>', 'Remove a game from the ping system.'], ['/pinglistgames', 'List all games subscribed to the ping system.'], ['/imagine <prompt>', 'Make Marl Karx create an image out of your prompt.'], ['/complete <prompt>', 'Make Marl Karx write a text based on your prompt.'], ['/purge <amount>', 'Delete the last <amount> messages.']]) + '```')

@bot.tree.command(name='ping', description='Get the squad together')
@app_commands.checks.cooldown(1, 15, key=lambda i: (i.user.id))
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
        await interaction.response.send_message(f"**{user.display_name}** is already part of the **{game.name}** ping, cannot add user twice")
    else:
        c = open('config.json', 'w')
        data['games'][game.value]['players'].append(user.id)
        json.dump(data, c)
        c.close()
        await interaction.response.send_message(f"**{user.display_name}** was added to the **{game.name}** ping")

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
        await interaction.response.send_message(f"**{user.display_name}** was removed from the **{game.name}** ping")
    else:
        await interaction.response.send_message(f"**{user.display_name}** is not part of the **{game.name}** ping, cannot remove user")

@bot.tree.command(name='pingaddgame', description='Add a game to the ping list')
@app_commands.checks.has_role(781223345319706646)
@app_commands.describe(game='game')
async def ping_add_game(interaction: discord.Interaction, game: str):
    for i in data['games']:
        if i['name'] == game:
            await interaction.response.send_message(f"**{game}** is already pingable, cannot add game twice")
            return
    c = open('config.json', 'w')
    game_obj = {'name': game, 'players': []}
    json.dumps(game_obj)
    data['games'].append(game_obj)
    json.dump(data, c)
    c.close()
    global game_choices
    game_choices.append(discord.app_commands.Choice(name=data['games'][len(data['games']) - 1]['name'], value=len(data['games']) - 1))
    await interaction.response.send_message(f"**{game}** was added to the ping system")

@bot.tree.command(name='pingremovegame', description='Remove a game fromd the ping list')
@app_commands.checks.has_role(781223345319706646)
@app_commands.describe(game='game')
@app_commands.choices(game=game_choices)
async def ping_remove_game(interaction: discord.Interaction, game: discord.app_commands.Choice[int]):
    for i in data['games']:
        if i['name'] == game.name:
            c = open('config.json', 'w')
            data['games'].remove(i)
            json.dump(data, c)
            c.close()
            global game_choices
            game_choices = []
            i = 0
            while i < len(data['games']):
                game_choices.append(discord.app_commands.Choice(name=data['games'][i]['name'], value=i))
                i += 1
            await interaction.response.send_message(f"**{game.name}** was removed from the ping system")
            return
    await interaction.response.send_message(f"**{game.name}** is not part of the ping system, cannot remove it")

@bot.tree.command(name='pinglist', description='List all users of a game ping')
@app_commands.describe(game='game')
@app_commands.choices(game=game_choices)
async def ping_list(interaction: discord.Interaction, game: discord.app_commands.Choice[int]):
    if len(data['games'][game.value]['players']) == 0:
        await interaction.response.send_message(f"No users are being pinged by the **{game.name}** ping")
    else:
        result = f"Users pinged by the **{game.name}** ping:\n"
        for userid in data['games'][game.value]['players']:
            u = get(bot.get_all_members(), id=userid)
            result += f"**{u.display_name}**\n"
        await interaction.response.send_message(result)

@bot.tree.command(name='pinglistgames', description='List all users of a game ping')
async def ping_list(interaction: discord.Interaction):
    if len(data['games']) == 0:
        await interaction.response.send_message(f"No games are registered in the ping system")
    else:
        result = f"Games registered in the ping system:\n"
        for i in data['games']:
            result += f"**{i['name']}**\n"
        await interaction.response.send_message(result)

@bot.tree.command(name='imagine', description='Generate an image using a description')
@app_commands.describe(prompt='description')
async def imagine(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer(ephemeral=False)
    # await interaction.response.send_message(f"Let the workers work on that...")
    try:
        response = openai.Image.create(prompt=prompt, n=1, size="1024x1024")
    except openai.InvalidRequestError:
        return await interaction.channel.send(f"*{prompt}* cannot be imagined by the workers. Try another prompt that is less nsfw.")
    image_url = response['data'][0]['url']
    # await interaction.channel.send(image_url)
    await interaction.followup.send(image_url)

@bot.tree.command(name='complete', description='Generate a text using a prompt')
@app_commands.describe(prompt='description')
async def complete(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer(ephemeral=False)
    # await interaction.response.send_message(f"Let the workers work on that...")
    try:
        response = openai.Completion.create(model="text-davinci-003", prompt=prompt, max_tokens=500)
    except openai.InvalidRequestError and discord.NotFound:
        return await interaction.response.send_message(f"*{prompt}* cannot be worked out by the workers. Try another prompt that is less nsfw.")
    text = response['choices'][0]['text']
    # await interaction.channel.send(f"```{text}```")
    await interaction.followup.send(f"```{text}```")

@bot.tree.command(name='purge', description='Delete a desired amount of messages')
@app_commands.checks.has_role(781223345319706646)
@app_commands.describe(amount='amount')
async def purge(interaction: discord.Interaction, amount: int):
    if 25 >= amount > 0:
        await interaction.response.send_message(f"Deleting {amount} message(s).")
        await interaction.channel.purge(limit=amount, before=interaction)
    elif amount < 0:
        await interaction.response.send_message('You can\'t delete a negative amount of messages.')
    else:
        await interaction.response.send_message('You can\'t delete more than 25 messages at once!')

@bot.tree.error
async def role_error_catch(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message(f"Role **{get(bot.get_guild(170953505610137600).roles, id=781223345319706646)}** is required to run this command. Execution failed.")
    elif isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"Not so fast, comrade. Wait for another {int(error.retry_after)} seconds before executing the command again.", ephemeral=True)
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
   await bot.get_channel(751907139425009694).send(f"{member.display_name} left the server.")

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
        await message.add_reaction("<:sickle:1049066010692554843>")

    if message.content == prefix + 'help':
        await message.channel.send('```' + tabulate([['.quote', 'Marl Karx quotes Karl Marx.'], ['.echo <message>', 'Marl Karx quotes you.'], ['.manifest', 'Get the Manifest of the Communist Party for free!'], ['.choose <max>', 'Marl Karx chooses a random number from 1 to <max>.']]) + '```')

    if message.content.startswith(prefix + 'choose') and message.content[7] == ' ':
        msg = message.content[8:]
        x = 0
        if (msg.isnumeric()):
            x = random.randint(1, int(msg))
        await message.channel.send(x)

#class Dropdown(discord.ui.Select):
    #def __init__(self, message, images, user):
    #    super().__init__()
    #    self.message = message
    #    self.images = images
    #    self.user = user

    #options = [
     #   discord.SelectOption(label="1"),
    #    discord.SelectOption(label="2"),
    #    discord.SelectOption(label="3"),
    #    discord.SelectOption(label="4"),
    #    discord.SelectOption(label="5"),
    #    discord.SelectOption(label="6"),
    #    discord.SelectOption(label="7"),
    #    discord.SelectOption(label="8"),
    #    discord.SelectOption(label="9"),
    #]

    #super().__init__(
    #   placeholder="Choose your image",
    #    min_values=1,
    #    max_values=1,
    #    options=options
    #)
    #async def callback(self, interaction: discord.Interaction):
    #    if not int(self.user) == interaction.user.id:
    #        await interaction.response.send_message("You are not the author of this message!", ephemeral=True)
    #    selection = int(self.values[0])-1
    #    image = BytesIO(base64.decodebytes(self.images[selection].encode("utf-8")))
    #    return await bot.get_channel(interaction.channel.name).send(file=discord.File(image, "generatedImage.png"),
    #                                                                view=DropdownView(self.message, self.images, self.user))

#class DropdownView(discord.ui.View):
    #def __int__(self, message, images, user):
        #super.__init__()
        #self.message = message
        #self.images = images
        #self.user = user
        #self.add_item(Dropdown(self.message, self.images, self.user))
bot.run(data['token'])