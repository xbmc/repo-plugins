# -*- coding: utf-8 -*-
from resources.lib import nightcrawler

__author__ = 'bromix'

import re
import unittest

from resources.lib.content import Client


class TestClient(unittest.TestCase):
    USERNAME = 'co4hu41hkqud5cm@my10minutemail.com'
    PASSWORD = '1234567890'

    def test_get_trending(self):
        client = Client()
        result = client.get_trending('audio')
        pass

    def test_get_categories(self):
        client = Client()
        result = client.get_categories()
        pass

    def test_get_genre(self):
        client = Client()
        result = client.get_genre('techno')
        pass

    def test_search(self):
        client = Client()
        tracks = client.search('angerfist', category='sounds')
        pass

    def test_get_favorites(self):
        client = Client()
        json_data = client.get_favorites(520685)
        pass

    def test_get_likes(self):
        client = Client()
        json_data = client.get_likes(520685)
        pass

    def test_get_playlists(self):
        client = Client()
        json_data = client.get_playlists(520685)
        pass

    def test_get_playlist(self):
        client = Client()
        json_data = client.get_playlist(55019726)
        self.assertGreater(len(json_data), 0)
        pass

    def test_get_following(self):
        client = Client()
        json_data = client.get_following(520685)
        pass

    def test_get_follower(self):
        client = Client()
        json_data = client.get_follower(520685)
        pass

    def test_get_recommended_for_track(self):
        client = Client()
        json_data = client.get_recommended_for_track(193347852, page=1)
        pass

    def test_user(self):
        client = Client()
        json_data = client.get_user(1701116)
        pass

    def test_tracks(self):
        client = Client()
        json_data = client.get_tracks(1701116)
        pass

    def test_get_track(self):
        client = Client()
        json_data = client.get_track(193347852)
        pass

    def test_get_track_url(self):
        client = Client()
        url = client.get_track_url(193347852)
        pass

    def test_resolve_url(self):
        client = Client()

        url = 'http://soundcloud.com/qdance/luna-presents-minus-is-more-december-2014-yearmix'
        json_data = client.resolve_url(url)

        url = 'http://soundcloud.com/julyukie/sets/juliana-yamasaki-new-tracks'
        json_data = client.resolve_url(url)
        pass

    def test_login(self):
        login_data = Client().login(username=self.USERNAME, password=self.PASSWORD)

        self.assertRaises(nightcrawler.CredentialsException, Client().login, username=self.USERNAME, password='0')
        pass

    def test_get_stream(self):
        login_data = Client().login(username=self.USERNAME, password=self.PASSWORD)
        client = Client(access_token=login_data['access_token'])
        json_data = client.get_stream()
        pass

    def test_follow(self):
        login_data = Client().login(username=self.USERNAME, password=self.PASSWORD)
        client = Client(access_token=login_data['access_token'])
        json_data = client.follow_user(1647796, False)
        self.assertGreater(len(json_data), 0)

        json_data = client.follow_user(1647796, True)
        self.assertGreater(len(json_data), 0)
        pass

    def test_cursor(self):
        next_href = u'https://api.soundcloud.com/me/activities/tracks/affiliated?cursor=aedb3280-55fb-11e3-8019-38efa603dd45&limit=50'
        re_match = re.match('.*cursor\=(?P<cursor>[a-z0-9-]+).*', next_href)
        page_cursor = re_match.group('cursor')
        self.assertEqual('aedb3280-55fb-11e3-8019-38efa603dd45', page_cursor)
        pass

    pass
