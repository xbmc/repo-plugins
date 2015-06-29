__author__ = 'bromix'

import unittest
from resources.lib import nowtv


class TestClient(unittest.TestCase):
    USERNAME = 'bromix@trash-mail.com'
    PASSWORD = '1234567890'

    def test_login(self):
        client = nowtv.Client()
        json_data = client.login(self.USERNAME, self.PASSWORD)
        pass

    def test_my_favorites(self):
        json_data = nowtv.Client().login(self.USERNAME, self.PASSWORD)
        token = json_data['token']
        user_id = json_data['id']

        client = nowtv.Client(token=token, user_id=user_id)
        formats = client.get_favorites()
        pass

    def test_my_watch_later(self):
        json_data = nowtv.Client().login(self.USERNAME, self.PASSWORD)
        token = json_data['token']
        user_id = json_data['id']

        client = nowtv.Client(token=token, user_id=user_id)
        videos = client.get_watch_later()
        pass

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

        format_tabs = client.get_format_tabs(channel_config, 'verdachtsfaelle')
        format_tabs = client.get_format_tabs(channel_config, 'der-traummann')
        format_tabs = client.get_format_tabs(channel_config, 'der-troedeltrupp-das-geld-liegt-im-keller')
        format_tabs = client.get_format_tabs(channel_config, 'gzsz')
        pass

    def test_get_videos_by_date_filter(self):
        json_data = nowtv.Client().login(self.USERNAME, self.PASSWORD)
        token = json_data['token']
        user_id = json_data['id']

        channel_config = nowtv.Client.CHANNELS['rtl']
        client = nowtv.Client(token=token, user_id=user_id)

        formats = client.get_videos_by_date_filter(channel_config, 1, '2015-06-01 00:00:00', '2015-06-30 23:59:59')
        pass

    def test_get_videos_by_format_list(self):
        channel_config = nowtv.Client.CHANNELS['rtl2']
        client = nowtv.Client()
        formats = client.get_videos_by_format_list(channel_config, 5455)

        formats = client.get_videos_by_format_list(channel_config, 9679)

        formats = client.get_videos_by_format_list(channel_config, 6067)
        pass

    def test_get_video_streams(self):
        channel_config = nowtv.Client.CHANNELS['rtl']
        client = nowtv.Client()
        formats = client.get_video_streams(channel_config, 'rtl-aktuell/thema-ua-bahnstreik-beendet')
        pass

    pass