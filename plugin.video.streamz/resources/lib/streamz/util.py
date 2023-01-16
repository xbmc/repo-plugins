# -*- coding: utf-8 -*-
""" Streamz utility functions """

from __future__ import absolute_import, division, unicode_literals

import logging

import requests
from requests import HTTPError
from requests.adapters import BaseAdapter

from resources.lib import kodiutils
from resources.lib.streamz.exceptions import InvalidTokenException, LimitReachedException, UnavailableException

_LOGGER = logging.getLogger(__name__)


class StreamzAdapter(BaseAdapter):
    """ Fake adapter to handle the calls to streamz:// """

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        """ Sends PreparedRequest object. Returns Response object. """
        response = requests.Response()
        response.url = request.url
        response.status_code = 200
        return response

    def close(self):
        """ Cleans up adapter specific items. """


# Setup a static session that can be reused for all calls
SESSION = requests.Session()
SESSION.headers = {
    'User-Agent': 'STREAMZ/13.8 (be.dpgmedia.streamz; build:17133; Android TV 28) okhttp/4.10.0',
    'x-app-version': '13',
    'x-persgroep-mobile-app': 'true',
    'x-persgroep-os': 'android',
    'x-persgroep-os-version': '28',
}
PROXIES = kodiutils.get_proxies()


def http_get(url, params=None, token=None, profile=None, headers=None):
    """ Make a HTTP GET request for the specified URL.

    :param str url:                 The URL to call.
    :param dict params:             The query parameters to include to the URL.
    :param str token:               The token to use in Bearer authentication.
    :param str profile:             The profile to use in authentication.
    :param dict headers:            A dictionary with additional headers.

    :returns:                       The HTTP Response object.
    :rtype: requests.Response
    """
    try:
        return _request('GET', url=url, params=params, token=token, profile=profile, headers=headers)
    except HTTPError as exc:
        if exc.response.status_code == 401:
            raise InvalidTokenException(exc)
        if exc.response.status_code == 404:
            raise UnavailableException(exc)
        if exc.response.status_code == 429:
            raise LimitReachedException(exc)
        raise


def http_post(url, params=None, form=None, data=None, token=None, profile=None, headers=None):
    """ Make a HTTP POST request for the specified URL.

    :param str url:                 The URL to call.
    :param dict params:             The query parameters to include to the URL.
    :param dict form:               A dictionary with form parameters to POST.
    :param dict data:               A dictionary with json parameters to POST.
    :param str token:               The token to use in Bearer authentication.
    :param str profile:             The profile to use in authentication.
    :param dict headers:            A dictionary with additional headers.

    :returns:                       The HTTP Response object.
    :rtype: requests.Response
    """
    try:
        return _request('POST', url=url, params=params, form=form, data=data, token=token, profile=profile, headers=headers)
    except HTTPError as exc:
        if exc.response.status_code == 401:
            raise InvalidTokenException(exc)
        if exc.response.status_code == 404:
            raise UnavailableException(exc)
        if exc.response.status_code == 429:
            raise LimitReachedException(exc)
        raise


def http_put(url, params=None, form=None, data=None, token=None, profile=None, headers=None):
    """ Make a HTTP PUT request for the specified URL.

    :param str url:                 The URL to call.
    :param dict params:             The query parameters to include to the URL.
    :param dict form:               A dictionary with form parameters to POST.
    :param dict data:               A dictionary with json parameters to POST.
    :param str token:               The token to use in Bearer authentication.
    :param str profile:             The profile to use in authentication.
    :param dict headers:            A dictionary with additional headers.

    :returns:                       The HTTP Response object.
    :rtype: requests.Response
    """
    try:
        return _request('PUT', url=url, params=params, form=form, data=data, token=token, profile=profile, headers=headers)
    except HTTPError as exc:
        if exc.response.status_code == 401:
            raise InvalidTokenException(exc)
        if exc.response.status_code == 404:
            raise UnavailableException(exc)
        raise


def http_delete(url, params=None, token=None, profile=None, headers=None):
    """ Make a HTTP DELETE request for the specified URL.

    :param str url:                 The URL to call.
    :param dict params:             The query parameters to include to the URL.
    :param str token:               The token to use in Bearer authentication.
    :param str profile:             The profile to use in authentication.
    :param dict headers:            A dictionary with additional headers.

    :returns:                       The HTTP Response object.
    :rtype: requests.Response
    """
    try:
        return _request('DELETE', url=url, params=params, token=token, profile=profile, headers=headers)
    except HTTPError as exc:
        if exc.response.status_code == 401:
            raise InvalidTokenException(exc)
        if exc.response.status_code == 404:
            raise UnavailableException(exc)
        raise


def _request(method, url, params=None, form=None, data=None, token=None, profile=None, headers=None):
    """ Makes a request for the specified URL.

    :param str method:              The HTTP Method to use.
    :param str url:                 The URL to call.
    :param dict params:             The query parameters to include to the URL.
    :param dict form:               A dictionary with form parameters to POST.
    :param dict data:               A dictionary with json parameters to POST.
    :param str token:               The token to use in Bearer authentication.
    :param str profile:             The profile to use in authentication.
    :param dict headers:            A dictionary with additional headers.

    :returns:                       The HTTP Response object.
    :rtype: requests.Response
    """
    if form or data:
        # Make sure we don't log the password
        debug_data = {}
        debug_data.update(form or data)
        if 'password' in debug_data:
            debug_data['password'] = '**redacted**'
        _LOGGER.debug('Sending %s %s: %s', method, url, debug_data)
    else:
        _LOGGER.debug('Sending %s %s', method, url)

    if headers is None:
        headers = {}

    if token:
        headers['lfvp-auth'] = token

    if profile:
        headers['x-dpp-profile'] = profile

    response = SESSION.request(method, url, params=params, data=form, json=data, headers=headers, proxies=PROXIES)

    # Set encoding to UTF-8 if no charset is indicated in http headers (https://github.com/psf/requests/issues/1604)
    if not response.encoding:
        response.encoding = 'utf-8'

    _LOGGER.debug('Got response (status=%s): %s', response.status_code, response.text)

    # Raise a generic HTTPError exception when we got an non-okay status code.
    response.raise_for_status()

    return response
