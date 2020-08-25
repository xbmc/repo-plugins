# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from ..addon.constants import MODES
from ..addon.strings import encode_utf8
from ..addon.strings import i18n


class PlexSection:

    def __init__(self, data=None):

        self.title = None
        self.sectionuuid = None
        self.path = None
        self.key = None
        self.art = None
        self.type = None
        self.location = 'local'
        self.server_uuid = None

        if data is not None:
            self.populate(data)

    def populate(self, data):

        path = data.get('key')
        if not path.startswith(('/', 'http')):
            path = '/library/sections/%s' % path

        if (path.startswith('http') and data.get('path', '') and
                data.get('path', '').startswith('/')):
            path = data.get('path')

        self.title = encode_utf8(self.translate(data.get('title')))
        self.sectionuuid = data.get('uuid', '')
        self.path = encode_utf8(path)
        self.key = data.get('key')
        self.art = encode_utf8(data.get('art', ''))
        self.type = data.get('type', '')
        self.server_uuid = data.get('machineIdentifier')

    def content_type(self):
        if self.type == 'show':
            return 'tvshows'
        if self.type == 'movie':
            return 'movies'
        if self.type == 'artist':
            return 'music'
        if self.type == 'photo':
            return 'photos'
        return None

    def mode(self):
        if self.type == 'show':
            return MODES.TVSHOWS
        if self.type == 'movie':
            return MODES.MOVIES
        if self.type == 'artist':
            return MODES.ARTISTS
        if self.type == 'photo':
            return MODES.PHOTOS
        return None

    def get_details(self):

        return {
            'title': self.title,
            'sectionuuid': self.sectionuuid,
            'path': self.path,
            'key': self.key,
            'location': self.location,
            'art': self.art,
            'type': self.type,
            'content_type': self.content_type(),
            'mode': self.mode(),
            'server_uuid': self.get_server_uuid(),
        }

    def get_title(self):
        return self.title

    def get_uuid(self):
        return self.sectionuuid

    def get_path(self):
        return self.path

    def get_key(self):
        return self.key

    def get_art(self):
        return self.art

    def get_type(self):
        return self.type

    def is_show(self):
        if self.type == 'show':
            return True
        return False

    def is_movie(self):
        if self.type == 'movie':
            return True
        return False

    def is_artist(self):
        if self.type == 'artist':
            return True
        return False

    def is_photo(self):
        if self.type == 'photo':
            return True
        return False

    def get_server_uuid(self):
        return self.server_uuid

    @staticmethod
    def translate(value):
        _i = {
            'Movies': True,
            'TV Shows': True,
            'Music': True,
            'Photos': True,
        }

        if not value:
            return i18n('Unknown')

        if _i.get(value):
            return i18n(value)

        return value
