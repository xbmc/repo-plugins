# -*- coding: utf-8 -*-

'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import urlparse,sys

from resources.lib.indexers import trakt

params = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))


try:
    action = params['action']
except:
    action = None
try:
    url = params['url']
except:
    url = None



if action == None:
    trakt.indexer().root()

elif action == 'authTrakt':
    trakt.indexer().authTrakt()

elif action == 'collectMovie':
    trakt.indexer().traktLists(url, action)

elif action == 'collectTVShow':
    trakt.indexer().traktLists(url, action)

elif action == 'watchlistMovie':
    trakt.indexer().traktLists(url, action)

elif action == 'watchlistTVShow':
    trakt.indexer().traktLists(url, action)

elif action == 'newlistMovie':
    trakt.indexer().traktLists(url, action)

elif action == 'newlistTVShow':
    trakt.indexer().traktLists(url, action)

elif action == 'listMovie':
    trakt.indexer().traktLists(url, action)

elif action == 'listTVShow':
    trakt.indexer().traktLists(url, action)

elif action == 'movies':
    trakt.indexer().movies(url)

elif action == 'tvshows':
    trakt.indexer().tvshows(url)

elif action == 'play':
    trakt.indexer().play(url)


