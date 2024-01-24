import datetime
from datetime import datetime
import json
import random
import openai
import discord
import dateparser as dp
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from discord.utils import get
from pagination import HelpView
import os
from typing import Union
from PIL import Image
from emojify import emojify_image
import requests

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
        self.send_daily_quote.start()
        self.send_reminder.start()
        i = 0
        while i < len(data['games']):
            game_choices.append(discord.app_commands.Choice(name=data['games'][i]['name'], value=i))
            i += 1
    
    def pick_quote(self):
        global l_quote
        quote = random.randint(0, len(quotes) - 1)
        while l_quote == quote:
            quote = random.randint(0, len(quotes) - 1)
        l_quote = quote
        return quotes[quote]

    def test_user_or_role(ctx):
        return ctx.author.guild_permissions.administrator or ctx.author.guild

    @tasks.loop(minutes=1)
    async def send_daily_quote(self):
        if (datetime.now().time().hour == 19 and datetime.now().time().minute == 0):
            channel = self.bot.get_channel(779824836498948118)
            await channel.send('**Tägliches Zitat:**\n*\"' + self.pick_quote() + '\"*')
            
    @tasks.loop(minutes=1)
    async def send_reminder(self):
        global data
        for reminder in data['reminders']:
            if (datetime.now() >= datetime.strptime(reminder['datetime'], '%d/%m/%Y %H:%M')):
                print(reminder['receiver'])
                receiver = await self.bot.fetch_user(reminder['receiver'])
                sender = await self.bot.fetch_user(reminder['sender'])
                try:
                    await receiver.send(f"**Reminder by {sender.display_name}:**\n{reminder['message']}")
                except discord.HTTPException:
                    print(f"Could not send reminder to {receiver.display_name}")
                data['reminders'].remove(reminder)
                with open('config.json', 'w') as outfile:
                    json.dump(data, outfile)
                settings = open('config.json')
                data = json.load(settings)
                settings.close()
                break
        
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
        if max <= 0:
            await interaction.response.send_message('<max> has to be greater than 0')
            return
        x = random.randint(1, max)
        await interaction.response.send_message(x)


    @app_commands.command(name='help', description='Get a description of all the commands')
    async def help(self, interaction: discord.Interaction):
        view = HelpView()
        await view.send(interaction)


    @app_commands.command(name='ping', description='Get the squad together')
    @app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
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
        await interaction.response.defer()
        global data
        for i in data['games']:
            if i['name'] == game:
                await interaction.followup.send(f"**{game}** is already pingable, cannot add game twice")
                return
        c = open('config.json', 'w')
        game_obj = {'name': game, 'players': []}
        json.dumps(game_obj)
        data['games'].append(game_obj)
        json.dump(data, c)
        c.close()
        c = open('config.json')
        data = json.load(c)
        c.close()
        global game_choices
        game_choices.append(
            discord.app_commands.Choice(name=data['games'][len(data['games']) - 1]['name'], value=len(data['games']) - 1))
        try:
            synced = await self.bot.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)
        await interaction.followup.send(f"**{game}** was added to the ping system")


    @app_commands.command(name='pingremovegame', description='Remove a game fromd the ping list')
    @app_commands.checks.has_role(781223345319706646)
    @app_commands.describe(game='game')
    @app_commands.choices(game=game_choices)
    async def ping_remove_game(self, interaction: discord.Interaction, game: discord.app_commands.Choice[int]):
        await interaction.response.defer()
        global data
        for i in data['games']:
            if i['name'] == game.name:
                c = open('config.json', 'w')
                data['games'].remove(i)
                json.dump(data, c)
                c.close()
                c = open('config.json')
                data = json.load(c)
                c.close()
                global game_choices
                game_choices = []
                i = 0
                while i < len(data['games']):
                    game_choices.append(discord.app_commands.Choice(name=data['games'][i]['name'], value=i))
                    i += 1
                try:
                    synced = await self.bot.tree.sync()
                    print(f"Synced {len(synced)} command(s)")
                except Exception as e:
                    print(e)
                await interaction.followup.send(f"**{game.name}** was removed from the ping system")
                return
        await interaction.followup.send(f"**{game.name}** is not part of the ping system, cannot remove it")


    @app_commands.command(name='pinglist', description='List all users of a game ping')
    @app_commands.describe(game='game')
    @app_commands.choices(game=game_choices)
    async def ping_list(self, interaction: discord.Interaction, game: discord.app_commands.Choice[int]):
        if len(data['games'][game.value]['players']) == 0:
            await interaction.response.send_message(f"No users are being pinged by the **{game.name}** ping")
        else:
            result = f"Users pinged by the **{game.name}** ping:\n"
            for userid in data['games'][game.value]['players']:
                u = get(self.bot.get_all_members(), id=userid)
                result += f"**{u.display_name}**\n"
            await interaction.response.send_message(result)


    @app_commands.command(name='pinglistgames', description='List all games registered in the ping system')
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
        try:
            response = openai.Image.create(prompt=prompt, n=1, size="1024x1024")
        except openai.InvalidRequestError:
            return await interaction.channel.send(
                f"*{prompt}* cannot be imagined by the workers. Try another prompt that is less nsfw.")
        image_url = response['data'][0]['url']
        await interaction.followup.send(image_url)


    @app_commands.command(name='complete', description='Generate a text using a prompt')
    @app_commands.describe(prompt='description')
    async def complete(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer(ephemeral=False)
        try:
            response = openai.Completion.create(model="text-davinci-003", prompt=prompt, max_tokens=500)
        except openai.InvalidRequestError and discord.NotFound:
            return await interaction.response.send_message(
                f"*{prompt}* cannot be worked out by the workers. Try another prompt that is less nsfw.")
        text = response['choices'][0]['text']
        await interaction.followup.send(f"```{text}```")


    @app_commands.command(name='purge', description='Delete a desired amount of messages')
    @app_commands.checks.cooldown(1, 120,  key=lambda i: (i.user.id))
    @app_commands.describe(amount='amount')
    async def purge(self, interaction: discord.Interaction, amount: int):
        if 25 >= amount > 0:
            await interaction.response.send_message(f"Deleting {amount} message(s).")
            await interaction.channel.purge(limit=amount, before=interaction)
        elif amount < 0:
            await interaction.response.send_message('You can\'t delete a negative amount of messages.')
        else:
            await interaction.response.send_message('You can\'t delete more than 25 messages at once!')


    @app_commands.command(name='emojify', description='Emojify an image')
    @app_commands.describe(url='url', size='size')
    async def emojify(self, interaction: discord.Interaction, url: str, size: int = 14):

        await interaction.response.defer(ephemeral=False)
        if not isinstance(url, str):
            url = url.display_avatar.url
        print(url)

        def get_emojified_image():
            r = requests.get(url, stream=True)
            image = Image.open(r.raw).convert("RGB")
            print('test0')
            res = emojify_image(image, size)
            print('test1')
            if size > 14:
                res = f"```{res}```"
            return res

        await interaction.followup.send(get_emojified_image())
        
    @app_commands.command(name='remind', description='Let Marl Karx remind someone of something')
    @app_commands.describe(user='user', datetime='when to send the reminder', message='message')
    async def remind(self, interaction: discord.Interaction, user: discord.User, datetime: str, message: str):
        await interaction.response.defer(ephemeral=False)
        datetimeactual = dp.parse(datetime)
        if datetimeactual is None:
            await interaction.followup.send(f"Could not parse datetime, aborted.")
            return
        reminder_dict = {'sender': interaction.user.id, 'receiver': user.id, 'datetime': datetimeactual.strftime('%d/%m/%Y %H:%M'), 'message': message}
        c = open('config.json', 'w')
        data['reminders'].append(reminder_dict)
        json.dump(data, c)
        c.close()
        await interaction.followup.send(f"**{user.display_name}** will be reminded of *\"{message}\"* at **{datetimeactual.strftime('%d/%m/%Y %H:%M')}**")

    @app_commands.command(name='jail', description='Send someone to jail')
    @app_commands.describe(user='user')
    @app_commands.checks.has_role("Jailor")
    async def jail(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=False)
        jail_dict = {"server": interaction.guild.id, "user": user.id}
        if jail_dict in data["jailed"]:
            await interaction.followup.send(f"**{user.display_name}** is already in jail on this server.")
            return
        c = open('config.json', 'w')
        data['jailed'].append(jail_dict)
        json.dump(data, c)
        c.close()
        channel = self.bot.get_channel(data["jail"])
        if user.voice is not None:
            await user.move_to(channel)
        await interaction.followup.send(f"Sent **{user.display_name}** to jail.")

    @app_commands.command(name='release', description='Release someone from jail')
    @app_commands.describe(user='user')
    @app_commands.checks.has_role("Jailor")
    async def release(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=False)
        c = open('config.json', 'w')
        try:
            data['jailed'].remove({"server": interaction.guild.id, "user": user.id})
        except ValueError:
            await interaction.followup.send(f"**{user.display_name}** is already out of jail on this server.")
            return
        json.dump(data, c)
        c.close()
        await interaction.followup.send(f"Released **{user.display_name}** from jail.")

    @app_commands.command(name='jaillist', description='List everyone currently in jail')
    async def jaillist(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        result = "Inmate List:\n"
        for inmate in data["jailed"]:
            if inmate["server"] == interaction.guild.id:
                u = get(self.bot.get_all_members(), id=inmate["user"])
                result += f"**{u.display_name}**\n"
        await interaction.followup.send(result)


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