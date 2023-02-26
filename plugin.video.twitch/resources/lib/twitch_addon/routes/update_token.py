# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon.common import kodi
from ..addon.utils import i18n


def route(oauth_token):
    kodi.set_setting('oauth_token_helix', oauth_token)
    kodi.notify(msg=i18n('token_updated'))
