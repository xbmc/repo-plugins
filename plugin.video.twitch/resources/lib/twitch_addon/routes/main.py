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


def route(api):
    has_token = True if api.access_token else False
    kodi.set_view('files', set_sort=False)
    show_menu = utils.show_menu

    if show_menu('featured'):
        context_menu = list()
        kodi.create_item({'label': i18n('featured_streams'), 'path': {'mode': MODES.FEATUREDSTREAMS}, 'context_menu': context_menu,
                          'info': {'plot': i18n('featured_streams')}})
    if has_token:
        if show_menu('live', 'following'):
            context_menu = list()
            kodi.create_item(
                {'label': '%s %s' % (i18n('following'), i18n('live_channels')), 'path': {'mode': MODES.FOLLOWED, 'content': StreamType.LIVE}, 'context_menu': context_menu,
                 'info': {'plot': '%s - %s' % (i18n('following'), i18n('live_channels'))}})
        if show_menu('channels', 'following'):
            context_menu = list()
            context_menu.extend(menu_items.change_sort_by('followed_channels'))
            context_menu.extend(menu_items.change_direction('followed_channels'))
            kodi.create_item({'label': '%s %s' % (i18n('following'), i18n('channels')), 'path': {'mode': MODES.FOLLOWED, 'content': 'channels'}, 'context_menu': context_menu,
                              'info': {'plot': '%s - %s' % (i18n('following'), i18n('channels'))}})
        if show_menu('games', 'following') and utils.get_private_oauth_token():
            kodi.create_item({'label': '%s %s' % (i18n('following'), i18n('games')), 'path': {'mode': MODES.FOLLOWED, 'content': 'games'},
                              'info': {'plot': '%s - %s' % (i18n('following'), i18n('games'))}})
        if show_menu('clips', 'following'):
            context_menu = list()
            context_menu.extend(menu_items.change_sort_by('clips'))
            kodi.create_item({'label': '%s %s' % (i18n('following'), i18n('clips')), 'path': {'mode': MODES.FOLLOWED, 'content': 'clips'}, 'context_menu': context_menu,
                              'info': {'plot': '%s - %s' % (i18n('following'), i18n('clips'))}})
        if show_menu('following'):
            kodi.create_item({'label': i18n('following'), 'path': {'mode': MODES.FOLLOWING}, 'info': {'plot': i18n('following')}})
    if show_menu('live', 'browse'):
        context_menu = list()
        kodi.create_item({'label': '%s %s' % (i18n('browse'), i18n('live_channels')), 'path': {'mode': MODES.STREAMLIST, 'stream_type': StreamType.LIVE},
                          'context_menu': context_menu, 'info': {'plot': '%s - %s' % (i18n('browse'), i18n('live_channels'))}})
    if show_menu('xbox_one', 'browse'):
        context_menu = list()
        kodi.create_item({'label': '%s %s' % (i18n('browse'), i18n('xbox_one')), 'path': {'mode': MODES.STREAMLIST, 'platform': Platform.XBOX_ONE},
                          'context_menu': context_menu, 'info': {'plot': '%s - %s' % (i18n('browse'), i18n('xbox_one'))}})
    if show_menu('ps4', 'browse'):
        context_menu = list()
        kodi.create_item({'label': '%s %s' % (i18n('browse'), i18n('ps4')), 'path': {'mode': MODES.STREAMLIST, 'platform': Platform.PS4}, 'context_menu': context_menu,
                          'info': {'plot': '%s - %s' % (i18n('browse'), i18n('ps4'))}})
    if show_menu('videos', 'browse'):
        kodi.create_item({'label': '%s %s' % (i18n('browse'), i18n('videos')), 'path': {'mode': MODES.CHANNELVIDEOS, 'channel_id': 'all'},
                          'info': {'plot': '%s - %s' % (i18n('browse'), i18n('videos'))}})
    if show_menu('clips', 'browse'):
        context_menu = list()
        context_menu.extend(menu_items.change_sort_by('clips'))
        context_menu.extend(menu_items.change_period('clips'))
        kodi.create_item({'label': '%s %s' % (i18n('browse'), i18n('clips')), 'path': {'mode': MODES.CLIPSLIST}, 'context_menu': context_menu,
                          'info': {'plot': '%s - %s' % (i18n('browse'), i18n('clips'))}})
    if show_menu('games', 'browse'):
        kodi.create_item({'label': '%s %s' % (i18n('browse'), i18n('games')), 'path': {'mode': MODES.GAMES},
                          'info': {'plot': '%s - %s' % (i18n('browse'), i18n('games'))}})
    if show_menu('browse'):
        kodi.create_item({'label': i18n('browse'), 'path': {'mode': MODES.BROWSE}, 'info': {'plot': i18n('browse')}})
    if show_menu('streams', 'search'):
        context_menu = list()
        kodi.create_item({'label': '%s %s' % (i18n('search'), i18n('streams')), 'path': {'mode': MODES.NEWSEARCH, 'content': 'streams'}, 'context_menu': context_menu,
                          'info': {'plot': '%s - %s' % (i18n('search'), i18n('streams'))}})
    if show_menu('channels', 'search'):
        kodi.create_item({'label': '%s %s' % (i18n('search'), i18n('channels')), 'path': {'mode': MODES.NEWSEARCH, 'content': 'channels'},
                          'info': {'plot': '%s - %s' % (i18n('search'), i18n('channels'))}})
    if show_menu('games', 'search'):
        kodi.create_item({'label': '%s %s' % (i18n('search'), i18n('games')), 'path': {'mode': MODES.NEWSEARCH, 'content': 'games'},
                          'info': {'plot': '%s - %s' % (i18n('search'), i18n('games'))}})
    if show_menu('url', 'search'):
        kodi.create_item({'label': '%s %s' % (i18n('search'), i18n('video_id_url')), 'path': {'mode': MODES.NEWSEARCH, 'content': 'id_url'},
                          'info': {'plot': '%s - %s[CR]%s' % (i18n('search'), i18n('video_id_url'), i18n('search_id_url_description'))}})
    if show_menu('search'):
        kodi.create_item({'label': i18n('search'), 'path': {'mode': MODES.SEARCH}, 'info': {'plot': i18n('search')}})
    if show_menu('settings'):
        kodi.create_item({'label': i18n('settings'), 'path': {'mode': MODES.SETTINGS}, 'info': {'plot': i18n('settings')}, 'is_folder': False, 'is_playable': False})
    kodi.end_of_directory(cache_to_disc=False)
