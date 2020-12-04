# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from copy import deepcopy

import arrow

from ..api.utils import formatted_comment
from ..constants import ADDON_ID
from ..constants import MODES
from ..constants import SCRIPT_MODES
from ..items.action import Action
from ..items.directory import Directory
from ..lib.url_utils import create_addon_path


def thread_generator(context, items):
    for item in items:
        kind = item.get('kind', '')

        if not kind or kind != 'youtube#commentThread':
            continue

        snippet = item.get('snippet', {})
        if not snippet:
            continue

        thread_id = item.get('id', '')
        if not thread_id:
            continue

        comment = snippet.get('topLevelComment', {})
        comment_snippet = comment.get('snippet', {})
        if not comment or not comment_snippet:
            continue

        try:
            replies = int(snippet.get('totalReplyCount', 0))
        except ValueError:
            replies = 0

        label, plot = formatted_comment(context, comment_snippet, replies)

        if replies > 0:
            payload = Directory(
                label=label,
                path=create_addon_path({
                    'mode': str(MODES.COMMENTS),
                    'thread_id': thread_id
                })
            )
        else:
            payload = Action(
                label=label,
                path=create_addon_path({
                    'mode': str(MODES.READ_COMMENT),
                    'thread_id': thread_id
                })
            )

        published_arrow = arrow.get(comment_snippet['publishedAt']).to('local')

        info_labels = {
            'originaltitle': label,
            'sorttitle': label,
            'plot': plot,
            'plotoutline': plot,
            'year': published_arrow.year,
            'premiered': published_arrow.format('YYYY-MM-DD'),
            'dateadded': published_arrow.format('YYYY-MM-DD HH:mm:ss'),
        }
        payload.ListItem.setInfo('video', info_labels)

        payload.ListItem.setArt({
            'icon': comment_snippet.get('authorProfileImageUrl', 'DefaultUser.png'),
            'thumb': comment_snippet.get('authorProfileImageUrl', 'DefaultUser.png')
        })

        query = deepcopy(context.query)
        query['order'] = 'prompt'
        context_menus = [
            (context.i18n('Read comment'),
             'RunScript(%s,mode=%s&thread_id=%s)' %
             (ADDON_ID, str(SCRIPT_MODES.READ_COMMENT), thread_id)),

            (context.i18n('Sort order'),
             'Container.Update(%s)' % create_addon_path(query)),
        ]

        payload.ListItem.addContextMenuItems(context_menus)
        yield tuple(payload)


def comment_generator(context, items):
    for item in items:
        kind = item.get('kind', '')

        if not kind or kind != 'youtube#comment':
            continue

        snippet = item.get('snippet', {})
        if not snippet:
            continue

        comment_id = item.get('id', '')
        if not comment_id:
            continue

        label, plot = formatted_comment(context, snippet)

        payload = Action(
            label=label,
            path=create_addon_path({
                'mode': str(MODES.READ_COMMENT),
                'comment_id': comment_id
            })
        )

        published_arrow = arrow.get(snippet['publishedAt']).to('local')

        info_labels = {
            'originaltitle': label,
            'sorttitle': label,
            'plot': plot,
            'plotoutline': plot,
            'year': published_arrow.year,
            'premiered': published_arrow.format('YYYY-MM-DD'),
            'dateadded': published_arrow.format('YYYY-MM-DD HH:mm:ss'),
        }
        payload.ListItem.setInfo('video', info_labels)

        payload.ListItem.setArt({
            'icon': snippet.get('authorProfileImageUrl', 'DefaultUser.png'),
            'thumb': snippet.get('authorProfileImageUrl', 'DefaultUser.png'),
        })

        yield tuple(payload)
