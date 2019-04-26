# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals


class TitleItem:

    def __init__(self, title, url_dict, is_playable, art_dict=None, video_dict=None):
        self.title = title
        self.url_dict = url_dict
        self.is_playable = is_playable
        self.art_dict = art_dict
        self.video_dict = video_dict


class Credentials:

    def __init__(self, kodi_wrapper):
        self._kodi_wrapper = kodi_wrapper
        self._username = self._kodi_wrapper.get_setting('username')
        self._password = self._kodi_wrapper.get_setting('password')

    def are_filled_in(self):
        return not (self._username is None or self._password is None or self._username == '' or self._password == '')

    def reload(self):
        self._username = self._kodi_wrapper.get_setting('username')
        self._password = self._kodi_wrapper.get_setting('password')

    def reset(self):
        self._username = self._kodi_wrapper.set_setting('username', None)
        self._password = self._kodi_wrapper.set_setting('password', None)

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password
