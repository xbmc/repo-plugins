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

from resources.lib import novasports

params = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))


action = params.get('action')

url = params.get('url')


if action == None:
    novasports.indexer().root()

elif action == 'categories':
    novasports.indexer().categories()

elif action == 'shows':
    novasports.indexer().shows()

elif action == 'competitionsMenu':
    novasports.indexer().competitionsMenu()

elif action == 'competitions':
    novasports.indexer().competitions(url)

elif action == 'videos':
    novasports.indexer().videos(url)

elif action == 'play':
    novasports.indexer().play(url)


