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
from ..addon.twitch_exceptions import NotFound
from ..addon.utils import i18n


def route(api, broadcast_type, channel_id=None, game=None, after='MA=='):
    converter = JsonListItemConverter(LINE_LENGTH)
    if (channel_id is None) and (game is None):
        return
    kodi.set_view('videos', set_sort=True)
    per_page = utils.get_items_per_page()
    all_items = list()
    user_ids = list()

    if game is not None:
        period = utils.get_sort('top_videos', 'period')
        videos = api.get_top_videos(after=after, first=per_page, game_id=game,
                                    broadcast_type=broadcast_type, period=period)
    else:
        if channel_id == 'all':
            period = utils.get_sort('top_videos', 'period')
            videos = api.get_top_videos(after=after, first=per_page, broadcast_type=broadcast_type, period=period)
        else:
            period = utils.get_sort('channel_videos', 'period')
            sort_by = utils.get_sort('channel_videos', 'by')
            language = utils.get_language()
            videos = api.get_channel_videos(channel_id, broadcast_type, period, after=after, first=per_page,
                                            sort_by=sort_by, language=language)

    for video in videos[Keys.DATA]:
        if video.get(Keys.USER_ID):
            user_ids.append(video[Keys.USER_ID])

    if user_ids:
        channels = api.get_users(user_ids)
        if Keys.DATA in channels:
            for idx, video in enumerate(videos[Keys.DATA]):
                videos[Keys.DATA][idx][Keys.OFFLINE_IMAGE_URL] = ''
                for channel in channels[Keys.DATA]:
                    if channel.get(Keys.ID) == video.get(Keys.USER_ID):
                        videos[Keys.DATA][idx][Keys.OFFLINE_IMAGE_URL] = channel[Keys.OFFLINE_IMAGE_URL]
                        break

    for video in videos[Keys.DATA]:
        all_items.append(video)

    if len(all_items) > 0:
        for video in all_items:
            kodi.create_item(converter.video_list_to_listitem(video))

        cursor = videos.get('pagination', {}).get('cursor')
        if cursor:
            kodi.create_item(utils.link_to_next_page({
                                                         'mode': MODES.CHANNELVIDEOLIST,
                                                         'channel_id': channel_id,
                                                         'game': game,
                                                         'broadcast_type': broadcast_type,
                                                         'after': cursor
                                                     }))

        kodi.end_of_directory()
        return

    raise NotFound(i18n('videos'))
