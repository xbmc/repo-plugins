# -*- coding: utf-8 -*-
"""

    Copyright (C) 2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import json
import os
from copy import deepcopy

import xbmcvfs  # pylint: disable=import-error
from kodi_six import xbmc  # pylint: disable=import-error

from .common import CONFIG
from .logger import Logger

try:
    xbmc.translatePath = xbmcvfs.translatePath
except AttributeError:
    pass

LOG = Logger('json_store')


class JSONStore:

    def __init__(self, filename):
        self.base_path = xbmc.translatePath(CONFIG['addon'].getAddonInfo('profile'))
        self.filename = os.path.join(self.base_path, filename)

        self._data = None
        self.load()
        self.set_defaults()

    def set_defaults(self):
        raise NotImplementedError

    def save(self, data):
        if data != self._data:
            self._data = deepcopy(data)
            if not xbmcvfs.exists(self.base_path):
                if not self.make_dirs(self.base_path):
                    LOG.debug('JSONStore Save |{filename}| failed to create directories.'
                              .format(filename=self.filename.encode('utf-8')))
                    return
            with open(self.filename, 'w') as jsonfile:  # pylint: disable=unspecified-encoding
                LOG.debug('JSONStore Save |{filename}|'
                          .format(filename=self.filename.encode('utf-8')))
                json.dump(self._data, jsonfile, indent=4, sort_keys=True)

    def load(self):
        if xbmcvfs.exists(self.filename):
            with open(self.filename, 'r') as jsonfile:  # pylint: disable=unspecified-encoding
                data = json.load(jsonfile)
                self._data = data
                LOG.debug('JSONStore Load |{filename}|'
                          .format(filename=self.filename.encode('utf-8')))
        else:
            self._data = {}

    def get_data(self):
        return deepcopy(self._data)

    @staticmethod
    def make_dirs(path):
        if not path.endswith('/'):
            path = ''.join([path, '/'])
        path = xbmc.translatePath(path)
        if not xbmcvfs.exists(path):
            try:
                _ = xbmcvfs.mkdirs(path)
            except:  # pylint: disable=bare-except
                pass
            if not xbmcvfs.exists(path):
                try:
                    os.makedirs(path)
                except:  # pylint: disable=bare-except
                    pass
            return xbmcvfs.exists(path)

        return True
