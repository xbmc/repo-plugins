import xbmcgui
import requests
import xbmc
import json
import cookielib
import urlparse
import os
from resources.lib.helperobjects import helperobjects


class UrlToStreamService:

    _API_KEY ="3_qhEcPa5JGFROVwu5SWKqJ4mVOIkwlFNMSKwzPDAh8QZOtHqu6L4nD5Q7lk0eXOOG"
    _BASE_GET_STREAM_URL_PATH = "https://mediazone.vrt.be/api/v1/vrtvideo/assets/"

    def __init__(self, vrt_base, vrtnu_base_url, addon):
        self._vrt_base = vrt_base
        self._vrtnu_base_url = vrtnu_base_url
        self._addon = addon
        self._session = requests.session()

    def get_stream_from_url(self, url):
        cred = helperobjects.Credentials(self._addon)
        if not cred.are_filled_in():
            self._addon.openSettings()
            cred.reload()
        url = urlparse.urljoin(self._vrt_base, url)
        r = self._session.post("https://accounts.eu1.gigya.com/accounts.login",
                               {'loginID': cred.username, 'password': cred.password, 'APIKey': self._API_KEY,
                                'targetEnv': 'jssdk',
                                'includeSSOToken': 'true',
                                'authMode': 'cookie'})

        logon_json = r.json()
        if logon_json['errorCode'] == 0:
            uid = logon_json['UID']
            sig = logon_json['UIDSignature']
            ts = logon_json['signatureTimestamp']

            headers = {'Content-Type': 'application/json', 'Referer': self._vrtnu_base_url}
            data = '{"uid": "%s", ' \
                   '"uidsig": "%s", ' \
                   '"ts": "%s", ' \
                   '"email": "%s"}' % (uid, sig, ts, cred.username)

            response = self._session.post("https://token.vrt.be", data=data, headers=headers)
            securevideo_url = "{0}.securevideo.json".format(self.__cut_slash_if_present(url))
            securevideo_response = self._session.get(securevideo_url, cookies=response.cookies)
            json = securevideo_response.json()

            mzid = list(json
                        .values())[0]['mzid']
            final_url = urlparse.urljoin(self._BASE_GET_STREAM_URL_PATH, mzid)

            stream_response = self._session.get(final_url)
            hls = self.__get_hls(stream_response.json()['targetUrls']).replace("https", "http")
            subtitle = None
            if self._addon.getSetting("showsubtitles") == "true":
                subtitle = self.__get_subtitle(stream_response.json()['subtitleUrls'])
            return helperobjects.StreamURLS(hls, subtitle)
        else:
            xbmcgui.Dialog().ok(self._addon.getAddonInfo('name'),
                                self._addon.getLocalizedString(32051),
                                self._addon.getLocalizedString(32052))

    @staticmethod
    def __get_hls(dictionary):
        for item in dictionary:
            if item['type'] == 'HLS':
                return item['url']

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
