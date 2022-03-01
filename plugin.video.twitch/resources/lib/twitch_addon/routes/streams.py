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


def route(api, after='MA=='):
    converter = JsonListItemConverter(LINE_LENGTH)
    utils.refresh_previews()
    kodi.set_view('videos', set_sort=True)
    per_page = utils.get_items_per_page()

    all_items = list()
    user_ids = list()

    language = utils.get_language()
    streams = api.get_all_streams(after=after, first=per_page, language=language)
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
            kodi.create_item(utils.link_to_next_page({'mode': MODES.STREAMLIST, 'after': cursor}))

        kodi.end_of_directory()
        return

    raise NotFound(i18n('streams'))
