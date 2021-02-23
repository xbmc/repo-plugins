# -*- coding: utf-8 -*-
"""
The initial grouping model UI module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""

# pylint: disable=import-error
import xbmcgui
import xbmcplugin

import resources.lib.mvutils as mvutils


class Letter(object):
    """
    The initial grouping model view class
    """

    def __init__(self):
        self.letter = ''
        self.count = 0

    def init(self, pLetter, pCount):
        self.letter = pLetter
        self.count = pCount

    def get_as_dict(self):
        """ Returns the values as a map """
        return {
            "letter": self.letter,
            "count": self.count
        }

    def set_from_dict(self, data):
        """ Assigns internal values from a map """
        if not isinstance(data, dict):
            return
        self.initial = data.get('letter', '')
        self.count = data.get('count', 0)

