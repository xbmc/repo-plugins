# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

import json
import requests
from base64 import b64decode

from .common import log_utils

__key = 'QUl6YVN5RE1qUHVQTzExNDAxc19Ydl95TVNaa0hTUVZTRUwzV1R3'


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
