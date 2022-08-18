# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import re
from html import unescape

import xbmcgui  # pylint: disable=import-error

from ..constants import SUBTITLE_LANGUAGE
from ..lib.txt_fmt import bold
from ..lib.txt_fmt import color
from ..lib.txt_fmt import italic


def choose_subtitles(context, subtitles, prompt_override=False):
    if not subtitles:
        return []

    subtitles = sorted(subtitles, key=lambda sub: sub[1])

    youtube_language = context.settings.language

    if prompt_override:
        subtitle_language = SUBTITLE_LANGUAGE.PROMPT
    else:
        subtitle_language = context.settings.subtitle_language

    payload = []

    if subtitle_language == SUBTITLE_LANGUAGE.NONE:
        return []

    if subtitle_language == SUBTITLE_LANGUAGE.PROMPT:
        selection = [subtitle[1] for subtitle in subtitles]

        result = xbmcgui.Dialog().select(context.i18n('Subtitle language'), selection)
        if result == -1:
            return []

        payload.append(subtitles[result][3])

    elif subtitle_language == SUBTITLE_LANGUAGE.CURRENT_W_FALLBACK:

        payload.append(find_subtitle(subtitles, youtube_language))
        if '-' in youtube_language:
            payload.append(find_subtitle(subtitles, youtube_language.split('-')[0]))
        payload.append(find_subtitle(subtitles, 'en'))
        payload.append(find_subtitle(subtitles, 'en-US'))
        payload.append(find_subtitle(subtitles, 'en-GB'))

    elif subtitle_language == SUBTITLE_LANGUAGE.CURRENT:
        payload.append(find_subtitle(subtitles, youtube_language))
        if '-' in youtube_language:
            payload.append(find_subtitle(subtitles, youtube_language.split('-')[0]))

    elif subtitle_language == SUBTITLE_LANGUAGE.CURRENT_WO_ASR:
        payload.append(find_subtitle(subtitles, youtube_language, include_asr=False))
        if '-' in youtube_language:
            payload.append(
                find_subtitle(subtitles, youtube_language.split('-')[0], include_asr=False)
            )

    return list(set(subtitle for subtitle in payload if subtitle))


def find_subtitle(subtitles, language, include_asr=True):
    for language_code, _, kind, subtitle_url in subtitles:
        if not include_asr and kind == 'asr':
            continue

        if language_code == language:
            return subtitle_url

    return None


def formatted_comment(context, snippet, replies=None):
    author = snippet.get('authorDisplayName', '')
    if author:
        author = bold(author)

    description_body = unescape(snippet.get('textDisplay', ''))

    label_body = re.sub(r'\s\s+', ' ', description_body)
    label_body = re.sub(r'\n', ' ', label_body)

    try:
        likes = int(snippet.get('likeCount', 0))
    except ValueError:
        likes = 0

    if likes > 1000:
        likes = '%.1fK' % (likes / 1000.0)
    else:
        likes = str(likes)

    if isinstance(replies, int):
        if replies > 1000:
            replies = '%.1fK' % (replies / 1000.0)
        else:
            replies = str(replies)
    else:
        replies = None

    edited = snippet['publishedAt'] != snippet['updatedAt']
    label_edited = italic('*') if edited else ''
    description_edited = \
        '[CR]%s' % italic(context.i18n('Comment has been edited')) if edited else ''

    if replies is not None:
        label_properties = color('[', 'grey') + color('+%s' % likes, 'lightgreen') + \
                           color('|', 'grey') + color(replies, 'cyan') + color(']', 'grey')
        description_properties = \
            color('%s %s' % (likes, bold(context.i18n('Likes'))), 'lightgreen') + \
            '  ' + color('%s %s' % (replies, bold(context.i18n('Replies'))), 'cyan')

    else:
        label_properties = \
            color('[', 'grey') + color('+%s' % likes, 'lightgreen') + color(']', 'grey')
        description_properties = color('%s %s' % (likes, bold(context.i18n('Likes'))), 'lightgreen')

    label = '%s %s%s  %s' % (author, label_properties, label_edited, label_body)
    description = '%s [CR]%s%s[CR][CR]%s' % \
                  (author, description_properties, description_edited, label_body)

    return label, description
