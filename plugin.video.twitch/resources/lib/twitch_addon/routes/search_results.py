# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi
from ..addon.constants import Keys, LINE_LENGTH, MODES
from ..addon.converter import JsonListItemConverter
from ..addon.twitch_exceptions import TwitchException
from ..addon.utils import i18n


def route(api, content, query, index=0):
    converter = JsonListItemConverter(LINE_LENGTH)
    history_size = utils.get_search_history_size()
    use_history = history_size > 0
    if content == 'streams':
        utils.refresh_previews()
        kodi.set_view('videos', set_sort=True)
        index, offset, limit = utils.calculate_pagination_values(index)
        results = api.get_stream_search(search_query=query, offset=offset, limit=limit)
        if (results[Keys.TOTAL] > 0) and (Keys.STREAMS in results):
            if use_history:
                history = utils.get_search_history(content)
                if history:
                    history.update(query)
            for stream in results[Keys.STREAMS]:
                kodi.create_item(converter.stream_to_listitem(stream))
            if results[Keys.TOTAL] > (offset + limit):
                kodi.create_item(utils.link_to_next_page({'mode': MODES.SEARCHRESULTS, 'content': content, 'query': query, 'index': index}))
        else:
            kodi.create_item({'path': kodi.get_plugin_url({'mode': MODES.REFRESH}),
                              'label': i18n('refresh'),
                              'is_folder': False,
                              'is_playable': False})
        kodi.end_of_directory()
    elif content == 'channels':
        kodi.set_view('files', set_sort=False)
        index, offset, limit = utils.calculate_pagination_values(index)
        results = api.get_channel_search(search_query=query, offset=offset, limit=limit)
        if (results[Keys.TOTAL] > 0) and (Keys.CHANNELS in results):
            if use_history:
                history = utils.get_search_history(content)
                if history:
                    history.update(query)
            for channel in results[Keys.CHANNELS]:
                kodi.create_item(converter.channel_to_listitem(channel))
            if results[Keys.TOTAL] > (offset + limit):
                kodi.create_item(utils.link_to_next_page({'mode': MODES.SEARCHRESULTS, 'content': content, 'query': query, 'index': index}))
        kodi.end_of_directory()
    elif content == 'games':
        kodi.set_view('files', set_sort=False)
        results = api.get_game_search(search_query=query)
        if (Keys.GAMES in results) and (results[Keys.GAMES]):
            if use_history:
                history = utils.get_search_history(content)
                if history:
                    history.update(query)
            for game in results[Keys.GAMES]:
                kodi.create_item(converter.game_to_listitem(game))
        kodi.end_of_directory()
    elif content == 'id_url':
        kodi.set_view('videos', set_sort=True)
        video_id, seek_time = utils.extract_video(query)
        try:
            results = api.get_video_by_id(video_id)
        except TwitchException:
            results = None
        if results:
            if video_id.startswith('a') or video_id.startswith('c') or video_id.startswith('v'):
                if use_history:
                    history = utils.get_search_history(content)
                    if history:
                        history.update(query)
                window = kodi.Window(10000)
                if seek_time > 0:
                    window.setProperty(kodi.get_id() + '-_seek', '%s,%d' % (video_id, seek_time))
                else:
                    window.clearProperty(kodi.get_id() + '-_seek')
                kodi.create_item(converter.video_list_to_listitem(results))
        kodi.end_of_directory()
