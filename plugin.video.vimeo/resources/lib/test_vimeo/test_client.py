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
        client = Client()
        params = {'method': 'vimeo.videos.search',
                  'sort': 'relevant',
                  'page': '1',
                  'summary_response': '1',
                  'query': 'batman robin',
                  'oauth_timestamp': '1426349037',
                  'oauth_nonce': '903332784446098'}
        oauth = client._create_authorization(url='http://vimeo.com/api/rest/v2',
                                             method='POST',
                                             params=params)
        pass

    def test_get_video_streams(self):
        client = Client()
        streams = client.get_video_streams(video_id='121124509')
        pass

    def test_search(self):
        client = Client()
        xml_data = client.search(query='batman robin')
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
