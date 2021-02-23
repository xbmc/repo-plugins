# -*- coding: utf-8 -*-
"""
The show model module

Copyright 2017-2019, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""


class Show(object):
    """ The show model class """

    def __init__(self):
        self.showId = ''
        self.channelId = ''
        self.show = ''
        self.channel = ''

    def init(self, pShowId, pChannelId, pShow, pChannel):
        self.showId = pShowId
        self.channelId = pChannelId
        self.show = pShow
        self.channel = pChannel

    def get_as_dict(self):
        """ Returns the values as a map """
        return {
            "showId": self.showId,
            "channelId": self.channelId,
            "show": self.show,
            "channel": self.channel
        }

    def set_from_dict(self, data):
        """ Assigns internal values from a map """
        if not isinstance(data, dict):
            return
        self.showId = data.get('showId', '')
        self.channelId = data.get('channelId', '')
        self.show = data.get('show', '')
        self.channel = data.get('channel', '')
