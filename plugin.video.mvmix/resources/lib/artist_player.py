# -*- coding: utf-8 -*-

import random
import sys
import xbmc
import xbmcgui
import xbmcplugin

class mvmixArtistPlayer(xbmc.Player):

    def __init__(self, *args, **kwargs):
        xbmc.Player.__init__(self)

    def playArtists(self, plugin, videos, artists):
        self.plugin = plugin
        self.videos = videos
        self.is_active = True
        self.artists = artists
        self.video_list = []
        self.playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        self.clear_playlist()
        self.add_video()
        self.play(self.playlist)

    def onPlayBackStarted(self):
        self.plugin.log('[mvmixArtistPlayer] playback started')
        self.sleep(2000)
        if xbmc.Player().isPlayingVideo():
            duration = 15*1000
            title = self.plugin.get_string(30102)
            msg = xbmc.getInfoLabel('VideoPlayer.Title')
            thumb = xbmc.getInfoImage('VideoPlayer.Cover')
            self.plugin.notification(title, msg, thumb, duration)
            self.add_video()
            self.add_next_video()      

    def onPlayBackStopped(self):
        self.plugin.log('[mvmixArtistPlayer] playback stopped')
        self.is_active = False
        self.clear_playlist()

    def sleep(self, t):
        xbmc.sleep(t)

    def clear_playlist(self):
        self.playlist.clear()

    def add_video(self,artist=False):
        self.plugin.log('[mvmixArtistPlayer] add video')
        video_url = None
        loops = 0
        while not video_url and not xbmc.abortRequested and self.is_active:
            if self.artists:
                self.set_artist()
            else:
                self.is_active = False
                break
            self.plugin.log('[mvmixArtistPlayer] loops: {0}'.format(str(loops)))
            self.plugin.log('[mvmixArtistPlayer] artist: {0}'.format(str(self.artist)))
            result = self.videos.get_videos(self.artist)
            result = self.remove_added_videos(result)
            self.plugin.log('[mvmixArtistPlayer] videos found: %s' % str(len(result)))
            if result:
                video = result[random.randint(0,(len(result)-1))]
                self.video_list.append(video)
                video_url = self.plugin.import_site(video['site'], self.plugin).get_video_url(video['id'])
                if video_url:
                    artist = self.plugin.utfenc(video['artist'])
                    title = self.plugin.utfenc(video['title'])
                    name = '{0} - {1}'.format(artist, title)
                    listitem = xbmcgui.ListItem(name, thumbnailImage=video['thumb'])
                    self.playlist.add(video_url, listitem=listitem)
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, listitem)
            else:
                self.remove_artist_from_list()
            self.sleep(500)
            loops += 1
            if loops == 20:
                self.video_list = []
            elif loops > 30:
                self.is_active = False
                break

    def add_next_video(self):
        if xbmc.Player().isPlayingVideo():
            result = int(xbmc.getInfoLabel('Playlist.Length(video)')) - int(xbmc.getInfoLabel('Playlist.Position(video)'))
            if result < 2:
                self.add_video()

    def remove_added_videos(self, result):
        if result and self.video_list:
            for v in result[:]:
                for v_l in self.video_list:
                    if self.plugin.utfenc(v['title']) == self.plugin.utfenc(v_l['title']):
                        result.remove(v)
        return result

    def remove_artist_from_list(self):
        self.artists = [x for x in self.artists if self.plugin.utfenc(x['artist']) != self.plugin.utfenc(self.artist)]

    def set_artist(self):
        artist = self.artists[random.randint(0,(len(self.artists)-1))]
        self.artist = self.plugin.utfenc(artist['artist'])
