#!/usr/bin/env python
# Copyright 2011 Jonathan Beluch.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
import time
try:
    import json
except ImportError:
    import simplejson as json
from urlparse import urljoin
from xbmcswift import Plugin, download_page, xbmc
from BeautifulSoup import BeautifulSoup as BS
from resources.lib.khan import KhanData, download_playlists_json
from resources.lib.cache import get_cached_data, put_cached_data


__plugin_name__ = 'Khan Academy'
__plugin_id__ = 'plugin.video.khanacademy'
plugin = Plugin(__plugin_name__, __plugin_id__, __file__)
BASE_URL = 'http://www.khanacademy.org'


# Ugly temporary hack until xbmcswift is fixed. Need to ensure the basedirs
# for the cache already exist before we attempt to use it. Also, in pyton 2.4
# we don't get the lovely os.makedirs :(
def make_cache_dirs():
    '''Make plugin_id and .cache dirs for the current plugin.'''
    def make_if_not_exist(path):
        print path
        if not os.path.exists(path):
            os.mkdir(path)
    cache_root = xbmc.translatePath('special://profile/addon_data')
    make_if_not_exist(os.path.join(cache_root, __plugin_id__))
    make_if_not_exist(os.path.join(cache_root, __plugin_id__, '.cache'))
make_cache_dirs()


def full_url(path):
    '''Returns the full url for the given path. Uses BASE_URL.'''
    return urljoin(BASE_URL, path)


def htmlify(url):
    '''Returns a BeautifulSoup object for a give url's response.'''
    return BS(download_page(url))


def get_khan_data():
    '''Returns a KhanData instance containg playlist data.

    Behind the scenes, it checks for a local cached copy first. If the cached
    copy's lifetime has not expired it will use the local copy. Otherwise, it
    will fetch fresh data from the API and cache it locally.
    '''
    json_fn = plugin.cache_fn('playlists.json')
    timestamp_fn = plugin.cache_fn('playlists.json.ts')

    _json = get_cached_data(json_fn, timestamp_fn)
    if _json is None:
        _json = download_playlists_json()
        put_cached_data(json.dumps(_json), json_fn, timestamp_fn)

    return KhanData(_json)


KHAN_DATA = get_khan_data()


@plugin.route('/')
@plugin.route('/<category>/', name='show_category')
def main_menu(category='_root'):
    '''This view displays Categories or Playlists.

    This method does a lookup based on the passed category/playlist name to get
    the members. The "root" or base category is name "_root"
    '''
    items = [item.to_listitem(plugin)
             for item in KHAN_DATA.get_items(category)]
    return plugin.add_items(items)


@plugin.route('/play/<video_slug>/')
def play_video(video_slug):
    '''Resolves a video page's url to a playable video url.'''
    # Videos are both in .mp4 format and youtube. For simplicity's sake just
    # use mp4 for now.
    url = 'http://www.khanacademy.org/video/%s' % video_slug
    html = htmlify(url)
    a = html.find('a', {'title': 'Download this lesson'})
    plugin.set_resolved_url(a['href'])


if __name__ == '__main__':
    plugin.run()
