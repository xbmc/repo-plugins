# -*- coding: utf-8 -*-
""" VTM GO Stream API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
import os
import random

from resources.lib import kodiutils
from resources.lib.vtmgo import ResolvedStream, util

_LOGGER = logging.getLogger(__name__)


class VtmGoStream:
    """ VTM GO Stream API """

    _API_KEY = 'jL3yNhGpDsaew9CqJrDPq2UzMrlmNVbnadUXVOET'

    def __init__(self, auth=None):
        """ Initialise object """
        self._auth = auth
        self._tokens = self._auth.get_tokens() if self._auth else None

    def _mode(self):
        """ Return the mode that should be used for API calls """
        return 'vtmgo-kids' if self._tokens.product == 'VTM_GO_KIDS' else 'vtmgo'

    def get_stream(self, stream_type, stream_id):
        """ Return a ResolvedStream based on the stream type and id.
        :type stream_type: str
        :type stream_id: str
        :rtype ResolvedStream
        """
        # We begin with asking the api about the stream info.
        video_info = self._get_video_info(stream_type, stream_id)

        # Live channels are only available through anvato
        if video_info.get('video').get('streamType') == 'live':
            protocol = 'anvato'
        else:
            protocol = 'dash'

        # Extract the stream from our stream_info.
        stream_info = self._extract_stream_from_video_info(protocol, video_info)

        # Extract subtitles from our stream_info.
        subtitle_info = self._extract_subtitles_from_stream_info(video_info)

        if protocol == 'anvato':
            # Send a request for the stream info.
            anvato_stream_info = self._anvato_get_stream_info(anvato_info=stream_info.get('anvato'), stream_info=video_info)

            # Get published urls.
            url = anvato_stream_info['published_urls'][0]['embed_url']
            license_url = anvato_stream_info['published_urls'][0]['license_url']

            # Get MPEG DASH manifest url.
            json_manifest = self._download_manifest(url)
            url = json_manifest.get('master_m3u8')

            # Follow Location tag redirection because InputStream Adaptive doesn't support this yet.
            # https://github.com/peak3d/inputstream.adaptive/issues/286
            url = self._redirect_manifest(url)

            # No subtitles for the live stream
            subtitles = None

        else:
            # Get published urls.
            url = stream_info.get('url')
            license_url = stream_info.get('drm', {}).get('com.widevine.alpha', {}).get('licenseUrl')

            # Download subtitles locally so we can give them a better name
            subtitles = self._download_subtitles(subtitle_info)

        if stream_type == 'episodes':
            # TV episode
            return ResolvedStream(
                program=video_info['video']['metadata']['program']['title'],
                program_id=video_info['video']['metadata']['program']['id'],
                title=video_info['video']['metadata']['title'],
                duration=video_info['video']['duration'],
                url=url,
                subtitles=subtitles,
                license_url=license_url,
                cookies=util.SESSION.cookies.get_dict(),
            )

        if stream_type in ['movies', 'oneoffs']:
            # Movie or one-off programs
            return ResolvedStream(
                program=None,
                title=video_info['video']['metadata']['title'],
                duration=video_info['video']['duration'],
                url=url,
                subtitles=subtitles,
                license_url=license_url,
                cookies=util.SESSION.cookies.get_dict(),
            )

        if stream_type == 'channels':
            # Live TV
            if video_info['video']['metadata']['videoType'] == 'episode':
                program = video_info['video']['metadata']['program']['title']
            else:
                program = None

            return ResolvedStream(
                program=program,
                title=video_info['video']['metadata']['title'],
                duration=None,
                url=url,
                subtitles=subtitles,
                license_url=license_url,
                cookies=util.SESSION.cookies.get_dict()
            )

        raise Exception('Unknown video type {type}'.format(type=stream_type))

    def _get_video_info(self, strtype, stream_id):
        """ Get the stream info for the specified stream.
        :param str strtype:
        :param str stream_id:
        :rtype: dict
        """
        url = 'https://videoplayer-service.dpgmedia.net/config/%s/%s' % (strtype, stream_id)
        _LOGGER.debug('Getting video info from %s', url)
        response = util.http_get(url,
                                 params={
                                     'startPosition': '0.0',
                                     'autoPlay': 'true',
                                 },
                                 headers={
                                     'Accept': 'application/json',
                                     'x-api-key': self._API_KEY,
                                     'Popcorn-SDK-Version': '5',
                                 })

        info = json.loads(response.text)
        return info

    @staticmethod
    def _extract_stream_from_video_info(stream_type, stream_info):
        """ Extract the requested stream details.
        :type stream_info: dict
        :rtype dict
        """
        # Loop over available streams, and return the requested stream
        if stream_info.get('video'):
            for stream in stream_info.get('video').get('streams'):
                if stream.get('type') == stream_type:
                    return stream
        elif stream_info.get('code'):
            _LOGGER.error('VTM GO Videoplayer service API error: %s', stream_info.get('type'))
        raise Exception('No stream found that we can handle')

    @staticmethod
    def _extract_subtitles_from_stream_info(stream_info):
        """ Extract a list of the subtitles.
        :type stream_info: dict
        :rtype list[dict]
        """
        subtitles = list()
        if stream_info.get('video').get('subtitles'):
            for _, subtitle in enumerate(stream_info.get('video').get('subtitles')):
                name = subtitle.get('language')
                if name == 'nl':
                    name = 'nl.default'
                elif name == 'nl-tt':
                    name = 'nl.T888'
                subtitles.append(dict(name=name, url=subtitle.get('url')))
                _LOGGER.debug('Found subtitle url %s', subtitle.get('url'))
        return subtitles

    @staticmethod
    def _download_subtitles(subtitles):
        """ Download the subtitle file. """
        # Clean up old subtitles
        temp_dir = os.path.join(kodiutils.addon_profile(), 'temp', '')
        _, files = kodiutils.listdir(temp_dir)
        if files:
            for item in files:
                kodiutils.delete(temp_dir + kodiutils.to_unicode(item))

        # Return if there are no subtitles available
        if not subtitles:
            return None

        if not kodiutils.exists(temp_dir):
            kodiutils.mkdirs(temp_dir)

        downloaded_subtitles = list()
        for subtitle in subtitles:
            output_file = temp_dir + subtitle.get('name')
            webvtt_content = util.http_get(subtitle.get('url')).text
            with kodiutils.open_file(output_file, 'w') as webvtt_output:
                webvtt_output.write(kodiutils.from_unicode(webvtt_content))
            downloaded_subtitles.append(output_file)
        return downloaded_subtitles

    def _anvato_get_stream_info(self, anvato_info, stream_info):
        """ Get the stream info from anvato.
        :type anvato_info: dict
        :type stream_info: dict
        :rtype dict
        """
        url = 'https://tkx.apis.anvato.net/rest/v2/mcp/video/{video}'.format(**anvato_info)
        _LOGGER.debug('Getting stream info from %s with access_key %s and token %s', url, anvato_info['accessKey'], anvato_info['token'])
        response = util.http_post(url,
                                  data={
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
                                      "sdkver": "5.0.65_a",
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
                                  })

        _LOGGER.debug('Got response (status=%s): %s', response.status_code, response.text)

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

    @staticmethod
    def _download_manifest(url):
        """ Download the MPEG DASH manifest.
        :type url: str
        :rtype dict
        """
        response = util.http_get(url)
        try:
            decoded = json.loads(response.text)
            if decoded.get('master_m3u8'):
                _LOGGER.debug('Followed redirection from %s to %s', url, decoded.get('master_m3u8'))
                return decoded
        except ValueError:
            _LOGGER.error('No manifest url found at %s', url)

        # Fallback to the url like we have it
        return dict(master_m3u8=url)

    @staticmethod
    def _redirect_manifest(url):
        """ Follow the Location tag if it is found.
        :type url: str
        :rtype str
        """
        import re

        # Follow when a <Location>url</Location> tag is found.
        # https://github.com/xbmc/inputstream.adaptive/issues/286
        response = util.http_get(url)
        matches = re.search(r"<Location>([^<]+)</Location>", response.text)
        if matches:
            _LOGGER.debug('Followed redirection from %s to %s', url, matches.group(1))
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
            from urllib.parse import quote, urlencode
        except ImportError:  # Python 2
            from urllib import quote, urlencode

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
