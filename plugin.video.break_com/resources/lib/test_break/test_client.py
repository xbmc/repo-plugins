from resources.lib.break_api import Client

__author__ = 'bromix'

import unittest


class TestClient(unittest.TestCase):
    def test_get_video_url(self):
        client = Client()
        url = client.get_video_urls(2848412)
        pass

    def test_get_video(self):
        client = Client()
        json_data = client.get_video(2608653)
        pass

    def test_get_feed(self):
        client = Client()
        json_data = client.get_feed(40)
        pass

    def test_get_feeds(self):
        client = Client()
        for i in range(100, 200):
            print 'testing "%d"' % i
            json_data = client.get_feed(i)
            data = json_data.get('data', {}).get('data', [])
            if len(data) > 0:
                item = data[0]
                desc = item.get('description', '')
                if desc:
                    print 'desc: "%s"' % desc
                    pass
                pass
            pass
        pass

    def test_get_home(self):
        client = Client()
        json_data = client.get_home()
        pass
    pass
