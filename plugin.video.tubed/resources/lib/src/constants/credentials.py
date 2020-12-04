# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import json
from base64 import b64decode
from base64 import b64encode
from enum import Enum

import xbmcvfs  # pylint: disable=import-error

_KEY = 'QUl6YVN5QUR0T0RKVTB4d3BXdWZfbUE1N3VFdUNwT0FfcjN6WEtv'
_ID = 'OTAxOTQ1MDk2MjU2LWV2MGk5dmFuczd0Z25iYTRtNjZjaTQ2ZGFnc3RlY2Y1'
_SECRET = 'Y2RMSldUdHdrWENod2ZsV1dqYnNwYVNH'

try:
    _developer_key_json = xbmcvfs.translatePath(
        'special://profile/addon_data/plugin.video.tubed/api_keys.json'
    )

    if xbmcvfs.exists(_developer_key_json):
        with open(_developer_key_json, 'r') as file_handle:
            _json = json.load(file_handle)

        if ('keys' in _json and 'personal' in _json['keys'] and
                _json['keys']['personal'].get('api_key') and
                _json['keys']['personal'].get('client_id') and
                _json['keys']['personal'].get('client_secret')):

            _developer_keys = _json['keys']['personal']
            _KEY = b64encode(_developer_keys['api_key'].encode('utf-8')).decode('utf-8')
            _ID = b64encode(_developer_keys['client_id'].encode('utf-8')).decode('utf-8')
            _SECRET = b64encode(_developer_keys['client_secret'].encode('utf-8')).decode('utf-8')

except:  # pylint: disable=bare-except
    pass


class CREDENTIALS(Enum):
    KEY = _KEY
    ID = _ID
    SECRET = _SECRET
    TOKEN = ''

    def __str__(self):
        return b64decode(str(self.value)).decode('utf-8')
