#! /usr/bin/env python
# encoding: utf-8

from .base import AuthenticationMixinBase
from . import GrantFailed


class DeviceCodeMixin(AuthenticationMixinBase):
    """
    Implement helpers for the Device Code grant for OAuth2.
    Attention! This is not (yet) part of the official vimeo.py library!
    """

    def load_device_code(self, scope):
        """Perform the request for device code."""
        code, headers, resp = self.call_grant(
            "/oauth/device", {
                "grant_type": "device_grant",
                "scope": scope
            })

        if not code == 200:
            raise GrantFailed()

        return resp

    def device_code_authorize(self, user_code, device_code):
        """Perform the authorization step after the user entered the device code."""
        code, headers, resp = self.call_grant(
            "/oauth/device/authorize", {
                "user_code": user_code,
                "device_code": device_code
            })

        if not code == 200:
            raise GrantFailed()

        self.token = resp["access_token"]

        return self.token, resp["user"], resp["scope"]
