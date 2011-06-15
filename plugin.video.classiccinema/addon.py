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

from resources.lib.xbmcswift.plugin import XBMCSwiftPlugin
from resources.lib.xbmcswift.common import download_page
from resources.lib.xbmcswift.getflashvideo import get_flashvideo_url
from BeautifulSoup import BeautifulSoup as BS, SoupStrainer as SS
from urlparse import urljoin
import re
from urllib import urlencode

__plugin__ = 'Classic Cinema'
__plugin_id__ = 'plugin.video.classiccinema'

plugin = XBMCSwiftPlugin(__plugin__, __plugin_id__)
#plugin.settings(plugin_cache=False, http_cache=False)

BASE_URL = 'http://www.classiccinemaonline.com'
def full_url(path):
    return urljoin(BASE_URL, path)

@plugin.route('/', default=True)
def show_browse_methods():
    '''Default view. Displays the different ways to browse the site.'''
    items = [
        {'label': 'Movies', 'url': plugin.url_for('show_movie_genres')},
        {'label': 'Silent Films', 'url': plugin.url_for('show_silent_genres')},
        {'label': 'Serials', 'url': plugin.url_for('show_serials')},
    ]
    return plugin.add_items(items)

@plugin.route('/movies/', name='show_movie_genres', path='index.php/movie-billboards')
@plugin.route('/silents/', name='show_silent_genres', path='index.php/silent-films-menu')
@plugin.route('/serials/', name='show_serials', path='index.php/serials')
def show_genres(path):
    '''For movies and silent films, will display genres. For serials, will display serial names.'''
    src = download_page(full_url(path))
    html = BS(src)

    a_tags = html.findAll('a', {'class': 'category'})
    items = [{'label': a.string,
              'url': plugin.url_for('show_movies', url=full_url(a['href'])),
             } for a in a_tags]
    return plugin.add_items(items)

@plugin.route('/movies/<url>/')
def show_movies(url):
    '''Displays available movies for a given url.'''
    # Need to POST to url in order to get back all results and not be limited to 10.
    # Currently can hack using only the 'limit=0' querystring, other params aren't needed.
    data = {'limit': '0'}
    src = download_page(url, urlencode(data))
    html = BS(src)

    trs = html.findAll('tr', {'class': lambda c: c in ['even', 'odd']})

    items = [{'label': tr.a.string,
              'url': plugin.url_for('show_movie', url=full_url(tr.a['href'])),
              'is_folder': False,
              'is_playable': True,
              'info': {'title': tr.a.string, },
             } for tr in trs]
    return plugin.add_items(items)

@plugin.route('/watch/<url>/')
def show_movie(url):
    '''Show the video.'''
    src = download_page(url)
    url = get_flashvideo_url(src)
    return plugin.set_resolved_url(url)

if __name__ == '__main__':
    plugin.run()

    # For testing
    #plugin.interactive()
    #plugin.crawl()

