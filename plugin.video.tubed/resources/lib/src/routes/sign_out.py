# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmc  # pylint: disable=import-error
import xbmcgui  # pylint: disable=import-error


def invoke(context):
    if xbmcgui.Dialog().yesno(context.i18n('Sign Out'),
                              context.i18n('You are about to sign out, are you sure?')):

        context.api.revoke_token()
        context.api.tv_revoke_token()

        xbmc.executebuiltin('Container.Refresh')
