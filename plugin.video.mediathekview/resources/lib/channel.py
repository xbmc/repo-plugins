# -*- coding: utf-8 -*-
"""
The channel model module

Copyright 2017-2019, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""


class Channel(object):
    """ The channel model class """

    def __init__(self):
        self.channelid = 0
        self.channel = ''

    def get_as_dict(self):
        """ Returns the values as a map """
        return {
            "channelid": self.channelid,
            "channel": self.channel
        }

    def set_from_dict(self, data):
        """ Assigns internal values from a map """
        if not isinstance(data, dict):
            return
        self.channelid = data.get('channelid', 0)
        self.channel = data.get('channel', '')
