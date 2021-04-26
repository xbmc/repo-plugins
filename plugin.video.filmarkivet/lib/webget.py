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

import requests
import requests_cache

session = requests.Session()
session.headers['User-Agent'] = 'kodi.tv'


class GetException(Exception):
    pass


class WebGet(object):
    API_URL = "https://www.filmarkivet.se"

    def __init__(self, cache_file):
        requests_cache.install_cache(cache_file, backend='sqlite', expire_after=604800)

    def getURL(self, url='/'):
        try:
            if not (url.startswith('http://') or url.startswith('https://')):
                url = self.API_URL + url

            request = session.get(url)
            request.raise_for_status()
            return request.text
        except Exception as ex:
            raise GetException(ex)
