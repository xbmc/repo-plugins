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

from twitch.api.parameters import StreamType


def route(api):
    has_token = True if api.access_token else False
    kodi.set_view('files', set_sort=False)
    show_menu = utils.show_menu
    if not has_token:
        _ = kodi.Dialog().ok(
            i18n('oauth_heading'),
            i18n('oauth_message') % (i18n('settings'), i18n('login'), i18n('get_oauth_token'))
        )

    if has_token:
        if show_menu('live', 'browse'):
            context_menu = list()
            kodi.create_item({'label': i18n('live_channels'), 'path': {'mode': MODES.STREAMLIST, 'stream_type': StreamType.LIVE},
                              'context_menu': context_menu, 'info': {'plot': '%s - %s' % (i18n('browse'), i18n('live_channels'))}, 'thumbfile': 'Live_Channels.png'})
        if show_menu('games', 'browse'):
            kodi.create_item({'label': i18n('games'), 'path': {'mode': MODES.GAMES},
                              'info': {'plot': '%s - %s' % (i18n('browse'), i18n('games'))}, 'thumbfile': 'Games.png'})

        if show_menu('live', 'following'):
            context_menu = list()
            kodi.create_item(
                {'label': '%s %s' % (i18n('following'), i18n('live_channels')), 'path': {'mode': MODES.FOLLOWED, 'content': StreamType.LIVE}, 'context_menu': context_menu,
                 'info': {'plot': '%s - %s' % (i18n('following'), i18n('live_channels'))}, 'thumbfile': 'Live_Channels.png'})
        if show_menu('channels', 'following'):
            context_menu = list()
            context_menu.extend(menu_items.change_sort_by('followed_channels'))
            context_menu.extend(menu_items.change_direction('followed_channels'))
            kodi.create_item({'label': '%s %s' % (i18n('following'), i18n('channels')), 'path': {'mode': MODES.FOLLOWED, 'content': 'channels'}, 'context_menu': context_menu,
                              'info': {'plot': '%s - %s' % (i18n('following'), i18n('channels'))}, 'thumbfile': 'Channels.png'})
        if show_menu('games', 'following') and utils.get_private_oauth_token():
            kodi.create_item({'label': '%s %s' % (i18n('following'), i18n('games')), 'path': {'mode': MODES.FOLLOWED, 'content': 'games'},
                              'info': {'plot': '%s - %s' % (i18n('following'), i18n('games'))}, 'thumbfile': 'Games.png'})
        if show_menu('following'):
            kodi.create_item({'label': i18n('following'), 'path': {'mode': MODES.FOLLOWING}, 'info': {'plot': i18n('following')}, 'thumbfile': 'Following.png'})

        if show_menu('streams', 'search'):
            context_menu = list()
            kodi.create_item({'label': '%s %s' % (i18n('search'), i18n('streams')), 'path': {'mode': MODES.NEWSEARCH, 'content': 'streams'}, 'context_menu': context_menu,
                              'info': {'plot': '%s - %s' % (i18n('search'), i18n('streams'))}, 'thumbfile': 'Streams.png'})
        if show_menu('channels', 'search'):
            kodi.create_item({'label': '%s %s' % (i18n('search'), i18n('channels')), 'path': {'mode': MODES.NEWSEARCH, 'content': 'channels'},
                              'info': {'plot': '%s - %s' % (i18n('search'), i18n('channels'))}, 'thumbfile': 'Channels.png'})
        if show_menu('games', 'search'):
            kodi.create_item({'label': '%s %s' % (i18n('search'), i18n('games')), 'path': {'mode': MODES.NEWSEARCH, 'content': 'games'},
                              'info': {'plot': '%s - %s' % (i18n('search'), i18n('games'))}, 'thumbfile': 'Games.png'})
        if show_menu('url', 'search'):
            kodi.create_item({'label': '%s %s' % (i18n('search'), i18n('video_id_url')), 'path': {'mode': MODES.NEWSEARCH, 'content': 'id_url'},
                              'info': {'plot': '%s - %s[CR]%s' % (i18n('search'), i18n('video_id_url'), i18n('search_id_url_description'))}, 'thumbfile': 'Video_Url.png'})
        if show_menu('search'):
            kodi.create_item({'label': i18n('search'), 'path': {'mode': MODES.SEARCH}, 'info': {'plot': i18n('search')}, 'thumbfile': 'Search.png'})

    if show_menu('settings'):
        kodi.create_item({'label': i18n('settings'), 'path': {'mode': MODES.SETTINGS}, 'info': {'plot': i18n('settings')}, 'is_folder': False, 'is_playable': False, 'thumbfile': 'Settings.png'})

    kodi.end_of_directory(cache_to_disc=False)
