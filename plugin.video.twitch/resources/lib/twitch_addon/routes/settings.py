# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon.common import kodi
from ..addon.constants import Scripts


def route(refresh=True):
    kodi.show_settings()
    if refresh:
        kodi.execute_builtin('RunScript(%s)' % Scripts.REFRESH)
