# -*- coding: utf-8 -*-
"""
    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

from .common.search_history import SearchHistory


class StreamsSearchHistory(SearchHistory):
    def __init__(self, max_items=10):
        SearchHistory.__init__(self, 'streams_search', max_items=max_items)


class ChannelsSearchHistory(SearchHistory):
    def __init__(self, max_items=10):
        SearchHistory.__init__(self, 'channels_search', max_items=max_items)


class GamesSearchHistory(SearchHistory):
    def __init__(self, max_items=10):
        SearchHistory.__init__(self, 'games_search', max_items=max_items)


class IdUrlSearchHistory(SearchHistory):
    def __init__(self, max_items=10):
        SearchHistory.__init__(self, 'id_url_search', max_items=max_items)
