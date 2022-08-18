# -*- coding: utf-8 -*-
"""

    Copyright (C) 2014-2016 bromix (plugin.video.youtube)
    Copyright (C) 2016-2020 plugin.video.youtube
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import hashlib

from .database import Database


class Storage(Database):
    def __init__(self, filename, max_item_count=10):
        super().__init__(filename, max_item_count=max_item_count)

    def is_empty(self):
        return self._is_empty()

    def list(self):
        payload = []

        keys = self._get_ids(ascending=False)
        for index, key in enumerate(keys):
            if index >= self.max_item_count:
                break

            item = self._get(key)

            if item:
                payload.append(item[0])

        return payload

    def clear(self):
        self._clear()

    @staticmethod
    def _make_id(text):
        if not isinstance(text, bytes):
            text = text.encode('utf-8')

        md5 = hashlib.md5()
        md5.update(text)
        return md5.hexdigest()

    def rename(self, old, new):
        self.remove(old)
        self.update(new)

    def remove(self, text):
        self._remove(self._make_id(text))

    def update(self, text):
        self._set(self._make_id(text), text)
