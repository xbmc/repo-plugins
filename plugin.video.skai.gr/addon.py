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

from resources.lib.indexers import skai

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
    skai.indexer().root()

elif action == 'addBookmark':
    from resources.lib.modules import bookmarks
    bookmarks.add(url)

elif action == 'deleteBookmark':
    from resources.lib.modules import bookmarks
    bookmarks.delete(url)

elif action == 'bookmarks':
    skai.indexer().bookmarks()

elif action == 'tvshows':
    skai.indexer().tvshows()

elif action == 'podcasts':
    skai.indexer().podcasts()

elif action == 'archive':
    skai.indexer().archive()

elif action == 'episodes':
    skai.indexer().episodes(url)

elif action == 'reverseEpisodes':
    skai.indexer().episodes(url, reverse=True)

elif action == 'popular':
    skai.indexer().popular()

elif action == 'news':
    skai.indexer().news()

elif action == 'sports':
    skai.indexer().sports()

elif action == 'live':
    skai.indexer().live()

elif action == 'play':
    skai.indexer().play(url)


