# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils, menu_items
from ..addon.common import kodi
from ..addon.constants import MODES
from ..addon.utils import i18n

from twitch.api.parameters import StreamType, Platform


def route():
    kodi.set_view('files', set_sort=False)
    context_menu = list()
    kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.STREAMLIST, 'stream_type': StreamType.LIVE},
                      'context_menu': context_menu, 'info': {'plot': '%s - %s' % (i18n('browse'), i18n('live_channels'))}, 'thumbfile': 'Live_Channels.png'})
    kodi.create_item({'label': i18n('xbox_one'), 'path': {'mode': MODES.STREAMLIST, 'platform': Platform.XBOX_ONE},
                      'context_menu': context_menu, 'info': {'plot': '%s - %s' % (i18n('browse'), i18n('xbox_one'))}, 'thumbfile': 'Xbox_One.png'})
    kodi.create_item({'label': i18n('ps4'), 'path': {'mode': MODES.STREAMLIST, 'platform': Platform.PS4}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (i18n('browse'), i18n('ps4'))}, 'thumbfile': 'Playstation_4.png'})
    kodi.create_item({'label': i18n('videos'), 'path': {'mode': MODES.CHANNELVIDEOS, 'channel_id': 'all'},
                      'info': {'plot': '%s - %s' % (i18n('browse'), i18n('videos'))}, 'thumbfile': 'Videos.png'})
    context_menu = list()
    context_menu.extend(menu_items.change_sort_by('clips'))
    context_menu.extend(menu_items.change_period('clips'))
    kodi.create_item({'label': i18n('clips'), 'path': {'mode': MODES.CLIPSLIST}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (i18n('browse'), i18n('clips'))}, 'thumbfile': 'Clips.png'})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.GAMES},
                      'info': {'plot': '%s - %s' % (i18n('browse'), i18n('games'))}, 'thumbfile': 'Games.png'})
    kodi.end_of_directory(cache_to_disc=False)
