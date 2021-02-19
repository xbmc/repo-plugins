from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import json
import time

from future.standard_library import install_aliases
from future.utils import (PY2)

install_aliases()

from urllib.parse import unquote
import requests
from builtins import *
from html.parser import HTMLParser


class Band:
    def __init__(self, band_id=None, band_name=""):
        self.band_name = band_name
        self.band_id = str(band_id)

    def __eq__(self, other):
        if type(other) is type(self):
            return self.band_id == other.band_id
        else:
            return False

    def __hash__(self):
        return hash(self.band_id)


class Album:
    ALBUM_TYPE = "a"
    TRACK_TYPE = "t"

    def __init__(self, album_id, album_name, art_id, item_type=ALBUM_TYPE, genre=""):
        self.album_name = album_name
        self.art_id = art_id
        self.album_id = album_id
        self.item_type = item_type
        self.genre = genre

    def get_art_img(self, quality=9):
        return "https://f4.bcbits.com/img/a0{art_id}_{quality}.jpg".format(art_id=self.art_id, quality=quality)


class Track:
    def __init__(self, track_name, file, duration, number=None):
        self.track_name = track_name
        self.file = file
        self.duration = duration
        self.number = number


class _DataBlobParser(HTMLParser):
    data_blob = None

    def handle_starttag(self, tag, attrs):
        for attr in attrs:
            if attr[0] == "data-blob" and self.data_blob is None:
                data_html = attr[1]
                self.data_blob = json.loads(data_html)


class _PlayerDataParser(HTMLParser):
    player_data = None

    def handle_data(self, data):
        if "playerdata" in data:
            end = data.index('};') + 1
            player_data = data[26:end]
            self.player_data = json.loads(player_data)


