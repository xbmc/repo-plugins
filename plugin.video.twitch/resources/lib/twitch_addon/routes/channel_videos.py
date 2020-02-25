# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi
from ..addon.constants import Keys, LINE_LENGTH, MODES, MAX_REQUESTS, REQUEST_LIMIT
from ..addon.converter import JsonListItemConverter
from ..addon.twitch_exceptions import NotFound
from ..addon.utils import i18n


def route(api, broadcast_type, channel_id=None, game=None, offset=0):
    blacklist_filter = utils.BlacklistFilter()
    converter = JsonListItemConverter(LINE_LENGTH)
    if (channel_id is None) and (game is None): return
    kodi.set_view('videos', set_sort=True)
    per_page = utils.get_items_per_page()
    videos = None
    all_items = list()
    requests = 0
    while (per_page >= (len(all_items) + 1)) and (requests < MAX_REQUESTS):
        requests += 1
        if game is not None:
            period = utils.get_sort('top_videos', 'period')
            videos = api.get_top_videos(offset, limit=REQUEST_LIMIT, game=game, broadcast_type=broadcast_type, period=period)
        else:
            if channel_id == 'all':
                period = utils.get_sort('top_videos', 'period')
                videos = api.get_top_videos(offset, limit=REQUEST_LIMIT, broadcast_type=broadcast_type, period=period)
            else:
                sort_by = utils.get_sort('channel_videos', 'by')
                languages = ','.join(utils.get_languages())
                videos = api.get_channel_videos(channel_id, offset, limit=REQUEST_LIMIT, broadcast_type=broadcast_type, sort_by=sort_by, language=languages)
        if Keys.VODS in videos or ((videos[Keys.TOTAL] > 0) and (Keys.VIDEOS in videos)):
            key = Keys.VODS if Keys.VODS in videos else Keys.VIDEOS
            filtered = \
                blacklist_filter.by_type(videos, key, parent_keys=[Keys.CHANNEL], id_key=Keys._ID, list_type='user')
            filtered = \
                blacklist_filter.by_type(filtered, key, game_key=Keys.GAME, list_type='game')
            last = None
            for video in filtered[key]:
                last = video
                if per_page >= (len(all_items) + 1):
                    add_item = last if last not in all_items else None
                    if add_item:
                        all_items.append(add_item)
                else:
                    break
            offset = utils.get_offset(offset, last, videos[key])
            if (offset is None) or ((key == Keys.VIDEOS) and ((videos[Keys.TOTAL] <= offset) or (videos[Keys.TOTAL] <= REQUEST_LIMIT))):
                break
        else:
            break
    has_items = False
    if len(all_items) > 0 and videos is not None:
        has_items = True
        for video in all_items:
            kodi.create_item(converter.video_list_to_listitem(video))
    if Keys.VODS in videos or videos[Keys.TOTAL] > (offset + 1):
        has_items = True
        kodi.create_item(utils.link_to_next_page({'mode': MODES.CHANNELVIDEOLIST, 'channel_id': channel_id, 'broadcast_type': broadcast_type, 'offset': offset}))
    if has_items:
        kodi.end_of_directory()
        return
    raise NotFound(i18n('videos'))
