# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
from ..addon import utils, cache
from ..addon.common import kodi
from ..addon.twitch_exceptions import TwitchException
from ..addon.utils import i18n


def route(api):
    token = utils.get_oauth_token()
    if not token:
        kodi.notify(msg=i18n('token_required'))
        return
    result = kodi.Dialog().yesno(i18n('revoke_token'), i18n('revoke_confirmation'))
    if result:
        response = api.client.revoke_token(token=token)

        if 'error' in response:
            if ('status' in response) and ('message' in response):
                raise TwitchException(response)
            raise TwitchException(response['error'])
        else:
            kodi.set_setting('oauth_token_helix', '')
            kodi.notify(msg=i18n('token_revoked'))
            cache.reset_cache()
