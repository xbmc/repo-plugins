
# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

import logging
import requests
import json

from codequick.support import logger_id

from resources.lib import kodi_utils
from resources.lib.constants import USER_AGENT, WEB_TIMEOUT
from resources.lib.errors import *


logger = logging.getLogger('.'.join((logger_id, __name__)))


def web_request(method, url, headers=None, data=None, **kwargs):
    std_headers = {
        'User-Agent': USER_AGENT,
        'Referer': 'https://www.cintree.nl/',
        'Origin': 'https://www.cintree.nl',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }
    if headers:
        std_headers.update(headers)

    kwargs.setdefault('timeout', WEB_TIMEOUT)
    logger.debug("Making %s request to %s", method, url)
    try:
        resp = requests.request(method, url, json=data, headers=std_headers, **kwargs)
        resp.raise_for_status()
        return resp
    except requests.HTTPError as e:
        # noinspection PyUnboundLocalVariable
        logger.info("HTTP error %s for url %s: '%s'", e.response.status_code, url, resp.content)
        if e.response.status_code == 401:
            try:
                msg = resp.json().get('message')
            except json.JSONDecodeError:
                msg = ''
            if 'no transaction' in msg:
                raise NotPaidError(msg)
            elif 'no subscription' in msg:
                raise NoSubscriptionError(msg)
            else:
                raise AuthenticationError(msg if msg else None)
        if e.response.status_code == 403:
            raise GeoRestrictedError
        else:
            resp = e.response
            raise HttpError(resp.status_code, resp.reason)
    except requests.RequestException as e:
        logger.error('Error connecting to %s: %r', url, e)
        raise FetchError(str(e))


def post_json(url, data, headers=None, **kwargs):
    """Post JSON data and expect JSON data back."""
    dflt_headers = {'Accept': 'application/json'}
    if headers:
        dflt_headers.update(headers)
    resp = web_request('post', url, dflt_headers, data, **kwargs)
    try:
        return resp.json()
    except json.JSONDecodeError:
        raise FetchError(Script.localize(30920))


def get_json(url, headers=None, **kwargs):
    dflt_headers = {'Accept': 'application/json'}
    if headers:
        dflt_headers.update(headers)
    resp = web_request('get', url, dflt_headers, **kwargs)
    try:
        return resp.json()
    except json.JSONDecodeError:
        raise FetchError(Script.localize(30920))


def put_json(url, data, headers=None, **kwargs):
    """PUT JSON data and return the HTTP response, which can be inspected by the
    caller for status, etc."""
    resp = web_request('put', url, headers, data, **kwargs)
    return resp


def get_document(url, headers=None, **kwargs):
    """GET any document. Expects the document to be UTF-8 encoded and returns
    the contents as string.
    It may be necessary to provide and 'Accept' header.
    """
    resp = web_request('get', url, headers, **kwargs)
    resp.encoding = 'utf8'
    return resp.text


def fetch_authenticated(funct, url, **kwargs):
    """Call one of the fetch function, but with user authentication

    Call the specified function with authentication header and return the result.
    If the server responds with an authentication error, refresh tokens, or
    login and try once again.

    To prevent `headers` to turn up as both positional and keyword argument,
    accept keyword arguments only apart from the callable and url.

    """
    from resources.lib.ctree.ct_account import session
    account = session()

    for tries in range(2):
        try:
            if 'headers' in kwargs.keys():
                kwargs['headers'].update(
                    {'Authorization': 'Bearer ' + account.access_token})
            else:
                kwargs['headers'] = {'Authorization': 'Bearer ' + account.access_token}

            return funct(url, **kwargs)
        except AuthenticationError:
            # This is quite common, as tokens seem to expire rather quickly on Cinetree
            if tries == 0:
                if account.refresh() is False:
                    if not (kodi_utils.show_msg_not_logged_in() and account.login()):
                        raise
            else:
                # A NotAuthenticatedError even after refresh or login succeeded:
                # No access with this account; e.g. trying to play a subscription film on a free account.
                raise AccessRestrictedError from None
