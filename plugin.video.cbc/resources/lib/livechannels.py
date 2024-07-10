"""Module for live channels."""
from concurrent import futures
import json
from urllib.parse import urlencode

import requests

from resources.lib.utils import save_cookies, loadCookies, log, get_iptv_channels_file
from resources.lib.cbc import CBC

LIST_URL = 'https://services.radio-canada.ca/ott/catalog/v2/gem/home?device=web'
LIST_ELEMENT = '2415871718'

class LiveChannels:
    """Class for live channels."""

    def __init__(self):
        """Initialize the live channels class."""
        # Create requests session object
        self.session = requests.Session()
        session_cookies = loadCookies()
        if session_cookies is not None:
            self.session.cookies = session_cookies

    def get_live_channels(self):
        """Get the list of live channels."""
        resp = self.session.get(LIST_URL)

        if not resp.status_code == 200:
            log('ERROR: {} returns status of {}'.format(LIST_URL, resp.status_code), True)
            return None
        save_cookies(self.session.cookies)

        ret = None
        for result in json.loads(resp.content)['lineups']['results']:
            if result['key'] == LIST_ELEMENT:
                ret = result['items']

        future_to_callsign = {}
        with futures.ThreadPoolExecutor(max_workers=20) as executor:
            for i, channel in enumerate(ret):
                callsign = CBC.get_callsign(channel)
                future = executor.submit(self.get_channel_metadata, callsign)
                future_to_callsign[future] = i

        for future in futures.as_completed(future_to_callsign):
            i = future_to_callsign[future]
            metadata = future.result()
            ret[i]['image'] = metadata['Metas']['imageHR']
        return ret

    def get_iptv_channels(self):
        """Get the channels in a IPTV Manager compatible list."""
        cbc = CBC()
        channels = self.get_live_channels()
        channels = [channel for channel in channels if channel['feedType'].lower() == 'livelinear']
        blocked = self.get_blocked_iptv_channels()
        result = []
        for channel in channels:
            callsign = CBC.get_callsign(channel)

            # if the user has omitted this from the list of their channels, don't populate it
            if f'{callsign}' in blocked:
                continue

            labels = CBC.get_labels(channel)
            image = cbc.get_image(channel)

            # THE FORMAT OF THESE IS VERY IMPORTANT
            # - values is passed to /channels/play in default.py
            # - channel_dict is used by the IPTVManager for the guide and stream is how the IPTV manager calls us back to play something
            values = {
                'id': callsign,
                'image': image,
                'labels': urlencode(labels)
            }
            channel_dict = {
                'name': channel['title'],
                'stream': 'plugin://plugin.video.cbc/channels/play?' + urlencode(values),
                'id': callsign,
                'logo': image,
            }

            # Use "CBC Toronto" instead of "Toronto"
            if len(channel_dict['name']) < 4 or channel_dict['name'][0:4] != 'CBC ':
                channel_dict['name'] = 'CBC {}'.format(channel_dict['name'])
            result.append(channel_dict)

        return result

    def get_channel_stream(self, id):
        url = f'https://services.radio-canada.ca/media/validation/v2/?appCode=medianetlive&connectionType=hd&deviceType=ipad&idMedia={id}&multibitrate=true&output=json&tech=hls&manifestType=desktop'
        resp = self.session.get(url)
        if not resp.status_code == 200:
            log('ERROR: {} returns status of {}'.format(LIST_URL, resp.status_code), True)
            return None
        save_cookies(self.session.cookies)
        return json.loads(resp.content)['url']

    def get_channel_metadata(self, id):
        url = f'https://services.radio-canada.ca/media/meta/v1/index.ashx?appCode=medianetlive&idMedia={id}&output=jsonObject'
        resp = self.session.get(url)
        if not resp.status_code == 200:
            log('ERROR: {} returns status of {}'.format(LIST_URL, resp.status_code), True)
            return None
        save_cookies(self.session.cookies)
        return json.loads(resp.content)

    @staticmethod
    def get_blocked_iptv_channels():
        """Get the list of blocked channels."""
        chan_file = get_iptv_channels_file()
        try:
            with open(get_iptv_channels_file(), 'r') as chan_file:
                return json.load(chan_file)
        except FileNotFoundError:
            return []

    @staticmethod
    def remove_iptv_channel(channel):
        """Add all live channels for IPTV."""
        blocked = LiveChannels.get_blocked_iptv_channels()

        if channel not in blocked:
            blocked.append(channel)

        with open(get_iptv_channels_file(), 'w') as chan_file:
            json.dump(blocked, chan_file)

    @staticmethod
    def add_iptv_channel(channel):
        """Add all live channels for IPTV."""
        blocked = LiveChannels.get_blocked_iptv_channels()
        if len(blocked) == 0:
            return

        if channel in blocked:
            blocked.remove(channel)

        with open(get_iptv_channels_file(), 'w') as chan_file:
            json.dump(blocked, chan_file)

    @staticmethod
    def add_only_iptv_channel(channel):
        """
        Add only a single specified channel to the list of IPTV channels.

        This method gets the list of all channels, and removes the only one the user wants, leaving the rest as an
        extensive filter.
        """
        blocked = [CBC.get_callsign(chan) for chan in LiveChannels().get_live_channels()]

        if channel in blocked:
            blocked.remove(channel)

        with open(get_iptv_channels_file(), 'w') as chan_file:
            json.dump(blocked, chan_file)
