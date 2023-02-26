# -*- coding: utf-8 -*-
"""
     
    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

from . import utils
from .common import kodi
from .constants import MODES, Scripts

i18n = utils.i18n


def run_plugin(label, queries):
    return [(label, 'RunPlugin(%s)' % kodi.get_plugin_url(queries))]


def update_container(label, queries):
    return [(label, 'Container.Update(%s)' % kodi.get_plugin_url(queries))]


def clear_search_history(search_type, do_refresh=False):
    params = {'mode': MODES.CLEARSEARCHHISTORY, 'search_type': search_type}
    if do_refresh:
        params['refresh'] = do_refresh
    return run_plugin(i18n('clear_search_history'), params)


def remove_search_history(search_type, query, do_refresh=True):
    query_label = '[B]%s[/B]' % query
    params = {'mode': MODES.REMOVESEARCHHISTORY, 'search_type': search_type, 'query': query}
    if not do_refresh:
        params['refresh'] = do_refresh
    return run_plugin(i18n('remove_') % query_label, params)


def channel_videos(channel_id, channel_name, display_name):
    return update_container(i18n('go_to') % ''.join(['[COLOR=white][B]', display_name, '[/B][/COLOR]']),
                            {'mode': MODES.CHANNELVIDEOS, 'channel_id': channel_id, 'channel_name': channel_name, 'display_name': display_name})


def go_to_game(game, game_id):
    return update_container(i18n('go_to') % ''.join(['[COLOR=white][B]', game, '[/B][/COLOR]']),
                            {'mode': MODES.GAMELISTS, 'game_name': game, 'game_id': game_id})


def refresh():
    return [(i18n('refresh'), 'RunScript(%s)' % Scripts.REFRESH)]


def edit_follow(channel_id, display_name):
    return run_plugin(i18n('toggle_follow'), {'mode': MODES.EDITFOLLOW, 'channel_id': channel_id, 'channel_name': display_name})


def set_default_quality(content_type, target_id, name, video_id=None, clip_id=None):
    return run_plugin(i18n('set_default_quality'),
                      {'mode': MODES.EDITQUALITIES, 'content_type': content_type, 'target_id': target_id,
                       'name': name, 'video_id': video_id, 'clip_id': clip_id})


def edit_follow_game(game_id, game_name, follow=True):
    if follow:
        return run_plugin(i18n('Follow'), {'mode': MODES.EDITFOLLOW, 'game_id': game_id, 'game_name': game_name, 'follow': True})
    else:
        return run_plugin(i18n('Unfollow'), {'mode': MODES.EDITFOLLOW, 'game_id': game_id, 'game_name': game_name, 'follow': False})


def change_sort_by(for_type):
    return run_plugin(i18n('change_sort_by'), {'mode': MODES.EDITSORTING, 'list_type': for_type, 'sort_type': 'by'})


def change_period(for_type):
    return run_plugin(i18n('change_period'), {'mode': MODES.EDITSORTING, 'list_type': for_type, 'sort_type': 'period'})


def change_direction(for_type):
    return run_plugin(i18n('change_direction'), {'mode': MODES.EDITSORTING, 'list_type': for_type, 'sort_type': 'direction'})


def queue():
    return [(i18n('Add_to_queue'), 'Action(Queue)')]
