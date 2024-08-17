from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import json
import time

from future.standard_library import install_aliases
from future.utils import (PY2)

install_aliases()

from urllib.parse import unquote, quote_plus
from urllib.request import Request, urlopen
from builtins import *
from html.parser import HTMLParser

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'

def urlopen_ua(url, data=None):
    return urlopen(Request(url, data=data, headers={'User-Agent': USER_AGENT}), timeout=5)

def req(url, data=None):
    body = data.encode() if data else None
    return urlopen_ua(url, data=body).read().decode()

class Band:
    def __init__(self, band_id=None, band_name="", band_img=None):
        self.band_name = band_name
        self.band_id = str(band_id)
        self.band_img = band_img

    def __eq__(self, other):
        if type(other) is type(self):
            return self.band_id == other.band_id
        else:
            return False

    def __hash__(self):
        return hash(self.band_id)

    def get_art_img(self, quality=20):
        if self.band_img:
            return "https://f4.bcbits.com/img/{band_img}_{quality}.jpg".format(band_img=self.band_img, quality=quality)


class Album:
    ALBUM_TYPE = "a"
    TRACK_TYPE = "t"

    def __init__(self, album_id, album_name, art_id, item_type=ALBUM_TYPE, genre="", band=None):
        self.album_name = album_name
        self.art_id = art_id
        self.album_id = album_id
        self.item_type = item_type
        self.genre = genre
        self.band = band

    def get_art_img(self, quality=2):
        if self.art_id:
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
        request = req(url)
        items = json.loads(request)['items']
        discover_list = {}
        for item in items:
            track = Track(item['featured_track']['title'], item['featured_track']['file']['mp3-128'],
                          item['featured_track']['duration'])
            album_genre = u'{genre} ({slice})'.format(genre=item['genre_text'], slice=slice)
            band = Band(band_id=item['band_id'], band_name=item['secondary_text'],
                        band_img=item['bio_image']['image_id'])
            album = Album(album_id=item['id'], album_name=item['primary_text'], art_id=item['art_id'],
                          genre=album_genre, item_type=item['type'], band=band)
            discover_list[band] = {album: [track]}
        return discover_list

    def get_fan_id(self):
        return self._get_data_blob()['fan_data']['fan_id']

    def get_genres(self):
        return self._get_data_blob()['signup_params']['genres']

    def get_subgenres(self):
        return self._get_data_blob()['signup_params']['subgenres']

    def get_collection(self, fan_id, count=1000, return_albums=False):
        url = "https://bandcamp.com/api/fancollection/1/collection_items"
        token = self._get_token()
        body = '{{"fan_id": "{fan_id}", "older_than_token": "{token}", "count":"{count}"}}' \
            .format(fan_id=fan_id, token=token, count=count)
        x = req(url, data=body)
        items = json.loads(x)['items']
        bands = {}
        albums = []
        for item in items:
            band = Band(band_id=item['band_id'], band_name=item['band_name'])
            album = Album(album_id=item['tralbum_id'], album_name=item['item_title'],
                          art_id=item['item_art_id'], item_type=item['tralbum_type'],
                          band=band)
            if band not in bands:
                bands[band] = {}
            bands[band].update({album: [None]})
            albums.append(album)
        if return_albums:
            return albums
        else:
            return bands

    def get_wishlist(self, fan_id, count=1000, return_albums=False):
        url = "https://bandcamp.com/api/fancollection/1/wishlist_items"
        token = self._get_token()
        body = '{{"fan_id": "{fan_id}", "older_than_token": "{token}", "count":"{count}"}}' \
            .format(fan_id=fan_id, token=token, count=count)
        x = req(url, data=body)
        items = json.loads(x)['items']
        bands = {}
        albums = []
        for item in items:
            band = Band(band_id=item['band_id'], band_name=item['band_name'])
            album = Album(album_id=item['tralbum_id'], album_name=item['item_title'],
                          art_id=item['item_art_id'], item_type=item['tralbum_type'],
                          band=band)
            if band not in bands:
                bands[band] = {}
            bands[band].update({album: [None]})
            albums.append(album)
        if return_albums:
            return albums
        else:
            return bands

    def get_album(self, album_id, item_type=Album.ALBUM_TYPE, band_id=1):
        url = "https://bandcamp.com/api/mobile/24/tralbum_details" \
              "?band_id={band_id}&tralbum_type={item_type}&tralbum_id={album_id}" \
            .format(band_id=band_id, item_type=item_type, album_id=album_id)
        request = req(url)
        album_details = json.loads(request)
        track_list = []
        for track in album_details['tracks']:
            # sometimes not all tracks are available online
            if track['streaming_url'] is not None:
                track_list.append(
                    Track(track['title'], track['streaming_url']['mp3-128'], track['duration'],
                          number=track['track_num']))
        art_id = album_details['art_id']
        band = Band(band_name=album_details['band']['name'], band_id=album_details['band']['band_id'],
                    band_img=album_details['band']['image_id'])
        album = Album(album_id, album_details['title'], art_id, band=band)
        return band, album, track_list

    def get_album_legacy(self, album_id, item_type="album"):
        url = "https://bandcamp.com/EmbeddedPlayer/{item_type}={album_id}" \
            .format(album_id=album_id, item_type=item_type)
        content = req(url)
        parser = _PlayerDataParser()
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
        album = Album(album_id, player_data['album_title'], art_id, band=band)
        return band, album, track_list

    def get_album_by_url(self, url):
        url = unquote(url)
        request = req(url)
        parser = _DataBlobParser()
        parser.feed(request)
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
        request = req(url, data=body)
        band_details = json.loads(request)
        band = Band(band_id=band_details['id'], band_name=band_details['name'],
                    band_img=band_details['bio_image_id'])
        albums = []
        for album in band_details['discography']:
            albums.append(Album(album_id=album['item_id'], album_name=album['title'],
                                art_id=album['art_id'], item_type=album['item_type'][0],
                                band=band))
        return band, albums

    def search(self, query):
        if PY2:
            query = query.decode('utf-8')
        url = "https://bandcamp.com/api/fuzzysearch/1/autocomplete?q={query}".format(query=quote_plus(query))
        request = req(url)
        results = json.loads(request)['auto']['results']
        items = []
        for result in results:
            if result['type'] == "b":
                item = Band(band_id=result['id'], band_name=result['name'],
                            band_img=result['img'])
            elif result['type'] == "a" or result['type'] == "t":
                band = Band(band_id=result['band_id'], band_name=result['band_name'])
                item = Album(album_id=result['id'], album_name=result['name'],
                             art_id=result['art_id'], item_type=result['type'],
                             band=band)
            if item is not None:
                items.append(item)
        return items


    @staticmethod
    def _get_token():
        return str(int(time.time())) + "::FOO::"

    def _get_data_blob(self):
        if self.data_blob is None:
            url = "https://bandcamp.com/{user_name}".format(user_name=quote_plus(self.user_name))
            content = req(url)
            parser = _DataBlobParser()
            parser.feed(content)
            self.data_blob = parser.data_blob
        return self.data_blob
