__author__ = 'bromix'

import unittest

from resources.lib import prosiebensat1


class TestClient(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_new_video(self):
        format_ids = ['pro7:277', 'pro7:505']
        client = prosiebensat1.Client()
        json_data = client.get_new_videos(format_ids)
        pass
    pass
