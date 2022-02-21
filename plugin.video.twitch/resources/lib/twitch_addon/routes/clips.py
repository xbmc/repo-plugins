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


def route(api, after='MA==', channel_id='', game_id=''):
    converter = JsonListItemConverter(LINE_LENGTH)
    kodi.set_view('videos', set_sort=True)
    per_page = utils.get_items_per_page()
    all_items = list()

    clips = api.get_clips(broadcaster_id=channel_id, game_id=game_id, after=after, first=per_page)

    if Keys.DATA in clips:
        for clip in clips[Keys.DATA]:
            all_items.append(clip)

    if len(all_items) > 0:
        for clip in all_items:
            kodi.create_item(converter.clip_to_listitem(clip))

        cursor = clips.get('pagination', {}).get('cursor')
        if cursor:
            kodi.create_item(utils.link_to_next_page({'mode': MODES.CLIPSLIST, 'channel_id': channel_id,
                                                      'game_id': game_id, 'after': cursor}))

        kodi.end_of_directory()
        return

    raise NotFound(i18n('clips'))
