# -*- coding: utf-8 -*-
"""

    Copyright (C) 2024 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

import xbmc
import xbmcgui

from ..addon import utils, device_oauth
from ..addon.common import kodi, log_utils
from ..addon.constants import SCOPES
from ..addon.utils import i18n


def do_device_login(heading, body_i18n, client_id, scopes, store_tokens, success_i18n, log_tag):
    """Shared device-code login flow: show code, poll, store tokens via store_tokens()."""
    ok, data = device_oauth.request_device_code(client_id, scopes)
    if not ok or not data.get('user_code'):
        kodi.Dialog().ok(heading, i18n('device_login_unsupported'))
        return

    user_code = data['user_code']
    device_code = data['device_code']
    interval = int(data.get('interval', 5)) or 5
    expires_in = int(data.get('expires_in', 1800)) or 1800

    # Short, clean activation URL (Twitch's verification_uri carries the code as a long query string).
    activate_url = 'https://www.twitch.tv/activate'
    body = i18n(body_i18n) % (activate_url, user_code)

    monitor = xbmc.Monitor()
    progress = xbmcgui.DialogProgress()
    progress.create(heading, body)

    token = None
    waited = 0
    while waited < expires_in:
        # wait the poll interval, abortable (user cancel or Kodi shutdown)
        for _ in range(interval):
            if progress.iscanceled():
                progress.close()
                kodi.notify(i18n('login'), i18n('device_login_cancelled'), sound=False)
                return
            if monitor.waitForAbort(1):  # Kodi is shutting down
                progress.close()
                return
            waited += 1
        status, tdata = device_oauth.poll_device_token(client_id, scopes, device_code)
        if status == 'ok':
            token = tdata
            break
        elif status == 'slow_down':
            interval += 2
        elif status in ('expired', 'denied'):
            break
        # 'pending' / transient 'error' -> keep polling
        try:
            progress.update(int(min(99, (waited * 100) // expires_in)),
                            body + '[CR]' + i18n('device_login_waiting'))
        except Exception:
            pass

    progress.close()
    if token and token.get('access_token'):
        store_tokens(token['access_token'],
                     token.get('refresh_token', ''),
                     token.get('expires_in', 14400))
        log_utils.log('OAuth%s: device login succeeded, refresh token stored' % log_tag,
                      log_utils.LOGNOTICE)
        kodi.Dialog().ok(heading, i18n(success_i18n))
    else:
        kodi.notify(i18n('login'), i18n('device_login_failed'), sound=False)


def route():
    do_device_login(heading=i18n('device_login'),
                    body_i18n='device_login_instructions',
                    client_id=utils.get_client_id(),
                    scopes=' '.join(SCOPES),
                    store_tokens=utils.store_oauth_tokens,
                    success_i18n='device_login_success',
                    log_tag='')
