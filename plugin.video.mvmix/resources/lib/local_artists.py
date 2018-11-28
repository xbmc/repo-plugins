# -*- coding: utf-8 -*-

import xbmc
import xbmcvfs
import json
import re

class Local_Artists:

    def __init__(self, plugin):
        self.plugin = plugin
        self.artists_source = self.plugin.get_setting('artists_source')
        self.artists_path = self.plugin.utfenc(self.plugin.get_setting('artists_path'))

    def get_local_artists(self):
        artists = []
        if self.artists_source == '0':
            artists = self.get_artists_from_library()
        else:
            if self.artists_path:
                artists = self.get_artists_from_folder()
        return artists

    def get_artists_from_library(self):
        artists = []
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "params": { "properties": [ "thumbnail" ] }, "sort": { "order": "ascending", "method": "artist", "ignorearticle": false }, "id": 1}')
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_response = json.loads(json_query)
        if json_response.has_key('result') and json_response['result'] != None and json_response['result'].has_key('artists'):
            artists = json_response["result"]["artists"]
        return artists

    def get_artists_from_folder(self):
        artists = []
        dirs, files = xbmcvfs.listdir(self.artists_path)
        for d in dirs:
            dir_ = re.sub('\_', ' ', d)
            match = dir_.split(' - ')
            if len(match) == 1:
                match = dir_.split('-')
            if len(match) > 1:
                artist = match[0].strip()
                thumbnail = ''
                if artist and artist.lower() != 'va':
                    artists.append(
                        {
                            'title': self.plugin.utfenc(artist),
                            'artist': self.plugin.utfenc(artist),
                            'thumb': thumbnail
                        }
                    )
        artists = self.remove_duplicates(artists)
        artists.sort()
        return artists

    def remove_duplicates(self, artists):
        all_ids = [ i['artist'].lower() for i in artists ]
        artists = [ artists[ all_ids.index(id) ] for id in set(all_ids) ]
        return artists
