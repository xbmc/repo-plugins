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


def route(oauth_token):
    # Manually entered token has no refresh token; route it through the race-free store.
    utils.store_oauth_tokens(oauth_token, '', 0)
    kodi.notify(msg=i18n('token_updated'))
