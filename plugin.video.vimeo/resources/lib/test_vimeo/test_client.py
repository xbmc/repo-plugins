__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.vimeo.client import Client

import unittest


class TestClient(unittest.TestCase):
    USERNAME = ''
    PASSWORD = ''

    def get_client(self, logged_in=False):
        client = Client()
        data = client.login(self.USERNAME, self.PASSWORD)
        client = Client(data['oauth_token'], data['oauth_token_secret'])
        return client

    def test_create_authorization(self):
        client = self.get_client()
        params = {'x_auth_password': '',
                  'x_auth_username': '',
                  'x_auth_mode': 'client_auth',
                  'x_auth_permission': 'delete',
                  'oauth_timestamp': '1425168546',
                  'oauth_nonce': '721035593002863'}
        oauth = client._create_authorization(url='https://secure.vimeo.com/oauth/access_token',
                                             method='POST',
                                             params=params)
        pass

    def test_get_video_streams(self):
        client = Client()
        streams = client.get_video_streams(video_id='121124509')
        pass

    def test_search(self):
        client = self.get_client()
        xml_data = client.search(query='daredevil')
        pass

    def test_featured(self):
        client = self.get_client()
        xml_data = client.get_featured()
        pass

    def test_get_all_contacts(self):
        client = self.get_client()
        data = client.get_contacts()
        pass

    def test_login(self):
        client = self.get_client()
        xml_data = client.login('', '')

    pass
