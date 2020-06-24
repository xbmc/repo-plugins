# -*- coding: utf-8 -*-
"""

    Copyright (C) 2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from copy import deepcopy

from .json_store import JSONStore


class ServerConfigStore(JSONStore):
    _default_server = {
        'access_urls': [],
    }

    def __init__(self):
        JSONStore.__init__(self, 'server_config.json')

    def set_defaults(self):
        data = self.get_data()
        if not data:
            data = {}
        self.save(data)

    def get_config(self, uuid):
        data = self.get_data()
        return data.get(uuid, deepcopy(self._default_server))

    def access_urls(self, uuid):
        data = self.get_data()
        return data.get(uuid, deepcopy(self._default_server)).get('access_urls', [])

    def add_access_url(self, uuid, url, index=None):
        data = self.get_data()
        if not data.get(uuid, deepcopy(self._default_server)).get('access_urls', []):
            if not data.get('uuid'):
                data[uuid] = self._default_server
            if not data[uuid].get('access_urls'):
                data[uuid]['access_urls'] = []

        if index is None:
            data[uuid]['access_urls'].append(url)
        else:
            try:
                data[uuid]['access_urls'][index] = url
            except:  # pylint: disable=bare-except
                return

        self.save(data)

    def delete_access_url(self, uuid, index):
        data = self.get_data()
        try:
            del data[uuid]['access_urls'][index]
        except:  # pylint: disable=bare-except
            return

        self.save(data)
