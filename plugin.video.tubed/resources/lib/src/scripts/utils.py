# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from html import unescape

import xbmcgui  # pylint: disable=import-error

from ..constants.media import LOGO_SMALL
from ..generators.data_cache import get_cached
from ..generators.utils import get_thumbnail
from ..lib.logger import Log
from ..lib.txt_fmt import bold

LOG = Log('scripts', __file__)


def rate(context, video_id):
    payload = context.api.rating(video_id)
    try:
        payload = payload.get('items', [{}])[0]
    except IndexError:
        return

    rating = payload.get('rating', 'none')

    cached_payload = get_cached(context, context.api.videos, [video_id])
    cached_video = cached_payload.get(video_id, {})
    cached_snippet = cached_video.get('snippet', {})

    thumbnail = get_thumbnail(cached_snippet)
    video_title = unescape(cached_snippet.get('title', ''))

    choice_strings = [
        context.i18n('I like this'),
        context.i18n('I dislike this'),
        context.i18n('Remove rating')
    ]

    choices = []
    for string in choice_strings:
        if video_title:
            label2 = context.i18n('Rate %s') % video_title
        else:
            label2 = context.i18n('Rate the selected video')

        item = xbmcgui.ListItem(
            label=string,
            label2=label2
        )

        item.setArt({
            'icon': thumbnail,
            'thumb': thumbnail,
        })

        choices.append(item)

    choice_map = [
        'like',
        'dislike',
        'none'
    ]

    del choices[choice_map.index(rating)]
    del choice_map[choice_map.index(rating)]

    result = xbmcgui.Dialog().select(context.i18n('Rate'), choices, useDetails=True)
    if result == -1:
        return

    rating = choice_map[result]

    payload = context.api.rate(video_id, rating)

    try:
        successful = int(payload.get('error', {}).get('code', 204)) == 204
    except ValueError:
        successful = False

    if successful:
        message = ''

        if video_title:
            video_title = bold(video_title)
            if rating == 'none':
                message = context.i18n('Rating removed from %s') % video_title

            elif rating == 'like':
                message = context.i18n('Liked %s') % video_title

            elif rating == 'dislike':
                message = context.i18n('Disliked %s') % video_title

        else:
            if rating == 'none':
                message = context.i18n('Rating removed')

            elif rating == 'like':
                message = context.i18n('Liked')

            elif rating == 'dislike':
                message = context.i18n('Disliked')

        xbmcgui.Dialog().notification(
            context.addon.getAddonInfo('name'),
            message,
            LOGO_SMALL,
            sound=False
        )
