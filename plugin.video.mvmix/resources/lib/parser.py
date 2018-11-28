# -*- coding: utf-8 -*-

import xbmc

from .items import Items
from .cache import Cache,Artist_List,Hide_List,Resume
from .local_artists import Local_Artists
from .lastfm import LastFM
from .artist_player import mvmixArtistPlayer
from .player import mvmixPlayer
from .videos import Videos
from .context import Context

class Parser:

    def __init__(self, plugin):
        self.plugin = plugin
        self.items = Items(self.plugin)
        self.cache = Cache(self.plugin)
        self.local_artists = Local_Artists(self.plugin)
        self.lastfm = LastFM(self.plugin)
        self.artist_list = Artist_List(self.plugin)
        self.hide_list = Hide_List(self.plugin)
        self.resume = Resume(self.plugin)
        self.videos = Videos(self.plugin)

    def home_items(self):
        self.items.add_item(
            {
                'mode': 'play_artists',
                'title': self.plugin.get_string(30103),
                'cm': Context(self.plugin).list_local_artists()
            }
        )
        artist = self.resume.get_start_artist()
        if artist:
            self.items.add_item(
                {
                    'mode': 'play',
                    'title': '{0}: {1}'.format(self.plugin.get_string(30105), artist),
                    'artist': artist
                }
            )
        self.items.add_item(
            {
                'mode': 'fm_search',
                'title': self.plugin.get_string(30104)
            }
        )
        artist_list = self.artist_list.get_artist_list()
        for item in artist_list:
            item['mode'] = 'play'
            context = Context(self.plugin)
            item['cm'] = context.list_artist_videos(item)
            item['cm'] = context.remove_artist(item)
            self.items.add_item(item)
        self.items.list_items()

    def fm_artists_items(self):
        artist = ''
        artist = self.plugin.enter_artist()
        artist = self.plugin.utfdec(artist)
        self.plugin.log('[{0}] artist entered: {1}'.format(self.plugin.addon_id, self.plugin.utfenc(artist)))
        if artist:
            item = {
                'mode': 'play',
                'artist': self.plugin.utfenc(artist),
                'title': self.plugin.utfenc(artist),
                'params': 'add'
            }
            item['cm'] = Context(self.plugin).list_artist_videos(item, params='add')
            self.items.add_item(item)
            artists = self.lastfm.get_artists(artist)
            self.plugin.log('[{0}] artists found: {1}'.format(self.plugin.addon_id, str(len(artists))))
            for item in artists:
                item['mode'] = 'play'
                item['params'] = 'add'
                item['cm'] = Context(self.plugin).list_artist_videos(item, params='add')
                self.items.add_item(item)
        self.items.list_items()

    def local_artists_items(self):
        artists = self.local_artists.get_local_artists()
        for item in artists:
            item['mode'] = 'play'
            item['cm'] = Context(self.plugin).list_artist_videos(item)
            self.items.add_item(item)
        self.items.list_items(sort=1)

    def play_artists(self, artists=False):
        if not artists:
            artists = self.local_artists.get_local_artists()
        self.kill_old_process()
        if artists:
            player = mvmixArtistPlayer()
            player.playArtists(self.plugin, self.videos, artists)
            while player.is_active and not xbmc.abortRequested:
                player.sleep(200)

    def play(self, artist, params, thumb):
        if params == 'add':
            self.artist_list.add_to_artist_list(artist, thumb)
        self.kill_old_process()
        if artist:
            player = mvmixPlayer()
            player.playArtist(artist, self.plugin, self.lastfm, self.resume, self.videos)
            while player.is_active and self.plugin.get_setting('process') == 'True' and not xbmc.abortRequested:
                player.sleep(200)

    def kill_old_process(self):
        if self.plugin.get_setting('process') == 'True':
            self.plugin.set_setting('process', 'False')
            xbmc.sleep(300)

    def artist_video_items(self, artist, params, thumb):
        if params == 'add':
            self.artist_list.add_to_artist_list(artist, thumb)
        videos = self.videos.get_videos(artist)
        for item in videos:
            context = Context(self.plugin)
            item['mode'] = 'play_video'
            item['cm'] = context.queue_video(item)
            item['cm'] = context.hide_video(item)
            self.items.add_item(item)
        self.items.list_items(sort=1)

    def queue_video(self, title, thumb, params):
        self.items.queue_item(title, thumb, params)

    def hide_video(self, site, id_):
        self.hide_list.add_to_hide_list(site, id_)

    def play_video(self, title, site, id_):
        resolved = False
        video_url = self.plugin.import_site(site, self.plugin).get_video_url(id_)
        if video_url:
            resolved = True
        self.items.play_item(title, video_url, resolved)

    def remove_artist(self, artist):
        self.artist_list.remove_from_artist_list(artist)
