# -*- coding: utf-8 -*-
"""
The film model module

Copyright 2017-2019, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""


class Film(object):
    """ The film model class """

    def __init__(self):
        self.filmid = 0
        self.title = ''
        self.show = ''
        self.channel = ''
        self.description = ''
        self.seconds = 0
        self.size = 0
        self.aired = ''
        self.url_sub = ''
        self.url_video = ''
        self.url_video_sd = ''
        self.url_video_hd = ''

    def get_as_dict(self):
        """ Returns the values as a map """
        return {
            "filmid": self.filmid,
            "title": self.title,
            "show": self.show,
            "channel": self.channel,
            "description": self.description,
            "seconds": self.seconds,
            "size": self.size,
            "aired": self.aired,
            "url_sub": self.url_sub,
            "url_video": self.url_video,
            "url_video_sd": self.url_video_sd,
            "url_video_hd": self.url_video_hd
        }

    def set_from_dict(self, data):
        """ Assigns internal values from a map """
        if not isinstance(data, dict):
            return
        self.filmid = data.get('filmid', 0)
        self.title = data.get('title', '')
        self.show = data.get('show', '')
        self.channel = data.get('channel', '')
        self.description = data.get('description', '')
        self.seconds = data.get('seconds', 0)
        self.size = data.get('size', 0)
        self.aired = data.get('aired', '')
        self.url_sub = data.get('url_sub', '')
        self.url_video = data.get('url_video', '')
        self.url_video_sd = data.get('url_video_sd', '')
        self.url_video_hd = data.get('url_video_hd', '')
