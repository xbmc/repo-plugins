# -*- coding: utf-8 -*-

# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)

import re
import requests
from bs4 import BeautifulSoup, SoupStrainer

from resources.lib.helperobjects import apidata, streamurls


class StreamService:

    _VUPLAY_API_URL = 'https://api.vuplay.co.uk'
    _VUALTO_API_URL = 'https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1'
    _CLIENT = 'vrtvideo'


    def __init__(self, vrt_base, vrtnu_base_url, kodi_wrapper, token_resolver):
        self._kodi_wrapper = kodi_wrapper
        self._proxies = self._kodi_wrapper.get_proxies()
        self.token_resolver = token_resolver
        self._vrt_base = vrt_base
        self._vrtnu_base_url = vrtnu_base_url
        self._create_settings_dir()
        self._can_play_drm = self._kodi_wrapper.can_play_widevine() and self._kodi_wrapper.has_inputstream_adaptive_installed()
        self._license_url = self._get_license_url()

    def _get_license_url(self):
        return requests.get(self._VUPLAY_API_URL, proxies=self._proxies).json()['drm_providers']['widevine']['la_url']

    def _create_settings_dir(self):
        settingsdir = self._kodi_wrapper.get_userdata_path()
        if not self._kodi_wrapper.check_if_path_exists(settingsdir):
            self._kodi_wrapper.make_dir(settingsdir)

    def _get_license_key(self, key_url, key_type='R', key_headers=None, key_value=None):
        ''' Generates a propery license key value

            # A{SSM} -> not implemented
            # R{SSM} -> raw format
            # B{SSM} -> base64 format
            # D{SSM} -> decimal format

            The generic format for a LicenseKey is:
            |<url>|<headers>|<key with placeholders|

            The Widevine Decryption Key Identifier (KID) can be inserted via the placeholder {KID}

            @type key_url: str
            @param key_url: the URL where the license key can be obtained

            @type key_type: str
            @param key_type: the key type (A, R, B or D)

            @type key_headers: dict
            @param key_headers: A dictionary that contains the HTTP headers to pass

            @type key_value: str
            @param key_value: i
            @return:
        '''
        header = ''
        if key_headers:
            for k, v in list(key_headers.items()):
                header = ''.join((header, '&', k, '=', requests.utils.quote(v)))

        if key_type in ('A', 'R', 'B'):
            key_value = ''.join((key_type, '{SSM}'))
        elif key_type == 'D':
            if 'D{SSM}' not in key_value:
                raise ValueError('Missing D{SSM} placeholder')
            key_value = requests.utils.quote(key_value)

        return ''.join((key_url, '|', header.strip('&'), '|', key_value, '|'))

    def _get_api_data(self, video_url):
        html_page = requests.get(video_url, proxies=self._proxies).text
        strainer = SoupStrainer('div', {'class': 'cq-dd-vrtvideo'})
        soup = BeautifulSoup(html_page, 'html.parser', parse_only=strainer)
        video_data = soup.find(lambda tag: tag.name == 'div' and tag.get('class') == ['vrtvideo']).attrs
        is_live_stream = False
        xvrttoken = None

        # Store required data attributes
        client = video_data['data-client']
        media_api_url = video_data['data-mediaapiurl']
        if 'data-videoid' in video_data.keys():
            video_id = video_data['data-videoid']
            xvrttoken = self.token_resolver.get_xvrttoken()
        else:
            video_id = video_data['data-livestream']
            is_live_stream = True
        publication_id = ''
        if 'data-publicationid' in video_data.keys():
            publication_id = video_data['data-publicationid'] + requests.utils.quote('$')
        return apidata.ApiData(client, media_api_url, video_id, publication_id, xvrttoken, is_live_stream)

    def _get_video_json(self, api_data):
        token_url = api_data.media_api_url + '/tokens'
        if api_data.is_live_stream:
            playertoken = self.token_resolver.get_live_playertoken(token_url, api_data.xvrttoken)
        else:
            playertoken = self.token_resolver.get_ondemand_playertoken(token_url, api_data.xvrttoken)

        # Construct api_url and get video json
        api_url = api_data.media_api_url + '/videos/' + api_data.publication_id + \
            api_data.video_id + '?vrtPlayerToken=' + playertoken + '&client=' + api_data.client
        video_json = requests.get(api_url, proxies=self._proxies).json()

        return video_json

    def _handle_error(self, video_json):
        self._kodi_wrapper.log_error(video_json['message'])
        message = self._kodi_wrapper.get_localized_string(32054)
        self._kodi_wrapper.show_ok_dialog('', message)

    def get_stream(self, video, retry=False, api_data=None):
        self._kodi_wrapper.log_notice('video_url ' + video['video_url'])
        if video['video_id'] is not None and video['publication_id'] is not None and retry is False:
            xvrttoken = self.token_resolver.get_xvrttoken()
            api_data = apidata.ApiData(self._CLIENT, self._VUALTO_API_URL, video['video_id'], video['publication_id'] + requests.utils.quote('$'), xvrttoken, False)
        else:
            api_data = api_data or self._get_api_data(video['video_url'])
        vudrm_token = None
        video_json = self._get_video_json(api_data)

        if 'drm' in video_json:
            vudrm_token = video_json['drm']
            target_urls = video_json['targetUrls']
            stream_dict = dict(list(map(lambda x: (x['type'], x['url']), target_urls)))
            return self._select_stream(stream_dict, vudrm_token)

        if video_json['code'] == 'INVALID_LOCATION' or video_json['code'] == 'INCOMPLETE_ROAMING_CONFIG':
            self._kodi_wrapper.log_notice(video_json['message'])
            roaming_xvrttoken = self.token_resolver.get_xvrttoken(True)
            if not retry and roaming_xvrttoken is not None:
                # Delete cached playertokens
                if api_data.is_live_stream:
                    self._kodi_wrapper.delete_path(self._kodi_wrapper.get_userdata_path() + 'live_vrtPlayerToken')
                else:
                    self._kodi_wrapper.delete_path(self._kodi_wrapper.get_userdata_path() + 'ondemand_vrtPlayerToken')
                # Update api_data with roaming_xvrttoken and try again
                api_data.xvrttoken = roaming_xvrttoken
                return self.get_stream(video, retry=True, api_data=api_data)
            message = self._kodi_wrapper.get_localized_string(32053)
            self._kodi_wrapper.show_ok_dialog('', message)
        else:
            self._handle_error(video_json)

        return None

    def _try_get_drm_stream(self, stream_dict, vudrm_token):
        protocol = "mpeg_dash"
        encryption_json = '{{"token":"{0}","drm_info":[D{{SSM}}],"kid":"{{KID}}"}}'.format(vudrm_token)
        license_key = self._get_license_key(key_url=self._license_url,
                                            key_type='D',
                                            key_value=encryption_json,
                                            key_headers={'Content-Type': 'text/plain;charset=UTF-8'})
        return streamurls.StreamURLS(stream_dict[protocol], license_key=license_key, use_inputstream_adaptive=True) if protocol in stream_dict else None

    def _select_stream(self, stream_dict, vudrm_token):
        stream_url = None
        protocol = None
        if vudrm_token and self._can_play_drm and self._kodi_wrapper.get_setting('usedrm') == 'true':
            protocol = 'mpeg_dash drm'
            self._kodi_wrapper.log_notice('protocol: ' + protocol)
            stream_url = self._try_get_drm_stream(stream_dict, vudrm_token)

        if vudrm_token and stream_url is None:
            protocol = 'hls_aes'
            self._kodi_wrapper.log_notice('protocol: ' + protocol)
            stream_url = streamurls.StreamURLS(*self._select_hls_substreams(stream_dict[protocol])) if protocol in stream_dict else None

        if self._kodi_wrapper.has_inputstream_adaptive_installed() and stream_url is None:
            protocol = 'mpeg_dash'
            self._kodi_wrapper.log_notice('protocol: ' + protocol)
            stream_url = streamurls.StreamURLS(stream_dict[protocol], use_inputstream_adaptive=True) if protocol in stream_dict else None

        if stream_url is None:
            protocol = 'hls'
            self._kodi_wrapper.log_notice('protocol: ' + protocol)
            # No if-else statement because this is the last resort stream selection
            stream_url = streamurls.StreamURLS(*self._select_hls_substreams(stream_dict[protocol]))

        return stream_url

    # Speed up HLS selection, workaround for slower kodi selection
    def _select_hls_substreams(self, master_hls_url):
        base_url = master_hls_url.split('.m3u8')[0]
        m3u8 = requests.get(master_hls_url, proxies=self._proxies).text
        direct_audio_url = None
        direct_video_url = None
        direct_subtitle_url = None

        # Get audio uri
        audio_regex = re.compile(r'#EXT-X-MEDIA:TYPE=AUDIO[\w\-=,\.\"\/]+URI=\"([\w\-=]+)\.m3u8\"')
        match_audio = re.findall(audio_regex, m3u8)
        if match_audio:
            direct_audio_url = match_audio[len(match_audio)-1]

        # Get video uri
        video_regex = re.compile(r'#EXT-X-STREAM-INF:[\w\-=,\.\"]+[\r\n]{1}([\w\-=]+\.m3u8(\?vbegin=[0-9]{10})?(&vend=[0-9]{10})?)[\r\n]{2}')
        match_video = re.search(video_regex, m3u8)
        if match_video:
            direct_video_url = base_url + match_video.group(1)

        # Get subtitle uri
        if self._kodi_wrapper.get_setting('showsubtitles') == 'true':
            subtitle_regex = re.compile(r'#EXT-X-MEDIA:TYPE=SUBTITLES[\w\-=,\.\"\/]+URI=\"([\w\-=]+)\.m3u8\"')
            match_sub = re.search(subtitle_regex, m3u8)
            if match_sub and '/live/' not in master_hls_url:
                direct_subtitle_url = ''.join((base_url, match_sub.group(1), '.webvtt'))

        # Merge audio and video uri
        if direct_audio_url is not None:
            direct_video_url = ''.join((base_url, direct_audio_url, '-', direct_video_url.split('-')[-1]))

        return direct_video_url, direct_subtitle_url
