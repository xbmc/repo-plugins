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

from resources.lib import blitzr


params = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))

action = params.get('action')

query = params.get('query')

url = params.get('url')


if action == None:
    blitzr.indexer().root()

elif action == 'collectArtist':
    blitzr.indexer().collectArtist(url)

elif action == 'uncollectArtist':
    blitzr.indexer().uncollectArtist(url)

elif action == 'collectAlbum':
    blitzr.indexer().collectAlbum(url)

elif action == 'uncollectAlbum':
    blitzr.indexer().uncollectAlbum(url)

elif action == 'unrecommendArtist':
    blitzr.indexer().unrecommendArtist(url)

elif action == 'joinPlaylist':
    blitzr.indexer().joinPlaylist(url)

elif action == 'newPlaylist':
    blitzr.indexer().newPlaylist(url)

elif action == 'leavePlaylist':
    blitzr.indexer().leavePlaylist(url)

elif action == 'renamePlaylist':
    blitzr.indexer().renamePlaylist(url)

elif action == 'deletePlaylist':
    blitzr.indexer().deletePlaylist(url)

elif action == 'search':
    blitzr.indexer().search()

elif action == 'artistSearch':
    blitzr.indexer().artistSearch(query)

elif action == 'albumSearch':
    blitzr.indexer().albumSearch(query)

elif action == 'songSearch':
    blitzr.indexer().songSearch(query)

elif action == 'radio':
    blitzr.indexer().radio()

elif action == 'artists':
    blitzr.indexer().artists(url)

elif action == 'liteartists':
    blitzr.indexer().liteartists(url)

elif action == 'simartists':
    blitzr.indexer().simartists(url)

elif action == 'albums':
    blitzr.indexer().albums(url)

elif action == 'songs':
    blitzr.indexer().songs(url)

elif action == 'litesongs':
    blitzr.indexer().litesongs(url)

elif action == 'usersongs':
    blitzr.indexer().usersongs(url)

elif action == 'userlists':
    blitzr.indexer().userlists()

elif action == 'play':
    blitzr.indexer().play(url)


