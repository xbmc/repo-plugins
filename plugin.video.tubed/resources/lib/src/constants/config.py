# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import xbmcvfs  # pylint: disable=import-error

ADDON_ID = 'plugin.video.tubed'

ADDONDATA_PATH = xbmcvfs.translatePath('special://profile/addon_data/%s/' % ADDON_ID)
MEDIA_PATH = xbmcvfs.translatePath('special://home/addons/%s/resources/media/' % ADDON_ID)

PRIVACY_POLICY_MARKDOWN = xbmcvfs.translatePath('special://home/addons/%s/PRIVACY.md' % ADDON_ID)
PRIVACY_POLICY_REVISION = '10222020'
