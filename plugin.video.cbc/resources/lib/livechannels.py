"""Module for live channels."""
import json
import re
from urllib.parse import urlencode

import requests

from resources.lib.utils import log, get_iptv_channels_file
from resources.lib.cbc import CBC
from resources.lib.gemv2 import GemV2

GEM_BASE_URL = 'https://gem.cbc.ca/'
FALLBACK_BUILD_ID = '7ByKb_CElwT2xVJeTO43g'
LIST_URL_TEMPLATE = 'https://gem.cbc.ca/_next/data/{}/live.json'

class LiveChannels:
    """Class for live channels."""

    def __init__(self):
        """Initialize the live channels class."""
        # Create requests session object
        self.session = requests.Session()

    @staticmethod
    def extract_build_id(html):
        """Extract Next.js buildId from page HTML."""
        script_start = '<script id="__NEXT_DATA__" type="application/json">'
        script_end = '</script>'
        start_pos = html.find(script_start)
        if start_pos >= 0:
            start_pos += len(script_start)
            end_pos = html.find(script_end, start_pos)
            if end_pos > start_pos:
                try:
                    next_data = json.loads(html[start_pos:end_pos])
                    build_id = next_data.get('buildId')
                    if build_id:
                        return build_id
                except (ValueError, TypeError):
                    pass

        match = re.search(r'/_next/static/([^/]+)/_buildManifest\\.js', html)
        if match:
            return match.group(1)

        return None

    def get_live_list_url(self):
        """Build the live channel JSON URL dynamically from current Next.js buildId."""
        try:
            resp = self.session.get(GEM_BASE_URL)
            if resp.status_code == 200:
                build_id = self.extract_build_id(resp.text)
                if build_id:
                    return LIST_URL_TEMPLATE.format(build_id)
                log('WARNING: Unable to find buildId in {} response'.format(GEM_BASE_URL), True)
            else:
                log('WARNING: {} returns status of {}'.format(GEM_BASE_URL, resp.status_code), True)
        except requests.RequestException as err:
            log('WARNING: Error fetching {}: {}'.format(GEM_BASE_URL, err), True)

        return LIST_URL_TEMPLATE.format(FALLBACK_BUILD_ID)

    def get_live_channels(self):
        """Get the list of live channels."""
        list_url = self.get_live_list_url()
        resp = self.session.get(list_url)

        if not resp.status_code == 200:
            log('ERROR: {} returns status of {}'.format(list_url, resp.status_code), True)
            return None

        data = json.loads(resp.content)
        page_data = data.get('pageProps', {}).get('data', {})
        streams = page_data.get('streams', [])
        free_tv_items = page_data.get('freeTv', {}).get('items', [])

        channels = []
        for stream in streams:
            items = stream.get('items', [])
            if len(items) == 0:
                continue

            for item in items:
                channel = dict(item)
                if 'title' not in channel or not channel['title']:
                    channel['title'] = stream.get('title')
                if 'genericImage' in channel and 'image' not in channel:
                    channel['image'] = channel['genericImage']
                channels.append(channel)

        for item in free_tv_items:
            channel = dict(item)
            if 'genericImage' in channel and 'image' not in channel:
                channel['image'] = channel['genericImage']
            channels.append(channel)

        unique_channels = []
        seen_ids = set()
        for channel in channels:
            id_media = channel.get('idMedia')

            if id_media is None:
                unique_channels.append(channel)
                continue

            if id_media in seen_ids:
                continue

            seen_ids.add(id_media)
            unique_channels.append(channel)

        return unique_channels

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
                'app_code': 'medianetlive',
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
        return GemV2.get_stream(id=id,app_code='medianetlive')

    def get_channel_metadata(self, id):
        url = f'https://services.radio-canada.ca/media/meta/v1/index.ashx?appCode=medianetlive&idMedia={id}&output=jsonObject'
        resp = self.session.get(url)
        if not resp.status_code == 200:
            log('ERROR: {} returns status of {}'.format(LIST_URL, resp.status_code), True)
            return None
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
