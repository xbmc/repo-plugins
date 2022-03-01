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


def route():
    kodi.set_view('files', set_sort=False)
    context_menu = list()
    kodi.create_item({'label': i18n('live_channels'),
                      'path': {'mode': MODES.STREAMLIST},
                      'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (i18n('browse'), i18n('live_channels'))},
                      'thumbfile': 'Live_Channels.png'})

    context_menu = list()
    context_menu.extend(menu_items.change_sort_by('clips'))
    context_menu.extend(menu_items.change_period('clips'))
    kodi.create_item({'label': i18n('clips'), 'path': {'mode': MODES.CLIPSLIST}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (i18n('browse'), i18n('clips'))}, 'thumbfile': 'Clips.png'})
    kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.GAMES},
                      'info': {'plot': '%s - %s' % (i18n('browse'), i18n('games'))}, 'thumbfile': 'Games.png'})
    kodi.end_of_directory(cache_to_disc=False)
