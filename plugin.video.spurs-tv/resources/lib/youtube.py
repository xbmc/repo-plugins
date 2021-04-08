import base64
from datetime import datetime
import html
import requests
from urllib.parse import urljoin


CHANNEL_ID = 'UCEg25rdRZXg32iwai6N6l0w'


def _get_items(resource, key='channel', channel_id=CHANNEL_ID, max_results=50, order='date', query=''):
    params=dict(
        key=base64.b64decode('QUl6YVN5Q1NDWDRmMmhpNjhuUlo3eGhxbFdLTi0wMDJXZTBxaGV3'),
        part='snippet',
        type='video',
        maxResults=max_results,
        q=query,
        order=order
    )
    params['{}Id'.format(key)] = channel_id
    response = requests.get(
        url=urljoin('https://www.googleapis.com/youtube/v3/', resource),
        params=params
    ).json()

    for item in response['items']:
        snippet = item['snippet']
        title = html.unescape(snippet['title'])
        if title == "Private video":
            continue
        try:
            thumbnail = snippet['thumbnails']['high']['url']
        except KeyError:
            thumbnail = None
        published_at = datetime.strptime(snippet['publishedAt'].split('T')[0], '%Y-%m-%d').date()

        try:
            video_id = item['id']['videoId'] # search result
        except TypeError:
            try:
                video_id = snippet['resourceId']['videoId'] # playlist video
            except KeyError:
                video_id = item['id'] # playlist

        yield video_id, title, thumbnail, published_at


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
