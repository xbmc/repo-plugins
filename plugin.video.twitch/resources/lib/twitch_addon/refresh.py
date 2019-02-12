# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

from addon import cache
from addon.common import kodi

if __name__ == '__main__':
    do_cache_reset = kodi.get_setting('refresh_cache') == 'true'
    if do_cache_reset:
        result = cache.reset_cache()
    kodi.refresh_container()
