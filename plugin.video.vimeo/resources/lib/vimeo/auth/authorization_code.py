#! /usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import

from .base import AuthenticationMixinBase
from . import GrantFailed

# We need to get urlencode from urllib.parse in Python 3, but fall back to
# urllib in Python 2
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

try:
    basestring
except NameError:
    basestring = str


class AuthorizationCodeMixin(AuthenticationMixinBase):
    """Implement helpers for the Authorization Code grant for OAuth2."""

    def auth_url(self, scope, redirect, state):
        """Get the url to direct a user to authenticate."""
        url = self.API_ROOT + "/oauth/authorize?"

        query = {
            "response_type": "code",
            "client_id": self.app_info[0]
        }

        if scope:
            if not isinstance(scope, basestring):
                scope = ' '.join(scope)

            query['scope'] = scope

        if redirect:
            query['redirect_uri'] = redirect

        if state:
            query['state'] = state

        return url + urlencode(query)

    def exchange_code(self, code, redirect):
        """Perform the exchange step for the code from the redirected user."""
        code, headers, resp = self.call_grant(
            '/oauth/access_token', {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect
            })

        if not code == 200:
            raise GrantFailed()

        self.token = resp['access_token']

        return self.token, resp['user'], resp['scope']
