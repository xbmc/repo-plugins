# -*- coding: utf-8 -*-
""" VTM GO Stream API """

from __future__ import absolute_import, division, unicode_literals

import json
import random
from datetime import timedelta

import requests

from resources.lib.kodiwrapper import from_unicode, LOG_DEBUG, LOG_ERROR


class StreamGeoblockedException(Exception):
    """ Is thrown when a geoblocked item is played. """


class StreamUnavailableException(Exception):
    """ Is thrown when an unavailable item is played. """


class ResolvedStream:
    """ Defines a stream that we can play"""

    def __init__(self, program=None, program_id=None, title=None, duration=None, url=None, license_url=None, subtitles=None, cookies=None):
        """
        :type program: str|None
        :type program_id: int|None
        :type title: str
        :type duration: str|None
        :type url: str
        :type license_url: str
        :type subtitles: list[str]
        :type cookies: dict
        """
        self.program = program
        self.program_id = program_id
        self.title = title
        self.duration = duration
        self.url = url
        self.license_url = license_url
        self.subtitles = subtitles
        self.cookies = cookies

    def __repr__(self):
        return "%r" % self.__dict__


class VtmGoStream:
    """ VTM GO Stream API """

    _VTM_API_KEY = 'zTxhgTEtb055Ihgw3tN158DZ0wbbaVO86lJJulMl'
    _ANVATO_API_KEY = 'HOydnxEYtxXYY1UfT3ADuevMP7xRjPg6XYNrPLhFISL'
    _ANVATO_USER_AGENT = 'ANVSDK Android/5.0.39 (Linux; Android 6.0.1; Nexus 5)'

    def __init__(self, kodi):
        """ Initialise object
        :type kodi: resources.lib.kodiwrapper.KodiWrapper
        """
        self._kodi = kodi

        self._session = requests.session()

    def get_stream(self, stream_type, stream_id):
        """ Return a ResolvedStream based on the stream type and id.
        :type stream_type: str
        :type stream_id: str
        :rtype ResolvedStream
        """
        # We begin with asking vtm about the stream info.
        stream_info = self._get_stream_info(stream_type, stream_id)

        # Extract the anvato stream from our stream_info.
        anvato_info = self._extract_anvato_stream_from_stream_info(stream_info)

        # Ask the anvacks to know where we have to send our requests. (This is hardcoded for now)
        # anv_acks = self._anvato_get_anvacks(anvato_info.get('accessKey'))

        # Get the server time. (We don't seem to need this)
        # server_time = self._anvato_get_server_time(anvato_info.get('accessKey'))

        # Send a request for the stream info.
        anvato_stream_info = self._anvato_get_stream_info(anvato_info=anvato_info, stream_info=stream_info)

        # Get published urls.
        url = anvato_stream_info['published_urls'][0]['embed_url']
        license_url = anvato_stream_info['published_urls'][0]['license_url']

        # Get MPEG DASH manifest url.
        json_manifest = self._download_manifest(url)
        url = json_manifest.get('master_m3u8')

        # Follow Location tag redirection because InputStream Adaptive doesn't support this yet.
        # https://github.com/peak3d/inputstream.adaptive/issues/286
        url = self._redirect_manifest(url)

        # Extract subtitles from our stream_info.
        subtitles = self._extract_subtitles_from_stream_info(stream_info)

        # Delay subtitles taking into account advertisements breaks.
        if subtitles:
            subtitles = self._delay_subtitles(subtitles, json_manifest)

        if stream_type == 'episodes':
            # TV episode
            return ResolvedStream(
                program=stream_info['video']['metadata']['program']['title'],
                program_id=stream_info['video']['metadata']['program']['id'],
                title=stream_info['video']['metadata']['title'],
                duration=stream_info['video']['duration'],
                url=url,
                subtitles=subtitles,
                license_url=license_url,
                cookies=self._session.cookies.get_dict()
            )

        if stream_type in ['movies', 'oneoffs']:
            # Movie or one-off programs
            return ResolvedStream(
                program=None,
                title=stream_info['video']['metadata']['title'],
                duration=stream_info['video']['duration'],
                url=url,
                subtitles=subtitles,
                license_url=license_url,
                cookies=self._session.cookies.get_dict()
            )

        if stream_type == 'channels':
            # Live TV
            if stream_info['video']['metadata']['videoType'] == 'episode':
                program = stream_info['video']['metadata']['program']['title']
            else:
                program = None

            return ResolvedStream(
                program=program,
                title=stream_info['video']['metadata']['title'],
                duration=None,
                url=url,
                subtitles=subtitles,
                license_url=license_url,
                cookies=self._session.cookies.get_dict()
            )

        raise Exception('Unknown video type {type}'.format(type=stream_type))

    def _get_stream_info(self, strtype, stream_id):
        """ Get the stream info for the specified stream.
        :type strtype: str
        :type stream_id: str
        :rtype: dict
        """
        url = 'https://videoplayer-service.api.persgroep.cloud/config/%s/%s' % (strtype, stream_id)
        self._kodi.log('Getting stream info from {url}', url=url)
        response = self._session.get(url,
                                     params={
                                         'startPosition': '0.0',
                                         'autoPlay': 'true',
                                     },
                                     headers={
                                         'x-api-key': self._VTM_API_KEY,
                                         'Popcorn-SDK-Version': '2',
                                         'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 6.0.1; Nexus 5 Build/M4B30Z)',
                                     },
                                     proxies=self._kodi.get_proxies())

        self._kodi.log('Got response: {response}', LOG_DEBUG, response=response.text)

        if response.status_code == 403:
            error = json.loads(response.text)
            if error['type'] == 'videoPlaybackGeoblocked':
                raise StreamGeoblockedException()
            if error['type'] == 'serviceError':
                raise StreamUnavailableException()

        if response.status_code == 404:
            raise StreamUnavailableException()

        if response.status_code != 200:
            raise StreamUnavailableException()

        info = json.loads(response.text)
        return info

    def _extract_anvato_stream_from_stream_info(self, stream_info):
        """ Extract the anvato stream details.
        :type stream_info: dict
        :rtype dict
        """
        # Loop over available streams, and return the one from anvato
        if stream_info.get('video'):
            for stream in stream_info.get('video').get('streams'):
                if stream.get('type') == 'anvato':
                    return stream.get('anvato')
        elif stream_info.get('code'):
            self._kodi.log('VTM GO Videoplayer service API error: {type}', LOG_ERROR, type=stream_info.get('type'))
        raise Exception('No stream found that we can handle')

    def _extract_subtitles_from_stream_info(self, stream_info):
        """ Extract a list of the subtitles.
        :type stream_info: dict
        :rtype list[str]
        """
        subtitles = list()
        if stream_info.get('video').get('subtitles'):
            for subtitle in stream_info.get('video').get('subtitles'):
                subtitles.append(subtitle.get('url'))
                self._kodi.log('Found subtitle url {url}', url=subtitle.get('url'))
        return subtitles

    @staticmethod
    def _delay_webvtt_timing(match, ad_breaks):
        """ Delay the timing of a webvtt subtitle.
        :type match: any
        :type ad_breaks: list[dict]
        :rtype str
        """
        sub_timings = list()
        for timestamp in match.groups():
            hours, minutes, seconds, millis = (int(x) for x in [timestamp[:-10], timestamp[-9:-7], timestamp[-6:-4], timestamp[-3:]])
            sub_timings.append(timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=millis))
        for ad_break in ad_breaks:
            # time format: seconds.fraction or seconds
            ad_break_start = timedelta(milliseconds=ad_break.get('start') * 1000)
            ad_break_duration = timedelta(milliseconds=ad_break.get('duration') * 1000)
            if ad_break_start < sub_timings[0]:
                for idx, item in enumerate(sub_timings):
                    sub_timings[idx] += ad_break_duration
        for idx, item in enumerate(sub_timings):
            hours, remainder = divmod(item.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            millis = item.microseconds // 1000
            sub_timings[idx] = '%02d:%02d:%02d,%03d' % (hours, minutes, seconds, millis)
        delayed_webvtt_timing = '\n{} --> {} '.format(sub_timings[0], sub_timings[1])
        return delayed_webvtt_timing

    def _delay_subtitles(self, subtitles, json_manifest):
        """ Modify the subtitles timings to account for ad breaks.
        :type subtitles: list[string]
        :type json_manifest: dict
        :rtype list[str]
        """
        import re
        temp_dir = self._kodi.get_userdata_path() + 'temp/'
        if not self._kodi.check_if_path_exists(temp_dir):
            self._kodi.mkdir(temp_dir)
        else:
            dirs, files = self._kodi.listdir(temp_dir)  # pylint: disable=unused-variable
            if files:
                for item in files:
                    if item.endswith('.vtt'):
                        self._kodi.delete_file(temp_dir + item)
        ad_breaks = list()
        delayed_subtitles = list()
        webvtt_timing_regex = re.compile(r'\n(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})\s')

        # Get advertising breaks info from json manifest
        cues = json_manifest.get('interstitials').get('cues')
        for cue in cues:
            ad_breaks.append(
                dict(start=cue.get('start'), duration=cue.get('break_duration'))
            )

        for subtitle in subtitles:
            output_file = temp_dir + '/' + subtitle.split('/')[-1].split('.')[0] + '.nl-NL.' + subtitle.split('.')[-1]
            webvtt_content = requests.get(subtitle).text
            webvtt_content = webvtt_timing_regex.sub(lambda match: self._delay_webvtt_timing(match, ad_breaks), webvtt_content)
            with self._kodi.open_file(output_file, 'w') as webvtt_output:
                webvtt_output.write(from_unicode(webvtt_content))
            delayed_subtitles.append(output_file)
        return delayed_subtitles

    def _anvato_get_anvacks(self, access_key):
        """ Get the anvacks from anvato. (not needed)
        :type access_key: string
        :rtype dict
        """
        url = 'https://access-prod.apis.anvato.net/anvacks/{key}'.format(key=access_key)
        self._kodi.log('Getting anvacks from {url}', url=url)
        response = self._session.get(url,
                                     params={
                                         'apikey': self._ANVATO_API_KEY,
                                     },
                                     headers={
                                         'X-Anvato-User-Agent': self._ANVATO_USER_AGENT,
                                         'User-Agent': self._ANVATO_USER_AGENT,
                                     })

        if response.status_code != 200:
            raise Exception('Error %s in _anvato_get_anvacks.' % response.status_code)

        info = json.loads(response.text)
        return info

    def _anvato_get_server_time(self, access_key):
        """ Get the server time from anvato. (not needed)
        :type access_key: string
        :rtype dict
        """
        url = 'https://tkx.apis.anvato.net/rest/v2/server_time'
        self._kodi.log('Getting servertime from {url} with access_key {access_key}', url=url, access_key=access_key)
        response = self._session.get(url,
                                     params={
                                         'anvack': access_key,
                                         'anvtrid': self._generate_random_id(),
                                     },
                                     headers={
                                         'X-Anvato-User-Agent': self._ANVATO_USER_AGENT,
                                         'User-Agent': self._ANVATO_USER_AGENT,
                                     })
        if response.status_code != 200:
            raise Exception('Error %s.' % response.status_code)

        info = json.loads(response.text)
        return info

    def _anvato_get_stream_info(self, anvato_info, stream_info):
        """ Get the stream info from anvato.
        :type anvato_info: dict
        :type stream_info: dict
        :rtype dict
        """
        url = 'https://tkx.apis.anvato.net/rest/v2/mcp/video/{video}'.format(**anvato_info)
        self._kodi.log('Getting stream info from {url} with access_key {access_key} and token {token}', url=url, access_key=anvato_info['accessKey'],
                       token=anvato_info['token'])

        response = self._session.post(url,
                                      json={
                                          "ads": {
                                              "freewheel": {
                                                  "custom": {
                                                      "ml_userid": "",  # TODO: fill in
                                                      "ml_dmp_userid": "",  # TODO: fill in
                                                      "ml_gdprconsent": "",
                                                      "ml_apple_advertising_id": "",
                                                      "ml_google_advertising_id": "",
                                                  },
                                                  "network_id": stream_info['video']['ads']['freewheel']['networkId'],
                                                  "profile_id": stream_info['video']['ads']['freewheel']['profileId'],
                                                  "server_url": stream_info['video']['ads']['freewheel']['serverUrl'],
                                                  "site_section_id": "mdl_vtmgo_phone_android_default",
                                                  "video_asset_id": stream_info['video']['ads']['freewheel'].get('assetId', ''),
                                              }
                                          },
                                          "api": {
                                              "anvstk2": anvato_info['token']
                                          },
                                          "content": {
                                              "mcp_video_id": anvato_info['video'],
                                          },
                                          "sdkver": "5.0.39",
                                          "user": {
                                              "adobepass": {
                                                  "err_msg": "",
                                                  "maxrating": "",
                                                  "mvpd": "",
                                                  "resource": "",
                                                  "short_token": ""
                                              },
                                              "device": "android",
                                              "device_id": "",
                                          },
                                          "version": "3.0"
                                      },
                                      params={
                                          'anvack': anvato_info['accessKey'],
                                          'anvtrid': self._generate_random_id(),
                                          'rtyp': 'fp',
                                      },
                                      headers={
                                          'X-Anvato-User-Agent': self._ANVATO_USER_AGENT,
                                          'User-Agent': self._ANVATO_USER_AGENT,
                                      })

        self._kodi.log('Got response: {response}', LOG_DEBUG, response=response.text)

        if response.status_code != 200:
            raise Exception('Error %s.' % response.status_code)

        import re
        matches = re.search(r"^anvatoVideoJSONLoaded\((.*)\)$", response.text)
        if not matches:
            raise Exception('Could not parse media info')
        info = json.loads(matches.group(1))
        return info

    @staticmethod
    def _generate_random_id(length=32):
        """ Generate a random id.
        :type length: int
        :rtype str
        """
        letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        return ''.join(random.choice(letters) for i in range(length))

    def _download_text(self, url):
        """ Download a file as text.
        :type url: str
        :rtype str
        """
        self._kodi.log('Downloading text from {url}', url=url)
        response = self._session.get(url,
                                     headers={
                                         'X-Anvato-User-Agent': self._ANVATO_USER_AGENT,
                                         'User-Agent': self._ANVATO_USER_AGENT,
                                     })
        if response.status_code != 200:
            raise Exception('Error %s.' % response.status_code)

        return response.text

    def _download_manifest(self, url):
        """ Download the MPEG DASH manifest.
        :type url: str
        :rtype dict
        """
        download = self._download_text(url)
        try:
            decoded = json.loads(download)
            if decoded.get('master_m3u8'):
                self._kodi.log('Followed redirection from {url_from} to {url_to}', url_from=url, url_to=decoded.get('master_m3u8'))
                return decoded
        except ValueError:
            self._kodi.log('No manifest url found {url}', LOG_ERROR, url=url)

        # Fallback to the url like we have it
        return dict(master_m3u8=url)

    def _redirect_manifest(self, url):
        """ Follow the Location tag if it is found.
        :type url: str
        :rtype str
        """
        import re
        # Follow when a <Location>url</Location> tag is found.
        # https://github.com/peak3d/inputstream.adaptive/issues/286
        download = self._download_text(url)
        matches = re.search(r"<Location>([^<]+)</Location>", download)
        if matches:
            self._kodi.log('Followed redirection from {url_from} to {url_to}', url_from=url, url_to=matches.group(1))
            return matches.group(1)

        # Fallback to the url like we have it
        return url

    @staticmethod
    def create_license_key(key_url, key_type='R', key_headers=None, key_value=None):
        """ Create a license key string that we need for inputstream.adaptive.
        :type key_url: str
        :type key_type: str
        :type key_headers: dict[str, str]
        :type key_value: str
        :rtype str
        """
        try:  # Python 3
            from urllib.parse import urlencode, quote
        except ImportError:  # Python 2
            from urllib import urlencode, quote

        header = ''
        if key_headers:
            header = urlencode(key_headers)

        if key_type in ('A', 'R', 'B'):
            key_value = key_type + '{SSM}'
        elif key_type == 'D':
            if 'D{SSM}' not in key_value:
                raise ValueError('Missing D{SSM} placeholder')
            key_value = quote(key_value)

        return '%s|%s|%s|' % (key_url, header, key_value)
