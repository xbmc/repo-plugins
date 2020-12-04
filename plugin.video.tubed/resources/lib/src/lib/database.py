# -*- coding: utf-8 -*-
"""

    Copyright (C) 2014-2016 bromix (plugin.video.youtube)
    Copyright (C) 2016-2020 plugin.video.youtube
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import os
import pickle
import sqlite3
import time

import xbmcvfs  # pylint: disable=import-error

from .time import now


class Database:
    def __init__(self, filename, max_item_count=0, max_file_size_kb=-1):
        self._table_name = 'storage'

        self._filename = ''.join([filename.replace('.sqlite', ''), '.sqlite'])

        self._file = None
        self._cursor = None

        self._max_item_count = max_item_count
        self._max_file_size_kb = max_file_size_kb

        self._table_created = False
        self._needs_commit = False

    @property
    def max_item_count(self):
        return int(self._max_item_count)

    @max_item_count.setter
    def max_item_count(self, value):
        self._max_item_count = int(value)

    @property
    def max_file_size_kb(self):
        return int(self._max_file_size_kb)

    @max_file_size_kb.setter
    def max_file_size_kb(self, value):
        self._max_file_size_kb = int(value)

    @property
    def table_name(self):
        return self._table_name

    @property
    def table_created(self):
        return bool(self._table_created)

    @table_created.setter
    def table_created(self, value):
        self._table_created = bool(value)

    @property
    def needs_commit(self):
        return bool(self._needs_commit)

    @needs_commit.setter
    def needs_commit(self, value):
        self._needs_commit = bool(value)

    @property
    def filename(self):
        return self._filename

    def __del__(self):
        self._close()

    def _open(self):
        if self._file is None:
            path = os.path.dirname(self.filename)
            if not xbmcvfs.exists(path):
                xbmcvfs.mkdirs(path)

            self._file = sqlite3.connect(self.filename, check_same_thread=False,
                                         detect_types=0, timeout=1)

            self._file.isolation_level = None
            self._cursor = self._file.cursor()
            self._cursor.execute('PRAGMA journal_mode=MEMORY')
            self._cursor.execute('PRAGMA busy_timeout=20000')
            self._create_table()

    def _execute(self, needs_commit, query, values=None):
        if values is None:
            values = []

        if not self.needs_commit and needs_commit:
            self.needs_commit = True
            self._cursor.execute('BEGIN')

        for _ in range(3):
            try:
                return self._cursor.execute(query, values)
            except TypeError:
                return None
            except:  # pylint: disable=bare-except
                time.sleep(0.1)

        return None

    def _close(self):
        if self._file is not None:
            self._sync()
            self._file.commit()
            self._cursor.close()
            self._cursor = None
            self._file.close()
            self._file = None

    def _optimize_file_size(self):
        if self.max_file_size_kb <= 0:
            return

        if not xbmcvfs.exists(self.filename):
            return

        file_size_kb = (xbmcvfs.Stat(self.filename).st_size() // 1024)
        if file_size_kb >= self.max_file_size_kb:
            self._open()

            result = self._execute(
                False,
                'SELECT COUNT(key) FROM %s' % self.table_name
            )

            item_count = result.fetchone()[0]
            try:
                item_count = int(item_count)
            except ValueError:
                item_count = 0

            crop_count = max(item_count, item_count - 150)

            result = self._execute(
                True,
                'DELETE FROM %s WHERE key in '
                '(SELECT key FROM %s ORDER BY time DESC LIMIT -1 OFFSET %d)' %
                (self.table_name, self.table_name, crop_count)
            )

            self._close()

    def _create_table(self):
        self._open()

        if not self.table_created:
            self._execute(
                True,
                'CREATE TABLE IF NOT EXISTS %s (key TEXT PRIMARY KEY, '
                'time TIMESTAMP, value BLOB)' % self.table_name
            )
            self.table_created = True

    def _sync(self):
        if self._cursor is not None and self.needs_commit:
            self.needs_commit = False
            self._execute(False, 'COMMIT')

    def _set(self, item_id, item):
        if self.max_file_size_kb < 1 and self.max_item_count < 1:
            self._optimize_item_count()
            self._optimize_file_size()
            return

        self._open()

        self._execute(
            True,
            'REPLACE INTO %s (key,time,value) VALUES(?,?,?)' % self.table_name,
            values=[item_id, now(), self._encode(item)]
        )

        self._close()
        self._optimize_item_count()
        self._optimize_file_size()

    def _optimize_item_count(self):
        if self.max_item_count < 1:
            if not self._is_empty():
                self._clear()

            return

        self._open()

        result = self._execute(
            False,
            'SELECT key FROM %s ORDER BY time DESC LIMIT -1 OFFSET %d' % \
            (self.table_name, self.max_item_count)
        )

        if result is not None:
            for item in result:
                self._remove(item[0])

        self._close()

    def _clear(self):
        self._open()
        self._execute(True, 'DELETE FROM %s' % self.table_name)
        self._create_table()
        self._close()
        self._open()
        self._execute(False, 'VACUUM')
        self._close()

    def _is_empty(self):
        self._open()

        result = self._execute(False, 'SELECT exists(SELECT 1 FROM %s LIMIT 1);' % self.table_name)

        empty = True
        if result is not None:
            for item in result:
                empty = item[0] == 0
                break

        self._close()

        return empty

    def _get_ids(self, ascending=True):
        self._open()

        query = 'SELECT key FROM %s' % self.table_name
        query = '%s ORDER BY time %s' % (query, 'ASC' if ascending else 'DESC')

        result = self._execute(False, query)

        payload = []
        if result:
            for item in result:
                payload.append(item[0])

        self._close()
        return payload

    def _get(self, item_id):
        self._open()

        result = self._execute(
            False,
            'SELECT time, value FROM %s WHERE key=?' % self.table_name,
            [item_id]
        )

        if result is None:
            self._close()
            return None

        item = result.fetchone()
        if item is None:
            self._close()
            return None

        self._close()
        return pickle.loads(item[1]), item[0]

    def _remove(self, item_id):
        self._open()
        self._execute(True, 'DELETE FROM %s WHERE key = ?' % self.table_name, [item_id])

    @staticmethod
    def _encode(obj):
        return sqlite3.Binary(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL))
