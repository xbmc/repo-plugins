# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from html import unescape

import xbmc  # pylint: disable=import-error
import xbmcgui  # pylint: disable=import-error

from ..constants.media import LOGO_SMALL
from ..generators.data_cache import get_cached
from ..lib.txt_fmt import bold
from ..lib.url_utils import unquote
from ..storage.favorite_playlists import FavoritePlaylists
from ..storage.users import UserStorage


def invoke(context, action, playlist_id='', playlist_name=''):
    favorite_playlists = FavoritePlaylists(UserStorage().uuid,
                                           context.settings.favorite_playlist_maximum)

    if not playlist_name:
        cached_payload = get_cached(context, context.api.playlists, [playlist_id])
        cached_playlist = cached_payload.get(playlist_id, {})
        cached_snippet = cached_playlist.get('snippet', {})
        playlist_name = unescape(cached_snippet.get('title', ''))

    if action == 'add':
        if not playlist_id or not playlist_name:
            return

        if playlist_name and '%' in playlist_name:
            playlist_name = unquote(playlist_name)

        favorite_playlists.update(playlist_id, playlist_name)

        xbmcgui.Dialog().notification(
            context.i18n('Favorite Playlists'),
            context.i18n('Added %s to favorite playlists') % bold(playlist_name),
            LOGO_SMALL,
            sound=False
        )

    if action == 'clear':
        result = xbmcgui.Dialog().yesno(
            context.i18n('Clear favorite playlists'),
            context.i18n('You are about to clear your favorite playlists, are you sure?')
        )
        if not result:
            return

        favorite_playlists.clear()

        xbmcgui.Dialog().notification(
            context.i18n('Favorite Playlists'),
            context.i18n('Favorite playlists cleared'),
            LOGO_SMALL,
            sound=False
        )

    elif action == 'remove':
        if not playlist_id:
            return

        favorite = favorite_playlists.pop(playlist_id)
        if not favorite:
            return

        _, favorite_name = favorite

        if not favorite_name:
            message = context.i18n('Removed from favorite playlists')
        else:
            message = context.i18n('Removed %s from favorite playlists') % bold(favorite_name)

        xbmcgui.Dialog().notification(
            context.i18n('Favorite Playlists'),
            message,
            LOGO_SMALL,
            sound=False
        )

    xbmc.executebuiltin('Container.Refresh')
