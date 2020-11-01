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

from twitch.api.parameters import StreamType, Platform


def route(api, stream_type=StreamType.LIVE, offset=0, platform=Platform.ALL):
    blacklist_filter = utils.BlacklistFilter()
    converter = JsonListItemConverter(LINE_LENGTH)
    utils.refresh_previews()
    kodi.set_view('videos', set_sort=True)
    per_page = utils.get_items_per_page()

    all_items = list()
    requests = 0
    total = 1000

    while (per_page >= (len(all_items) + 1)) and (requests < MAX_REQUESTS) and (int(offset) <= 900):
        requests += 1
        language = utils.get_language()
        streams = api.get_all_streams(stream_type=stream_type, platform=platform, offset=offset, limit=REQUEST_LIMIT, language=language)

        if (total > 0) and (Keys.STREAMS in streams):
            filtered = \
                blacklist_filter.by_type(streams, Keys.STREAMS, parent_keys=[Keys.CHANNEL], id_key=Keys._ID, list_type='user')
            filtered = \
                blacklist_filter.by_type(filtered, Keys.STREAMS, game_key=Keys.GAME, list_type='game')
            last = None
            for stream in filtered[Keys.STREAMS]:
                last = stream
                if per_page >= (len(all_items) + 1):
                    add_item = last if last not in all_items else None
                    if add_item:
                        all_items.append(add_item)
                else:
                    break
            offset = utils.get_offset(offset, last, streams[Keys.STREAMS])
            if (offset is None) or (total <= offset) or (total <= REQUEST_LIMIT):
                break
        else:
            break
    has_items = False
    if len(all_items) > 0:
        has_items = True
        for stream in all_items:
            kodi.create_item(converter.stream_to_listitem(stream))
    if (total - 100) > (int(offset) + 1) and (len(all_items) == per_page):
        has_items = True
        kodi.create_item(utils.link_to_next_page({'mode': MODES.STREAMLIST, 'stream_type': stream_type, 'platform': platform, 'offset': offset}))
    if has_items:
        kodi.end_of_directory()
        return
    raise NotFound(i18n('streams'))
