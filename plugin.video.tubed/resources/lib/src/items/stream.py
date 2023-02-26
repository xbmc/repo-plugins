# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from .base import Base


class Stream(Base):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.ListItem.setIsFolder(False)
        self.setIsPlayable(True)

        headers = kwargs.get('headers', '')
        license_key = kwargs.get('license_key', '')

        self.ListItem.setPath('|'.join([self.ListItem.getPath(), headers]))
        self.ListItem.setContentLookup(False)
        self.ListItem.setMimeType('application/dash+xml')

        self.ListItem.setProperty('inputstream', 'inputstream.adaptive')
        self.ListItem.setProperty('inputstream.adaptive.manifest_type', 'mpd')

        if headers:
            self.ListItem.setProperty('inputstream.adaptive.stream_headers', headers)

        if license_key:
            self.ListItem.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            self.ListItem.setProperty('inputstream.adaptive.license_key', license_key)
