# -*- coding: utf-8 -*-
"""
The channel model module

Copyright 2017-2019, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""


class Livestream(object):
    """ The livestream model class """

    def __init__(self):
        self.name = ''
        self.url = ''

    def init(self, pName, pUrl):
        """ init the object with new values """
        self.name = pName
        self.url = pUrl

    def get_as_dict(self):
        """ Returns the values as a map """
        return {
            "name": self.name,
            "url": self.url
        }

    def set_from_dict(self, data):
        """ Assigns internal values from a map """
        if not isinstance(data, dict):
            return
        self.name = data.get('name', '')
        self.url = data.get('url', '')
