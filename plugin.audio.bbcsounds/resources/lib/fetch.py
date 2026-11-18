# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

from __future__ import annotations
import os
import json
from http.cookiejar import LWPCookieJar

import requests
import xbmcaddon
import xbmcvfs

from resources.lib.exceptions import AccountError, GeoBlockError
from resources.lib.log import log

REQ_TIMEOUT = (3.5, 4)

ID_MSG_SIGN_IN = 30321
ID_MSG_GEOBLOCK = 30320


def cookie_jar() -> LWPCookieJar:
    cj = getattr(cookie_jar, '_cj_', None)
    if cj is None:
        profile_dir = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
        os.makedirs(profile_dir, exist_ok=True)
        _cookie_file = os.path.join(profile_dir, 'cookies.txt')
        cookie_jar._cj_ = cj = LWPCookieJar(_cookie_file)
        if os.path.exists(_cookie_file):
            try:
                cj.load(ignore_discard=True)
                log("Loaded cookies from file")
            except Exception as err:
                log('Failed to load cookies from file: "%r"', err)
    return cj


def request(method: str, url: str, **kwargs) -> requests.Response:
    save = False
    kwargs.setdefault('timeout', REQ_TIMEOUT)
    try:
        with requests.Session() as session:
            session.cookies = cj = cookie_jar()
            resp = session.request(method, url, **kwargs)
            if resp.status_code == 401:
                # Contrary to www pages, requests to RMS do not automatically refresh auth cookies.
                if refresh_tokens(session):
                    save = True
                    resp = session.request(method, url, **kwargs)
        resp.raise_for_status()
    except requests.HTTPError:
        try:
            json_content = json.dumps(json.loads(resp.content), indent=4)
        except json.JSONDecodeError:
            json_content = '<non-JSON response content>'
        log('HTTPError %s for url %s:\n"%s"', resp.status_code, resp.url, json_content)

        if resp.status_code == 401:
            raise AccountError(resp)
        if resp.status_code == 403:
            raise GeoBlockError(resp)
        raise

    if resp.history or save:
        log('Save cookies')
        cj.save(ignore_discard=True)
    resp.encoding = 'UTF-8'
    return resp


def refresh_tokens(session: requests.Session) -> bool:
    return_url = 'https://www.bbc.co.uk/sounds'
    resp = session.get(
        url='https://session.bbc.co.uk/session',
        params={'ptrt': return_url,
                'context': 'iplayerradio',
                'userOrigins': 'sounds'},
        allow_redirects=False,
        timeout=REQ_TIMEOUT
    )
    return resp.headers.get('location') == return_url


def get(url: str, **kwargs) -> requests.Response:
    return request('get', url, **kwargs)


def post(url: str, **kwargs) -> requests.Response:
    return request('post', url, **kwargs)


def delete(url: str, **kwargs) -> requests.Response:
    return request('delete', url, **kwargs)


def put(url: str, **kwargs) -> requests.Response:
    return request('put', url, **kwargs)
