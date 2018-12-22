import requests
from urlparse import urljoin
import datetime
import time
import _strptime
import json
import re
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from resources.lib.helperobjects import helperobjects

class UrlToStreamService:

    _API_KEY = '3_qhEcPa5JGFROVwu5SWKqJ4mVOIkwlFNMSKwzPDAh8QZOtHqu6L4nD5Q7lk0eXOOG'
    _VUPLAY_API_URL = 'https://api.vuplay.co.uk'
    _LOGIN_URL = 'https://accounts.vrt.be/accounts.login'
    _TOKEN_GATEWAY_URL = 'https://token.vrt.be'

    def __init__(self, vrt_base, vrtnu_base_url, kodi_wrapper):
        self._kodi_wrapper = kodi_wrapper
        self._vrt_base = vrt_base
        self._vrtnu_base_url = vrtnu_base_url
        self._create_settings_dir()
        self._has_drm = self._check_drm()
        self._license_url = self._get_license_url()

    def _check_drm(self):
        return self._kodi_wrapper.check_inputstream_adaptive() and self._kodi_wrapper.check_widevine()

    def _get_license_url(self):
        return requests.get(self._VUPLAY_API_URL).json()['drm_providers']['widevine']['la_url']

    def _create_settings_dir(self):
        settingsdir = self._kodi_wrapper.get_userdata_path()
        if not self._kodi_wrapper.check_if_path_exists(settingsdir):
            self._kodi_wrapper.make_dir(settingsdir)

    def _get_new_playertoken(self, path, token_url, headers):
        playertoken = requests.post(token_url, headers=headers).json()
        json.dump(playertoken, open(path,'w'))
        return playertoken['vrtPlayerToken']

    def _get_cached_token(self, path, token_url=None, xvrttoken=None):
        token = json.loads(open(path, 'r').read())
        now = datetime.datetime.utcnow()
        exp = datetime.datetime(*(time.strptime(token['expirationDate'], '%Y-%m-%dT%H:%M:%S.%fZ')[0:6]))
        if exp > now:
            return token[token.keys()[0]]
        else:
            self._kodi_wrapper.delete_path(path)
            if 'XVRTToken' in path:
                return self._get_xvrttoken()
            else:
                return self._get_playertoken(token_url, xvrttoken)

    def _get_playertoken(self, token_url, xvrttoken=None):
        #on demand cache
        tokenfile = self._kodi_wrapper.get_userdata_path() + 'ondemand_vrtPlayerToken'
        if self._kodi_wrapper.check_if_path_exists(tokenfile):
            playertoken = self._get_cached_token(tokenfile, token_url, xvrttoken)
            return playertoken
        #live cache
        elif xvrttoken is None:
            tokenfile = self._kodi_wrapper.get_userdata_path() + 'live_vrtPlayerToken'
            if self._kodi_wrapper.check_if_path_exists(tokenfile):
                playertoken = self._get_cached_token(tokenfile, token_url, xvrttoken)
                return playertoken
            #renew live 
            else:
                headers = {'Content-Type': 'application/json'}
                return self._get_new_playertoken(tokenfile, token_url, headers)
        #renew on demand
        else:
            cookie_value = 'X-VRT-Token=' + xvrttoken
            headers = {'Content-Type': 'application/json', 'Cookie' : cookie_value}
            return self._get_new_playertoken(tokenfile, token_url, headers)

    def _get_new_xvrttoken(self, path):
        cred = helperobjects.Credentials(self._kodi_wrapper)
        if not cred.are_filled_in():
            self._kodi_wrapper.open_settings()
            cred.reload()
        data = {'loginID': cred.username, 'password': cred.password, 'APIKey': self._API_KEY, 'targetEnv': 'jssdk'}
        logon_json = requests.post(self._LOGIN_URL, data).json()
        if logon_json['errorCode'] == 0:
            login_token = logon_json['sessionInfo']['login_token']
            cookie_value = 'glt_'.join((self._API_KEY, '=', login_token))
            payload = {'uid': logon_json['UID'], 'uidsig': logon_json['UIDSignature'], 'ts': logon_json['signatureTimestamp'], 'email': cred.password}
            headers = {'Content-Type': 'application/json', 'Cookie': cookie_value}
            cookie_jar = requests.post(self._TOKEN_GATEWAY_URL, headers=headers, json=payload).cookies
            if 'X-VRT-Token' in cookie_jar:
                xvrttoken_cookie = cookie_jar._cookies['.vrt.be']['/']['X-VRT-Token']
                xvrttoken = { xvrttoken_cookie.name : xvrttoken_cookie.value, 'expirationDate' : datetime.datetime.fromtimestamp(xvrttoken_cookie.expires).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}
                json.dump(xvrttoken, open(path,'w'))
                return xvrttoken['X-VRT-Token']
            else:
                return self._get_new_xvrttoken(path)
        else:
            title = self._kodi_wrapper.get_localized_string(32051)
            message = self._kodi_wrapper.get_localized_string(32052)
            self._kodi_wrapper.show_ok_dialog(title, message)

    def _get_xvrttoken(self):
        tokenfile = self._kodi_wrapper.get_userdata_path() + 'XVRTToken'
        if self._kodi_wrapper.check_if_path_exists(tokenfile):
            xvrttoken = self._get_cached_token(tokenfile)
            return xvrttoken
        else:
            return self._get_new_xvrttoken(tokenfile)

    def _get_license_key(self, key_url, key_type='R', key_headers=None, key_value=None):
            """ Generates a propery license key value

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
            """

            header = ''
            if key_headers:
                for k, v in list(key_headers.items()):
                    header = ''.join((header, '&', k, '=', requests.utils.quote(v)))

            if key_type in ('A', 'R', 'B'):
                key_value = ''.join((key_type,'{SSM}'))
            elif key_type == 'D':
                if 'D{SSM}' not in key_value:
                    raise ValueError('Missing D{SSM} placeholder')
                key_value = requests.utils.quote(key_value)

            return ''.join((key_url, '|', header.strip('&'), '|', key_value, '|'))


    def get_stream_from_url(self, url):
        url = urljoin(self._vrt_base, url)
        html_page = requests.get(url).text
        strainer = SoupStrainer('div', {'class': 'cq-dd-vrtvideo'})
        soup = BeautifulSoup(html_page, 'html.parser', parse_only=strainer)
        video_data = soup.find(lambda tag: tag.name == 'div' and tag.get('class') == ['vrtvideo']).attrs
        client = video_data['data-client']
        media_api_url = video_data['data-mediaapiurl']
        if 'data-videoid' in video_data.keys():
            video_id = video_data['data-videoid']
            xvrttoken = self._get_xvrttoken()
        else:
            video_id = video_data['data-livestream']
            xvrttoken = None
        if 'data-publicationid' in video_data.keys():
            publication_id = video_data['data-publicationid'] + requests.utils.quote('$')
        else:
            publication_id = ''
        token_url = media_api_url + '/tokens'
        playertoken = self._get_playertoken(token_url, xvrttoken) 
        url = ''.join((media_api_url, '/videos/', publication_id, video_id, '?vrtPlayerToken=', playertoken, '&client=', client))
        video_json = requests.get(url).json()
        try:
            vudrm_token = video_json['drm']
            target_urls = video_json['targetUrls']
            stream_dict = {}
            for stream in target_urls:
                stream_dict[stream['type']] = stream['url']
            return self._select_stream(stream_dict, vudrm_token)
        except KeyError as error:
            self._kodi_wrapper.show_ok_dialog('', video_json['message'])

    def _select_stream(self, stream_dict, vudrm_token):        
        if vudrm_token:
            if self._has_drm and self._kodi_wrapper.get_setting('usedrm') == 'true':
                encryption_json = '{{"token":"{0}","drm_info":[D{{SSM}}],"kid":"{{KID}}"}}'.format(vudrm_token)
                license_key = self._get_license_key(key_url=self._license_url, key_type='D', key_value=encryption_json, key_headers={'Content-Type': 'text/plain;charset=UTF-8'})
                return helperobjects.StreamURLS(stream_dict['mpeg_dash'], license_key=license_key)
            else:
                return helperobjects.StreamURLS(*self._select_hls_substreams(stream_dict['hls_aes']))
        else:
            if self._kodi_wrapper.check_inputstream_adaptive():
                return helperobjects.StreamURLS(stream_dict['mpeg_dash'])
            else:
                return helperobjects.StreamURLS(*self._select_hls_substreams(stream_dict['hls']))

    #speed up hls selection, workaround for slower kodi selection
    def _select_hls_substreams(self, master_hls_url):
        base_url = master_hls_url.split('.m3u8')[0]
        m3u8 = requests.get(master_hls_url).text
        stream_regex = re.compile(r'#EXT-X-STREAM-INF:[\w\-=,\.\"]+[\r\n]{1}([\w\-=]+\.m3u8)[\r\n]{2}')
        direct_stream_url = None
        direct_subtitle_url = None
        match_stream = re.search(stream_regex, m3u8)
        if match_stream:
            direct_stream_url = base_url + match_stream.group(1)
        if self._kodi_wrapper.get_setting('showsubtitles') == 'true':
            subtitle_regex = re.compile(r'#EXT-X-MEDIA:TYPE=SUBTITLES[\w\-=,\.\"\/]+URI=\"([\w\-=]+)\.m3u8\"')
            match_sub = re.search(subtitle_regex, m3u8)
            if match_sub and '/live/' not in master_hls_url:
                direct_subtitle_url = ''.join((base_url, match_sub.group(1), '.webvtt'))
        return direct_stream_url, direct_subtitle_url
