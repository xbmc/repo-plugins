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


def route(api, content, query, after='MA='):
    converter = JsonListItemConverter(LINE_LENGTH)
    history_size = utils.get_search_history_size()
    use_history = history_size > 0
    if content == 'streams':
        utils.refresh_previews()
        kodi.set_view('videos', set_sort=True)
        per_page = utils.get_items_per_page()
        all_items = []
        streams = api.get_stream_search(search_query=query, after=after, first=per_page)

        if Keys.DATA in streams:
            for stream in streams[Keys.DATA]:
                all_items.append(stream)

        if len(all_items) > 0:
            if use_history:
                history = utils.get_search_history(content)
                if history:
                    history.update(query)

            for stream in all_items:
                kodi.create_item(converter.search_stream_to_listitem(stream))

            cursor = streams.get('pagination', {}).get('cursor')
            if cursor:
                kodi.create_item(utils.link_to_next_page({'mode': MODES.SEARCHRESULTS, 'content': content,
                                                          'query': query, 'after': cursor}))
        else:
            kodi.create_item({'path': kodi.get_plugin_url({'mode': MODES.REFRESH}),
                              'label': i18n('refresh'),
                              'is_folder': False,
                              'is_playable': False})
        kodi.end_of_directory()
    elif content == 'channels':
        kodi.set_view('files', set_sort=False)
        per_page = utils.get_items_per_page()
        all_items = []
        channels = api.get_channel_search(search_query=query, after=after, first=per_page)

        if Keys.DATA in channels:
            for channel in channels[Keys.DATA]:
                all_items.append(channel)

        if len(all_items) > 0:
            if use_history:
                history = utils.get_search_history(content)
                if history:
                    history.update(query)

            for channel in all_items:
                kodi.create_item(converter.search_channel_to_listitem(channel))

            cursor = channels.get('pagination', {}).get('cursor')
            if cursor:
                kodi.create_item(utils.link_to_next_page({'mode': MODES.SEARCHRESULTS, 'content': content,
                                                          'query': query, 'after': cursor}))
        else:
            kodi.create_item({'path': kodi.get_plugin_url({'mode': MODES.REFRESH}),
                              'label': i18n('refresh'),
                              'is_folder': False,
                              'is_playable': False})

        kodi.end_of_directory()
    elif content == 'games':
        kodi.set_view('files', set_sort=False)
        per_page = utils.get_items_per_page()

        all_items = []
        games = api.get_game_search(search_query=query, after=after, first=per_page)
        if Keys.DATA in games:
            for game in games[Keys.DATA]:
                all_items.append(game)

        if len(all_items) > 0:
            if use_history:
                history = utils.get_search_history(content)
                if history:
                    history.update(query)

            for game in all_items:
                kodi.create_item(converter.game_to_listitem(game))

            cursor = games.get('pagination', {}).get('cursor')
            if cursor:
                kodi.create_item(utils.link_to_next_page({
                    'mode': MODES.GAMES,
                    'after': cursor
                }))

            kodi.end_of_directory()
        else:
            kodi.create_item({'path': kodi.get_plugin_url({'mode': MODES.REFRESH}),
                              'label': i18n('refresh'),
                              'is_folder': False,
                              'is_playable': False})
    elif content == 'id_url':
        kodi.set_view('videos', set_sort=True)
        all_items = []

        video_id, seek_time = utils.extract_video(query)
        try:
            results = api.get_video_by_id(video_id)
        except TwitchException:
            results = None

        if Keys.DATA in results:
            for video in results[Keys.DATA]:
                all_items.append(video)

        if all_items:
            if use_history:
                history = utils.get_search_history(content)
                if history:
                    history.update(query)
            window = kodi.Window(10000)
            if seek_time > 0:
                window.setProperty(kodi.get_id() + '-_seek', '%s,%d' % (video_id, seek_time))
            else:
                window.clearProperty(kodi.get_id() + '-_seek')

            for video in all_items:
                kodi.create_item(converter.video_list_to_listitem(video))

        kodi.end_of_directory()
