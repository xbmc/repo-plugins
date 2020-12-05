# -*- coding: utf-8 -*-
"""

    Copyright (C) 2014-2016 bromix (plugin.video.youtube)
    Copyright (C) 2016-2020 plugin.video.youtube
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import json
import pickle

from .database import Database
from .time import now
from .time import timestamp_diff


class Cache(Database):

    def __init__(self, filename, max_file_size_mb=5):
        super().__init__(filename, max_file_size_kb=max_file_size_mb * 1024)

    def is_empty(self):
        return self._is_empty()

    def get_items(self, seconds, content_ids):
        self._open()

        result = self._execute(
            False,
            'SELECT * FROM %s WHERE key IN (%s)' %
            (self.table_name, ','.join(['?' for _ in content_ids])),
            [str(item) for item in content_ids]
        )

        payload = {}
        if result:
            for item in result:
                diff_seconds = timestamp_diff(item[1] if item[1] is not None else now())
                if diff_seconds <= seconds:
                    payload[str(item[0])] = json.loads(pickle.loads(item[2]))

        self._close()
        return payload

    def get_item(self, seconds, content_id):
        content_id = str(content_id)
        result = self._get(content_id)

        payload = {}
        if result:
            diff_seconds = timestamp_diff(result[1] if result[1] is not None else now())
            if diff_seconds <= seconds:
                payload[content_id] = json.loads(result[0])

        return payload

    def set(self, content_id, item):
        self._set(content_id, item)

    def set_all(self, items):
        self._set_all(items)

    def clear(self):
        self._clear()

    def remove(self, content_id):
        self._remove(content_id)

    def update(self, content_id, item):
        self._set(str(content_id), json.dumps(item))

    def _optimize_item_count(self):
        pass

    def _set(self, content_id, item):  # pylint: disable=arguments-differ
        self._open()

        self._execute(
            True,
            'REPLACE INTO %s (key,time,value) VALUES(?,?,?)' % self.table_name,
            values=[content_id, now(), self._encode(item)]
        )

        self._close()
        self._optimize_file_size()

    def _set_all(self, items):

        needs_commit = True

        query = 'REPLACE INTO %s (key,time,value) VALUES(?,?,?)' % self.table_name

        self._open()

        for key in list(items.keys()):
            item = items[key]
            self._execute(needs_commit, query, values=[key, now(), self._encode(json.dumps(item))])
            needs_commit = False

        self._close()
        self._optimize_file_size()
