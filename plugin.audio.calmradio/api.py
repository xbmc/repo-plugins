from config import config
import requests
import json


class API(object):
    def __init__(self, plugin):
        self.plugin = plugin

    @staticmethod
    def get_json(url):
        """
        Gets JSON file
        :param url: Link to JSON
        :return: Object
        """
        r = requests.get(url)
        if r.status_code == 200:
            return json.loads(r.text)

    def get_categories(self):
        """
        Returns calm radio top level categories
        :return:
        """
        return [
            {
                'id': 1,
                'name': self.plugin.get_string(32100),
                'image': 'special://home/addons/plugin.audio.calmradio/resources/media/fanart/0.jpg',
                'description': self.plugin.get_string(32101)
            },
            {
                'id': 3,
                'name': self.plugin.get_string(32102),
                'image': 'special://home/addons/plugin.audio.calmradio/resources/media/fanart/3.jpg',
                'description': self.plugin.get_string(32103)
            },
            {
                'id': 99,
                'name': self.plugin.get_string(32104),
                'image': 'special://home/addons/plugin.audio.calmradio/resources/media/fanart/99.jpg',
                'description': self.plugin.get_string(32105)
            }
        ]

    def get_all_subcategories(self):
        """
        Returns a list of all sub categories
        :return:
        """
        results = []
        for category in self.get_json(config['urls']['calm_categories_api']):
            results += category['categories']
        return results

    def get_subcategories(self, category_id):
        """
        Returns a list of sub categories which belongs to specific category
        :param category_id: Category ID
        :return:
        """
        return [item['categories'] for item in self.get_json(config['urls']['calm_categories_api'])
                if item['id'] == category_id][0]

    def get_all_channels(self):
        """
        Returns a list of all playable channels
        :return:
        """
        results = []
        for category in self.get_json(config['urls']['calm_channels_api']):
            results += category['channels']
        return results

    def get_channels(self, subcategory_id):
        """
        Returns a list of playable channels which belongs to specific category
        :param subcategory_id: Sub category ID
        :return:
        """
        return [item['channels'] for item in self.get_json(config['urls']['calm_channels_api'])
                if item['category'] == subcategory_id][0]

    def get_favorites(self, username, token):
        """
        Returns users favorites channels
        :return:
        """
        results = []

        if username and token:
            favorites = self.get_json(config['urls']['calm_favorites_api'].format(username, token, 'list', 0))
            if len(favorites) > 0:
                for category in self.get_json(config['urls']['calm_channels_api']):
                    for channel in category['channels']:
                        if str(channel['id']) in favorites:
                            results.append(channel)

        return results

    def add_to_favorites(self, username, token, channel_id):
        """
        Returns users favorites channels
        :return:
        """
        if channel_id > 0 and username and token:
            result = self.get_json(config['urls']['calm_favorites_api'].format(username, token, 'add', channel_id))
            self.plugin.log.info(config['urls']['calm_favorites_api'].format(username, token, 'add', channel_id))
            return 'success' in result and result['success'] == True

        return False

    def remove_from_favorites(self, username, token, channel_id):
        """
        Returns users favorites channels
        :return:
        """
        if channel_id > 0 and username and token:
            result = self.get_json(config['urls']['calm_favorites_api'].format(username, token, 'remove', channel_id))
            return 'success' in result and result['success'] == True

        return False

    def get_url(self, streams, username, token, is_authenticated):
        """
        Returns the stream URL based on chosen quality
        :param streams: Chosen quality
        :return:
        """
        bitrate = {
            '0': '32',
            '1': '64',
            '2': '192',
            '3': '320'
        }[self.plugin.get_setting('bitrate') or 0]

        if not is_authenticated and 'free' in streams:
            return streams['free']
        elif is_authenticated:
            return streams[bitrate].replace('http://', 'http://{0}:{1}@'.format(
                username,
                token
            ))

        return None
