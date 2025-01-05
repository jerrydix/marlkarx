import discord
import yt_dlp
from bot import config


class Queue(list):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_song = None
        self._skip_voters = []

    def next_song(self):
        # if list.count > 0:
        self._current_song = self.pop(0)
        return self._current_song

    def next_song_no_pop(self):
        # if list.count > 0:
        self._current_song = self[0]
        return self._current_song

    def clear(self):
        super().clear()
        self._current_song = None

    def add_skip_vote(self, voter: discord.Member):
        self._skip_voters.append(voter)

    def clear_skip_votes(self):
        self._skip_voters.clear()

    @property
    def skip_voters(self):
        return self._skip_voters

    @property
    def current_song(self):
        return self._current_song

    def get_embed(self, song_id: int):

        if song_id <= 0:
            song = self.current_song
        else:
            song = self[song_id - 1]

        if len(song.description) > 300:
            song['description'] = f'{song.description[:300]}...'

        embed = discord.Embed(title="Audio Info", colour=discord.Colour.dark_red())
        embed.set_thumbnail(url=song.thumbnail)
        embed.add_field(name='Song', value=song.title, inline=True)
        embed.add_field(name='Uploader', value=song.uploader, inline=True)
        embed.add_field(name='Duration', value=song.duration_formatted, inline=True)
        # embed.add_field(name='Description', value=song.description, inline=True)
        embed.add_field(name='Upload Date', value=song.upload_date_formatted, inline=True)
        embed.add_field(name='Views', value=song.views, inline=True)
        embed.add_field(name='Likes', value=song.likes, inline=True)
        # embed.add_field(name='Dislikes', value=song.dislikes, inline=True)
        embed.add_field(name='Requested By', value=song.requested_by.display_name, inline=True)

        return embed


class SongRequestError(Exception):
    pass


class Song(dict):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    def __init__(self, url: str, author: discord.Member):
        super().__init__()
        self._url = None
        self._title = None
        self._uploader = None
        self._duration_raw = None
        self._description = None
        self._upload_date_raw = None
        self._views = None
        self._likes = None
        self._dislikes = None
        self._thumbnail = None
        self._requested_by = None

        if url == '':
            self['requested_by'] = author
            return

        if not url.startswith("https://open.spotify.com/"):
            self.download_info(url, author)

        if self.duration_raw > config.MUSIC_MAX_DURATION_MINS * 60:
            raise SongRequestError(f'Your song was too long, keep it under {config.MUSIC_MAX_DURATION_MINS}mins')
        elif self.get('is_live', True):
            raise SongRequestError('Invalid video - either live stream or unsupported website.')
        elif self.url is None:
            raise SongRequestError('Invalid URL provided or no video found.')

    @property
    def url(self):
        if self._url is None:
            return self.get('url', None)
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    @property
    def title(self):
        if self._title is None:
            return self.get('title', 'Unable To Fetch')
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def uploader(self):
        if self._uploader is None:
            return self.get('uploader', 'Unable To Fetch')
        return self._uploader

    @uploader.setter
    def uploader(self, value):
        self._uploader = value

    @property
    def duration_raw(self):
        if self._duration_raw is None:
            return self.get('duration', 0)
        return self._duration_raw

    @duration_raw.setter
    def duration_raw(self, value):
        self._duration_raw = value

    @property
    def duration_formatted(self):
        minutes, seconds = self.duration_raw // 60, self.duration_raw % 60
        return f'[{minutes:02d}:{seconds:02d}]'

    @property
    def description(self):
        if self._description is None:
            return self.get('description', 'Unable To Fetch')
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

    @property
    def upload_date_raw(self):
        if self._upload_date_raw is None:
            return self.get('upload_date', '01011970')
        return self._upload_date_raw

    @upload_date_raw.setter
    def upload_date_raw(self, value):
        self._upload_date_raw = value

    @property
    def upload_date_formatted(self):
        m, d, y = self.upload_date_raw[4:6], self.upload_date_raw[6:8], self.upload_date_raw[0:4]
        return f'{m}/{d}/{y}'

    @property
    def views(self):
        if self._views is None:
            return self.get('view_count', 0)
        return self._views

    @views.setter
    def views(self, value):
        self._views = value

    @property
    def likes(self):
        if self._likes is None:
            return self.get('like_count', 0)
        return self._likes

    @likes.setter
    def likes(self, value):
        self._likes = value

    @property
    def dislikes(self):
        if self._dislikes is None:
            return self.get('dislike_count', 0)
        return self._dislikes

    @dislikes.setter
    def dislikes(self, value):
        self._dislikes = value

    @property
    def thumbnail(self):
        if self._thumbnail is None:
            return self.get('thumbnail', 'http://i.imgur.com/dDTCO6e.png')
        return self._thumbnail

    @thumbnail.setter
    def thumbnail(self, value):
        self._thumbnail = value

    @property
    def requested_by(self):
        if self._requested_by is None:
            return self.get('requested_by', None)
        return self._requested_by

    @requested_by.setter
    def requested_by(self, value):
        self._requested_by = value

    def download_info(self, url: str, author: discord.Member):
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            self.update(ydl.extract_info(url, download=False))

            if not url.startswith('https'):
                self.update(ydl.extract_info(self['entries'][0]['webpage_url'], download=False))

            self['url'] = url
            self['requested_by'] = author
