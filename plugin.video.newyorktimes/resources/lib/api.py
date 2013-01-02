'''
    resources.lib.api
    ~~~~~~~~~~~~~~~~~

    This module contains functions to interact with the NYT website and
    associated brightcove api for videos.

   :copyright: (c) 2012 by Jonathan Beluch
   :license: GPLv3, see LICENSE.txt for more details.
'''
import urlparse
import requests
from BeautifulSoup import BeautifulSoup as BS
from brightcove.api import Brightcove


BASE_URL = 'http://www.nytimes.com/video/'
TOKEN = 'cE97ArV7TzqBzkmeRVVhJ8O6GWME2iG_bRvjBTlNb4o.'


def _url(path):
    '''Returns an absoulte URL for the given path'''
    return urlparse.urljoin(BASE_URL, path)


def get_topics():
    '''Returns a list of (topic_name, url) of available topics'''
    html = BS(requests.get(BASE_URL).text)
    menu = html.find('div', {'class': 'navigation clearfix'})
    links = menu.findAll('a', href=lambda h: h.startswith('/video/landing/'))
    return [(a.text, _url(a['href'])) for a in links]


def get_sub_topics(topic_url):
    '''Returns al ist of (topic_name, url) for sub topics available on the
    given topic page. If the provided url is a sub topic page, an empty list
    will be returned.
    '''
    html = BS(requests.get(topic_url).text)
    menu = html.find('div', {'class': 'subCategories clearfix'})

    if menu.find('li', {'class': 'firstItem selected'}):
        # Viewing a sub-topic page, don't return sub topics again
        return []

    links = menu.findAll('a')
    return [(a.text, _url(a['href'])) for a in links]


def get_videos(url):
    '''For a given topic url, returns a list of associated videos from the
    Brightcove API.
    '''
    ref_id = url.split('/')[-2]
    brightcove = Brightcove(TOKEN)
    playlist = brightcove.find_playlist_by_reference_id(ref_id)
    return playlist.videos
