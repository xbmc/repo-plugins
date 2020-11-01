# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi
from ..addon.constants import Keys, LINE_LENGTH, MODES, CURSOR_LIMIT, MAX_REQUESTS
from ..addon.converter import JsonListItemConverter
from ..addon.twitch_exceptions import NotFound
from ..addon.utils import i18n


def route(api, cursor='MA==', channel_name=None, game=None):
    blacklist_filter = utils.BlacklistFilter()
    converter = JsonListItemConverter(LINE_LENGTH)
    kodi.set_view('videos', set_sort=True)
    sorting = utils.get_sort('clips')
    all_items = list()
    requests = 0
    language = utils.get_language()
    while (CURSOR_LIMIT >= (len(all_items) + 1)) and cursor and (requests < MAX_REQUESTS):
        requests += 1
        clips = api.get_top_clips(cursor, limit=CURSOR_LIMIT, channel=channel_name, game=game, period=sorting['period'], trending=sorting['by'], language=language)
        cursor = clips[Keys.CURSOR]
        if Keys.CLIPS in clips and len(clips[Keys.CLIPS]) > 0:
            filtered = \
                blacklist_filter.by_type(clips, Keys.CLIPS, parent_keys=[Keys.BROADCASTER], id_key=Keys.ID, list_type='user')
            filtered = \
                blacklist_filter.by_type(filtered, Keys.CLIPS, game_key=Keys.GAME, list_type='game')
            for clip in filtered[Keys.CLIPS]:
                add_item = clip if clip not in all_items else None
                if add_item:
                    all_items.append(add_item)
        else:
            break
    has_items = False
    if len(all_items) > 0:
        has_items = True
        for clip in all_items:
            kodi.create_item(converter.clip_to_listitem(clip))
    if cursor:
        has_items = True
        item_dict = {'mode': MODES.CLIPSLIST, 'cursor': cursor}
        if channel_name:
            item_dict['channel_name'] = channel_name
        kodi.create_item(utils.link_to_next_page(item_dict))
    if has_items:
        kodi.end_of_directory()
        return
    raise NotFound(i18n('clips'))
