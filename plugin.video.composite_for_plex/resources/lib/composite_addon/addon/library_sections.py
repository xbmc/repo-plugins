# -*- coding: utf-8 -*-
"""

    Copyright (C) 2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from copy import deepcopy

from kodi_six import xbmcvfs  # pylint: disable=import-error

from .json_store import JSONStore


class LibrarySectionsStore(JSONStore):
    _default_section = {
        'movie': [],
        'show': []
    }

    def __init__(self):
        JSONStore.__init__(self, 'library_sections.json')

    def exists(self):
        return xbmcvfs.exists(self.filename)

    def set_defaults(self):
        pass

    def get_data(self):
        if not self._data:
            return {}
        return deepcopy(self._data)

    def reset_to_default(self):
        xbmcvfs.delete(self.filename)

    def _create_default(self, uuid):
        data = self.get_data()
        save = False

        if uuid not in data:
            data[uuid] = deepcopy(self._default_section)
            save = True

        if 'movie' not in data[uuid]:
            data[uuid]['movie'] = []
            save = True

        if 'show' not in data[uuid]:
            data[uuid]['show'] = []
            save = True

        if save:
            self.save(data)

    def get_sections(self, uuid):
        data = self.get_data()
        return data.get(uuid, deepcopy(self._default_section))

    def get_movie_sections(self, uuid):
        data = self.get_data()
        return data.get(uuid, deepcopy(self._default_section)).get('movie', [])

    def get_tvshow_sections(self, uuid):
        data = self.get_data()
        return data.get(uuid, deepcopy(self._default_section)).get('show', [])

    def add_movie_sections(self, uuid, section_uuids):
        self._create_default(uuid)
        data = self.get_data()
        data[uuid]['movie'] = section_uuids
        self.save(data)

    def add_tvshow_sections(self, uuid, section_uuids):
        self._create_default(uuid)
        data = self.get_data()
        data[uuid]['show'] = section_uuids
        self.save(data)

    def reset_movie_sections(self, uuid):
        self._create_default(uuid)
        data = self.get_data()
        data[uuid]['movie'] = []
        self.save(data)

    def reset_tvshow_sections(self, uuid):
        self._create_default(uuid)
        data = self.get_data()
        data[uuid]['show'] = []
        self.save(data)

    def reset_all_movie_sections(self):
        data = self.get_data()
        for key in list(data.keys()):
            data[key]['movie'] = []
        self.save(data)

    def reset_all_tvshow_sections(self):
        data = self.get_data()
        for key in list(data.keys()):
            data[key]['show'] = []
        self.save(data)

    def remove_all_movie_sections(self):
        data = self.get_data()
        for key in list(data.keys()):
            data[key]['movie'] = []
        self.save(data)

    def remove_all_tvshow_sections(self):
        data = self.get_data()
        for key in list(data.keys()):
            data[key]['show'] = []
        self.save(data)

    def add_movie_section(self, uuid, section_uuid):
        self._create_default(uuid)
        data = self.get_data()
        if section_uuid not in data[uuid]['movie']:
            data[uuid]['movie'].append(section_uuid)
        self.save(data)

    def add_tvshow_section(self, uuid, section_uuid):
        self._create_default(uuid)
        data = self.get_data()
        if section_uuid not in data[uuid]['show']:
            data[uuid]['show'].append(section_uuid)
        self.save(data)

    def remove_movie_section(self, uuid, section_uuid):
        self._create_default(uuid)
        data = self.get_data()
        try:
            data[uuid]['movie'].remove(section_uuid)
            self.save(data)
        except ValueError:
            pass

    def remove_tvshow_section(self, uuid, section_uuid):
        self._create_default(uuid)
        data = self.get_data()
        try:
            data[uuid]['show'].remove(section_uuid)
            self.save(data)
        except ValueError:
            pass
