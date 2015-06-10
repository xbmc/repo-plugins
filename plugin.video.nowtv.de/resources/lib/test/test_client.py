__author__ = 'bromix'

import unittest
from resources.lib import nowtv


class TestClient(unittest.TestCase):
    def test_get_formats(self):
        channel_config = nowtv.Client.CHANNELS['rtl']
        client = nowtv.Client()
        formats = client.get_formats(channel_config)
        pass

    def test_get_search(self):
        client = nowtv.Client()
        formats = client.search('Hochzeiten')
        pass

    def test_get_format_tabs(self):
        channel_config = nowtv.Client.CHANNELS['rtl']
        client = nowtv.Client()
        format_tabs = client.get_format_tabs(channel_config, 'alles-was-zaehlt')
        pass

    def test_get_videos_by_format_list(self):
        channel_config = nowtv.Client.CHANNELS['rtl']
        client = nowtv.Client()
        formats = client.get_videos_by_format_list(channel_config, 9679)

        formats = client.get_videos_by_format_list(channel_config, 6067)
        pass

    def test_get_video_streams(self):
        channel_config = nowtv.Client.CHANNELS['rtl']
        client = nowtv.Client()
        formats = client.get_video_streams(channel_config, 'rtl-aktuell/thema-ua-bahnstreik-beendet')
        pass

    pass