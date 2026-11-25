# -*- coding: utf-8 -*-
"""

    Copyright (C) 2024 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.

    Logout / revoke the PRIVATE (Turbo/ad-free) credentials used for ad-free playback.
    Clears the device-login store (oauth_private_tokens.json) AND the manual
    `private_oauth_token` setting, and best-effort revokes them server-side. Analogous
    to revoke_token (which handles the main login/Helix token).
"""

from ..addon import utils, device_oauth
from ..addon.common import kodi
from ..addon.utils import i18n


def route():
    store_token = (utils._read_private_store().get('access') or '').strip()
    manual_token = (kodi.get_setting('private_oauth_token') or '').strip()
    if not store_token and not manual_token:
        kodi.notify(msg=i18n('token_required'))
        return
    if not kodi.Dialog().yesno(i18n('revoke_token'), i18n('revoke_confirmation')):
        return

    client_id = utils.effective_private_client_id()
    for token in {store_token, manual_token}:
        if token:
            device_oauth.revoke_token(client_id, token)  # best-effort, server-side

    utils.clear_private_tokens()
    kodi.set_setting('private_oauth_token', '')
    kodi.notify(msg=i18n('token_revoked'))
