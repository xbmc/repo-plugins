# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import shutil

import xbmcgui  # pylint: disable=import-error
import xbmcvfs  # pylint: disable=import-error

from ..constants.media import LOGO_SMALL
from ..lib.memoizer import PATH as cache_path
from ..lib.memoizer import make_path
from ..lib.memoizer import reset_cache
from ..storage.data_cache import DataCache


def invoke(context, action, cache_type):
    if cache_type not in ['data', 'function']:
        return

    addon_name = context.addon.getAddonInfo('name')

    if cache_type == 'data':
        cache = DataCache(context)

        if action == 'clear':
            try:
                cache.clear()
                xbmcgui.Dialog().notification(
                    addon_name,
                    context.i18n('Data cache was cleared'),
                    LOGO_SMALL,
                    sound=False
                )
                return

            except:  # pylint: disable=bare-except
                xbmcgui.Dialog().notification(
                    addon_name,
                    context.i18n('Failed to clear data cache'),
                    LOGO_SMALL,
                    sound=False
                )
                return

        if action == 'delete':
            try:
                if xbmcvfs.exists(cache.filename):
                    success = xbmcvfs.delete(cache.filename)
                    if not success:
                        raise Exception

                xbmcgui.Dialog().notification(
                    addon_name,
                    context.i18n('Data cache was deleted'),
                    LOGO_SMALL,
                    sound=False
                )
                return

            except:  # pylint: disable=bare-except
                xbmcgui.Dialog().notification(
                    addon_name,
                    context.i18n('Failed to delete data cache'),
                    LOGO_SMALL,
                    sound=False
                )
                return

    if cache_type == 'function':
        if action == 'clear':
            try:
                reset_cache()
                xbmcgui.Dialog().notification(
                    addon_name,
                    context.i18n('Function cache was cleared'),
                    LOGO_SMALL,
                    sound=False
                )
                return

            except:  # pylint: disable=bare-except
                xbmcgui.Dialog().notification(
                    addon_name,
                    context.i18n('Failed to clear function cache'),
                    LOGO_SMALL,
                    sound=False
                )
                return

        if action == 'delete':
            try:
                if xbmcvfs.exists(cache_path):
                    shutil.rmtree(cache_path)
                    make_path()
                xbmcgui.Dialog().notification(
                    addon_name,
                    context.i18n('Function cache was deleted'),
                    LOGO_SMALL,
                    sound=False
                )
                return

            except:  # pylint: disable=bare-except
                xbmcgui.Dialog().notification(
                    addon_name,
                    context.i18n('Failed to delete function cache'),
                    LOGO_SMALL,
                    sound=False
                )
                make_path()
                return
