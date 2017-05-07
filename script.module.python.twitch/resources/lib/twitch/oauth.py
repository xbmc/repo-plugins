# -*- encoding: utf-8 -*-

from twitch import CLIENT_ID
from twitch import scopes
from six.moves.urllib_parse import urlsplit, urlencode


class MobileClient:
    _auth_base_url = 'https://api.twitch.tv/kraken/oauth2/authorize'

    def __init__(self, client_id=''):
        self.client_id = client_id if client_id else CLIENT_ID

    def prepare_request_uri(self, redirect_uri='http://localhost:3000/', scope=list(), force_verify=False, state=''):
        params = {'response_type': 'token',
                  'client_id': self.client_id,
                  'redirect_uri': redirect_uri,
                  'scope': ' '.join(scope),
                  'force_verify': str(force_verify).lower(),
                  'state': state}
        params = urlencode(params)
        url = '{base_uri}?{params}'.format(base_uri=self._auth_base_url, params=params)
        return url

    @staticmethod
    def parse_implicit_response(url):
        pairs = urlsplit(url).fragment.split('&')
        fragment = dict()
        for pair in pairs:
            key, value = pair.split('=')
            fragment[key] = value
        return {'access_token': fragment.get('access_token'), 'scope': fragment.get('scope', '').split('+'), 'state': fragment.get('state')}
