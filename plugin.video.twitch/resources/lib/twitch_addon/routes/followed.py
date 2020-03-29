# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi
from ..addon.constants import Keys, LINE_LENGTH, MODES, MAX_REQUESTS, REQUEST_LIMIT, CURSOR_LIMIT
from ..addon.converter import JsonListItemConverter
from ..addon.twitch_exceptions import NotFound
from ..addon.utils import i18n

from twitch.api.parameters import StreamType


def route(api, content, offset=0, cursor='MA=='):
    blacklist_filter = utils.BlacklistFilter()
    converter = JsonListItemConverter(LINE_LENGTH)
    user_id = api.get_user_id()
    username = api.get_username()
    per_page = utils.get_items_per_page()
    if content == StreamType.LIVE or content == StreamType.PLAYLIST:
        if content == StreamType.LIVE:
            utils.refresh_previews()
        kodi.set_view('videos', set_sort=True)

        all_items = list()
        requests = 0
        total = 1000

        last_page = False
        while ((per_page >= (len(all_items) + 1)) and
               (requests < MAX_REQUESTS) and (int(offset) <= 900)):
            requests += 1
            streams = api.get_followed_streams(stream_type=content, offset=offset, limit=REQUEST_LIMIT)

            if len(streams.get(Keys.STREAMS, [])) < per_page:
                last_page = True

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

            if last_page:
                break

        has_items = False
        if len(all_items) > 0:
            has_items = True
            for stream in all_items:
                kodi.create_item(converter.stream_to_listitem(stream))

        if (total - 100) > (int(offset) + 1) and (len(all_items) == per_page):
            has_items = True
            kodi.create_item(utils.link_to_next_page({'mode': MODES.FOLLOWED, 'content': content, 'offset': offset}))
        if has_items:
            kodi.end_of_directory()
            return
        if content == StreamType.LIVE:
            raise NotFound(i18n('streams'))
        else:
            raise NotFound(i18n('playlists'))
    elif content == 'channels':
        kodi.set_view('files', set_sort=False)
        sorting = utils.get_sort('followed_channels')
        channels = None
        all_items = list()
        requests = 0
        while (per_page >= (len(all_items) + 1)) and (requests < MAX_REQUESTS):
            requests += 1
            channels = api.get_followed_channels(user_id=user_id, offset=offset, limit=REQUEST_LIMIT, direction=sorting['direction'], sort_by=sorting['by'])
            if (channels[Keys.TOTAL] > 0) and (Keys.FOLLOWS in channels):
                filtered = \
                    blacklist_filter.by_type(channels, Keys.FOLLOWS, parent_keys=[Keys.CHANNEL], id_key=Keys._ID, list_type='user')
                last = None
                for follow in filtered[Keys.FOLLOWS]:
                    channel = follow[Keys.CHANNEL]
                    last = channel
                    if per_page >= (len(all_items) + 1):
                        add_item = last if last not in all_items else None
                        if add_item:
                            all_items.append(add_item)
                    else:
                        break
                offset = utils.get_offset(offset, last, channels[Keys.FOLLOWS], key=Keys.CHANNEL)
                if (offset is None) or (channels[Keys.TOTAL] <= offset) or (channels[Keys.TOTAL] <= REQUEST_LIMIT):
                    break
            else:
                break
        has_items = False
        if len(all_items) > 0:
            has_items = True
            for channel in all_items:
                kodi.create_item(converter.channel_to_listitem(channel))
        if channels[Keys.TOTAL] > (offset + 1):
            has_items = True
            kodi.create_item(utils.link_to_next_page({'mode': MODES.FOLLOWED, 'content': content, 'offset': offset}))
        if has_items:
            kodi.end_of_directory()
            return
        raise NotFound(i18n('channels'))
    elif content == 'games':
        kodi.set_view('files', set_sort=False)
        games = None
        all_items = list()
        requests = 0
        while (per_page >= (len(all_items) + 1)) and (requests < MAX_REQUESTS):
            requests += 1
            games = api.get_followed_games(username, offset, REQUEST_LIMIT)
            if (games[Keys.TOTAL] > 0) and (Keys.FOLLOWS in games):
                filtered = \
                    blacklist_filter.by_type(games, Keys.FOLLOWS, game_key=Keys._ID, list_type='game')
                last = None
                for game in filtered[Keys.FOLLOWS]:
                    last = game
                    if per_page >= (len(all_items) + 1):
                        add_item = last if last not in all_items else None
                        if add_item:
                            all_items.append(add_item)
                    else:
                        break
                offset = utils.get_offset(offset, last, games[Keys.FOLLOWS])
                if (offset is None) or (games[Keys.TOTAL] <= offset) or (games[Keys.TOTAL] <= REQUEST_LIMIT):
                    break
            else:
                break
        has_items = False
        if len(all_items) > 0:
            has_items = True
            for game in all_items:
                kodi.create_item(converter.game_to_listitem(game))
        if games[Keys.TOTAL] > (offset + 1):
            has_items = True
            kodi.create_item(utils.link_to_next_page({'mode': MODES.FOLLOWED, 'content': content, 'offset': offset}))
        if has_items:
            kodi.end_of_directory()
            return
        raise NotFound(i18n('games'))
    elif content == 'clips':
        kodi.set_view('videos', set_sort=True)
        sort_by = utils.get_sort('clips', 'by')
        all_items = list()
        requests = 0
        languages = ','.join(utils.get_languages())
        while (CURSOR_LIMIT >= (len(all_items) + 1)) and cursor and (requests < MAX_REQUESTS):
            requests += 1
            clips = api.get_followed_clips(cursor=cursor, limit=CURSOR_LIMIT, trending=sort_by, language=languages)
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
            kodi.create_item(utils.link_to_next_page({'mode': MODES.FOLLOWED, 'content': content, 'cursor': cursor}))
        if has_items:
            kodi.end_of_directory()
            return
        raise NotFound(i18n('clips'))
