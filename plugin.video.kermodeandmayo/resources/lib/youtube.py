from __future__ import print_function
import os
import json
import time
from datetime import date
from urlparse import urljoin, urlunparse

import requests


SCHEME = "https"
HOST = "www.googleapis.com"
PATH = "/youtube/v3/"

CHANNEL_ID = "UCCxKPNMqjnqbxVEt1tyDUsA"
API_KEY = "AIzaSyDc9qkxPf5Bl3KhjuWUQ_6WDx3TqCAp4OE"

QS_FMT = "part=snippet&key={0}&{{0}}Id={{1}}&maxResults={{2}}&q={{3}}&order={{4}}&type=video".format(API_KEY)


def date_from_str(date_str, date_format):
    return date(*(time.strptime(date_str, date_format)[0:3]))

def _get_items(resource, key="channel", id=CHANNEL_ID, max_results=50, order='date', query=""):
    qs = QS_FMT.format(key, id, max_results, query, order)
    url = urlunparse((SCHEME, HOST, os.path.join(PATH, resource), None, qs, None))
    response = json.loads(requests.get(url, headers={'referer': 'kermodeandmayo'}).text)

    for item in response['items']:
        snippet = item['snippet']
        thumbnail = snippet['thumbnails']['high']['url']
        title = snippet['title']
        published_at = date_from_str(snippet['publishedAt'].split('T')[0], "%Y-%m-%d")
        
        try:
            id = item['id']['videoId'] # search result
        except TypeError:
            try:
                id = snippet['resourceId']['videoId'] # playlist video
            except KeyError:
                id = item['id'] # playlist

        yield id, title, thumbnail, published_at

def get_playlists():
    return _get_items("playlists")

def get_playlist_items(playlist_id):
    return _get_items("playlistItems", "playlist", playlist_id)

def get_popular():
    return _get_items("search", max_results=14, order="viewCount")

def get_latest():
    return _get_items("search", max_results=14)

def get_search_results(query):
    return _get_items("search", query=query)
    
        
if __name__ == "__main__":
    for playlist_id, title, thumbnail, published_at in get_playlists():
        print()
        print(title)
        for item_id, title, thumbnail, published_at in get_playlist_items(playlist_id):
            print('\t', title)
