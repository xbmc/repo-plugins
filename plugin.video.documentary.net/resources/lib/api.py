'''
    resources.lib.api
    ~~~~~~~~~~~~~~~~~

    This module contains helper functions that interact with the
    documentary.net JSON API.

    :copyright: (c) 2012 by Jonathan Beluch
    :license: GPLv3, see LICENSE.txt for more details.
'''
import json
import urllib2
import HTMLParser
from urlparse import urljoin


CATEGORIES_URL = 'http://documentary.net/api/get_category_index/?dev=1'
# For now, use a count param of 500, otherwise the response is paginated
CATEGORY_PTN = 'http://documentary.net/api/get_category_posts/?id=%d&count=500'


h = HTMLParser.HTMLParser()
def _unescape(text):
    '''Unescapes HTML entities in the provided text'''
    return h.unescape(text)


def _json(url):
    '''Returns a decoded JSON response for the given url'''
    return json.load(urllib2.urlopen(url))


def get_categories():
    '''Returns the list of available categories'''
    # The JSON api returns a few categories that are only relevant to the
    # website and don't contain videos, so we'll ignore them
    ignore_ids = [955, 18, 17, 23]
    resp = _json(CATEGORIES_URL)
    return [{
        'url': CATEGORY_PTN % cat['id'],
        'title': cat['title']
    } for cat in resp['categories'] if cat['id'] not in ignore_ids]


def _get_thumbnail(post):
    '''For a given post, attempts to find the best thumbnail image and returns
    the url. Returns None if a thumbnail url can't be found.
    '''
    if post['attachments']:
        return post['attachments'][0]['images']['full']['url']
    return post.get('thumbnail')


def _build_item(post):
    '''Builds a dict of metadata from an API post item.'''
    hosts = ['vimeo', 'youtube', 'ooyala']
    resources = ['mp4', 'ogg']

    item = {
        'title': _unescape(post['title']),
        'excerpt': post['excerpt'],
        'content': post['content'],
        'date': post['date'],
    }

    thumbnail = _get_thumbnail(post)
    if thumbnail:
        item['thumbnail'] = thumbnail

    # Some posts will have a direct link to a video resource such as an ogg
    # or mp4 file. It is found in the custom_fields dict, with a key of
    # either 'ogg' or 'mp4'.
    try: 
        item['video_url'] = (key for key in post['custom_fields']
                              if key in resources).next()
    except StopIteration:
        pass

    # Some posts will have a video id for a given video host stored in the
    # custom_fields dict. The hosts include 'youtube', 'ooyala' and
    # 'vimeo'.
    try:
        host = (key for key in post['custom_fields'] if key in hosts).next()
        item['video_host'] = host
        item['video_id'] = post['custom_fields'][host][0]
    except StopIteration:
        # No video id was found. If we haven't already parsed a direct
        # video url, then this item isn't playable. However, we'll let the
        # caller filter out items which don't contain playable metadata
        pass

    return item


def _has_video(item):
    '''Returns True if the provided item has metadata to play a video.'''
    return 'video_url' in item.keys() or 'video_host' in item.keys()


def get_category_posts(url):
    '''Returns available videos for a given category API url'''
    resp = _json(url)
    items = [_build_item(post) for post in resp['posts']]

    # Some items won't have a correctly parsed video id or video url, so we
    # skip them
    return [item for item in items if _has_video(item)]
