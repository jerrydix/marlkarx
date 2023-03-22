import discord
from tabulate import tabulate

class QueueView(discord.ui.View):
    
    current_page: int = 1
    sep: int = 10
    
    async def send(self, interaction: discord.Interaction):
        self.message = await interaction.response.send_message(f'Currently playing: **{self.data.current_song.title}**, Requested by: {self.data.current_song.requested_by}')
        self.message = await interaction.channel.send(view=self)
        await self.update_msg(self.data[:self.sep])
         
    def create_embed(self, data):
        embed = discord.Embed(title='Current Queue:', colour=discord.Colour.dark_red())
        for i in data:
            embed.add_field(name=i.title, value=i.uploader, inline=True)
            embed.add_field(name=i.duration_formatted, value=i.requested_by, inline=True)
            embed.add_field(name='', value='', inline=True)
        return embed
    
    async def update_msg(self, data):
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(data), view=self)
        
    def update_buttons(self):
        if self.current_page == 1:
            self.first_button.disabled = True
            self.prev_button.disabled = True
            self.first_button.style = discord.ButtonStyle.gray
            self.prev_button.style = discord.ButtonStyle.gray
        else:
            self.first_button.disabled = False
            self.prev_button.disabled = False
            self.first_button.style = discord.ButtonStyle.red
            self.prev_button.style = discord.ButtonStyle.red
        
        if self.current_page == int(len(self.data) / self.sep) + 1:
            self.next_button.disabled = True
            self.last_button.disabled = True
            self.next_button.style = discord.ButtonStyle.gray
            self.last_button.style = discord.ButtonStyle.gray
        else:
            self.next_button.disabled = False
            self.last_button.disabled = False
            self.next_button.style = discord.ButtonStyle.red
            self.last_button.style = discord.ButtonStyle.red
    
    @discord.ui.button(label='|<', style=discord.ButtonStyle.primary)
    async def first_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = 1
        until_item = self.current_page * self.sep
        await self.update_msg(self.data[:until_item])
        
        
    @discord.ui.button(label='<', style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page -= 1
        until_item = self.current_page * self.sep
        from_item = until_item - self.sep
        await self.update_msg(self.data[from_item:until_item])
        
        
    @discord.ui.button(label='>', style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page += 1
        until_item = self.current_page * self.sep
        from_item = until_item - self.sep
        await self.update_msg(self.data[from_item:until_item])
        
    
    @discord.ui.button(label='>|', style=discord.ButtonStyle.primary)
    async def last_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = int(len(self.data) / self.sep) + 1
        until_item = self.current_page * self.sep
        from_item = until_item - self.sep
        await self.update_msg(self.data[from_item:])
    
        
class HelpView(discord.ui.View):
    current_page: int = 1
    
    core_help: str = '```Core Commands:\n' + tabulate([['/quote', 'Marl Karx quotes Karl Marx.'],
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
                                                               'Delete the last <amount> messages.']]) + '```'
    
    music_help: str = '```Music commands:\n' + tabulate([['/play <prompt>', 'Marl Karx plays the desired song for you. (Resumes playback if no argument given)'], ['/pause', 'Marl Karx pauses the playback.'], ['/skip', 'Marl Karx skips the currently playing song.'], ['/stop', 'Marl Karx stops the playback and clear the queue.'], ['/nowplaying <index> || /songinfo <index>', 'Displays info about the song at <index> in the queue. (Current song if no index given)'], ['/createplaylist <name>', 'Marl Karx creates a playlist with the specified name.'], ['/playlist <name>', 'Marl Karx enqueues the desired playlist.'], ['/playlistadd <playlist> <song>', 'Marl Karx adds <song> to <playlist>.']]) + '```'
    
    async def send(self, interaction: discord.Interaction):
        self.message = await interaction.response.send_message(f'**Marl Karx help Page:**')
        self.message = await interaction.channel.send(view=self)
        await self.update_msg()
    
    
    async def update_msg(self):
        self.update_buttons()
        await self.message.edit(content=self.choose_page(self.current_page), view=self)
       
        
    def choose_page(self, number: int):
        match number:
            case 1:
                return self.core_help
            case 2: 
                return self.music_help
                    
    def update_buttons(self):
        if self.current_page == 1:
            self.prev_button.disabled = True
            self.prev_button.style = discord.ButtonStyle.gray
        else:
            self.prev_button.disabled = False
            self.prev_button.style = discord.ButtonStyle.red
        
        if self.current_page == 2:
            self.next_button.disabled = True
            self.next_button.style = discord.ButtonStyle.gray
        else:
            self.next_button.disabled = False
            self.next_button.style = discord.ButtonStyle.red
        
    
    @discord.ui.button(label='<', style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page -= 1
        await self.update_msg()
        
        
    @discord.ui.button(label='>', style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page += 1
        await self.update_msg()

