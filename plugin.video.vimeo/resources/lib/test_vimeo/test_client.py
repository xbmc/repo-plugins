# -*- coding: utf-8 -*-

__author__ = 'bromix'

import unittest

from resources.lib.vimeo.client import Client


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
        params = {'x_auth_password': 'ENTER YOU PW HERE ^^',
                  'x_auth_username': 'YOUR@MAIL.COM',
                  'x_auth_permission': 'delete',
                  'x_auth_mode': 'client_auth',
                  'oauth_timestamp': '1428164862',
                  'oauth_nonce': '2826375882870'}
        oauth = client._create_authorization(url='https://secure.vimeo.com/oauth/access_token',
                                             method='POST',
                                             params=params)
        pass

    def test_get_video_streams(self):
        client = Client()
        streams = client.get_video_streams(video_id='128267976')
        pass

    def test_search(self):
        client = Client()
        xml_data = client.search(query='The Breakfast Club é Extras')
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
