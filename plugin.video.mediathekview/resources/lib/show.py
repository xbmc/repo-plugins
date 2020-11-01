# -*- coding: utf-8 -*-
"""
The show model module

Copyright 2017-2019, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""


class Show(object):
    """ The show model class """

    def __init__(self):
        self.showid = 0
        self.channelid = 0
        self.show = ''
        self.channel = ''

    def get_as_dict(self):
        """ Returns the values as a map """
        return {
            "showid": self.showid,
            "channelid": self.channelid,
            "show": self.show,
            "channel": self.channel
        }

    def set_from_dict(self, data):
        """ Assigns internal values from a map """
        if not isinstance(data, dict):
            return
        self.showid = data.get('showid', 0)
        self.channelid = data.get('channelid', 0)
        self.show = data.get('show', '')
        self.channel = data.get('channel', '')
