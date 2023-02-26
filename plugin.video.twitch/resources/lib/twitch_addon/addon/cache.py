# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from .common import cache, kodi

cache_function = cache.cache_function
cache_method = cache.cache_method
reset_cache = cache.reset_cache
limit = float(kodi.get_setting('cache_expire_time')) / 60
cache.cache_enabled = limit > 0
