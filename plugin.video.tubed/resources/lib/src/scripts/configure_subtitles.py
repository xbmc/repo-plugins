# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmcgui  # pylint: disable=import-error


def invoke(context):
    language = context.settings.language

    choices = [
        context.i18n('None'),
        context.i18n('Prompt'),
    ]

    if language.startswith('en'):
        choices.append(context.i18n('%s with %s fallback') % ('en', 'en-US/en-GB'))
    else:
        choices.append(context.i18n('%s with %s fallback') % (language, 'en'))

    choices.append(language)
    choices.append('%s (%s)' % (language, context.i18n('No auto-generated')))

    result = xbmcgui.Dialog().select(
        context.i18n('Subtitle language'),
        choices
    )

    if result == -1:
        return

    context.settings.subtitle_language = result
    context.settings.subtitle_label = choices[result]
