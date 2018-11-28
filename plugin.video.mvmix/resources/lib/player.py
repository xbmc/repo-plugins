# -*- coding: utf-8 -*-

import random
import sys
import xbmc
import xbmcgui
import xbmcplugin

class mvmixPlayer(xbmc.Player):

    def __init__(self, *args, **kwargs):
        xbmc.Player.__init__(self)

    def playArtist(self, artist, plugin, lastfm, resume, videos):
        self.plugin = plugin
        self.lastfm = lastfm
        self.videos = videos
        self.resume = resume
        self.is_active = True
        self.plugin.set_setting('process', 'True')
        self.plugin.set_setting('limit_artists', self.plugin.get_setting('limit_result'))
        self.similar_artists = []
        self.ignore_list = []
        self.video_list = []
        self.genre_list = self.lastfm.get_artist_genre(artist)
        self.start_artist = artist
        self.last_artist = self.start_artist
        self.artist = artist
        self.set_resume_point()
        self.playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        self.clear_playlist()
        self.add_video(artist)
        self.play(self.playlist)

    def onPlayBackStarted(self):
        self.plugin.log('[mvmixPlayer] playback started')
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
        self.plugin.log('[mvmixPlayer] playback stopped')
        self.is_active = False
        self.clear_playlist()

    def sleep(self, t):
        xbmc.sleep(t)

    def clear_playlist(self):
        self.playlist.clear()

    def add_video(self, artist=False):
        self.plugin.log('[mvmixPlayer] add video')
        video_url = None
        loops = 0
        if not artist:
            self.similar_artists = self.lastfm.get_similar_artists(self.artist)
        while not video_url and not xbmc.abortRequested and self.is_active:
            loops += 1
            self.set_artist(artist)
            self.artist = self.plugin.utfenc(self.artist)
            self.plugin.log('[mvmixPlayer] loop: {0}'.format(str(loops)))
            self.plugin.log('[mvmixPlayer] artist: {0}'.format(str(self.artist)))
            result = self.videos.get_videos(self.artist)
            result = self.remove_added_videos(result)
            self.plugin.log('[mvmixPlayer] videos found: {0}'.format(str(len(result))))
            if result:
                self.plugin.set_setting('limit_artists', self.plugin.get_setting('limit_result'))
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
                self.add_to_ignore_list()
            if artist and not video_url and not self.similar_artists:
                self.similar_artists = self.lastfm.get_similar_artists(artist)
            resume_point = {
                'start_artist': self.start_artist,
                'artist': self.artist,
                'genre_list': self.genre_list,
                'video_list': self.video_list,
                'ignore_list': self.ignore_list
            }
            self.resume.save_resume_point(resume_point)
            self.sleep(500)
            if loops == 20:
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

    def set_similiar_artists(self):
        limit_artists = self.plugin.get_setting('limit_artists')
        if int(limit_artists) <= 50 or not self.similar_artists:
            self.plugin.set_setting('limit_artists', str(int(limit_artists)+5))
            self.similar_artists = self.lastfm.get_similar_artists(self.last_artist)
        elif int(limit_artists) > 50:
            self.similar_artists = self.lastfm.get_similar_artists(self.last_artist)
            if self.similar_artists:
                self.last_artist = self.similar_artists[random.randint(0,(len(self.similar_artists)-1))]

    def set_artist(self, a):
        next_artist = False
        loop = 0
        if a and not self.similar_artists:
            return
        while not next_artist and not xbmc.abortRequested and self.is_active:
            loop += 1
            self.remove_ignored_artists()
            for x in range(0,10):
                if self.similar_artists:
                    artist = self.similar_artists[random.randint(0,(len(self.similar_artists)-1))]
                    genres = self.lastfm.get_artist_genre(artist)
                    if self.lastfm.compare_genres(self.genre_list,genres) == True:
                        self.artist = artist
                        next_artist = True
                        break
                    else:
                        self.add_to_ignore_list(artist)
                        self.remove_ignored_artists()
            if not next_artist:
                self.set_similiar_artists()
            if loop == 20:
                break

    def add_to_ignore_list(self, artist=False):
        if not artist:
            artist = self.artist
        match = False
        for ignored in self.ignore_list:
            if self.plugin.utfenc(artist) == self.plugin.utfenc(ignored):
                match = True
                break
        if not match:
            self.ignore_list.append(artist)
            self.remove_ignored_artists()

    def remove_ignored_artists(self):
        if self.similar_artists and self.ignore_list:
            for a in self.similar_artists[:]:
                for b in self.ignore_list:
                    if self.plugin.utfenc(a) == self.plugin.utfenc(b):
                        self.similar_artists.remove(a)

    def set_resume_point(self):
        resume_point = self.resume.get_resume_point()
        if resume_point:
            if self.start_artist == resume_point['start_artist']:
                self.start_artist = resume_point['start_artist']
                self.artist = resume_point['artist']
                self.genre_list = resume_point['genre_list']
                self.video_list = resume_point['video_list']
                self.ignore_list = resume_point['ignore_list']
