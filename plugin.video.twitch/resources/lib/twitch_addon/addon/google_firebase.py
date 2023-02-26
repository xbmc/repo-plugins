# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2019 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

import json
import requests
from base64 import b64decode
from urllib.parse import quote

from .common import log_utils

__key = 'QUl6YVN5RDBtVGtVUU1TQnZ2dzVobnN4LTRZeGktNXNKSmdRR0E4'


def dynamic_links_short_url(url):
    key = b64decode(__key)
    if isinstance(key, bytes):
        key = key.decode('utf-8')
    post_url = 'https://firebasedynamiclinks.googleapis.com/v1/shortLinks?key=%s' % key
    data = {
        'longDynamicLink': 'https://twitchaddon.page.link/?link=%s' % quote(url),
        'suffix': {
            'option': 'SHORT'
        }
    }
    headers = {'content-type': 'application/json'}
    request = requests.post(post_url, data=json.dumps(data), headers=headers)
    json_data = request.json()

    if 'shortLink' in json_data:
        return json_data['shortLink']
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
