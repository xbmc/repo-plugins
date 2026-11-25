# -*- coding: utf-8 -*-
"""

    Twitch OAuth 2.0 Device Code Grant Flow + silent refresh.

    Replaces the manual implicit-grant link flow (which never returned a
    refresh token, forcing periodic manual re-login). Pure logic only; the
    interactive login UI lives in routes/device_login.py.

    SPDX-License-Identifier: GPL-3.0-only
"""

import requests

from .common import log_utils

OAUTH_BASE = 'https://id.twitch.tv/oauth2'
DEVICE_GRANT = 'urn:ietf:params:oauth:grant-type:device_code'
TIMEOUT = 15


def request_device_code(client_id, scopes):
    """Start the device flow. scopes = space-separated string.
    Returns (ok, data): on ok, data has device_code/user_code/verification_uri/interval/expires_in."""
    try:
        r = requests.post(OAUTH_BASE + '/device',
                          data={'client_id': client_id, 'scopes': scopes}, timeout=TIMEOUT)
        data = r.json() if r.content else {}
        return (r.status_code == 200 and bool(data.get('device_code'))), data
    except Exception as e:
        log_utils.log('device_oauth.request_device_code error: %s' % e, log_utils.LOGERROR)
        return False, {'message': str(e)}


def poll_device_token(client_id, scopes, device_code):
    """Poll the token endpoint. Returns (status, data) where status is one of
    'ok' | 'pending' | 'slow_down' | 'expired' | 'denied' | 'error'."""
    try:
        r = requests.post(OAUTH_BASE + '/token',
                          data={'client_id': client_id, 'scopes': scopes,
                                'device_code': device_code, 'grant_type': DEVICE_GRANT},
                          timeout=TIMEOUT)
        data = r.json() if r.content else {}
        if r.status_code == 200 and data.get('access_token'):
            return 'ok', data
        msg = str(data.get('message', '')).lower()
        if 'pending' in msg:
            return 'pending', data
        if 'slow' in msg:
            return 'slow_down', data
        if 'expired' in msg:
            return 'expired', data
        if 'denied' in msg or r.status_code == 403:
            return 'denied', data
        return 'error', data
    except Exception as e:
        log_utils.log('device_oauth.poll_device_token error: %s' % e, log_utils.LOGERROR)
        return 'error', {'message': str(e)}


def refresh_access_token(client_id, refresh_token):
    """Refresh silently via grant_type=refresh_token (public client -> NO client_secret).
    Returns (ok, data): on ok, data has a new access_token + (rotated) refresh_token + expires_in."""
    try:
        r = requests.post(OAUTH_BASE + '/token',
                          data={'client_id': client_id, 'grant_type': 'refresh_token',
                                'refresh_token': refresh_token}, timeout=TIMEOUT)
        data = r.json() if r.content else {}
        return (r.status_code == 200 and bool(data.get('access_token'))), data
    except Exception as e:
        log_utils.log('device_oauth.refresh_access_token error: %s' % e, log_utils.LOGERROR)
        return False, {'message': str(e)}


def revoke_token(client_id, token):
    """Best-effort server-side revoke of an access token (public client). Returns True on 200."""
    if not token:
        return False
    try:
        r = requests.post(OAUTH_BASE + '/revoke',
                          data={'client_id': client_id, 'token': token}, timeout=TIMEOUT)
        return r.status_code == 200
    except Exception as e:
        log_utils.log('device_oauth.revoke_token error: %s' % e, log_utils.LOGWARNING)
        return False
