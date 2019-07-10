# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' Various helper classes used throughtout the VRT NU add-on '''

from __future__ import absolute_import, division, unicode_literals


class ApiData:
    ''' This helper object holds all media information '''

    def __init__(self, client, media_api_url, video_id, publication_id, is_live_stream):
        ''' The constructor for the ApiData class '''
        self.client = client
        self.media_api_url = media_api_url
        self.video_id = video_id
        self.publication_id = publication_id
        self.is_live_stream = is_live_stream


class Credentials:
    ''' This helper object holds all credential information '''

    def __init__(self, _kodi):
        ''' The constructor for the Credentials class '''
        self._kodi = _kodi
        self.username = _kodi.get_setting('username')
        self.password = _kodi.get_setting('password')

    def are_filled_in(self):
        ''' Whether the credentials have been filled in and are stored in the settings '''
        return bool(self.username and self.password)

    def reload(self):
        ''' Reload the credentials from the settings '''
        self.username = self._kodi.get_setting('username')
        self.password = self._kodi.get_setting('password')

    def reset(self):
        ''' Reset the credentials in the settings '''
        # NOTE: Do not reset the username, this can be edited by the user and doesn't need to be retyped
        # self.username = self._kodi.set_setting('username', None)
        self.password = self._kodi.set_setting('password', None)


class StreamURLS:
    ''' This helper object holds all information to be used when playing streams '''

    def __init__(self, stream_url, subtitle_url=None, license_key=None, use_inputstream_adaptive=False):
        ''' The constructor for the StreamURLS class '''
        self.stream_url = stream_url
        self.subtitle_url = subtitle_url
        self.license_key = license_key
        self.use_inputstream_adaptive = use_inputstream_adaptive
        self.video_id = None


class TitleItem:
    ''' This helper object holds all information to be used with Kodi xbmc's ListItem object '''

    def __init__(self, title, path, art_dict=None, info_dict=None, stream_dict=None, context_menu=None, is_playable=False):
        ''' The constructor for the TitleItem class '''
        self.title = title
        self.path = path
        self.art_dict = art_dict
        self.info_dict = info_dict
        self.stream_dict = stream_dict
        self.context_menu = context_menu
        self.is_playable = is_playable

    def __str__(self):
        return 'TitleItem[%s]' % self.title
