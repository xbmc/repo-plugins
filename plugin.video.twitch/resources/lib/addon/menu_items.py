# -*- coding: utf-8 -*-
"""
     
    Copyright (C) 2016 Twitch-on-Kodi
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import utils
from common import kodi
from constants import MODES

i18n = utils.i18n


def run_plugin(label, queries):
    return [(label, 'RunPlugin(%s)' % kodi.get_plugin_url(queries))]


def update_container(label, queries):
    return [(label, 'Container.Update(%s)' % kodi.get_plugin_url(queries))]


def clear_previews():
    if kodi.get_setting('live_previews_enable') == 'true':
        return run_plugin(i18n('clear_live_preview'), {'mode': MODES.CLEARLIVEPREVIEWS, 'notify': utils.notify_refresh()})
    return []


def channel_videos(channel_id, channel_name, display_name):
    return update_container(i18n('go_to') % '[COLOR white][B]%s[/B][/COLOR]' % display_name,
                            {'mode': MODES.CHANNELVIDEOS, 'channel_id': channel_id, 'channel_name': channel_name, 'display_name': display_name})


def go_to_game(game):
    return update_container(i18n('go_to') % '[COLOR white][B]%s[/B][/COLOR]' % game, {'mode': MODES.GAMELISTS, 'game': game})


def refresh():
    return [(i18n('refresh'), 'Container.Refresh')]


def edit_follow(channel_id, display_name):
    return update_container(i18n('toggle_follow'), {'mode': MODES.EDITFOLLOW, 'channel_id': channel_id, 'channel_name': display_name})


def edit_block(target_id, display_name):
    return update_container(i18n('toggle_block'), {'mode': MODES.EDITBLOCK, 'target_id': target_id, 'name': display_name})


def add_blacklist(target_id, display_name, list_type='user'):
    return update_container(i18n('add_blacklist') % '[COLOR white][B]%s[/B][/COLOR]' % display_name,
                            {'mode': MODES.EDITBLACKLIST, 'target_id': target_id, 'name': display_name, 'list_type': list_type})


def set_default_quality(content_type, target_id, name, video_id=None, clip_id=None):
    return update_container(i18n('set_default_quality'),
                            {'mode': MODES.EDITQUALITIES, 'content_type': content_type, 'target_id': target_id,
                             'name': name, 'video_id': video_id, 'clip_id': clip_id})


def edit_follow_game(game):
    return update_container(i18n('toggle_follow'), {'mode': MODES.EDITFOLLOW, 'game': game})


def change_sort_by(for_type):
    return update_container(i18n('change_sort_by'), {'mode': MODES.EDITSORTING, 'list_type': for_type, 'sort_type': 'by'})


def change_period(for_type):
    return update_container(i18n('change_period'), {'mode': MODES.EDITSORTING, 'list_type': for_type, 'sort_type': 'period'})


def change_direction(for_type):
    return update_container(i18n('change_direction'), {'mode': MODES.EDITSORTING, 'list_type': for_type, 'sort_type': 'direction'})
