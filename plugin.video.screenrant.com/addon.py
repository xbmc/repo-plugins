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

from resources.lib import screenrant

params = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))


action = params.get('action')

url = params.get('url')


if action == None:
    screenrant.indexer().root()

elif action == 'addBookmark':
    from lamlib import bookmarks
    bookmarks.add(url)

elif action == 'deleteBookmark':
    from lamlib import bookmarks
    bookmarks.delete(url)

elif action == 'bookmarks':
    screenrant.indexer().bookmarks()

elif action == 'youtube':
    screenrant.indexer().youtube(url)

elif action == 'videos':
    screenrant.indexer().videos(url)

elif action == 'play':
    screenrant.indexer().play(url)


