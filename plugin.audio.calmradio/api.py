from xbmcaddon import Addon
from config import config
from cache import cache
import requests
import json


ADDON = Addon()


class API(object):
    def __init__(self):
        pass

    @staticmethod
    @cache
    def get_json(url, verify=False):
        """
        Gets JSON file
        :param url: Link to JSON
        :return: Object
        """
        r = requests.get(url, verify=verify)
        if r.status_code == 200:
            return json.loads(r.text)

    def get_all_categories(self):
        """
        Returns a list of all categories
        :return:
        """
        results = []
        for section in self.get_json(config['urls']['calm_categories_api']):
            results += section['categories']
        return results

    def get_categories(self, section_id):
        """
        Returns a list of categories which belongs to specific section
        :param section_id: Section ID
        :return:
        """
        return [item['categories'] for item in self.get_json(config['urls']['calm_categories_api'])
                if item['id'] == section_id][0]

    def get_all_channels(self):
        """
        Returns a list of all playable channels
        :return:
        """
        results = []
        for category in self.get_json(config['urls']['calm_channels_api']):
            results += category['channels']
        return results

    def get_channels(self, category_id):
        """
        Returns a list of playable channels which belongs to specific category
        :param category_id: Category ID
        :return:
        """
        return [item['channels'] for item in self.get_json(config['urls']['calm_channels_api'])
                if item['category'] == category_id][0]

    def get_favorites(self, username, token):
        """
        Returns users favorites channels
        :param username: Username
        :param token: Access token
        :return:
        """
        results = []

        if username and token:
            favorites = self.get_json(config['urls']['calm_favorites_api'].format(username, token, 'list', 0))
            if len(favorites) > 0:
                for category in self.get_json(config['urls']['calm_channels_api']):
                    for channel in category['channels']:
                        if str(channel['id']) in favorites:
                            channel['category'] = category['category']
                            results.append(channel)

        return results

    def add_to_favorites(self, username, token, channel_id):
        """
        Returns users favorites channels
        :param username: Username
        :param token: Access token
        :param channel_id: Channel ID
        :return:
        """
        if channel_id > 0 and username and token:
            result = self.get_json(config['urls']['calm_favorites_api'].format(username, token, 'add', channel_id))
            return 'success' in result and result['success'] == True

        return False

    def remove_from_favorites(self, username, token, channel_id):
        """
        Returns users favorites channels
        :param username: Username
        :param token: Access token
        :param channel_id: Channel ID
        :return:
        """
        if channel_id > 0 and username and token:
            result = self.get_json(config['urls']['calm_favorites_api'].format(username, token, 'remove', channel_id))
            return 'success' in result and result['success'] == True

        return False

    def get_streaming_url(self, streams, username, token, is_authenticated):
        """
        Returns the stream URL based on chosen quality
        :param streams: List of available channel streams
        :param username: Username
        :param token: Access token
        :param is_authenticated: Indicates whether user is authenticated
        :return:
        """
        # datafix:
        if ADDON.getSetting('bitrate') == '3':
            ADDON.setSetting('bitrate', '2')

        if not is_authenticated:
            bitrate = 'free_128'
        else:
            bitrate = {
                '0': '64',
                '1': '192',
                '2': '320'
            }[ADDON.getSetting('bitrate') or '0']

        if not is_authenticated and bitrate in streams:
            return streams[bitrate]
        elif is_authenticated:
            return streams[bitrate].replace('http://', 'http://{0}:{1}@'.format(
                username,
                token
            ))

        return None
