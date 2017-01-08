from config import config
from cache import Cache
import requests
import time
import xml.etree.ElementTree as ET


class API(object):
    def __init__(self):
        pass

    @staticmethod
    @Cache
    def get_file_content(url):
        """
        Gets XML data file
        :param url: Link of XML file
        :return: Object
        """
        r = requests.get(url)
        r.encoding = 'utf-8'
        if r.status_code == 200:
            return r.text

    def get_all_channels(self):
        """
        Returns a list of all digital radio stations
        :return:
        """
        root = ET.fromstring(self.get_file_content(config['urls']['radius_data_file']).encode('utf-8'))

        return [{
                    'name': channel.find('name').text.encode('utf-8'),
                    'thumbnail': channel.find('img').text,
                    'label': channel.find('font').text,
                    'stream': channel.find('Feed').text,
                    'meta': channel.find('nowplaying').text,
                    'description': channel.find('desc').text.encode('utf-8'),
                } for channel in root.findall('Channel')]

    def get_current_song(self, url):
        """
        Returns current song details
        :return:
        """
        root = ET.fromstring(self.get_file_content('{0}?rand={1}'.format(url, str(time.time()))).encode('utf-8'))

        return {
            'name': root.find('name').text.encode('utf-8') if root.find('name').text else '',
            'artist': root.find('artist').text.encode('utf-8') if root.find('artist').text else ''
        }
