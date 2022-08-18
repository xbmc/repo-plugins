# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
from xbmcaddon import Addon


class Credentials:
    def __init__(self):
        self.reload()

    def are_filled_in(self):
        return not (self.username is None or self.password is None
                    or self.username == '' or self.password == '')

    def reload(self):
        self.username = Addon().getSetting('username')
        self.password = Addon().getSetting('password')


class EPG:
    EPG_CACHE_FILE_NAME = "EPG.json"

    def __init__(self):
        self.reload()

    @property
    def is_enabled(self):
        import json
        return json.loads(self.epg.lower())

    @classmethod
    def to_cache(cls, json_data):
        import json
        import os
        from kodiwrapper import KodiWrapper

        path = KodiWrapper.get_addon_data_path()

        if not os.path.exists(path):
            os.mkdir(path, 0o775)

        data = {}
        if os.path.isfile(os.path.join(path, cls.EPG_CACHE_FILE_NAME)):
            with open(os.path.join(path, cls.EPG_CACHE_FILE_NAME), "r") as json_file:
                data = json.load(json_file)

        data.update(json_data)

        with open(os.path.join(path, cls.EPG_CACHE_FILE_NAME), "w") as json_file:
            json.dump(data, json_file, sort_keys=True, indent=True)

    @classmethod
    def get_from_cache(cls):
        import json
        import os
        from kodiwrapper import KodiWrapper

        path = KodiWrapper.get_addon_data_path()

        try:
            with open(os.path.join(path, cls.EPG_CACHE_FILE_NAME), "r") as json_file:
                data = json.load(json_file)
                return data

        except IOError:
            return {}

    @property
    def is_cached(self):
        import os
        from kodiwrapper import KodiWrapper

        path = KodiWrapper.get_addon_data_path()

        if not os.path.isfile(os.path.join(path, self.EPG_CACHE_FILE_NAME)):
            return False
        return True

    def reload(self):
        self.epg = Addon().getSetting('epg')


class PluginCache:  # pylint: disable=no-init
    CACHE_FILE_NAME = "data.json"

    @classmethod
    def key_exists(cls, key):
        import json
        import os
        from kodiwrapper import KodiWrapper

        path = KodiWrapper.get_addon_data_path()

        if not os.path.isfile(os.path.join(path, cls.CACHE_FILE_NAME)):
            return False

        with open(os.path.join(path, cls.CACHE_FILE_NAME), "r") as json_file:
            data = json.load(json_file)

        return key in data

    @classmethod
    def set_data(cls, json_data):
        import json
        import os
        from kodiwrapper import KodiWrapper

        path = KodiWrapper.get_addon_data_path()

        if not os.path.exists(path):
            os.mkdir(path, 0o775)

        data = {}
        if os.path.isfile(os.path.join(path, cls.CACHE_FILE_NAME)):
            with open(os.path.join(path, cls.CACHE_FILE_NAME), "r") as json_file:
                data = json.load(json_file)

        data.update(json_data)

        with open(os.path.join(path, cls.CACHE_FILE_NAME), "w") as json_file:
            json.dump(data, json_file, sort_keys=True, indent=True)

    @classmethod
    def get_by_key(cls, key):
        import json
        import os
        from kodiwrapper import KodiWrapper

        path = KodiWrapper.get_addon_data_path()

        with open(os.path.join(path, cls.CACHE_FILE_NAME), "r") as json_file:
            data = json.load(json_file)

        return data.get(key)
