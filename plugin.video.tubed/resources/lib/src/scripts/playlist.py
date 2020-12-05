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
from ..generators.utils import get_thumbnail
from ..lib.memoizer import reset_cache
from ..lib.txt_fmt import bold
from ..lib.url_utils import unquote
from ..storage.users import UserStorage


def invoke(context, action, video_id='', video_title='', playlist_id='',  # pylint: disable=too-many-branches
           playlist_title='', playlistitem_id=''):
    if not required_arguments_check(action, video_id, playlist_id, playlistitem_id):
        return

    if '%' in video_title:
        video_title = unquote(video_title)

    if '%' in playlist_title:
        playlist_title = unquote(playlist_title)

    choosing_watch_later = playlist_id == 'watch_later_prompt'

    message = ''

    if action == 'add':
        result = add(context, video_id, playlist_id, playlist_title)
        if not result:
            return

        video_title, playlist_title = result

        if choosing_watch_later:
            message = context.i18n('Added %s to the new watch later playlist %s') % \
                      (bold(video_title), bold(playlist_title))

        else:
            message = context.i18n('Added %s to %s') % (bold(video_title), bold(playlist_title))

    elif action == 'delete':
        result = delete(context, playlist_id, playlist_title)
        if not result:
            return

        message = context.i18n('Playlist deleted')
        if playlist_title:
            message = context.i18n('%s playlist deleted') % bold(playlist_title)

    elif action == 'remove':
        result = remove(context, playlistitem_id)
        if not result:
            return

        message = context.i18n('Removed from playlist')
        if video_title:
            message = context.i18n('Removed %s from playlist') % bold(video_title)

    elif action == 'rename':
        result = rename(context, playlist_id)
        if not result:
            return

        message = context.i18n('Playlist renamed to %s') % bold(result)
        if playlist_title:
            message = context.i18n('%s renamed to %s') % (bold(playlist_title), bold(result))

    if message:
        xbmcgui.Dialog().notification(
            context.addon.getAddonInfo('name'),
            message,
            LOGO_SMALL,
            sound=False
        )

        reset_cache()
        xbmc.executebuiltin('Container.Refresh')


def required_arguments_check(action, video_id, playlist_id, playlistitem_id):
    if action == 'add' and not video_id:
        return False

    if action == 'remove' and not playlistitem_id:
        return False

    if action == 'delete' and not playlist_id:
        return False

    return True


def add(context, video_id, playlist_id='', playlist_title=''):  # pylint: disable=too-many-branches
    page_token = ''
    default_title = ''

    choosing_watch_later = playlist_id == 'watch_later_prompt'
    if choosing_watch_later:
        default_title = playlist_title
        playlist_id = ''
        playlist_title = ''

    while not playlist_id and not playlist_title:

        payload = context.api.playlists_of_channel(
            'mine',
            page_token=page_token,
            fields='items(kind,id,snippet(title,description,thumbnails))'
        )

        if 'error' in payload:
            return None

        playlists = [(item.get('snippet', {}), item.get('id'))
                     for item in payload['items']]

        if playlists:
            playlist_snippets, playlist_ids = zip(*playlists)
            playlist_snippets = list(playlist_snippets)
            playlist_ids = list(playlist_ids)
        else:
            playlist_ids = []
            playlist_snippets = []

        if not page_token:
            playlist_ids = ['new'] + playlist_ids
            snippet = {
                'title': bold(context.i18n('New playlist')),
                'description': context.i18n('Create a new playlist'),
                'thumbnails': {
                    'standard': {
                        'url': 'DefaultVideoPlaylists.png'
                    }
                }
            }
            playlist_snippets = [snippet] + playlist_snippets

        page_token = payload.get('nextPageToken')
        if page_token:
            playlist_ids += ['next']
            snippet = {
                'title': bold(context.i18n('Next Page')),
                'description': context.i18n('Go to the next page'),
                'thumbnails': {
                    'standard': {
                        'url': ''
                    }
                }
            }
            playlist_snippets += [snippet]

        list_items = []
        for index, _ in enumerate(playlist_ids):
            item = xbmcgui.ListItem(
                label=unescape(playlist_snippets[index].get('title', '')),
                label2=unescape(playlist_snippets[index].get('description', ''))
            )

            thumbnail = get_thumbnail(playlist_snippets[index])
            item.setArt({
                'icon': thumbnail,
                'thumb': thumbnail,
            })

            list_items.append(item)

        if choosing_watch_later:
            heading = context.i18n('Choose watch later playlist')
        else:
            heading = context.i18n('Add to playlist')

        result = xbmcgui.Dialog().select(heading, list_items, useDetails=True)
        if result == -1:
            return None

        playlist_id = playlist_ids[result]
        if playlist_id == 'next':
            playlist_id = ''
            continue

        playlist_title = unescape(playlist_snippets[result].get('title', ''))
        break

    if playlist_id == 'new':
        playlist_title = _get_title_from_user(context, default_title)
        if not playlist_title:
            return None

        payload = context.api.create_playlist(playlist_title,
                                              fields='kind,id,snippet(title)')
        if payload.get('kind') != 'youtube#playlist':
            return None

        playlist_id = payload['id']
        playlist_title = unescape(payload['snippet'].get('title', ''))

    if not playlist_id:
        return None

    payload = context.api.add_to_playlist(playlist_id, video_id, fields='kind,snippet(title)')
    if payload.get('kind') != 'youtube#playlistItem':
        return None

    video_title = unescape(payload['snippet'].get('title', ''))

    if choosing_watch_later:
        users = UserStorage()
        users.watchlater_playlist = playlist_id
        users.save()

    return video_title, playlist_title


def delete(context, playlist_id, playlist_title):
    message = context.i18n('You are about to delete a playlist, are you sure?')
    if playlist_title:
        message = context.i18n('You are about to delete %s, are you sure?') % bold(playlist_title)

    result = xbmcgui.Dialog().yesno(context.i18n('Delete playlist'), message)
    if not result:
        return False

    payload = context.api.remove_playlist(playlist_id)

    try:
        success = int(payload.get('error', {}).get('code', 204)) == 204
    except ValueError:
        success = False

    if success:

        users = UserStorage()
        if playlist_id == users.history_playlist:
            users.history_playlist = ''
            users.save()

        elif playlist_id == users.watchlater_playlist:
            users.watchlater_playlist = ''
            users.save()

    return success


def remove(context, playlistitem_id):
    payload = context.api.remove_from_playlist(playlistitem_id)
    try:
        return int(payload.get('error', {}).get('code', 204)) == 204
    except ValueError:
        return False


def rename(context, playlist_id):
    playlist_title = _get_title_from_user(context)
    if not playlist_title:
        return False

    payload = context.api.rename_playlist(playlist_id, playlist_title, fields='kind,snippet(title)')
    if payload.get('kind', '') != 'youtube#playlist':
        return False

    return unescape(payload['snippet'].get('title', '')) or playlist_title


def _get_title_from_user(context, default=''):
    keyboard = xbmc.Keyboard()
    keyboard.setHeading(context.i18n('Enter your playlist title'))
    keyboard.setDefault(default)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return None

    playlist_title = keyboard.getText()
    playlist_title = playlist_title.strip()
    if not playlist_title:
        return None

    return playlist_title
