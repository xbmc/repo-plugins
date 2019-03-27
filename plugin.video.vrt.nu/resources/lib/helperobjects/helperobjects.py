# -*- coding: utf-8 -*-

# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)

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
        self.reload()

    def are_filled_in(self):
        return not (self.username is None or self.password is None or self.username == '' or self.password == '')

    def reload(self):
        self.username = self._kodi_wrapper.get_setting('username')
        self.password = self._kodi_wrapper.get_setting('password')
