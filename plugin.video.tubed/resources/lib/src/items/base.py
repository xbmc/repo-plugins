# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from xbmcgui import ListItem  # pylint: disable=import-error


class Base:

    def __init__(self, **kwargs):
        self._list_item = ListItem(
            label=kwargs.get('label', ''),
            label2=kwargs.get('label2', ''),
            path=kwargs.get('path', ''),
            offscreen=True
        )

        self._is_folder = False

    @property
    def ListItem(self):  # pylint: disable=invalid-name
        return self._list_item

    def setIsPlayable(self, value=True):  # pylint: disable=invalid-name
        self.ListItem.setProperty('isPlayable', str(value).lower())

    def __iter__(self):
        payload = [self.ListItem.getPath(), self.ListItem, self._is_folder]
        for item in payload:
            yield item
