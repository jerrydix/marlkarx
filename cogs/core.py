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
    
class Core(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def pick_quote():
        global l_quote
        quote = random.randint(0, len(quotes) - 1)
        while l_quote == quote:
            quote = random.randint(0, len(quotes) - 1)
        l_quote = quote
        return quotes[quote]

    def test_user_or_role(ctx):
        return ctx.author.guild_permissions.administrator or ctx.author.guild


    @app_commands.command(name='quote', description='Marl Karx quotes Karl Marx')
    async def quote(self, interaction: discord.Interaction):
        await interaction.response.send_message('*\"' + self.pick_quote() + '\"*')


    @app_commands.command(name='quoteadd', description='Extend Marl Karx\' quote collection')
    @app_commands.describe(message='message')
    async def quote_add(self, interaction: discord.Interaction, message: str):
        quotes.append(message)
        await interaction.response.send_message(f"**{interaction.user.display_name}** added a quote: *\"{message}\"*")


    @app_commands.command(name='echo', description='Marl Karx quotes you')
    @app_commands.describe(message='message')
    async def echo(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(f'{message}')


    @app_commands.command(name='manifest', description='Get the Manifest of the Communist Party for free!')
    async def manifest(self, interaction: discord.Interaction):
        with open('manifest_der_kommunistischen_partei.pdf', 'rb') as fp:
            await interaction.channel.send(file=discord.File(fp, 'manifest_der_kommunistischen_partei.pdf'))
        await interaction.response.send_message("**Das Manifest der Kommunistischen Partei:**")
        
    @app_commands.command(name='choose', description='Marl Karx chooses a random number from 1 to <max>')
    @app_commands.describe(max='max')
    async def choose(self, interaction: discord.Interaction, max: int):
        if x <= 0:
            await interaction.response.send_message('<max> has to be greater than 0')
            return
        x = random.randint(1, x)
        await interaction.response.send_message(x)


    @app_commands.command(name='help', description='Get a description of all the commands')
    async def help(self, interaction: discord.Interaction):
        await interaction.response.send_message('```' + tabulate([['/quote', 'Marl Karx quotes Karl Marx.'],
                                                              ['/quoteadd <quote>',
                                                               'Add a quote to Marl Karx\' quote collection.'],
                                                              ['/echo <message>', 'Marl Karx quotes you.'],
                                                              ['/manifest',
                                                               'Get the Manifest of the Communist Party for free!'],
                                                              ['/choose <max>',
                                                               'Marl Karx chooses a random number from 1 to <max>.'],
                                                              ['/ping <game>',
                                                               'Ping all users who are added to this game ping.'],
                                                              ['/pingadd <game> <user>',
                                                               'Add a user to a specific game ping.'],
                                                              ['/pingremove <game> <user>',
                                                               'Remove a user from a specific game ping.'],
                                                              ['/pinglist <game>', 'List all users of a game ping.'],
                                                              ['/pingaddgame <name>', 'Add a game to the ping system.'],
                                                              ['/pingremovegame <game>',
                                                               'Remove a game from the ping system.'],
                                                              ['/pinglistgames',
                                                               'List all games subscribed to the ping system.'],
                                                              ['/imagine <prompt>',
                                                               'Make Marl Karx create an image out of your prompt.'],
                                                              ['/complete <prompt>',
                                                               'Make Marl Karx write a text based on your prompt.'],
                                                              ['/purge <amount>',
                                                               'Delete the last <amount> messages.']]) + '```')


    @app_commands.command(name='ping', description='Get the squad together')
    @app_commands.checks.cooldown(1, 15, key=lambda i: (i.user.id))
    @app_commands.describe(game='game')
    @app_commands.choices(game=game_choices)
    async def ping(self, interaction: discord.Interaction, game: discord.app_commands.Choice[int]):
        result = f"I hereby request that you come and play some **{game.name}** "
        for player in data['games'][game.value]['players']:
            result += f"<@{player}> "
        await interaction.response.send_message(result)


    @app_commands.command(name='pingadd', description='Add a user to a ping command')
    @app_commands.checks.has_role(781223345319706646)
    @app_commands.describe(game='game')
    @app_commands.choices(game=game_choices)
    async def ping_add(self, interaction: discord.Interaction, game: discord.app_commands.Choice[int], user: discord.User):
        if user.id in data['games'][game.value]['players']:
            await interaction.response.send_message(
                f"**{user.display_name}** is already part of the **{game.name}** ping, cannot add user twice")
        else:
            c = open('config.json', 'w')
            data['games'][game.value]['players'].append(user.id)
            json.dump(data, c)
            c.close()
            await interaction.response.send_message(f"**{user.display_name}** was added to the **{game.name}** ping")


    @app_commands.command(name='pingremove', description='Remove a user from a ping command')
    @app_commands.checks.has_role(781223345319706646)
    @app_commands.describe(game='game')
    @app_commands.choices(game=game_choices)
    async def ping_remove(self, interaction: discord.Interaction, game: discord.app_commands.Choice[int], user: discord.User):
        if user.id in data['games'][game.value]['players']:
            c = open('config.json', 'w')
            data['games'][game.value]['players'].remove(user.id)
            json.dump(data, c)
            c.close()
            await interaction.response.send_message(f"**{user.display_name}** was removed from the **{game.name}** ping")
        else:
            await interaction.response.send_message(
                f"**{user.display_name}** is not part of the **{game.name}** ping, cannot remove user")


    @app_commands.command(name='pingaddgame', description='Add a game to the ping list')
    @app_commands.checks.has_role(781223345319706646)
    @app_commands.describe(game='game')
    async def ping_add_game(self, interaction: discord.Interaction, game: str):
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
        game_choices.append(
            discord.app_commands.Choice(name=data['games'][len(data['games']) - 1]['name'], value=len(data['games']) - 1))
        await interaction.response.send_message(f"**{game}** was added to the ping system")


    @app_commands.command(name='pingremovegame', description='Remove a game fromd the ping list')
    @app_commands.checks.has_role(781223345319706646)
    @app_commands.describe(game='game')
    @app_commands.choices(game=game_choices)
    async def ping_remove_game(self, interaction: discord.Interaction, game: discord.app_commands.Choice[int]):
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


    @app_commands.command(name='pinglist', description='List all users of a game ping')
    @app_commands.describe(game='game')
    @app_commands.choices(game=game_choices)
    async def ping_list(self, interaction: discord.Interaction, game: discord.app_commands.Choice[int]):
        if len(data['games'][game.value]['players']) == 0:
            await interaction.response.send_message(f"No users are being pinged by the **{game.name}** ping")
        else:
            result = f"Users pinged by the **{game.name}** ping:\n"
            for userid in data['games'][game.value]['players']:
                u = get(bot.get_all_members(), id=userid)
                result += f"**{u.display_name}**\n"
            await interaction.response.send_message(result)


    @app_commands.command(name='pinglistgames', description='List all users of a game ping')
    async def ping_list_games(self, interaction: discord.Interaction):
        if len(data['games']) == 0:
            await interaction.response.send_message(f"No games are registered in the ping system")
        else:
            result = f"Games registered in the ping system:\n"
            for i in data['games']:
                result += f"**{i['name']}**\n"
            await interaction.response.send_message(result)


    @app_commands.command(name='imagine', description='Generate an image using a description')
    @app_commands.describe(prompt='description')
    async def imagine(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer(ephemeral=False)
        # await interaction.response.send_message(f"Let the workers work on that...")
        try:
            response = openai.Image.create(prompt=prompt, n=1, size="1024x1024")
        except openai.InvalidRequestError:
            return await interaction.channel.send(
                f"*{prompt}* cannot be imagined by the workers. Try another prompt that is less nsfw.")
        image_url = response['data'][0]['url']
        # await interaction.channel.send(image_url)
        await interaction.followup.send(image_url)


    @app_commands.command(name='complete', description='Generate a text using a prompt')
    @app_commands.describe(prompt='description')
    async def complete(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer(ephemeral=False)
        # await interaction.response.send_message(f"Let the workers work on that...")
        try:
            response = openai.Completion.create(model="text-davinci-003", prompt=prompt, max_tokens=500)
        except openai.InvalidRequestError and discord.NotFound:
            return await interaction.response.send_message(
                f"*{prompt}* cannot be worked out by the workers. Try another prompt that is less nsfw.")
        text = response['choices'][0]['text']
        # await interaction.channel.send(f"```{text}```")
        await interaction.followup.send(f"```{text}```")


    @app_commands.command(name='purge', description='Delete a desired amount of messages')
    @app_commands.checks.has_role(781223345319706646)
    @app_commands.describe(amount='amount')
    async def purge(self, interaction: discord.Interaction, amount: int):
        if 25 >= amount > 0:
            await interaction.response.send_message(f"Deleting {amount} message(s).")
            await interaction.channel.purge(limit=amount, before=interaction)
        elif amount < 0:
            await interaction.response.send_message('You can\'t delete a negative amount of messages.')
        else:
            await interaction.response.send_message('You can\'t delete more than 25 messages at once!')


    # class Dropdown(discord.ui.Select):
    # def __init__(self, message, images, user):
    #    super().__init__()
    #    self.message = message
    #    self.images = images
    #    self.user = user

    # options = [
    #   discord.SelectOption(label="1"),
    #    discord.SelectOption(label="2"),
    #    discord.SelectOption(label="3"),
    #    discord.SelectOption(label="4"),
    #    discord.SelectOption(label="5"),
    #    discord.SelectOption(label="6"),
    #    discord.SelectOption(label="7"),
    #    discord.SelectOption(label="8"),
    #    discord.SelectOption(label="9"),
    # ]

    # super().__init__(
    #   placeholder="Choose your image",
    #    min_values=1,
    #    max_values=1,
    #    options=options
    # )
    # async def callback(self, interaction: discord.Interaction):
    #    if not int(self.user) == interaction.user.id:
    #        await interaction.response.send_message("You are not the author of this message!", ephemeral=True)
    #    selection = int(self.values[0])-1
    #    image = BytesIO(base64.decodebytes(self.images[selection].encode("utf-8")))
    #    return await bot.get_channel(interaction.channel.name).send(file=discord.File(image, "generatedImage.png"),
    #                                                                view=DropdownView(self.message, self.images, self.user))

    # class DropdownView(discord.ui.View):
    # def __int__(self, message, images, user):
    # super.__init__()
    # self.message = message
    # self.images = images
    # self.user = user
    # self.add_item(Dropdown(self.message, self.images, self.user))


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Core(client))