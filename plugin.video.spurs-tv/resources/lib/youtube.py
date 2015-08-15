import os
import json
import requests
from urlparse import urljoin, urlunparse

import utils

SCHEME = "https"
HOST = "www.googleapis.com"
PATH = "/youtube/v3/"

CHANNEL_ID = "UCEg25rdRZXg32iwai6N6l0w"
API_KEY = "AIzaSyAyfLT-xP3vrQLwejc22hYe5m0RoZXX2vA"

QS_FMT = "part=snippet&key={0}&{{0}}Id={{1}}&maxResults={{2}}&q={{3}}&order={{4}}&type=video".format(API_KEY)


def _get_items(resource, key="channel", id=CHANNEL_ID, max_results=50, order='date', query=""):
    qs = QS_FMT.format(key, id, max_results, query, order)
    url = urlunparse((SCHEME, HOST, os.path.join(PATH, resource), None, qs, None))
    response = json.loads(requests.get(url).text)
    
    for item in response['items']:
        snippet = item['snippet']
        thumbnail = snippet['thumbnails']['high']['url']
        title = snippet['title']
        published_at = utils.date_from_str(snippet['publishedAt'].split('T')[0], "%Y-%m-%d")
        
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
    for playlist_id, title, thumbnail in get_playlists():
        print
        print title
        for item_id, title, thumbnail in get_playlist_items(playlist_id):
            print '\t', title
