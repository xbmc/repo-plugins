# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from html import unescape

import xbmcgui  # pylint: disable=import-error

from ..generators.data_cache import get_cached
from ..generators.utils import get_chapters
from ..generators.utils import get_thumbnail
from . import play


def invoke(context, video_id):
    cached_payload = get_cached(context, context.api.videos, [video_id])
    cached_video = cached_payload.get(video_id, {})
    cached_snippet = cached_video.get('snippet', {})

    thumbnail = get_thumbnail(cached_snippet)
    description = unescape(cached_snippet.get('description', ''))

    chapters = get_chapters(description)
    if not chapters:
        return

    choices = []
    for chapter in chapters:
        item = xbmcgui.ListItem(
            label=chapter[2],
            label2=context.i18n('Chapter starts at %s') % chapter[1]
        )

        item.setArt({
            'icon': thumbnail,
            'thumb': thumbnail,
        })

        choices.append(item)

    result = xbmcgui.Dialog().select(context.i18n('Chapters'), choices, useDetails=True)
    if result == -1:
        return

    chapter = chapters[result]

    play.invoke(context, video_id=video_id, start_offset=chapter[0])
