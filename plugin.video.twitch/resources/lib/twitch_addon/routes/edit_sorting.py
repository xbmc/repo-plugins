# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils
from ..addon.common import kodi
from ..addon.utils import i18n

from twitch.api.parameters import Boolean, Period, ClipPeriod, Direction, SortBy, VideoSort


def route(list_type, sort_type):
    if sort_type == 'by':
        choices = list()
        if list_type == 'followed_channels':
            choices = [(valid.replace('_', ' ').capitalize(), valid) for valid in SortBy.valid()]
        elif list_type == 'channel_videos':
            choices = [(valid.capitalize().replace('_', ' '), valid) for valid in VideoSort.valid()]
        elif list_type == 'clips':
            choices = [(i18n('popular'), Boolean.TRUE), (i18n('views'), Boolean.FALSE)]
        if choices:
            result = kodi.Dialog().select(i18n('change_sort_by'), [label for label, value in choices])
            if result > -1:
                sorting = utils.get_sort(list_type)
                utils.set_sort(list_type, sort_by=choices[result][1], period=sorting['period'], direction=sorting['direction'])

    elif sort_type == 'period':
        choices = list()
        if list_type == 'top_videos':
            choices = [(valid.replace('_', ' ').capitalize(), valid) for valid in Period.valid()]
        elif list_type == 'clips':
            choices = [(valid.replace('_', ' ').capitalize(), valid) for valid in ClipPeriod.valid()]
        if choices:
            result = kodi.Dialog().select(i18n('change_period'), [label for label, value in choices])
            if result > -1:
                sorting = utils.get_sort(list_type)
                utils.set_sort(list_type, sort_by=sorting['by'], period=choices[result][1], direction=sorting['direction'])

    elif sort_type == 'direction':
        choices = list()
        if list_type == 'followed_channels':
            choices = [(valid.replace('_', ' ').capitalize(), valid) for valid in Direction.valid()]
        if choices:
            result = kodi.Dialog().select(i18n('change_direction'), [label for label, value in choices])
            if result > -1:
                sorting = utils.get_sort(list_type)
                utils.set_sort(list_type, sort_by=sorting['by'], period=sorting['period'], direction=choices[result][1])


