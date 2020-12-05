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

from ..constants import ADDONDATA_PATH
from ..lib.sql_storage import Storage
from ..lib.time import now
from .users import UserStorage

# pylint: disable=arguments-differ


class FavoriteChannels(Storage):
    def __init__(self, uuid='', maximum_items=2500):
        if not uuid:
            uuid = UserStorage().uuid

        filename = os.path.join(ADDONDATA_PATH, 'channels', uuid, 'favorite_channels.sqlite')

        super().__init__(filename, max_item_count=maximum_items)

    def pop(self, channel_id):
        payload = None

        item = self._get(channel_id)
        if item:
            payload = (channel_id, item[0])
            self._remove(channel_id)

        return payload

    def remove(self, channel_id):
        self._remove(channel_id)

    def update(self, channel_id, channel_name):
        self._set(channel_id, channel_name)

    def list(self, offset, limit):
        payload = []

        keys = self._get_ids(offset, limit, ascending=True)
        for index, key in enumerate(keys):
            if index >= self.max_item_count:
                break

            item = self._get(key)
            if item:
                payload.append((key, item[0]))

        return payload

    def _get_ids(self, offset, limit, ascending=True):
        self._open()

        query = 'SELECT * FROM %s' % self.table_name
        query = '%s ORDER BY value %s LIMIT %s, %s' % \
                (query, 'ASC' if ascending else 'DESC', offset, limit)

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
        return item[1], item[0]

    def _set(self, item_id, item):
        if self.max_file_size_kb < 1 and self.max_item_count < 1:
            self._optimize_item_count()
            return

        self._open()

        self._execute(
            True,
            'REPLACE INTO %s (key,time,value) VALUES(?,?,?)' % self.table_name,
            values=[item_id, now(), item]
        )

        self._close()
        self._optimize_item_count()
