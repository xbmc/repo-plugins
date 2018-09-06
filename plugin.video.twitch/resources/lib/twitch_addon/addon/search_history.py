# -*- coding: utf-8 -*-
"""
    Copyright (C) 2018 Twitch-on-Kodi

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
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
