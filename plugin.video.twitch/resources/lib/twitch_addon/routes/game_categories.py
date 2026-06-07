# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon.common import kodi
from ..addon.constants import MODES
from ..addon.utils import i18n


def route(game_id, game_name):
    kodi.set_view('files', set_sort=False)
    context_menu = list()
    kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.GAMESTREAMS, 'game': game_id},
                      'context_menu': context_menu, 'info': {'plot': '%s - %s' % (game_name, i18n('live_channels'))},
                      'thumbfile': 'Live_Channels.png'})
    kodi.create_item({'label': i18n('videos'), 'path': {'mode': MODES.CHANNELVIDEOS, 'game': game_id,
                                                        'game_name': game_name},
                      'info': {'plot': '%s - %s' % (game_name, i18n('videos'))}, 'thumbfile': 'Videos.png'})
    kodi.end_of_directory()
