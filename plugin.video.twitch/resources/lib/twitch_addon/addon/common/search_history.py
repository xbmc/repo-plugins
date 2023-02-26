# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
import datetime
import pickle
import sqlite3

import xbmcvfs

from . import kodi


class SearchHistory:
    def __init__(self, filename, max_items=10):
        path = 'special://profile/addon_data/plugin.video.twitch/search/'
        filename = ''.join([path, filename])
        if not filename.endswith('.sqlite'):
            filename = ''.join([filename, '.sqlite'])

        self.path = kodi.translate_path(path)
        self.filename = kodi.translate_path(filename)

        self.database = None
        self.cursor = None

        self._max_items = max_items
        self._table_name = 'search_history_01'

        self.create_table()

        self.upgrade()

    def open(self):
        if not xbmcvfs.exists(self.path):
            xbmcvfs.mkdirs(self.path)

        self.database = sqlite3.connect(self.filename, check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES, timeout=1)
        self.database.isolation_level = None

        self.cursor = self.database.cursor()
        self.cursor.execute('PRAGMA journal_mode=MEMORY')
        self.cursor.execute('PRAGMA busy_timeout=20000')

        self.cursor.execute('BEGIN')

    def close(self):
        self.cursor.execute('COMMIT')
        self.cursor.execute('VACUUM')

        self.database.commit()

        self.cursor.close()
        self.cursor = None

        self.database.close()
        self.database = None

    def create_table(self):
        query = 'CREATE TABLE IF NOT EXISTS %s (value TEXT PRIMARY KEY, time TIMESTAMP)' % self._table_name

        self.open()
        self.execute(query)
        self.close()

    def execute(self, query, values=[]):
        ret_val = self.cursor.execute(query, values)
        return ret_val

    def list(self):
        results = []
        query = 'SELECT value FROM %s ORDER BY time DESC' % self._table_name

        self.open()
        ret_vals = self.execute(query)
        if ret_vals:
            for item in ret_vals:
                results.append(item[0])
        self.close()
        return results

    def clear(self):
        query = 'DELETE FROM %s' % self._table_name

        self.open()
        self.execute(query)
        self.close()

        self.create_table()

    def update(self, value):
        timestamp = datetime.datetime.now() + datetime.timedelta(microseconds=1)
        query = 'REPLACE INTO %s (value,time) VALUES(?,?)' % self._table_name

        self.open()
        self.execute(query, values=[kodi.decode_utf8(value), timestamp])
        self.close()

        self.trim()

    def remove(self, value):
        query = 'DELETE FROM %s WHERE value = ?' % self._table_name

        self.open()
        self.execute(query, [kodi.decode_utf8(value)])
        self.close()

    def rename(self, old_value, new_value):
        self.remove(old_value)
        self.update(new_value)

    def trim(self):
        query = 'SELECT value FROM %s ORDER BY time DESC LIMIT -1 OFFSET %d' % (self._table_name, self._max_items)

        self.open()
        ret_vals = self.execute(query)
        if ret_vals is not None:
            for item in ret_vals:
                self.remove(item[0])
        self.close()

    def upgrade(self):
        def _decode(obj):
            return pickle.loads(bytes(obj))

        table_to_upgrade = 'storage'
        query = 'SELECT name FROM sqlite_master WHERE type="table" AND name="%s"' % table_to_upgrade

        self.open()
        ret_val = self.execute(query)
        table_exists = ret_val.fetchone() is not None
        self.close()

        if table_exists:
            results = []
            query = 'SELECT value FROM %s ORDER BY time ASC' % table_to_upgrade

            self.open()
            ret_vals = self.execute(query)
            if ret_vals:
                for item in ret_vals:
                    results.append(_decode(item[0]))
            self.close()

            for result in results:
                self.update(result)

            query = 'DROP TABLE IF EXISTS %s' % table_to_upgrade

            self.open()
            self.execute(query)
            self.close()
