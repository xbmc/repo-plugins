# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmcgui  # pylint: disable=import-error

from ..lib.memoizer import reset_cache


def invoke(context):
    chosen_language = None
    chosen_region = None

    payload = context.api.languages()
    items = payload.get('items', [])

    invalid = ['es-419']
    languages = [(item['snippet']['name'], item['snippet']['hl'])
                 for item in items if item['id'] not in invalid]

    if languages:
        languages = sorted(languages, key=lambda language: language[0])
        selection = [language[0] for language in languages]

        heading = '%s: %s' % (context.i18n('Configure regional preferences'),
                              context.i18n('Language'))
        result = xbmcgui.Dialog().select(heading, selection)
        if result > -1:
            chosen_language = languages[result][1]
            context.api.language = chosen_language

    payload = context.api.regions()
    items = payload.get('items', [])

    regions = [(item['snippet']['name'], item['snippet']['gl']) for item in items]

    if regions:
        regions = sorted(regions, key=lambda region: region[0])
        selection = [region[0] for region in regions]

        heading = '%s: %s' % (context.i18n('Configure regional preferences'),
                              context.i18n('Region'))
        result = xbmcgui.Dialog().select(heading, selection)
        if result > -1:
            chosen_region = regions[result][1]
            context.api.region = chosen_region

    if chosen_language:
        context.settings.language = chosen_language

    if chosen_region:
        context.settings.region = chosen_region

    if chosen_language or chosen_region:
        reset_cache()