class Bandcamp:

    def __init__(self, user_name):
        self.data_blob = None
        if user_name is None:
            self.user_name = ""
        else:
            self.user_name = user_name

    @staticmethod
    def discover(genre="all", sub_genre="any", slice="best", page=0):
        url = "https://bandcamp.com/api/discover/3/get_web?g={genre}&t={sub_genre}&s={slice}&p={page}&f=all" \
            .format(genre=genre, sub_genre=sub_genre, slice=slice, page=page)
        request = requests.get(url)
        items = json.loads(request.text)['items']
        discover_list = {}
        for item in items:
            track = Track(item['featured_track']['title'], item['featured_track']['file']['mp3-128'],
                          item['featured_track']['duration'])
            album_genre = u'{genre} ({slice})'.format(genre=item['genre_text'], slice=slice)
            album = Album(album_id=item['id'], album_name=item['primary_text'], art_id=item['art_id'],
                          genre=album_genre, item_type=item['type'])
            band = Band(band_id=item['band_id'], band_name=item['secondary_text'])
            discover_list[band] = {album: [track]}
        return discover_list

    def get_fan_id(self):
        return self._get_data_blob()['fan_data']['fan_id']

    def get_genres(self):
        return self._get_data_blob()['signup_params']['genres']

    def get_subgenres(self):
        return self._get_data_blob()['signup_params']['subgenres']

    def get_collection(self, fan_id, count=1000):
        url = "https://bandcamp.com/api/fancollection/1/collection_items"
        token = self._get_token()
        body = '{{"fan_id": "{fan_id}", "older_than_token": "{token}", "count":"{count}"}}' \
            .format(fan_id=fan_id, token=token, count=count)
        x = requests.post(url, data=body)
        items = json.loads(x.text)['items']
        bands = {}
        for item in items:
            album = Album(album_id=item['tralbum_id'], album_name=item['item_title'],
                          art_id=item['item_art_id'], item_type=item['tralbum_type'])
            band = Band(band_id=item['band_id'], band_name=item['band_name'])
            if band not in bands:
                bands[band] = {}
            bands[band].update({album: [None]})
        return bands

    def get_wishlist(self, fan_id, count=1000):
        url = "https://bandcamp.com/api/fancollection/1/wishlist_items"
        token = self._get_token()
        body = '{{"fan_id": "{fan_id}", "older_than_token": "{token}", "count":"{count}"}}' \
            .format(fan_id=fan_id, token=token, count=count)
        x = requests.post(url, data=body)
        items = json.loads(x.text)['items']
        bands = {}
        for item in items:
            album = Album(album_id=item['tralbum_id'], album_name=item['item_title'],
                          art_id=item['item_art_id'], item_type=item['tralbum_type'])
            band = Band(band_id=item['band_id'], band_name=item['band_name'])
            if band not in bands:
                bands[band] = {}
            bands[band].update({album: [None]})
        return bands

    def get_album(self, album_id, item_type=Album.ALBUM_TYPE, band_id=1):
        url = "https://bandcamp.com/api/mobile/24/tralbum_details" \
              "?band_id={band_id}&tralbum_type={item_type}&tralbum_id={album_id}" \
            .format(band_id=band_id, item_type=item_type, album_id=album_id)
        request = requests.get(url)
        album_details = json.loads(request.text)
        track_list = []
        for track in album_details['tracks']:
            # sometimes not all tracks are available online
            if track['streaming_url'] is not None:
                track_list.append(
                    Track(track['title'], track['streaming_url']['mp3-128'], track['duration'],
                          number=track['track_num']))
        art_id = album_details['art_id']
        band = Band(band_name=album_details['band']['name'], band_id=album_details['band']['band_id'])
        album = Album(album_id, album_details['title'], art_id)
        return band, album, track_list

    def get_album_legacy(self, album_id, item_type="album"):
        url = "https://bandcamp.com/EmbeddedPlayer/{item_type}={album_id}" \
            .format(album_id=album_id, item_type=item_type)
        request = requests.get(url)
        parser = _PlayerDataParser()
        content = request.text
        parser.feed(content)
        player_data = parser.player_data
        track_list = []
        for track in player_data['tracks']:
            # sometimes not all tracks are available online
            if track['file'] is not None:
                track_list.append(
                    Track(track['title'], track['file']['mp3-128'], track['duration'], number=track['tracknum'] + 1))
        art_id = player_data['album_art_id']
        if item_type == "track":
            art_id = track['art_id']
        band = Band(band_name=player_data['artist'])
        album = Album(album_id, player_data['album_title'], art_id)
        return band, album, track_list

    def get_album_by_url(self, url):
        url = unquote(url)
        request = requests.get(url)
        parser = _DataBlobParser()
        parser.feed(request.text)
        if '/album/' in url:
            album_id = parser.data_blob['album_id']
            item_type = Album.ALBUM_TYPE
        elif '/track/' in url:
            album_id = parser.data_blob['track_id']
            item_type = Album.TRACK_TYPE
        return self.get_album(album_id, item_type)

    def get_band(self, band_id):
        url = "https://bandcamp.com/api/mobile/24/band_details"
        body = '{{"band_id": "{band_id}"}}'.format(band_id=band_id)
        request = requests.post(url, data=body)
        band_details = json.loads(request.text)
        band = Band(band_id=band_details['id'], band_name=band_details['name'])
        albums = []
        for album in band_details['discography']:
            albums.append(Album(album_id=album['item_id'], album_name=album['title'],
                                art_id=album['art_id'], item_type=album['item_type'][0]))
        return band, albums

    def search(self, query):
        if PY2:
            query = query.decode('utf-8')
        url = "https://bandcamp.com/api/fuzzysearch/1/autocomplete?q={query}".format(query=query)
        request = requests.get(url)
        results = json.loads(request.text)['auto']['results']
        items = []
        for result in results:
            if result['type'] == "b":
                item = Band(band_id=result['id'], band_name=result['name'])
            else:
                item = Album(album_id=result['id'], album_name=result['name'],
                             art_id=result['art_id'], item_type=result['type'])
            if item is not None:
                items.append(item)
        return items


    @staticmethod
    def _get_token():
        return str(int(time.time())) + "::FOO::"

    def _get_data_blob(self):
        if self.data_blob is None:
            url = "https://bandcamp.com/{user_name}".format(user_name=self.user_name)
            request = requests.get(url)
            parser = _DataBlobParser()
            content = request.content.decode('utf-8')
            parser.feed(content)
            self.data_blob = parser.data_blob
        return self.data_blob
