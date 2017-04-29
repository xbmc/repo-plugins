# -*- coding: utf-8 -*-
"""

    Copyright (C) 2016 Twitch-on-Kodi

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import requests
import json
from common import log_utils
from base64 import b64decode
import cache

__key = 'QUl6YVN5RE1qUHVQTzExNDAxc19Ydl95TVNaa0hTUVZTRUwzV1R3'


@cache.cache_function(cache_limit=1)
def googl_url(url):
    post_url = 'https://www.googleapis.com/urlshortener/v1/url?key=%s' % b64decode(__key)
    data = {'longUrl': url}
    headers = {'content-type': 'application/json'}
    request = requests.post(post_url, data=json.dumps(data), headers=headers)
    json_data = request.json()
    if 'id' in json_data:
        return json_data['id']
    else:
        if 'error' in json_data:
            if 'errors' in json_data['error']:
                errors = ''
                for err in json_data['error']['errors']:
                    errors += '%s |%s| ' % (err['message'], err['reason'])
                log_utils.log('Error: %s' % errors, log_utils.LOGERROR)
            else:
                log_utils.log('Error: %s |%s|' % (json_data['error']['code'], json_data['error']['message']), log_utils.LOGERROR)
        return None
