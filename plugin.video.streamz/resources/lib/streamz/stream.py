# -*- coding: utf-8 -*-
""" Streamz Stream API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
import os

from resources.lib import kodiutils
from resources.lib.streamz import API_ENDPOINT, ResolvedStream, util

_LOGGER = logging.getLogger(__name__)


class Stream:
    """ Streamz Stream API """

    _API_KEY = 'zs06SrhsKN2fEQvDdTMDR2t6wYwfceQu5HAmGa0p'

    def __init__(self, tokens=None):
        """ Initialise object """
        self._tokens = tokens

    def _mode(self):
        """ Return the mode that should be used for API calls """
        return self._tokens.product

    def get_stream(self, stream_type, stream_id):
        """ Return a ResolvedStream based on the stream type and id.

        :param str stream_type:         Type of stream (episodes or movies)
        :param str stream_id:           ID of the stream
        :rtype: ResolvedStream
        """
        # We begin with asking the api about the stream info
        stream_tokens = self._get_stream_tokens(stream_id)
        player_token = stream_tokens.get('playerToken')

        # Return video information
        video_info = self._get_video_info(stream_type, stream_id, player_token)

        # Extract the dash stream from our stream_info
        stream_info = self._extract_stream_from_video_info('dash', video_info)

        # Send heartbeat
        # self._send_heartbeat(video_info.get('heartbeat', {}).get('token'), video_info.get('heartbeat', {}).get('correlationId'))

        # Get published urls
        url = stream_info.get('url')
        license_url = stream_info.get('drm', {}).get('com.widevine.alpha', {}).get('licenseUrl')
        license_provider = stream_info.get('drm', {}).get('com.widevine.alpha', {}).get('provider')
        if license_provider == 'drmtoday':
            license_key = self.create_license_key(
                license_url,
                key_headers={
                    'x-dt-auth-token': stream_info.get('drm', {}).get('com.widevine.alpha', {}).get('drmtoday', {}).get('authToken'),
                    'Content-Type': 'application/octet-stream',
                },
                response_value='JBlicense'
            )
        else:
            # anvato
            license_key = self.create_license_key(license_url)

        # Extract subtitles from our video_info
        subtitle_info = self._extract_subtitles_from_stream_info(video_info)

        # Download subtitles locally so we can give them a better name
        subtitles = self._download_subtitles(subtitle_info)

        if stream_type == 'episodes':
            return ResolvedStream(
                program=video_info['video']['metadata']['program']['title'],
                program_id=video_info['video']['metadata']['program']['id'],
                title=video_info['video']['metadata']['title'],
                duration=video_info['video']['duration'],
                url=url,
                subtitles=subtitles,
                license_key=license_key,
            )

        if stream_type == 'movies':
            return ResolvedStream(
                program=None,
                title=video_info['video']['metadata']['title'],
                duration=video_info['video']['duration'],
                url=url,
                subtitles=subtitles,
                license_key=license_key,
            )

        raise Exception('Unknown video type {type}'.format(type=stream_type))

    def _get_stream_tokens(self, stream_id):
        """ Get the stream info for the specified stream.
        :param str stream_id:
        :rtype: dict
        """
        url = API_ENDPOINT + '/%s/play/%s' % (self._mode(), stream_id)

        _LOGGER.debug('Getting stream tokens from %s', url)
        response = util.http_get(url, token=self._tokens.access_token, profile=self._tokens.profile)

        return json.loads(response.text)

    def _get_video_info(self, strtype, stream_id, player_token):
        """ Get the stream info for the specified stream.
        :param str strtype:
        :param str stream_id:
        :param str player_token:
        :rtype: dict
        """
        url = 'https://videoplayer-service.api.persgroep.cloud/config/%s/%s' % (strtype, stream_id)
        _LOGGER.debug('Getting video info from %s', url)
        response = util.http_post(url,
                                  params={
                                      'startPosition': '0.0',
                                      'autoPlay': 'true',
                                  },
                                  data={
                                      "deviceType": "android-phone",
                                      "zone": "streamz"
                                  },
                                  headers={
                                      'Accept': 'application/json',
                                      'x-api-key': self._API_KEY,
                                      # 'x-dpg-correlation-id': '',
                                      'Popcorn-SDK-Version': '6',
                                      'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 6.0.1; MotoG3 Build/MPIS24.107-55-2-17)',
                                      'Authorization': 'Bearer ' + player_token,
                                  })

        info = json.loads(response.text)
        return info

    def _send_heartbeat(self, token, correlation_id):
        """ Notify the service we will start playing.

        :param str token:               JWT token
        :param str correlation_id:      Correlation ID
        :rtype: dict
        """
        url = 'https://videoplayer-service.api.persgroep.cloud/config/heartbeat'
        _LOGGER.debug('Sending heartbeat to %s', url)
        util.http_put(url,
                      data={
                          'token': token,
                      },
                      headers={
                          'Accept': 'application/json',
                          'Content-Type': 'application/json',
                          'x-api-key': self._API_KEY,
                          'x-dpg-correlation-id': correlation_id,
                          'Popcorn-SDK-Version': '4',
                          'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 6.0.1; MotoG3 Build/MPIS24.107-55-2-17)',
                      })

    @staticmethod
    def _extract_stream_from_video_info(stream_type, stream_info):
        """ Extract the anvato stream details.

        :param dict stream_info:        Dictionary with video info from the API.
        :rtype: dict
        """
        # Loop over available streams, and return the one from anvato
        if stream_info.get('video'):
            for stream in stream_info.get('video').get('streams'):
                if stream.get('type') == stream_type:
                    return stream
        elif stream_info.get('code'):
            _LOGGER.error('Streamz Videoplayer service API error: %s', stream_info.get('type'))
        raise Exception('No stream found that we can handle')

    @staticmethod
    def _extract_subtitles_from_stream_info(stream_info):
        """ Extract a list of the subtitles.

        :param dict stream_info:        Dictionary with stream info.
        :returns: A list of subtitles.
        :rtype: list[dict]
        """
        subtitles = []
        if stream_info.get('video').get('subtitles'):
            for _, subtitle in enumerate(stream_info.get('video').get('subtitles')):
                name = subtitle.get('language')
                if name == 'nl':
                    name = 'nl.default'
                elif name == 'nl-tt':
                    name = 'nl.T888'
                subtitles.append({'name': name,
                                  'url': subtitle.get('url')})
                _LOGGER.debug('Found subtitle url %s', subtitle.get('url'))
        return subtitles

    @staticmethod
    def _download_subtitles(subtitles):
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

        downloaded_subtitles = []
        for subtitle in subtitles:
            output_file = temp_dir + subtitle.get('name')
            webvtt_content = util.http_get(subtitle.get('url')).text
            with kodiutils.open_file(output_file, 'w') as webvtt_output:
                webvtt_output.write(kodiutils.from_unicode(webvtt_content))
            downloaded_subtitles.append(output_file)
        return downloaded_subtitles

    @staticmethod
    def create_license_key(key_url, key_type='R', key_headers=None, key_value='', response_value=''):
        """ Create a license key string that we need for inputstream.adaptive.

        :param str key_url:
        :param str key_type:
        :param dict[str, str] key_headers:
        :param str key_value:
        :param str response_value:
        :rtype: str
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

        return '%s|%s|%s|%s' % (key_url, header, key_value, response_value)
