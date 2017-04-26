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

import json
import log_utils
import xbmcvfs


class JSONStore:
    def __init__(self, filename):
        self.filename = filename
        if not xbmcvfs.exists(self.filename):
            self.save({})
        self._data = None

    def save(self, data):
        self._data = data
        with open(self.filename, 'wb') as jsonfile:
            log_utils.log('JSONStore Save |{filename}| Data |{data}|'.format(filename=self.filename,
                                                                             data=json.dumps(data, indent=4, sort_keys=True)))
            json.dump(data, jsonfile, indent=4, sort_keys=True)

    def load(self, force=False):
        if force or not self._data:
            with open(self.filename, 'rb') as jsonfile:
                data = json.load(jsonfile)
                self._data = data
                log_utils.log('JSONStore Load |{filename}| Data |{data}|'.format(filename=self.filename,
                                                                                 data=json.dumps(data, indent=4, sort_keys=True)))
                return data
        else:
            return self._data
