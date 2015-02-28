# -*- coding: utf-8 -*-
import re
from resources.lib.soundcloud.client import ClientException

__author__ = 'bromix'

import unittest
from resources.lib.soundcloud import Client


class TestClient(unittest.TestCase):
    TOKEN = u'1-21686-118589874-262b20fc160e44'
    FALSE_TOKEN = u'1-21686-118589874-262b20fc160e456'

    def setUp(self):
        pass

    def test_resolve_url(self):
        client = Client(access_token=self.TOKEN)

        url = 'http://soundcloud.com/qdance/luna-presents-minus-is-more-december-2014-yearmix'
        #url = 'http://soundcloud.com/julyukie/sets/juliana-yamasaki-new-tracks'
        json_data = client.resolve_url(url)
        pass

    def test_false_token(self):
        client = Client(access_token=self.FALSE_TOKEN)

        # me
        self.assertRaises(ClientException, client.get_user, 'me')
        pass

    def test_cursor(self):
        next_href = u'https://api.soundcloud.com/me/activities/tracks/affiliated?cursor=aedb3280-55fb-11e3-8019-38efa603dd45&limit=50'
        re_match = re.match('.*cursor\=(?P<cursor>[a-z0-9-]+).*', next_href)
        page_cursor = re_match.group('cursor')
        self.assertEqual('aedb3280-55fb-11e3-8019-38efa603dd45', page_cursor)
        pass

    def test_get_likes(self):
        client = Client(access_token=self.TOKEN)

        # me
        json_data = client.get_user('me')
        user_id = json_data['id']
        json_data = client.get_likes(user_id)
        self.assertGreater(len(json_data), 0)

        # some user
        json_data = client.get_likes('520685', page=2)
        self.assertGreater(len(json_data), 0)
        pass

    def test_get_trending(self):
        client = Client()
        json_data = client.get_trending('audio')
        pass

    def test_get_genre(self):
        client = Client()
        json_data = client.get_genre('techno')
        pass

    def test_get_track_url(self):
        client = Client()
        json_data = client.get_track_url(77773864)
        pass

    def test_search(self):
        client = Client()
        json_data = client.search('bäume', category='sounds')
        pass

    def test_get_recommended_for_track(self):
        client = Client(access_token=self.TOKEN)
        json_data = client.get_recommended_for_track(193347852, page=1)
        pass

    def test_get_stream(self):
        client = Client(access_token=self.TOKEN)
        json_data = client.get_stream()
        pass

    def test_tracks(self):
        client = Client(access_token=self.TOKEN)
        json_data = client.get_tracks('me')

        json_data = client.get_tracks(1701116)
        pass

    def test_follow(self):
        client = Client(access_token=self.TOKEN)
        json_data = client.follow_user(1701116, False)
        self.assertGreater(len(json_data), 0)

        json_data = client.follow_user(1701116, True)
        self.assertGreater(len(json_data), 0)
        pass

    def test_get_playlist(self):
        client = Client(access_token=self.TOKEN)
        json_data = client.get_playlist(55019726)
        self.assertGreater(len(json_data), 0)
        pass

    def test_get_playlists(self):
        # me
        client = Client(access_token=self.TOKEN)
        json_data = client.get_playlists('me')
        self.assertGreater(len(json_data), 0)

        # some user
        json_data = client.get_playlists(2442230)
        self.assertGreater(len(json_data), 0)
        pass

    def test_get_favorites(self):
        client = Client(access_token=self.TOKEN)
        json_data = client.get_favorites('me')
        self.assertGreater(len(json_data), 0)
        pass

    def test_get_follower(self):
        client = Client(access_token=self.TOKEN)
        json_data = client.get_follower('me')
        self.assertGreater(len(json_data), 0)
        pass

    def test_get_following(self):
        client = Client(access_token=self.TOKEN)
        json_data = client.get_following('me')
        self.assertGreater(len(json_data), 0)
        pass

    def test_user(self):
        client = Client(access_token=self.TOKEN)
        json_data = client.get_user('me')

        self.assertGreater(len(json_data), 0)
        pass

    def test_update_token(self):
        client = Client(username='co4hu41hkqud5cm@my10minutemail.com', password='1234567890')
        token = client.update_access_token()

        self.assertTrue(token is not None)
        print "Token: '%s'" % token
        pass

    pass
