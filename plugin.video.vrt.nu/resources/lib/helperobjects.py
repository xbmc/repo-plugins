# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals


class ApiData:

    def __init__(self, client, media_api_url, video_id, publication_id, xvrttoken, is_live_stream):
        self.client = client
        self.media_api_url = media_api_url
        self.video_id = video_id
        self.publication_id = publication_id
        self.xvrttoken = xvrttoken
        self.is_live_stream = is_live_stream


class Credentials:

    def __init__(self, _kodi):
        self._kodi = _kodi
        self.username = _kodi.get_setting('username')
        self.password = _kodi.get_setting('password')

    def are_filled_in(self):
        return bool(self.username and self.password)

    def reload(self):
        self.username = self._kodi.get_setting('username')
        self.password = self._kodi.get_setting('password')

    def reset(self):
        self.username = self._kodi.set_setting('username', None)
        self.password = self._kodi.set_setting('password', None)


class StreamURLS:

    def __init__(self, stream_url, subtitle_url=None, license_key=None, use_inputstream_adaptive=False):
        self.stream_url = stream_url
        self.subtitle_url = subtitle_url
        self.license_key = license_key
        self.use_inputstream_adaptive = use_inputstream_adaptive
        self.video_id = None


class TitleItem:

    def __init__(self, title, url_dict, is_playable, art_dict=None, video_dict=None, context_menu=None):
        self.title = title
        self.url_dict = url_dict
        self.is_playable = is_playable
        self.art_dict = art_dict
        self.video_dict = video_dict
        self.context_menu = context_menu
