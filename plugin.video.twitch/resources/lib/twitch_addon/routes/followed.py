# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi
from ..addon.constants import Keys, LINE_LENGTH, MODES
from ..addon.converter import JsonListItemConverter
from ..addon.twitch_exceptions import NotFound
from ..addon.utils import i18n

from twitch.api.parameters import StreamType


def route(api, content, after='MA=='):
    converter = JsonListItemConverter(LINE_LENGTH)
    user_id = api.get_user_id()
    _ = api.get_username()
    per_page = utils.get_items_per_page()
    if content == StreamType.LIVE or content == StreamType.PLAYLIST:
        if content == StreamType.LIVE:
            utils.refresh_previews()
        kodi.set_view('videos', set_sort=True)

        all_items = list()
        user_ids = list()

        streams = api.get_followed_streams(user_id=user_id, first=per_page, after=after)
        for stream in streams[Keys.DATA]:
            if stream.get(Keys.USER_ID):
                user_ids.append(stream[Keys.USER_ID])

        if user_ids:
            channels = api.get_users(user_ids)
            if Keys.DATA in channels:
                for idx, stream in enumerate(streams[Keys.DATA]):
                    streams[Keys.DATA][idx][Keys.OFFLINE_IMAGE_URL] = ''
                    for channel in channels[Keys.DATA]:
                        if channel.get(Keys.ID) == stream.get(Keys.USER_ID):
                            streams[Keys.DATA][idx][Keys.OFFLINE_IMAGE_URL] = channel[Keys.OFFLINE_IMAGE_URL]
                            break

        for stream in streams[Keys.DATA]:
            all_items.append(stream)

        if len(all_items) > 0:
            for stream in all_items:
                kodi.create_item(converter.stream_to_listitem(stream))

            cursor = streams.get('pagination', {}).get('cursor')
            if cursor:
                kodi.create_item(utils.link_to_next_page({'mode': MODES.FOLLOWED, 'content': content, 'after': cursor}))
            kodi.end_of_directory()
            return

        if content == StreamType.LIVE:
            raise NotFound(i18n('streams'))
        else:
            raise NotFound(i18n('playlists'))
    elif content == 'channels':
        kodi.set_view('files', set_sort=False)
        all_items = list()
        followed_ids = list()

        followed = api.get_followed_channels(user_id=user_id, after=after, first=per_page)
        if Keys.DATA in followed:
            for follow in followed[Keys.DATA]:
                if follow.get(Keys.BROADCASTER_ID):
                    followed_ids.append(follow[Keys.BROADCASTER_ID])

        channels = api.get_users(followed_ids)
        if Keys.DATA in channels:
            for channel in channels[Keys.DATA]:
                all_items.append(channel)

        if len(all_items) > 0:
            for channel in all_items:
                kodi.create_item(converter.channel_to_listitem(channel))

            cursor = followed.get('pagination', {}).get('cursor')
            if cursor:
                kodi.create_item(utils.link_to_next_page({'mode': MODES.FOLLOWED, 'content': content, 'after': cursor}))
            kodi.end_of_directory()
            return

        raise NotFound(i18n('channels'))
    elif content == 'games':
        kodi.set_view('files', set_sort=False)
        response = api.get_followed_games(per_page)
        if not isinstance(response, list):
            response = [{}]

        games = response[0].get('data', {}).get('currentUser', {})\
            .get('followedGames', {}).get('nodes', [])

        has_items = False
        if len(games) > 0:
            has_items = True
            for game in games:
                kodi.create_item(converter.followed_game_to_listitem(game))

        if has_items:
            kodi.end_of_directory()
            return
        raise NotFound(i18n('games'))
