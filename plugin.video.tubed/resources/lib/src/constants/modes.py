# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from enum import Enum


class MODES(Enum):
    MAIN = 'main'
    MOST_POPULAR = 'most_popular'
    PLAY = 'play'
    SEARCH = 'search'
    MY_CHANNEL = 'my_channel'
    LIKED_VIDEOS = 'liked_videos'
    DISLIKED_VIDEOS = 'disliked_videos'
    PLAYLISTS = 'playlists'
    CHANNEL = 'channel'
    SUBSCRIPTIONS = 'subscriptions'
    LIVE = 'live'
    SIGN_IN = 'sign_in'
    SIGN_OUT = 'sign_out'
    MANAGE_USERS = 'manage_users'
    SEARCH_QUERY = 'search_query'
    PLAYLIST = 'playlist'
    CATEGORIES = 'categories'
    CATEGORY = 'category'
    UPCOMING_NOTIFICATION = 'upcoming_notification'
    RELATED_VIDEOS = 'related_videos'
    COMMENTS_THREADS = 'comment_threads'
    COMMENTS = 'comments'
    READ_COMMENT = 'read_comment'
    FAVORITE_CHANNELS = 'favorite_channels'
    MOST_POPULAR_REGIONALLY = 'most_popular_regionally'
    LINKS_IN_DESCRIPTION = 'links_in_description'
    CHAPTERS = 'chapters'
    FAVORITE_PLAYLISTS = 'favorite_playlists'
    SETTINGS = 'settings'

    def __str__(self):
        return str(self.value).lower()
