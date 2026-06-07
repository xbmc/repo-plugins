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
from ..addon.utils import get_private_oauth_token
from ..addon.utils import i18n

from twitch.api.parameters import StreamType


def route():
    kodi.set_view('files', set_sort=False)
    context_menu = list()
    kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.FOLLOWED, 'content': StreamType.LIVE}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (i18n('following'), i18n('live_channels'))}, 'thumbfile': 'Live_Channels.png'})
    context_menu = list()
    context_menu.extend(menu_items.change_sort_by('followed_channels'))
    context_menu.extend(menu_items.change_direction('followed_channels'))
    kodi.create_item({'label': i18n('channels'), 'path': {'mode': MODES.FOLLOWED, 'content': 'channels'}, 'context_menu': context_menu,
                      'info': {'plot': '%s - %s' % (i18n('following'), i18n('channels'))}, 'thumbfile': 'Channels.png'})
    if get_private_oauth_token():
        kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.FOLLOWED, 'content': 'games'},
                          'info': {'plot': '%s - %s' % (i18n('following'), i18n('games'))}, 'thumbfile': 'Games.png'})

    kodi.end_of_directory(cache_to_disc=False)
