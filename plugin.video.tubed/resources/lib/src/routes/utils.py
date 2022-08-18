# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmcgui  # pylint: disable=import-error

from ..constants import MODES
from ..lib.memoizer import reset_cache


def get_sort_order(context):
    reset_cache()

    choice_ids = []
    choice_labels = []

    if context.mode == str(MODES.SEARCH_QUERY):
        choice_ids = ['relevance', 'date', 'rating', 'title', 'viewCount']
        choice_labels = [context.i18n('Relevance'), context.i18n('Date'), context.i18n('Rating'),
                         context.i18n('Title'), context.i18n('View Count')]

        if context.query.get('search_type') in ['channel', 'playlist']:
            choice_ids += ['videoCount']
            choice_labels += [context.i18n('Video Count')]

    elif context.mode == str(MODES.COMMENTS_THREADS):
        choice_ids = ['relevance', 'time']
        choice_labels = [context.i18n('Relevance'), context.i18n('Time')]

    elif context.mode == str(MODES.SUBSCRIPTIONS):
        choice_ids = ['relevance', 'alphabetical', 'unread']
        choice_labels = [context.i18n('Relevance'), context.i18n('Alphabetical'),
                         context.i18n('Activity')]

    elif context.mode == str(MODES.LIVE):
        choice_ids = ['relevance', 'date', 'rating', 'title']
        choice_labels = [context.i18n('Relevance'), context.i18n('Date'),
                         context.i18n('Rating'), context.i18n('Title')]

        if context.query.get('event_type') not in ['upcoming']:
            choice_ids += ['viewCount']
            choice_labels += [context.i18n('View Count')]

    result = xbmcgui.Dialog().select(context.i18n('Choose a sort order'), choice_labels)
    if result == -1:
        return None

    return choice_ids[result]
