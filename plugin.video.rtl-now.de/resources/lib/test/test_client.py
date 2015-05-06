__author__ = 'bromix'

import unittest
from resources.lib import rtlinteractive


class TestClient(unittest.TestCase):
    def test_get_film_streams(self):
        client = rtlinteractive.Client(rtlinteractive.Client.CONFIG_RTL_NOW)
        streams = client.get_film_streams(201205)
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