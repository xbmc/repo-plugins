# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmcplugin  # pylint: disable=import-error


def set_video_sort_methods(context):
    sort_methods = [
        xbmcplugin.SORT_METHOD_UNSORTED,
        xbmcplugin.SORT_METHOD_VIDEO_RUNTIME,
        xbmcplugin.SORT_METHOD_DATEADDED,
        xbmcplugin.SORT_METHOD_VIDEO_TITLE,
        xbmcplugin.SORT_METHOD_DATE,
        xbmcplugin.SORT_METHOD_VIDEO_YEAR,
        xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE,
    ]
    _set_methods(context, sort_methods)


def _set_methods(context, methods):
    for method in methods:
        xbmcplugin.addSortMethod(context.handle, method)
