import hashlib
import time
from resources.lib.nine_gag import Client

__author__ = 'bromix'

import unittest


class TestClient(unittest.TestCase):
    def setUp(self):
        self._client = Client()
        access_token, expires = self._client.authenticate()
        self._client = Client(access_token)
        pass

    def test_get_posts(self):
        json_data = self._client.get_posts('LJEGX')
        pass

    def test_get_available(self):
        json_data = self._client.get_available()
        pass

    def test_authenticate(self):
        client = Client()

        access_token, expires = client.authenticate()
        pass

    def test_calculate_request_signature(self):
        client = Client()

        sig = client.calculate_request_signature(time_stamp=1414434266907)
        self.assertEqual('7782bff6e9d3602c90379ee595fbc4620ba2dd2b', sig)

        sig = client.calculate_request_signature(time_stamp=1414434267559)
        self.assertEqual('88807861fe02b508b0604f578a56ecfeabb3be79', sig)
        pass

    pass
