# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from .directory import Directory


class SearchQuery(Directory):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.ListItem.setProperty('specialSort', 'top')
        self.ListItem.setArt({
            'icon': 'DefaultAddonsSearch.png'
        })
