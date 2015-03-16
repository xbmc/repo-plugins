__author__ = 'bromix'

from resources.lib.clipfish.client import Client

import unittest


class TestClient(unittest.TestCase):
    def test_get_categories(self):
        client = Client()
        json_data = client.get_categories()
        pass
    pass

