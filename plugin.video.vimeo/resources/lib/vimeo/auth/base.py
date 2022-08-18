#! /usr/bin/env python
# encoding: utf-8


class AuthenticationMixinBase:
    """Provide core logic to the authentication mixins."""

    def call_grant(self, path, data):
        """Perform the calls to the grant endpoints.

        These endpoints handle the echange to get the information from the API.
        """
        assert self.app_info[0] is not None and self.app_info[1] is not None

        resp = self.post(path, auth=self.app_info, jsonify=False, data=data)

        return resp.status_code, resp.headers, resp.json()
