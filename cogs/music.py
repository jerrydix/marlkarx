import asyncio
import os
import subprocess
import validators
from collections import defaultdict
import json

import discord
from discord import app_commands
import yt_dlp
from discord.ext import commands
from discord.utils import get
from pathlib import Path
import requests

from bot import config
from bot.music import Queue, Song, SongRequestError
from pagination import QueueView
from cogs.core import data

def set_str_len(s: str, length: int):
    '''Adds whitespace or trims string to enforce a specific size'''

    return s.ljust(length)[:length]

playlists = []
paused = False;

class Music(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.music_queues = defaultdict(Queue)
        i = 0
        while i < len(data['playlists']):
            playlists.append(discord.app_commands.Choice(name=data['playlists'][i]['name'], value=i))
            i += 1
        
    @app_commands.command(name='play', description='Marl Karx plays a song for you')
    @app_commands.describe(prompt='song name')
    async def playmusic(self, interaction: discord.Interaction, prompt: str = ''):
        '''Adds a song to the queue either by YouTube URL or YouTube Search.'''\
            
        music_queue = self.music_queues[interaction.guild]
        voice = get(self.bot.voice_clients, guild=interaction.guild)
        await interaction.response.defer(ephemeral=False)
        global paused

        try:
            channel = interaction.user.voice.channel
        except:
            await interaction.followup.send('You\'re not connected to a voice channel.')
            return

        if voice is not None and not self.client_in_same_channel(interaction.user, interaction.guild):
            await interaction.followup.send('You\'re not in my voice channel.')
            return
            
        if prompt == '' and voice.is_paused() and paused:
            voice.resume()
            paused = False;
            await interaction.followup.send('Resumed song.')
            return
        elif prompt == '':
            await interaction.followup.send('Cannot process an empty prompt.')
   
        if not validators.url(prompt):
            prompt = f'ytsearch1:{prompt}'

        try:
            song = Song(prompt, author=interaction.user)
        except SongRequestError as e:
            await interaction.followup.send(e.args[0])
            return

        music_queue.append(song)
        await interaction.followup.send(f'Queued song: **{song.title}**')

        print('test1')
        if voice is None or not voice.is_connected():
            print('test2')
            await channel.connect()
            print('test3')

        await self.play_all_songs(interaction.guild)
        
        # @app_commands.checks.has_role(781223345319706646)
        
    @app_commands.command(name='stop', description='Marl Karx stops all music and clears the queue')
    async def stopsong(self, interaction: discord.Interaction):
        '''Admin command that stops playback of music and clears out the music queue.'''

        voice = get(self.bot.voice_clients, guild=interaction.guild)
        queue = self.music_queues.get(interaction.guild)

        if self.client_in_same_channel(interaction.user, interaction.guild):
            voice.stop()
            queue.clear()
            await interaction.response.send_message('Stopping playback.')
            await voice.disconnect()
        else:
            await interaction.response.send_message('You\'re not in a voice channel with me.')
    
    @app_commands.command(name='skip', description='Marl Karx skips the currently playing song')
    async def skipsong(self, interaction: discord.Interaction):
        '''Puts in your vote to skip the currently played song.'''

        voice = get(self.bot.voice_clients, guild=interaction.guild)
        queue = self.music_queues.get(interaction.guild)

        if not self.client_in_same_channel(interaction.user, interaction.guild):
            await interaction.response.send_message('You\'re not in a voice channel with me.')
            return

        if voice is None or not voice.is_playing():
            await interaction.response.send_message('I\'m not playing a song right now.')
            return

        if interaction.user in queue.skip_voters:
            await interaction.response.send_message('You\'ve already voted to skip this song.')
            return

        channel = interaction.user.voice.channel
        required_votes = round(len(channel.members) / 2)

        queue.add_skip_vote(interaction.user)

        if len(queue.skip_voters) >= required_votes:
            await interaction.response.send_message('Skipping song after successful vote.')
            global paused
            paused = False;
            voice.stop()
        else:
            await interaction.response.send_message(f'You voted to skip this song. {required_votes - len(queue.skip_voters)} more votes are '
                           f'required.')
    
    @app_commands.command(name='fskip', description='Force skip a song')
    @app_commands.checks.has_role(781223345319706646)
    async def fskipsong(self, interaction: discord.Interaction):
        '''Admin command that forces skipping of the currently playing song.'''

        voice = get(self.bot.voice_clients, guild=interaction.guild)

        if not self.client_in_same_channel(interaction.user, interaction.guild):
            await interaction.response.send_message('You\'re not in a voice channel with me.')
        elif voice is None or not voice.is_playing():
            await interaction.response.send_message('I\'m not playing a song right now.')
        else:
            voice.stop()
            await interaction.response.send_message('Skipped song.')
    
    @app_commands.command(name='fremove', description='Force remove a song')
    @app_commands.checks.has_role(781223345319706646)
    async def fremovesong(self, interaction: discord.Interaction, id: int = None):
        '''Admin command to forcibly remove a song from the queue by it's position.'''

        queue = self.music_queues.get(interaction.guild)

        if not self.client_in_same_channel(interaction.user, interaction.guild):
            await interaction.response.send_message('You\'re not in a voice channel with me.')
            return

        if id is None or 0:
            await interaction.response.send_message('You need to specify a song by it\'s queue index.')
            return

        try:
            song = queue[id - 1]
        except IndexError:
            await interaction.response.send_message('A song does not exist at this queue index.')
            return

        queue.pop(id - 1)
        await interaction.response.send_message(f'Removed {song.title} from the queue.')
        return
    
    @app_commands.command(name='queuedepr', description='Marl Karx shows the current song queue')
    async def queuesong(self, interaction: discord.Interaction, page: int = 1):
        '''Prints out a specified page of the music queue, defaults to first page.'''

        queue = self.music_queues.get(interaction.guild)

        if not self.client_in_same_channel(interaction.user, interaction.guild):
            await interaction.response.send_message('You\'re not in a voice channel with me.')
            return

        if not queue:
            await interaction.response.send_message('I don\'t have anything in my queue right now.')
            return

        if len(queue) < config.MUSIC_QUEUE_PER_PAGE * (page - 1):
            await interaction.response.send_message('I don\'t have that many pages in my queue.')
            return

        to_send = f'```\n    {set_str_len("Song", 66)}{set_str_len("Uploader", 36)}Requested By\n'

        for pos, song in enumerate(queue[:config.MUSIC_QUEUE_PER_PAGE * page], start=config.MUSIC_QUEUE_PER_PAGE * (page - 1)):
            title = set_str_len(song.title, 65)
            uploader = set_str_len(song.uploader, 35)
            to_send += f'{set_str_len(f"{pos + 1})", 4)}{title}|{uploader}|{song.requested_by.display_name}\n'

        await interaction.response.send_message(to_send + '```')
        
        
    @app_commands.command(name='songinfo', description='Displays info about the currently playing song')
    @app_commands.describe(index='index')
    async def song_info(self, interaction: discord.Interaction, index: int = 0):
        queue = self.music_queues.get(interaction.guild)

        if index not in range(len(queue) + 1):
            return interaction.followup.send('A song does not exist at that index in the queue.')

        embed = queue.get_embed(index)
        await interaction.response.send_message(embed=embed)
        
        
    @app_commands.command(name='nowplaying', description='Displays info about the currently playing song')
    @app_commands.describe(index='index')
    async def nowplaying(self, interaction: discord.Interaction, index: int = 0):
        queue = self.music_queues.get(interaction.guild)

        if index not in range(len(queue) + 1):
            return interaction.followup.send('A song does not exist at that index in the queue.')

        embed = queue.get_embed(index)
        await interaction.response.send_message(embed=embed)
    
        
    @app_commands.command(name='queue', description='Marl Karx shows the current song queue')
    async def queueview(self, interaction: discord.Interaction):
        queue = self.music_queues.get(interaction.guild)
        
        if not queue:
            await interaction.response.send_message('I don\'t have anything in my queue right now.')
            return
        
        view = QueueView()
        view.data = queue
        await view.send(interaction)
        
    
    @app_commands.command(name='pause', description='Pause the currently playing song')
    async def pause(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        voice = get(self.bot.voice_clients, guild=interaction.guild)
        
        if not self.client_in_same_channel(interaction.user, interaction.guild):
            await interaction.response.send_message('You\'re not in a voice channel with me.')
            return
        
        if not voice.is_playing():
            await interaction.response.send_message('I don\'t have anything playing right now.')
            return
        
        global paused
        paused = True
        voice.pause()
        await interaction.followup.send('Paused song.')
       
        
    @app_commands.command(name='createplaylist', description='Create a new playlist')
    @app_commands.describe(name='name')
    async def createplaylist(self, interaction: discord.Interaction, name: str):
        if 'playlists' in data and len(data['playlists']) < 10:
            for list in data['playlists']:
                if list['name'] == name:
                    await interaction.response.send_message('This playlist already exits. Can\'t add playlist with same name twice.')
                    return
            c = open('config.json', 'w')
            list_obj = {'name': name, 'tracks': []}
            json.dumps(list_obj)
            data['playlists'].append(list_obj)
            json.dump(data, c)
            c.close()
            await interaction.response.send_message(f'Added playlist **{name}**')
            
        elif 'playlists' in data:
            await interaction.response.send_message('Cannot add more than 10 playlists.')
            return
        else:
            print(TODO)
            c = open('config.json', 'w')
            # playlists = {}
            list_obj = {'name': name, 'tracks': []}
            json.dumps(list_obj)
            data['playlists'].append(list_obj)
            json.dump(data, c)
            c.close()
    
            
    @app_commands.command(name='playlistadd', description='Add a song to a playlist')
    @app_commands.describe(playlist='playlist')
    @app_commands.choices(playlist=playlists)
    async def playlistadd(self, interaction: discord.Interaction, playlist: discord.app_commands.Choice[int], prompt: str):
        await interaction.response.defer(ephemeral=False)
        if not validators.url(prompt):
            prompt = f'ytsearch1:{prompt}'

        try:
            song = Song(prompt, author=interaction.user)
        except SongRequestError as e:
            await interaction.followup.send(e.args[0])
            return

        c = open('config.json', 'w')
        data['playlists'][playlist.value]['tracks'].append(song.title)
        json.dump(data, c)
        c.close()
        playlists.append(discord.app_commands.Choice(name=data['playlists'][len(data['playlists']) - 1]['name'], value=len(data['playlists']) - 1))
        await interaction.followup.send(f'Added **{song.title}** to the **{playlist.name}** playlist.')


    @app_commands.command(name='playlist', description='Play a playlist')
    @app_commands.describe(playlist='playlist')
    @app_commands.choices(playlist=playlists)
    async def playlist(self, interaction: discord.Interaction, playlist: discord.app_commands.Choice[int]):
        await interaction.response.defer(ephemeral=False)
        music_queue = self.music_queues[interaction.guild]
        voice = get(self.bot.voice_clients, guild=interaction.guild)
        try:
            channel = interaction.user.voice.channel
        except:
            await interaction.followup.send('You\'re not connected to a voice channel.')
            return

        if voice is not None and not self.client_in_same_channel(interaction.user, interaction.guild):
            await interaction.followup.send('You\'re not in my voice channel.')
            return
            
        if len(data['playlists'][playlist.value]['tracks']) == 0:
            await interaction.followup.send('There are no tracks in this playlist.')
            return
        
        first = True
        list = data['playlists'][playlist.value]['name']
        
        for track in data['playlists'][playlist.value]['tracks']:
            try:
                song = Song(f'ytsearch1:{track}', author=interaction.user)
            except SongRequestError as e:
                await interaction.followup.send(e.args[0])
                return
            music_queue.append(song)
            if first:
                await interaction.followup.send(f'Queued all tracks from the **{list}** playlist.')
                if voice is None or not voice.is_connected():
                    await channel.connect()   
                first = False
        print ('test')
        await self.play_all_songs(interaction.guild)


    @commands.command()
    async def play(self, ctx: commands.Context, url: str, *args: str):
        '''Adds a song to the queue either by YouTube URL or YouTube Search.'''

        music_queue = self.music_queues[ctx.guild]
        voice = get(self.bot.voice_clients, guild=ctx.guild)

        try:
            channel = ctx.message.author.voice.channel
        except:
            await ctx.send('You\'re not connected to a voice channel.')
            return

        if voice is not None and not self.client_in_same_channel(ctx.message.author, ctx.guild):
            await ctx.send('You\'re not in my voice channel.')
            return

        if not validators.url(url):
            url = f'ytsearch1:{url} {" ".join(args)}'

        try:
            song = Song(url, author=ctx.author)
        except SongRequestError as e:
            await ctx.send(e.args[0])
            return

        music_queue.append(song)
        await ctx.send(f'Queued song: **{song.title}**')

        if voice is None or not voice.is_connected():
            await channel.connect()

        await self.play_all_songs(ctx.guild)

    @commands.command()
    @commands.has_role(781223345319706646)
    async def stop(self, ctx: commands.Context):
        '''Admin command that stops playback of music and clears out the music queue.'''

        voice = get(self.bot.voice_clients, guild=ctx.guild)
        queue = self.music_queues.get(ctx.guild)

        if self.client_in_same_channel(ctx.message.author, ctx.guild):
            voice.stop()
            queue.clear()
            await ctx.send('Stopping playback')
            await voice.disconnect()
        else:
            await ctx.send('You\'re not in a voice channel with me.')

    @commands.command()
    async def skip(self, ctx: commands.Context):
        '''Puts in your vote to skip the currently played song.'''

        voice = get(self.bot.voice_clients, guild=ctx.guild)
        queue = self.music_queues.get(ctx.guild)

        if not self.client_in_same_channel(ctx.message.author, ctx.guild):
            await ctx.send('You\'re not in a voice channel with me.')
            return

        if voice is None or not voice.is_playing():
            await ctx.send('I\'m not playing a song right now.')
            return

        if ctx.author in queue.skip_voters:
            await ctx.send('You\'ve already voted to skip this song.')
            return

        channel = ctx.message.author.voice.channel
        required_votes = round(len(channel.members) / 2)

        queue.add_skip_vote(ctx.author)

        if len(queue.skip_voters) >= required_votes:
            await ctx.send('Skipping song after successful vote.')
            voice.stop()
        else:
            await ctx.send(f'You voted to skip this song. {required_votes - len(queue.skip_voters)} more votes are '
                           f'required.')

    @commands.command()
    @commands.has_role(781223345319706646)
    async def fskip(self, ctx: commands.Context):
        '''Admin command that forces skipping of the currently playing song.'''

        voice = get(self.bot.voice_clients, guild=ctx.guild)

        if not self.client_in_same_channel(ctx.message.author, ctx.guild):
            await ctx.send('You\'re not in a voice channel with me.')
        elif voice is None or not voice.is_playing():
            await ctx.send('I\'m not playing a song right now.')
        else:
            voice.stop()

    @commands.command()
    async def songinfo(self, ctx: commands.Context, song_index: int = 0):
        '''Print out more information on the song currently playing.'''

        queue = self.music_queues.get(ctx.guild)

        if song_index not in range(len(queue) + 1):
            await ctx.send('A song does not exist at that index in the queue.')
            return

        embed = queue.get_embed(song_index)
        await ctx.send(embed=embed)

    @commands.command()
    async def remove(self, ctx: commands.Context, song_id: int = None):
        '''Removes the last song you requested from the queue, or a specific song if queue position specified.'''

        if not self.client_in_same_channel(ctx.message.author, ctx.guild):
            await ctx.send('You\'re not in a voice channel with me.')
            return

        if song_id is None:
            queue = self.music_queues.get(ctx.guild)

            for index, song in reversed(list(enumerate(queue))):
                if ctx.author.id == song.requested_by.id:
                    queue.pop(index)
                    await ctx.send(f'Song "{song.title}" removed from queue.')
                    return
        else:
            queue = self.music_queues.get(ctx.guild)

            try:
                song = queue[song_id - 1]
            except IndexError:
                await ctx.send('An invalid index was provided.')
                return

            if ctx.author.id == song.requested_by.id:
                queue.pop(song_id - 1)
                await ctx.send(f'Song {song.title} removed from queue.')
            else:
                await ctx.send('You cannot remove a song requested by someone else.')

    @commands.command()
    @commands.has_role(781223345319706646)
    async def fremove(self, ctx: commands.Context, song_id: int = None):
        '''Admin command to forcibly remove a song from the queue by it's position.'''

        queue = self.music_queues.get(ctx.guild)

        if not self.client_in_same_channel(ctx.message.author, ctx.guild):
            await ctx.send('You\'re not in a voice channel with me.')
            return

        if song_id is None or 0:
            await ctx.send('You need to specify a song by it\'s queue index.')
            return

        try:
            song = queue[song_id - 1]
        except IndexError:
            await ctx.send('A song does not exist at this queue index.')
            return

        queue.pop(song_id - 1)
        await ctx.send(f'Removed {song.title} from the queue.')
        return

    @commands.command()
    async def queue(self, ctx: commands.Context, page: int = 1):
        '''Prints out a specified page of the music queue, defaults to first page.'''

        queue = self.music_queues.get(ctx.guild)

        if not self.client_in_same_channel(ctx.message.author, ctx.guild):
            await ctx.send('You\'re not in a voice channel with me.')
            return

        if not queue:
            await ctx.send('I don\'t have anything in my queue right now.')
            return

        if len(queue) < config.MUSIC_QUEUE_PER_PAGE * (page - 1):
            await ctx.send('I don\'t have that many pages in my queue.')
            return

        to_send = f'```\n    {set_str_len("Song", 66)}{set_str_len("Uploader", 36)}Requested By\n'

        for pos, song in enumerate(queue[:config.MUSIC_QUEUE_PER_PAGE * page], start=config.MUSIC_QUEUE_PER_PAGE * (page - 1)):
            title = set_str_len(song.title, 65)
            uploader = set_str_len(song.uploader, 35)
            to_send += f'{set_str_len(f"{pos + 1})", 4)}{title}|{uploader}|{song.requested_by.display_name}\n'

        await ctx.send(to_send + '```')

    async def play_all_songs(self, guild: discord.Guild):
        queue = self.music_queues.get(guild)
        print('before while')
        # Play next song until queue is empty
        while queue:
            print('in while before')
            await self.wait_for_end_of_song(guild)
            print('in while after')
            song = queue.next_song()

            # if int(queue.count) > 0:
            await self.play_song(guild, song)

        # Disconnect after song queue is empty
        await self.inactivity_disconnect(guild)

    async def play_song(self, guild: discord.Guild, song: Song):
        '''Downloads and starts playing a YouTube video's audio.'''
        
        audio_dir = os.path.join('.', 'audio')
        audio_path = os.path.join(audio_dir, f'{guild.id}')
        output_id = guild.id + 1
        output_path = os.path.join(audio_dir, f'{output_id}')
        
        try:
            os.remove(audio_path + '.opus')
        except:
            pass
        
        try:
            os.remove(output_path + '.opus')
        except:
            pass

        voice = get(self.bot.voice_clients, guild=guild)
        queue = self.music_queues.get(guild)
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '192',
            }],
            'outtmpl': audio_path
        }

        Path(audio_dir).mkdir(parents=True, exist_ok=True)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([f'{song.url}'])
            except:
                await self.play_all_songs(guild)
                print('Error downloading song. Skipping.')
                return
        
        # subprocess.run(['ffmpeg', '-i', os.path.abspath(audio_path) + '.opus', '-af', 'loudnorm=I=-16:LRA=11:TP=-1.5', os.path.abspath(output_path) + '.opus'])
        voice.play(discord.FFmpegPCMAudio(os.path.abspath(audio_path) + '.opus'))
        queue.clear_skip_votes()


    async def stream_song(self, guild: discord.Guild, prompt: str):
        '''Streams a YouTube video's audio into a VC.'''
        FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        audio_dir = os.path.join('.', 'audio')
        audio_path = os.path.join(audio_dir, f'{guild.id}')
        output_id = guild.id + 1
        output_path = os.path.join(audio_dir, f'{output_id}')
        
        try:
            os.remove(audio_path + '.opus')
        except:
            pass
        
        try:
            os.remove(output_path + '.opus')
        except:
            pass

        voice = get(self.bot.voice_clients, guild=guild)
        queue = self.music_queues.get(guild)
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'opus',
                'preferredquality': '192',
            }],
            'outtmpl': audio_path
        }

        Path(audio_dir).mkdir(parents=True, exist_ok=True)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([f'{song.url}'])
            except:
                await self.play_all_songs(guild)
                print('Error downloading song. Skipping.')
                return
        
        # subprocess.run(['ffmpeg', '-i', os.path.abspath(audio_path) + '.opus', '-af', 'loudnorm=I=-16:LRA=11:TP=-1.5', os.path.abspath(output_path) + '.opus'])
        voice.play(discord.FFmpegPCMAudio(os.path.abspath(audio_path) + '.opus'))
        queue.clear_skip_votes()


    def search(query):
        with yt_dlp.YoutubeDL({'format': 'bestaudio', 'noplaylist':'True'}) as ydl:
            try: requests.get(query)
            except: info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            else: info = ydl.extract_info(query, download=False)
        return (info, info['formats'][0]['url'])


    async def wait_for_end_of_song(self, guild: discord.Guild):
        voice = get(self.bot.voice_clients, guild=guild)
        global paused
        while voice.is_playing() or paused:
            await asyncio.sleep(1)

    async def inactivity_disconnect(self, guild: discord.Guild):
        '''If a song is not played for 5 minutes, automatically disconnects bot from server.'''

        voice = get(self.bot.voice_clients, guild=guild)
        queue = self.music_queues.get(guild)
        last_song = queue.current_song

        while voice.is_playing():
            await asyncio.sleep(10)

        await asyncio.sleep(300)
        if queue.current_song == last_song:
            await voice.disconnect()

    def client_in_same_channel(self, author: discord.Member, guild: discord.Guild):
        '''Checks to see if a client is in the same channel as the bot.'''

        voice = get(self.bot.voice_clients, guild=guild)

        try:
            channel = author.voice.channel
        except AttributeError:
            return False

        return voice is not None and voice.is_connected() and channel == voice.channel


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Music(client))
    
