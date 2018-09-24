import requests
import json
import cookielib
import urlparse
import os
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from resources.lib.helperobjects import helperobjects


class UrlToStreamService:

    _API_KEY ='3_qhEcPa5JGFROVwu5SWKqJ4mVOIkwlFNMSKwzPDAh8QZOtHqu6L4nD5Q7lk0eXOOG'
    _BASE_MEDIA_SERVICE_URL = 'https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1'
    _TOKEN_URL = _BASE_MEDIA_SERVICE_URL + '/tokens'
    _STREAM_URL_PATH = _BASE_MEDIA_SERVICE_URL + '/videos/{}%24{}?vrtPlayerToken={}'

    def __init__(self, vrt_base, vrtnu_base_url, kodi_wrapper):
        self._vrt_base = vrt_base
        self._vrtnu_base_url = vrtnu_base_url
        self._kodi_wrapper = kodi_wrapper

    def get_stream_from_url(self, url):
        session = requests.session()
        cred = helperobjects.Credentials(self._kodi_wrapper)
        if not cred.are_filled_in():
            self._kodi_wrapper.open_settings()
            cred.reload()
        url = urlparse.urljoin(self._vrt_base, url)
        r = session.post('https://accounts.vrt.be/accounts.login',
                               {'loginID': cred.username, 'password': cred.password, 'APIKey': self._API_KEY,
                                'sessionExpiration': '-1',
                                'targetEnv': 'jssdk',
                                'include': 'profile,data,emails,subscriptions,preferences,',
                                'includeUserInfo': 'true',
                                'loginMode': 'standard',
                                'lang': 'nl-inf',
                                'source': 'showScreenSet',
                                'sdk': 'js_latest',
                                'authMode': 'cookie',
                                'format': 'json'})

        session.get('https://token.vrt.be/vrtnuinitlogin?provider=site&destination=https://www.vrt.be/vrtnu/')

        logon_json = r.json()

        if logon_json['errorCode'] == 0:
            uid = logon_json['UID']
            sig = logon_json['UIDSignature']
            ts = logon_json['signatureTimestamp']

            data = {'UID': uid, 
                   'UIDSignature': sig,
                   'signatureTimestamp': ts ,
                   'client_id': 'vrtnu-site', 
                   'submit': 'submit'
                   } 

            response = session.post('https://login.vrt.be/perform_login', data=data)

            vrt_player_token_url = session.post(self._TOKEN_URL, headers={'Content-Type': 'application/json'})

            token = vrt_player_token_url.json()['vrtPlayerToken']

            url_response = session.get(url);
            strainer = SoupStrainer('div', {'class': 'vrtvideo videoplayer'})
            soup = BeautifulSoup(url_response.content, 'html.parser', parse_only=strainer)
            vrt_video = soup.find(lambda tag: tag.name == 'div' and tag.get('class') == ['vrtvideo'])
            
            data_publication_id = vrt_video['data-publicationid']
            data_video_id = vrt_video['data-videoid']
            final_url = self._STREAM_URL_PATH.format(data_publication_id, data_video_id, token)

            stream_response = session.get(final_url)
            hls = self.__get_hls(stream_response.json()['targetUrls'])
            subtitle = None
            #if self._kodi_wrapper.get_setting('showsubtitles') == 'true':
            #    subtitle = self.__get_subtitle(stream_response.json()['subtitleUrls'])
            return helperobjects.StreamURLS(hls, subtitle)
        else:
            title = self._kodi_wrapper.get_localized_string(32051)
            message = self._kodi_wrapper.get_localized_string(32052)
            self._kodi_wrapper.show_ok_dialog(title, message)

    @staticmethod
    def __get_hls(dictionary):
        hls_url = None
        hls_aes_url = None
        for item in dictionary:
            if item['type'] == 'hls_aes':
                hls_aes_url = item['url']
                break
            if item['type'] == 'hls':
                hls_url = item['url']
        return (hls_aes_url or hls_url).replace('remix.aka', 'remix-aka')

    @staticmethod
    def __get_subtitle(dictionary):
        for item in dictionary:
            if item['type'] == 'CLOSED':
                return item['url']

    @staticmethod
    def __cut_slash_if_present(url):
        if url.endswith('/'):
            return url[:-1]
        else:
            return url
