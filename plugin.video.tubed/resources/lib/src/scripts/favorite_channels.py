# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import re
from xml.etree import ElementTree

import xbmc  # pylint: disable=import-error
import xbmcgui  # pylint: disable=import-error

from ..constants.media import LOGO_SMALL
from ..lib.txt_fmt import bold
from ..lib.url_utils import unquote
from ..storage.favorite_channels import FavoriteChannels
from ..storage.users import UserStorage


def invoke(context, action, channel_id='', channel_name=''):
    favorite_channels = FavoriteChannels(UserStorage().uuid,
                                         context.settings.favorite_channel_maximum)

    if action == 'add':
        if not channel_id or not channel_name:
            return

        if channel_name and '%' in channel_name:
            channel_name = unquote(channel_name)

        favorite_channels.update(channel_id, channel_name)

        xbmcgui.Dialog().notification(
            context.i18n('Favorite Channels'),
            context.i18n('Added %s to favorite channels') % bold(channel_name),
            LOGO_SMALL,
            sound=False
        )

    if action == 'clear':
        result = xbmcgui.Dialog().yesno(
            context.i18n('Clear favorite channels'),
            context.i18n('You are about to clear your favorite channels, are you sure?')
        )
        if not result:
            return

        favorite_channels.clear()

        xbmcgui.Dialog().notification(
            context.i18n('Favorite Channels'),
            context.i18n('Favorite channels cleared'),
            LOGO_SMALL,
            sound=False
        )

    elif action == 'remove':
        if not channel_id:
            return

        favorite = favorite_channels.pop(channel_id)
        if not favorite:
            return

        _, favorite_name = favorite

        if not favorite_name:
            message = context.i18n('Removed from favorite channels')
        else:
            message = context.i18n('Removed %s from favorite channels') % bold(favorite_name)

        xbmcgui.Dialog().notification(
            context.i18n('Favorite Channels'),
            message,
            LOGO_SMALL,
            sound=False
        )

    elif action == 'import':
        files = xbmcgui.Dialog().browseMultiple(
            1,
            context.i18n('Import from xml'),
            'local',
            '.xml'
        )
        if not files:
            return

        for filename in files:
            success = import_xml(favorite_channels, filename)

            if success:
                xbmcgui.Dialog().notification(
                    context.i18n('Favorite Channels'),
                    context.i18n('Import completed successfully'),
                    LOGO_SMALL,
                    sound=False
                )
            else:
                xbmcgui.Dialog().notification(
                    context.i18n('Favorite Channels'),
                    context.i18n('Import failed'),
                    LOGO_SMALL,
                    sound=False
                )

    xbmc.executebuiltin('Container.Refresh')


def import_xml(favorite_channels, filename):
    try:
        root = ElementTree.parse(filename).getroot()
    except (ElementTree.ParseError, FileNotFoundError):
        return False

    body = root.find('body')
    if not body:
        return False

    outline = body.find('outline')
    if not outline:
        return False

    outlines = outline.findall('outline')
    if not outlines:
        return False

    imported_one = False
    for outline in outlines:
        if not outline.get('xmlUrl'):
            continue

        search = re.search(
            r'https://www\.youtube\.com/feeds/videos\.xml\?channel_id='
            r'(?P<channel_id>[a-zA-Z0-9_\-]+)',
            outline.get('xmlUrl')
        )

        if not search:
            continue

        channel_id = search.group('channel_id')
        if not channel_id:
            continue

        channel_name = outline.get('title') or outline.get('text')
        if not channel_name:
            continue

        favorite_channels.update(channel_id, channel_name)
        imported_one = True

    return imported_one
