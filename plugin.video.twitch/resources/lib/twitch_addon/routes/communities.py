# -*- coding: utf-8 -*-
from ..addon import utils
from ..addon.common import kodi
from ..addon.constants import Keys, LINE_LENGTH, MODES, MAX_REQUESTS, CURSOR_LIMIT
from ..addon.converter import JsonListItemConverter
from ..addon.twitch_exceptions import NotFound


def route(api, cursor):
    blacklist_filter = utils.BlacklistFilter()
    converter = JsonListItemConverter(LINE_LENGTH)
    kodi.set_view('files', set_sort=False)
    all_items = list()
    requests = 0
    while (CURSOR_LIMIT >= (len(all_items) + 1)) and cursor and (requests < MAX_REQUESTS):
        requests += 1
        communities = api.get_top_communities(cursor, limit=CURSOR_LIMIT)
        cursor = communities[Keys.CURSOR]
        if (communities[Keys.TOTAL] > 0) and (Keys.COMMUNITIES in communities):
            filtered = \
                blacklist_filter.by_type(communities, Keys.COMMUNITIES, id_key=Keys._ID, list_type='community')
            for community in filtered[Keys.COMMUNITIES]:
                add_item = community if community not in all_items else None
                if add_item:
                    all_items.append(add_item)
        else:
            break
    has_items = False
    if len(all_items) > 0:
        has_items = True
        for community in all_items:
            kodi.create_item(converter.community_to_listitem(community))
    if cursor:
        has_items = True
        kodi.create_item(utils.link_to_next_page({'mode': MODES.COMMUNITIES, 'cursor': cursor}))
    if has_items:
        kodi.end_of_directory()
        return
    raise NotFound('communities')
