# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import menu_items
from ..addon.common import kodi
from ..addon.constants import MODES
from ..addon.utils import i18n


def route(channel_id=None, channel_name=None, display_name=None, game=None):
    if (channel_id is None) and (game is None): return
    kodi.set_view('files', set_sort=False)
    context_menu = list()
    if channel_id == 'all' or game is not None:
        context_menu.extend(menu_items.change_period('top_videos'))
        menu_tag = display_name if display_name else game
        menu_tag = menu_tag if menu_tag else i18n('videos')
    else:
        context_menu.extend(menu_items.change_sort_by('channel_videos'))
        menu_tag = display_name if display_name else channel_name
        menu_tag = menu_tag if menu_tag else i18n('channels')
    kodi.create_item({'label': i18n('past_broadcasts'), 'path': {'mode': MODES.CHANNELVIDEOLIST, 'channel_id': channel_id, 'broadcast_type': 'archive', 'game': game},
                      'context_menu': context_menu, 'info': {'plot': '%s - %s' % (menu_tag, i18n('past_broadcasts'))}})
    kodi.create_item({'label': i18n('uploads'), 'path': {'mode': MODES.CHANNELVIDEOLIST, 'channel_id': channel_id, 'broadcast_type': 'upload', 'game': game},
                      'context_menu': context_menu, 'info': {'plot': '%s - %s' % (menu_tag, i18n('uploads'))}})
    kodi.create_item({'label': i18n('video_highlights'), 'path': {'mode': MODES.CHANNELVIDEOLIST, 'channel_id': channel_id, 'broadcast_type': 'highlight', 'game': game},
                      'context_menu': context_menu, 'info': {'plot': '%s - %s' % (menu_tag, i18n('video_highlights'))}})
    if channel_id != 'all':
        if channel_name or game:
            context_menu = list()
            context_menu.extend(menu_items.change_sort_by('clips'))
            context_menu.extend(menu_items.change_period('clips'))
            kodi.create_item({'label': i18n('clips'), 'path': {'mode': MODES.CLIPSLIST, 'channel_name': channel_name, 'game': game},
                              'context_menu': context_menu, 'info': {'plot': '%s - %s' % (menu_tag, i18n('clips'))}})
        if channel_id:
            kodi.create_item({'label': i18n('collections'), 'path': {'mode': MODES.COLLECTIONS, 'channel_id': channel_id},
                              'info': {'plot': '%s - %s' % (menu_tag, i18n('collections'))}})
    kodi.end_of_directory()
