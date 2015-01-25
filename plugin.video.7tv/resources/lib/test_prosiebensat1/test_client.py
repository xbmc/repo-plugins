__author__ = 'bromix'

import unittest

from resources.lib.prosiebensat1 import Client


class TestClient(unittest.TestCase):
    def setUp(self):
        pass

    def test_search(self):
        client = Client()

        result = client.search(client.API_V2, 'halligalli')
        screen = result.get('screen', {})
        screen_objects = screen.get('screen_objects', [])
        self.assertEqual(3, len(screen_objects))
        pass

    def test_get_home_page(self):
        client = Client()

        result = client.get_homepage(client.API_V2, 'pro7')
        screen = result.get('screen', {})
        screen_objects = screen.get('screen_objects', [])
        self.assertGreater(len(screen_objects), 3)
        pass

    def test_get_format_video(self):
        client = Client()
        result = client.get_format_videos(client.API_V2, 'pro7', '505', page=2)
        objects = result.get('objects', [])
        self.assertGreater(len(objects), 0)

        for video in objects:
            print video['title']
            pass
        pass

    def test_get_format_content(self):
        client = Client()

        result = client.get_format_content(client.API_V2, 'pro7', '789')
        screen = result.get('screen', {})
        screen_objects = screen.get('screen_objects', [])
        self.assertEqual(4, len(screen_objects))

        # Fanart and content
        for screen_object in screen_objects:
            if screen_object.get('type', '') == 'format_teaser_header_item':
                print 'Fanart: %s' % screen_object['image_url']
            elif screen_object.get('type', '') == 'sushi_bar':
                print '%s' % screen_object['title']
                pass
            pass
        pass

    def test_get_channel_formats(self):
        client = Client()
        result = client.get_formats(client.API_V2, 'pro7')

        screen = result.get('screen', {})
        screen_objects = screen.get('screen_objects', [])
        self.assertGreater(len(screen_objects), 0)

        for screen_object in screen_objects:
            print screen_object['title']
            pass
        pass

    def test_get_new_video(self):
        format_ids = ['pro7:277', 'pro7:505']
        client = Client()
        json_data = client.get_new_videos(client.API_V2, format_ids)
        screen_objects = json_data.get('screen_objects', [])
        self.assertGreater(len(screen_objects), 0)

        for screen_object in screen_objects:
            print screen_object['video_title']
            pass
        pass
    pass
