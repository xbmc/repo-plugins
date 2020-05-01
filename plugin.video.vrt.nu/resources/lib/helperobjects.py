# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Various helper classes used throughout the VRT NU add-on"""

from __future__ import absolute_import, division, unicode_literals


class ApiData:
    """This helper object holds all media information"""

    def __init__(self, client, media_api_url, video_id, publication_id, is_live_stream):
        """The constructor for the ApiData class"""
        self.client = client
        self.media_api_url = media_api_url
        self.video_id = video_id
        self.publication_id = publication_id
        self.is_live_stream = is_live_stream


class StreamURLS:
    """This helper object holds all information to be used when playing streams"""

    def __init__(self, stream_url, subtitle_url=None, license_key=None, use_inputstream_adaptive=False):
        """The constructor for the StreamURLS class"""
        self.stream_url = stream_url
        self.subtitle_url = subtitle_url
        self.license_key = license_key
        self.use_inputstream_adaptive = use_inputstream_adaptive
        self.video_id = None


class TitleItem:
    """This helper object holds all information to be used with Kodi xbmc's ListItem object"""

    def __init__(self, label, path=None, art_dict=None, info_dict=None, stream_dict=None, prop_dict=None, context_menu=None, is_playable=False):
        """The constructor for the TitleItem class"""
        self.label = label
        self.path = path
        self.art_dict = art_dict
        self.info_dict = info_dict
        self.stream_dict = stream_dict
        self.prop_dict = prop_dict
        self.context_menu = context_menu
        self.is_playable = is_playable
