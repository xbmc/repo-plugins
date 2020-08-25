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
        'certificate_verification': True
    }

    def __init__(self):
        JSONStore.__init__(self, 'server_config.json')

    def set_defaults(self):
        data = self.get_data()
        if not data:
            data = {}
        self.save(data)

    def _create_default(self, uuid):
        data = self.get_data()
        save = False

        if uuid not in data:
            data[uuid] = self._default_server
            save = True

        if 'access_urls' not in data[uuid]:
            data[uuid]['access_urls'] = []
            save = True

        if 'certificate_verification' not in data[uuid]:
            data[uuid]['certificate_verification'] = True
            save = True

        if save:
            self.save(data)

    def get_config(self, uuid):
        data = self.get_data()
        return data.get(uuid, deepcopy(self._default_server))

    def ssl_certificate_verification(self, uuid):
        data = self.get_data()
        return data.get(uuid, deepcopy(self._default_server)).get('certificate_verification', True)

    def set_certificate_verification(self, uuid, verification=True):
        self._create_default(uuid)
        data = self.get_data()
        data[uuid]['certificate_verification'] = bool(verification)
        self.save(data)

    def toggle_certificate_verification(self, uuid):
        self._create_default(uuid)
        data = self.get_data()
        data[uuid]['certificate_verification'] = not data[uuid]['certificate_verification']
        self.save(data)

    def access_urls(self, uuid):
        data = self.get_data()
        return data.get(uuid, deepcopy(self._default_server)).get('access_urls', [])

    def add_access_url(self, uuid, url, index=None):
        self._create_default(uuid)
        data = self.get_data()

        if index is None:
            data[uuid]['access_urls'].append(url)
        else:
            try:
                data[uuid]['access_urls'][index] = url
            except:  # pylint: disable=bare-except
                return

        self.save(data)

    def delete_access_url(self, uuid, index):
        self._create_default(uuid)
        data = self.get_data()
        try:
            del data[uuid]['access_urls'][index]
        except:  # pylint: disable=bare-except
            return

        self.save(data)
