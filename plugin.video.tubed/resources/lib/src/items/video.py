# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from .base import Base


class Video(Base):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.ListItem.setIsFolder(False)
        self.setIsPlayable(True)
