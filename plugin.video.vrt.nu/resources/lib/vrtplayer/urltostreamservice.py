import requests
import json
import cookielib
import urlparse
import os
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from resources.lib.helperobjects import helperobjects
from resources.lib.vrtplayer import streamservice


class UrlToStreamService(streamservice.StreamService):

    def __init__(self, vrt_base, vrtnu_base_url, kodi_wrapper):
        super(UrlToStreamService, self).__init__(kodi_wrapper)
        self._vrt_base = vrt_base
        self._vrtnu_base_url = vrtnu_base_url
        self._STREAM_URL_PATH = super(UrlToStreamService, self)._BASE_MEDIA_SERVICE_URL + '/videos/{}%24{}?vrtPlayerToken={}'

    def get_stream_from_url(self, url):
        (session, token) = super(UrlToStreamService, self)._get_session_and_token_from_()
        if token is not None:
            url = urlparse.urljoin(self._vrt_base, url)
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
