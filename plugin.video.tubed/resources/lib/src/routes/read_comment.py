# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmc  # pylint: disable=import-error
import xbmcgui  # pylint: disable=import-error

from ..api.utils import formatted_comment


def invoke(context, thread_id='', comment_id=''):
    if not thread_id and not comment_id or thread_id and comment_id:
        return

    if comment_id:
        payload = context.api.comment(comment_id)
        snippet = payload.get('items', [{}])[0].get('snippet', {})
        replies = None

    else:
        payload = context.api.comment_thread(thread_id)
        item_snippet = payload.get('items', [{}])[0].get('snippet', {})
        snippet = item_snippet.get('topLevelComment', {}).get('snippet', {})
        try:
            replies = int(item_snippet.get('totalReplyCount', 0))
        except ValueError:
            replies = 0

    _, description = formatted_comment(context, snippet, replies)

    xbmc.executebuiltin('ActivateWindow(10147)')
    window = xbmcgui.Window(10147)

    xbmc.sleep(100)

    window.getControl(1).setLabel(context.i18n('Comment'))
    window.getControl(5).setText(description)
