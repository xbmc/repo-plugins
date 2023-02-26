# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmc  # pylint: disable=import-error
import xbmcgui  # pylint: disable=import-error

from ..constants.media import LOGO_SMALL
from ..lib.txt_fmt import bold
from ..lib.url_utils import unquote
from ..storage.users import UserStorage


def invoke(context, action, playlist_type, playlist_id, playlist_title=''):  # pylint: disable=too-many-branches
    if playlist_type not in ['history', 'watchlater']:
        return

    message = ''
    users = UserStorage()

    if '%' in playlist_title:
        playlist_title = unquote(playlist_title)

    if action == 'add':
        if playlist_type == 'history':
            users.history_playlist = playlist_id
            if playlist_title:
                message = context.i18n('%s was configured as your history playlist') % \
                          bold(playlist_title)
            else:
                message = context.i18n('History playlist configured')

        if playlist_type == 'watchlater':
            users.watchlater_playlist = playlist_id
            if playlist_title:
                message = context.i18n('%s was configured as your watch later playlist') % \
                          bold(playlist_title)
            else:
                message = context.i18n('Watch later playlist configured')

    if action == 'remove':
        if playlist_type == 'history':
            if users.history_playlist == playlist_id:
                users.history_playlist = ''
                if playlist_title:
                    message = \
                        context.i18n('%s is no longer configured as your history playlist') % \
                        bold(playlist_title)
                else:
                    message = context.i18n('History playlist is no longer configured')

        if playlist_type == 'watchlater':
            if users.watchlater_playlist == playlist_id:
                users.watchlater_playlist = ''
                if playlist_title:
                    message = \
                        context.i18n('%s is no longer configured as your watch later playlist') % \
                        bold(playlist_title)
                else:
                    message = context.i18n('Watch later playlist is no longer configured')

    if message:
        xbmcgui.Dialog().notification(
            context.addon.getAddonInfo('name'),
            message,
            LOGO_SMALL,
            sound=False
        )
        users.save()
        del users

        xbmc.executebuiltin('Container.Refresh')
