# -*- coding: utf-8 -*-
""" GoPlay API """
from __future__ import absolute_import, division, unicode_literals

STREAM_DICT = {
    'codec': 'h264',
    'height': 544,
    'width': 960,
}


class ResolvedStream:
    """ Defines a stream that we can play"""

    def __init__(self, uuid=None, url=None, stream_type=None, license_key=None):
        """
        :type uuid: str
        :type url: str
        :type stream_type: str
        :type license_key: str
        """
        self.uuid = uuid
        self.url = url
        self.stream_type = stream_type
        self.license_key = license_key

    def __repr__(self):
        return "%r" % self.__dict__
