# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmc  # pylint: disable=import-error

from ..dialogs.autoplay_related import AutoplayRelated
from ..dialogs.common import open_dialog
from ..lib.memoizer import reset_cache
from ..lib.utils import wait_for_busy_dialog
from ..storage.users import UserStorage
from .utils import rate


def invoke(context, video_id, position=-1, live=False):
    users = UserStorage()
    if not post_play(context, users):
        return

    try:
        position = int(position)
    except ValueError:
        position = -1

    has_channel_mine = False
    if context.api.logged_in:
        has_channel_mine = context.api.channel_by_username('mine') != {}

    if not live and context.settings.post_play_rate:
        rate(context, video_id)

    if not live and context.settings.autoplay_related:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)

        spread = 1
        if position == -1:
            spread += 1

        if (position + spread) == playlist.size():
            start_position = position + spread
            successful = open_dialog(context, AutoplayRelated, video_id=video_id)

            if successful and start_position < playlist.size():
                safe = wait_for_busy_dialog()
                if safe:
                    xbmc.Player().play(item=playlist, startpos=start_position)

    if has_channel_mine and users.history_playlist:
        try:
            _ = context.api.add_to_playlist(users.history_playlist, video_id)
        except:  # pylint: disable=bare-except
            pass

    if has_channel_mine and users.watchlater_playlist:
        try:
            playlist_item_id = \
                context.api.video_id_to_playlist_item_id(users.watchlater_playlist, video_id)

            if playlist_item_id:
                _ = context.api.remove_from_playlist(playlist_item_id)
        except:  # pylint: disable=bare-except
            pass

    reset_cache()


def post_play(context, users):
    if context.settings.post_play_rate:
        return True

    if context.settings.autoplay_related:
        return True

    if users.history_playlist:
        return True

    if users.watchlater_playlist:
        return True

    return False
