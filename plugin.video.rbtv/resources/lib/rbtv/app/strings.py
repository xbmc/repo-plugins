"""IDs of the localized strings in resources/language/*/strings.po.

The app layer only knows these numbers; the Kodi adapter turns them into text
via xbmcaddon.Addon().getLocalizedString.
"""

from __future__ import annotations

from typing import Callable

Translate = Callable[[int], str]

SEARCH = 30100
REFRESH_LIST = 30101
MANAGE_FAVORITES = 30102
ALL_SHOWS = 30103
FAVORITE_ADD = 30104
FAVORITE_REMOVE = 30105
NEXT_PAGE = 30106
EPISODE_COUNT_ONE = 30107
EPISODE_COUNT_MANY = 30108
SEARCH_PROMPT = 30109
CHOOSE_FAVORITES = 30110
LOADING_SHOWS = 30111
RELOADING_SHOWS = 30112

ALL = (
    SEARCH,
    REFRESH_LIST,
    MANAGE_FAVORITES,
    ALL_SHOWS,
    FAVORITE_ADD,
    FAVORITE_REMOVE,
    NEXT_PAGE,
    EPISODE_COUNT_ONE,
    EPISODE_COUNT_MANY,
    SEARCH_PROMPT,
    CHOOSE_FAVORITES,
    LOADING_SHOWS,
    RELOADING_SHOWS,
)
