# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from enum import Enum


class SCRIPT_MODES(Enum):  # pylint: disable=invalid-name
    MAIN = 'main'
    SEARCH_HISTORY = 'search_history'
    CONFIGURE_REGIONAL = 'configure_regional'
    CONFIGURE_SUBTITLES = 'configure_subtitles'
    SUBSCRIPTIONS = 'subscriptions'
    PLAY = 'play'
    RATE = 'rate'
    PLAYLIST = 'playlist'
    CACHE = 'cache'
    READ_COMMENT = 'read_comment'
    POST_PLAY = 'post_play'
    CONFIGURE_PLAYLISTS = 'configure_playlists'
    FAVORITE_CHANNELS = 'favorite_channels'
    REFRESH = 'refresh'
    HIDE_MENU = 'hide_menu'
    DIALOG_DEMO = 'dialog_demo'
    FAVORITE_PLAYLISTS = 'favorite_playlists'
    BACKUP = 'backup'

    def __str__(self):
        return str(self.value).lower()
