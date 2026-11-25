# -*- coding: utf-8 -*-
"""

    Copyright (C) 2024 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.

    Device-code login for the PRIVATE (Turbo/ad-free) credentials: same flow as
    device_login, but with the private client id and the private token store used by
    usher/GQL for ad-free Turbo/subscriber playback. Additive to the manual
    `private_oauth_token` setting, which keeps working as a fallback.
"""

from ..addon import utils
from ..addon.utils import i18n

from . import device_login


def route():
    # No scopes: the playback entitlement (Turbo/subscription) is account-bound.
    device_login.do_device_login(heading=i18n('device_login_private'),
                                 body_i18n='device_login_private_instructions',
                                 client_id=utils.effective_private_client_id(),
                                 scopes='',
                                 store_tokens=utils.store_private_tokens,
                                 success_i18n='device_login_private_success',
                                 log_tag='(private)')
