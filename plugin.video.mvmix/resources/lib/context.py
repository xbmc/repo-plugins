# -*- coding: utf-8 -*-

class Context:

    def __init__(self, plugin):
        self.cm = []
        self.plugin = plugin

    def list_local_artists(self):
        d = {
            'mode': 'list_local_artists'
        }
        self.cm.append((self.plugin.get_string(30121), 'Container.Update({0})'.format(self.plugin.build_url(d))))
        return self.cm

    def list_artist_videos(self, item, params=''):
        d = {
            'mode': 'list_artist_videos',
            'artist': self.plugin.utfenc(item['artist']),
            'params': params
        }
        if item.get('thumb'):
            d['thumb'] = item['thumb']
        self.cm.append((self.plugin.get_string(30122), 'Container.Update({0})'.format(self.plugin.build_url(d))))
        return self.cm

    def hide_video(self, item):
        d = {
            'mode': 'hide_video',
            'site': item['site'],
            'id': item['id']
        }
        self.cm.append((self.plugin.get_string(30123), 'Container.Update({0})'.format(self.plugin.build_url(d))))
        return self.cm

    def queue_video(self, item):
        artist = self.plugin.utfenc(item['artist'])
        title = self.plugin.utfenc(item['title'])
        params = {
            'name':'{0} - {1}'.format(artist, title),
            'mode': 'play_video',
            'site': item['site'],
            'id': item['id']
        }
        d = {
            'mode': 'queue_video',
            'title': '{0} - {1}'.format(artist, title),
            'thumb': item['thumb'],
            'params': self.plugin.build_url(params)
        }
        self.cm.append((self.plugin.get_string(30124), 'XBMC.RunPlugin({0})'.format(self.plugin.build_url(d))))
        return self.cm

    def remove_artist(self, item):
        d = {
            'mode': 'remove_artist',
            'artist': self.plugin.utfenc(item['artist'])
        }
        self.cm.append((self.plugin.get_string(30125), 'Container.Update({0})'.format(self.plugin.build_url(d))))
        return self.cm
