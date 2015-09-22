__author__ = 'bromix'

import unittest

from resources.lib.content import Client


class TestClient(unittest.TestCase):

    def test_get_home_page(self):
        client = Client()

        for channel_id in Client.CHANNEL_ID_LIST:
            result = client.get_homepage(channel_id)
            pass
        pass

    def test_get_channel_formats(self):
        client = Client()

        for channel_id in Client.CHANNEL_ID_LIST:
            result = client.get_formats(channel_id)
            pass

        pass

    def test_get_format_content(self):
        client = Client()

        result = client.get_format_content('pro7', 'pro7:789')
        pass

    def test_get_format_video(self):
        client = Client()

        result = client.get_format_videos('pro7', 'pro7:505', page=2)
        objects = result.get('objects', [])
        self.assertGreater(len(objects), 0)

        for video in objects:
            print video['title']
            pass
        pass

    def test_search(self):
        client = Client()
        result = client.search('halligalli')
        pass

    def test_get_new_video(self):
        format_ids = ['pro7:277', 'pro7:505']

        client = Client()
        json_data = client.get_new_videos(format_ids)
        pass

    def test_get_video_streams(self):
        format_ids = ['pro7:277', 'pro7:505']

        client = Client()
        json_data = client.get_new_videos(format_ids)
        item = json_data['items'][0]

        video_data = client.get_video_url(item['id'])
        pass
    pass
