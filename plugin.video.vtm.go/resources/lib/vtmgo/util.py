# -*- coding: utf-8 -*-
""" VTM GO utility functions """

from __future__ import absolute_import, division, unicode_literals

import logging

import requests
from requests import HTTPError

from resources.lib.vtmgo.exceptions import InvalidTokenException, InvalidLoginException

_LOGGER = logging.getLogger(__name__)

# Setup a static session that can be reused for all calls
SESSION = requests.Session()
SESSION.headers = {
    'x-app-version': '8',
    'x-persgroep-mobile-app': 'true',
    'x-persgroep-os': 'android',
    'x-persgroep-os-version': '23',
}


def http_get(url, params=None, token=None, profile=None, headers=None, proxies=None):
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
        return _request('GET', url=url, params=params, token=token, profile=profile, headers=headers, proxies=proxies)
    except HTTPError as ex:
        if ex.response.status_code == 401:
            raise InvalidTokenException
        if ex.response.status_code == 403:
            raise InvalidLoginException
        raise


def http_post(url, params=None, form=None, data=None, token=None, profile=None, headers=None, proxies=None):
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
        return _request('POST', url=url, params=params, form=form, data=data, token=token, profile=profile, headers=headers, proxies=proxies)
    except HTTPError as ex:
        if ex.response.status_code == 401:
            raise InvalidTokenException
        if ex.response.status_code == 403:
            raise InvalidLoginException
        raise


def http_put(url, params=None, form=None, data=None, token=None, profile=None, headers=None, proxies=None):
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
        return _request('PUT', url=url, params=params, form=form, data=data, token=token, profile=profile, headers=headers, proxies=proxies)
    except HTTPError as ex:
        if ex.response.status_code == 401:
            raise InvalidTokenException
        if ex.response.status_code == 403:
            raise InvalidLoginException
        raise


def http_delete(url, params=None, token=None, profile=None, headers=None, proxies=None):
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
        return _request('DELETE', url=url, params=params, token=token, profile=profile, headers=headers, proxies=proxies)
    except HTTPError as ex:
        if ex.response.status_code == 401:
            raise InvalidTokenException
        if ex.response.status_code == 403:
            raise InvalidLoginException
        raise


def _request(method, url, params=None, form=None, data=None, token=None, profile=None, headers=None, proxies=None):
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
    _LOGGER.debug('Sending %s %s... (%s)', method, url, form or data)

    if headers is None:
        headers = {}

    if token:
        headers['x-dpp-jwt'] = token

    if profile:
        headers['x-dpp-profile'] = profile

    response = SESSION.request(method, url, params=params, data=form, json=data, headers=headers, proxies=proxies)

    # Set encoding to UTF-8 if no charset is indicated in http headers (https://github.com/psf/requests/issues/1604)
    if not response.encoding:
        response.encoding = 'utf-8'

    _LOGGER.debug('Got response (status=%s): %s', response.status_code, response.text)

    # Raise a generic HTTPError exception when we got an non-okay status code.
    response.raise_for_status()

    return response
