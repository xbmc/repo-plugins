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

from resources.lib import star

params = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))


action = params.get('action')

url = params.get('url')

image = params.get('image')


if action == None:
    star.indexer().root()

elif action == 'addBookmark':
    from lamlib import bookmarks
    bookmarks.add(url)

elif action == 'deleteBookmark':
    from lamlib import bookmarks
    bookmarks.delete(url)

elif action == 'bookmarks':
    star.indexer().bookmarks()

elif action == 'tvshows':
    star.indexer().tvshows()

elif action == 'cartoon':
    star.indexer().cartoon()

elif action == 'archive':
    star.indexer().archive()

elif action == 'episodes':
    star.indexer().episodes(url, image)

elif action == 'youtube':
    star.indexer().youtube(url)

elif action == 'popular':
    star.indexer().popular()

elif action == 'news':
    star.indexer().news()

elif action == 'play':
    star.indexer().play(url)


