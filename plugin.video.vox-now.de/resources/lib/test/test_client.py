__author__ = 'bromix'

import unittest
from resources.lib import rtlinteractive


class TestClient(unittest.TestCase):
    def test_get_server_id(self):
        server_id = rtlinteractive.Client.get_server_id()
        client = rtlinteractive.Client(rtlinteractive.Client.CONFIG_RTL_NOW)
        streams = client.get_film_streams(183331, server_id)
        pass

    def test_get_film_streams(self):
        client = rtlinteractive.Client(rtlinteractive.Client.CONFIG_VOX_NOW)
        streams = client.get_film_streams(200307)

        try:
            streams = client.get_film_streams(189735)
        except rtlinteractive.UnsupportedStreamException, ex:
            x = ex
            pass
        pass

    def test_get_film_details(self):
        client = rtlinteractive.Client(rtlinteractive.Client.CONFIG_RTL_NOW)
        json_data = client.get_film_details(183085)
        self.assertTrue(json_data['success'])
        pass

    def test_get_live_streams(self):
        client = rtlinteractive.Client(rtlinteractive.Client.CONFIG_RTL_NOW)
        json_data = client.get_live_streams()
        self.assertTrue(json_data['success'])
        pass

    def test_get_films(self):
        client = rtlinteractive.Client(rtlinteractive.Client.CONFIG_RTL_NOW)
        json_data = client.get_films(format_id=1061, page=1)
        self.assertTrue(json_data['success'])
        pass

    def test_get_formats(self):
        client = rtlinteractive.Client(rtlinteractive.Client.CONFIG_RTL_NOW)
        json_data = client.get_formats()
        self.assertTrue(json_data['success'])
        pass

    def test_tips(self):
        client = rtlinteractive.Client(rtlinteractive.Client.CONFIG_RTL_NOW)
        json_data = client.get_tips()
        self.assertTrue(json_data['success'])

    def test_top_10(self):
        client = rtlinteractive.Client(rtlinteractive.Client.CONFIG_RTL_NOW)
        json_data = client.get_top_10()
        self.assertTrue(json_data['success'])

    def test_search(self):
        client = rtlinteractive.Client(rtlinteractive.Client.CONFIG_RTL_NOW)
        json_data = client.search('bauer')
        self.assertTrue(json_data['success'])
        pass

    pass