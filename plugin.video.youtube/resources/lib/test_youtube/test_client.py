from resources.lib import kodion
from resources.lib.youtube.client import YouTube

__author__ = 'bromix'

import unittest


class TestClient(unittest.TestCase):
    USERNAME = ''
    PASSWORD = ''

    def test_playlist_item_id_of_video_id(self):
        client = YouTube(language='de-DE')

        json_data = client.get_playlist_item_id_of_video_id(playlist_id='PL3tRBEVW0hiBMoF9ihuu-x_aQVXvFYHIH', video_id='KpjgZ8xAeLI')
        pass

    def test_get_supported_regions(self):
        client = YouTube(language='de-DE')
        json_data = client.get_supported_regions()
        pass

    def test_get_supported_languages(self):
        client = YouTube(language='de-DE')
        json_data = client.get_supported_languages()
        pass

    def test_generate_user_code(self):
        client = YouTube(language='de-DE')
        json_data = client.generate_user_code()
        pass

    def test_popular_videos(self):
        client = YouTube(language='de-DE')

        json_data = client.get_popular_videos()
        pass

    def test_video_categories(self):
        client = YouTube(language='de-DE')
        json_data = client.get_video_categories()
        pass

    def test_video_category(self):
        client = YouTube(language='de-DE')

        # 10 Music
        json_data = client.get_video_category(10)
        pass

    """
    def test_create_playlist(self):
        client = YouTube()

        token, expires = client.authenticate(self.USERNAME, self.PASSWORD)
        client = YouTube(access_token=token)
        json_data = client.create_playlist(title='BLA')
        pass

    def test_activities(self):
        client = YouTube()

        token, expires = client.authenticate(self.USERNAME, self.PASSWORD)
        client = YouTube(access_token=token)
        #json_data = client.get_uploaded_videos_of_subscriptions()
        json_data = client.get_activities(channel_id='home')
        pass

    def test_guide_category(self):
        client = YouTube(language='de-DE')
        token, expires = client.authenticate(self.USERNAME, self.PASSWORD)
        client = YouTube(language='de-DE', access_token=token)

        # Music
        #json_data = client.get_guide_category('GCTXVzaWM')

        # Best of YouTube
        json_data = client.get_guide_category('GCQmVzdCBvZiBZb3VUdWJl')
        pass

    def test_guide_categories(self):
        client = YouTube(language='de-DE')

        token, expires = client.authenticate(self.USERNAME, self.PASSWORD)
        client = YouTube(access_token=token)
        json_data = client.get_guide_categories()
        pass

    def test_authenticate(self):
        client = YouTube()
        token, expires = client.authenticate(self.USERNAME, self.PASSWORD)
        pass

    def test_playlist_items_id_of_video(self):
        client = YouTube()

        token, expires = client.authenticate(self.USERNAME, self.PASSWORD)
        client = YouTube(access_token=token)

        playlist_item_id = client.get_playlist_item_id_of_video_id(u'WL', '-Zotg42zEEA')
        pass

    def test_get_playlist_items(self):
        client = YouTube()

        token, expires = client.authenticate(self.USERNAME, self.PASSWORD)
        client = YouTube(access_token=token)

        json_data = client.get_playlist_items(u'WL', video_id='-Zotg42zEEA')
        pass

    def test_get_channels(self):
        client = YouTube()

        token, expires = client.authenticate(self.USERNAME, self.PASSWORD)
        client = YouTube(access_token=token)

        json_data = client.get_channels('mine')
        #json_data = client.get_channels(['UCDbAn9LEzqONk__uXA6a9jQ', 'UC8i4HhaJSZhm-fu84Bl72TA'])
        pass
    """

    def test_get_video_streams(self):
        client = YouTube()

        context = kodion.Context()

        #Live
        #streams = client.get_video_streams(context, '7UFbGKo21lc')
        #streams = client.get_video_streams(context, 'RqbyYOCAFJU')
        #streams = client.get_video_streams(context, 'pvEWZY3Eqsg')

        # VEVO
        #streams = client.get_video_streams(context, 'nfWlot6h_JM')

        # 60fps
        # streams = client.get_video_streams(context, '_zPm3SSj6W8')

        # 1080p ?!?
        # streams = client.get_video_streams(context, 'qfPUVz_Hpqo')

        # Restricted?
        #streams = client.get_video_streams(context, 'U4DbJWA9JEw')

        # VEVO (Restricted)
        #streams = client.get_video_streams(context, 'O-zpOMYRi0w')
        #streams = client.get_video_streams(context, 'NmugSMBh_iI')

        # VEVO Gema
        #streams = client.get_video_streams(context, 'XbiH6pQI7pU')
        pass

    def test_get_playlists(self):
        client = YouTube()

        json_data = client.get_playlists('UCDbAn9LEzqONk__uXA6a9jQ')
        pass

    def test_get_videos(self):
        client = YouTube()

        json_data = client.get_videos(['vyD70Huufco', 'AFdezM3_m-c'])
        pass

    def test_get_related_videos(self):
        client = YouTube()

        json_data = client.get_related_videos(video_id='dbgPETJ-J9E')
        pass

    def test_search(self):
        client = YouTube()

        # json_data = client.search(q='batman')
        # json_data = client.search(q='batman', search_type='channel')
        json_data = client.search(q='batman', search_type='playlist')
        pass

    pass
