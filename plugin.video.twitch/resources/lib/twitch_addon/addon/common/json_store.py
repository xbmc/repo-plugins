# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

import json

from . import log_utils

import xbmcvfs


class JSONStore:
    def __init__(self, filename):
        self.filename = filename
        if not xbmcvfs.exists(self.filename):
            self.save({})
        self._data = None

    def save(self, data):
        self._data = data
        with open(self.filename, 'w') as jsonfile:
            log_utils.log('JSONStore Save |{filename}| Data |{data}|'.format(filename=self.filename.encode('utf-8'),
                                                                             data=json.dumps(data, indent=4, sort_keys=True)))
            json.dump(data, jsonfile, indent=4, sort_keys=True)

    def load(self, force=False):
        if force or not self._data:
            with open(self.filename, 'r') as jsonfile:
                data = json.load(jsonfile)
                self._data = data
                log_utils.log('JSONStore Load |{filename}| Data |{data}|'.format(filename=self.filename.encode('utf-8'),
                                                                                 data=json.dumps(data, indent=4, sort_keys=True)))
                return data
        else:
            return self._data
