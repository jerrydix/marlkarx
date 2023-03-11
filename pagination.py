import discord
from discord.ext import commands
from discord import app_commands

class QueueView(discord.ui.View):
    
    current_page: int = 1
    sep: int = 10
    
    async def send(self, interaction: discord.Interaction):
        self.message = await interaction.response.send_message('**Showing the queue:**')
        self.message = await interaction.channel.send(view=self)
        await self.update_msg(self.data[:self.sep])
        
    def create_embed(self, data):
        embed = discord.Embed(title='Current Queue:', colour=discord.Colour.dark_red())
        for i in data:
            embed.add_field(name=i.title, value=i.duration_formatted, inline=False)
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
    
        
        
    

