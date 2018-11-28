# -*- coding: utf-8 -*-

import json

from . import simple_requests as requests
from .cache import Cache

class LastFM:

    def __init__(self, plugin):
        self.plugin = plugin
        self.cache = Cache(self.plugin)
        self.api_url = 'http://ws.audioscrobbler.com/2.0/'
        self.api_key = 'b25b959554ed76058ac220b7b2e0a026'

    def get_artists(self, query):
        artists = []
        params = {
            'method': 'artist.search',
            'artist': query,
            'api_key': self.api_key,
            'format': 'json',
            'limit': '25'
        }
        json_data = requests.get(self.api_url, params=params).json()
        for a in json_data['results']['artistmatches']['artist']:
            artist = a['name']
            image = a['image'][-1]['#text']
            listeners = a['listeners']
            if image:
                artists.append(
                    {
                        'artist': artist,
                        'thumb': image,
                        'listeners': listeners
                    }
                )
        artists = self.remove_duplicates(artists)
        artists = sorted(artists, key=lambda k:int(k['listeners']), reverse=True)
        return artists

    def get_similar_artists(self, artist):
        n = '100'
        value = self.cache.get_value(artist, n, lastfm=True)
        if value == None:
            value = []
            params = {
                'method': 'artist.getsimilar',
                'artist': artist,
                'autocorrect':'1',
                'limit': n,
                'api_key': self.api_key,
                'format': 'json'
            }
            json_data = requests.get(self.api_url, params=params).json()
            for item in json_data['similarartists']['artist']:
                value.append(item['name'])
            self.cache.save_value(artist, n, value, lastfm=True)
        similar_artists = []
        for s in value:
            similar_artists.append(s)
            if len(similar_artists) == int(self.plugin.get_setting('limit_artists')):
                break
        return similar_artists

    def compare_genres(self, genre_list, genres):
        if genre_list and genres:
            x = 0
            for a in genres:
                for b in genre_list:
                    if a == b:
                        x += 1
                    if x == 2:
                        return True
        return False

    def get_artist_genre(self, artist):
        genre_list = self.cache.get_value(artist, 'genre', lastfm='tag')
        if genre_list == None:
            genre_list = []
            params = {
                'method': 'artist.gettoptags',
                'artist': artist,
                'api_key': self.api_key,
                'format': 'json'
            }
            json_data = requests.get(self.api_url, params=params).json()
            for tag in json_data['toptags']['tag']:
                genre_list.append(tag['name'])
                if len(genre_list) == 5:
                    break
            self.cache.save_value(artist, 'genre', genre_list, lastfm='tag')
        return genre_list

    def remove_duplicates(self, artists):
        all_ids = [ i['artist'] for i in artists ]
        artists = [ artists[ all_ids.index(id) ] for id in set(all_ids) ]
        return artists
