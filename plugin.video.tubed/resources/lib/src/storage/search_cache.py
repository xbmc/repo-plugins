# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import os

from ..constants import ADDONDATA_PATH
from ..lib.sql_storage import Storage
from .users import UserStorage


class SearchCache(Storage):
    def __init__(self, uuid=''):
        if not uuid:
            uuid = UserStorage().uuid

        filename = os.path.join(ADDONDATA_PATH, 'search', uuid, 'search_cache.sqlite')

        super().__init__(filename, max_item_count=1)

    @property
    def item(self):
        try:
            return self.list()[0]
        except IndexError:
            return ''

    @item.setter
    def item(self, value):
        self.update(value)
