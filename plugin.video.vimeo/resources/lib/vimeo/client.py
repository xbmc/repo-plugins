#! /usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import

from functools import wraps
import json
import requests
from .auth.client_credentials import ClientCredentialsMixin
from .auth.authorization_code import AuthorizationCodeMixin
from .auth.device_code import DeviceCodeMixin
from .exceptions import APIRateLimitExceededFailure


class VimeoClient(ClientCredentialsMixin, AuthorizationCodeMixin, DeviceCodeMixin):
    """Client handle for the Vimeo API."""

    API_ROOT = "https://api.vimeo.com"
    HTTP_METHODS = {'head', 'get', 'post', 'put', 'patch', 'options', 'delete'}
    ACCEPT_HEADER = "application/vnd.vimeo.*;version=3.4"
    USER_AGENT = "pyvimeo 1.0.11; (http://developer.vimeo.com/api/docs)"

    def __init__(self, token=None, key=None, secret=None, *args, **kwargs):
        """Prep the handle with the authentication information."""
        self.token = token
        self.app_info = (key, secret)
        self._requests_methods = dict()

        # Make sure we have enough info to be useful.
        assert token is not None or (key is not None and secret is not None)

    # Internally we back this with an auth mechanism for Requests.
    @property
    def token(self):
        """Get the token string from the class _BearerToken."""
        return self._token.token

    @token.setter
    def token(self, value):
        self._token = _BearerToken(value) if value else None

    def __getattr__(self, name):
        """
        Method used to get the function for the verb that was just requested.

        From here we can apply the authentication information we have.
        """
        if name not in self.HTTP_METHODS:
            raise AttributeError("%r is not an HTTP method" % name)

        # Get the Requests based function to use to preserve their defaults.
        request_func = getattr(requests, name, None)
        if request_func is None:
            raise AttributeError(
                "%r could not be found in the backing lib" % name
            )

        @wraps(request_func)
        def caller(url, jsonify=True, **kwargs):
            """Hand off the call to Requests."""
            headers = kwargs.get('headers', dict())
            headers['Accept'] = self.ACCEPT_HEADER
            headers['User-Agent'] = self.USER_AGENT

            if jsonify \
                    and 'data' in kwargs \
                    and isinstance(kwargs['data'], (dict, list)):
                kwargs['data'] = json.dumps(kwargs['data'])
                headers['Content-Type'] = 'application/json'

            kwargs['timeout'] = kwargs.get('timeout', (1, 30))
            kwargs['auth'] = kwargs.get('auth', self._token)
            kwargs['headers'] = headers
            if not url[:4] == "http":
                url = self.API_ROOT + url

            response = request_func(url, **kwargs)
            if response.status_code == 429:
                raise APIRateLimitExceededFailure(
                    response, 'Too many API requests'
                )
            return response
        return caller


class _BearerToken(requests.auth.AuthBase):
    """Model the bearer token and apply it to the request."""

    def __init__(self, token):
        self.token = token

    def __call__(self, request):
        request.headers['Authorization'] = 'Bearer ' + self.token
        return request
