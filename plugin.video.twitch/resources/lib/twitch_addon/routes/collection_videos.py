# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi
from ..addon.constants import Keys, LINE_LENGTH
from ..addon.converter import JsonListItemConverter
from ..addon.twitch_exceptions import NotFound
from ..addon.utils import i18n


def route(api, collection_id):
    blacklist_filter = utils.BlacklistFilter()
    converter = JsonListItemConverter(LINE_LENGTH)
    kodi.set_view('videos', set_sort=True)
    videos = api.get_collection_videos(collection_id)
    all_items = list()
    if (Keys.ITEMS in videos) and (len(videos[Keys.ITEMS]) > 0):
        filtered = \
            blacklist_filter.by_type(videos, Keys.ITEMS, parent_keys=[Keys.OWNER], id_key=Keys._ID, list_type='user')
        filtered = \
            blacklist_filter.by_type(filtered, Keys.ITEMS, game_key=Keys.GAME, list_type='game')
        for video in filtered[Keys.ITEMS]:
            add_item = video if video not in all_items else None
            if add_item:
                all_items.append(add_item)
        if len(all_items) > 0:
            for video in all_items:
                kodi.create_item(converter.collection_video_to_listitem(video))
            kodi.end_of_directory()
            return
    raise NotFound(i18n('videos'))
