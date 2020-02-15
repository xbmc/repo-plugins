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


def route(api, channel_id, cursor='MA=='):
    blacklist_filter = utils.BlacklistFilter()
    converter = JsonListItemConverter(LINE_LENGTH)
    kodi.set_view('files', set_sort=False)
    all_items = list()
    requests = 0
    while (CURSOR_LIMIT >= (len(all_items) + 1)) and cursor and (requests < MAX_REQUESTS):
        requests += 1
        collections = api.get_collections(channel_id, cursor, limit=CURSOR_LIMIT)
        cursor = collections[Keys.CURSOR]
        if (Keys.COLLECTIONS in collections) and (len(collections[Keys.COLLECTIONS]) > 0):
            filtered = \
                blacklist_filter.by_type(collections, Keys.COLLECTIONS, parent_keys=[Keys.OWNER], id_key=Keys._ID, list_type='user')
            for collection in filtered[Keys.COLLECTIONS]:
                if collection[Keys.ITEMS_COUNT] > 0:
                    add_item = collection if collection not in all_items else None
                    if add_item:
                        all_items.append(add_item)
        else:
            break
    has_items = False
    if len(all_items) > 0:
        has_items = True
        for collection in all_items:
            kodi.create_item(converter.collection_to_listitem(collection))
    if cursor:
        has_items = True
        kodi.create_item(utils.link_to_next_page({'mode': MODES.COLLECTIONS, 'channel_id': channel_id, 'cursor': cursor}))
    if has_items:
        kodi.end_of_directory()
        return
    raise NotFound(i18n('collections'))
