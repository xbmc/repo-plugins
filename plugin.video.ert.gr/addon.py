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

from resources.lib import ert

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
    ert.indexer().root()

elif action == 'addBookmark':
    from lamlib import bookmarks
    bookmarks.add(url)

elif action == 'deleteBookmark':
    from lamlib import bookmarks
    bookmarks.delete(url)

elif action == 'bookmarks':
    ert.indexer().bookmarks()

elif action == 'tvshows':
    ert.indexer().tvshows()

elif action == 'categories':
    ert.indexer().categories()

elif action == 'episodes':
    ert.indexer().episodes(url)

elif action == 'popular':
    ert.indexer().popular()

elif action == 'news':
    ert.indexer().news()

elif action == 'sports':
    ert.indexer().sports()

elif action == 'weather':
    ert.indexer().weather()

elif action == 'live':
    ert.indexer().live(url)

elif action == 'play':
    ert.indexer().play(url)


