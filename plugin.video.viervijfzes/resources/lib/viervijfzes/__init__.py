# -*- coding: utf-8 -*-
""" GoPlay API """
from __future__ import absolute_import, division, unicode_literals

from collections import OrderedDict

CHANNELS = OrderedDict([
    ('Play4', dict(
        name='Play4',
        epg_id='vier',
        logo='play4.png',
        background='play4-background.png',
        iptv_preset=4,
        iptv_id='play4.be',
        youtube=[
            dict(
                label='GoPlay',
                logo='goplay.png',
                path='plugin://plugin.video.youtube/user/viertv/',
            ),
        ],
    )),
    ('Play5', dict(
        name='Play5',
        epg_id='vijf',
        logo='play5.png',
        background='play5-background.png',
        iptv_preset=5,
        iptv_id='play5.be',
        youtube=[
            dict(
                label='GoPlay',
                logo='goplay.png',
                path='plugin://plugin.video.youtube/user/viertv/',
            ),
        ],
    )),
    ('Play6', dict(
        name='Play6',
        epg_id='zes',
        logo='play6.png',
        background='play6-background.png',
        iptv_preset=6,
        iptv_id='play6.be',
        youtube=[
            dict(
                label='GoPlay',
                logo='goplay.png',
                path='plugin://plugin.video.youtube/user/viertv/',
            ),
        ],
    )),
    ('Play7', dict(
        name='Play7',
        epg_id='zeven',
        url='https://www.goplay.be',
        logo='play7.png',
        background='play7-background.png',
        iptv_preset=17,
        iptv_id='play7.be',
        youtube=[],
    )),
    ('GoPlay', dict(
        name='Go Play',
        url='https://www.goplay.be',
        logo='goplay.png',
        background='goplay-background.png',
        youtube=[],
    ))
])

STREAM_DICT = {
    'codec': 'h264',
    'height': 544,
    'width': 960,
}


class ResolvedStream:
    """ Defines a stream that we can play"""

    def __init__(self, uuid=None, url=None, stream_type=None, license_url=None, auth=None):
        """
        :type uuid: str
        :type url: str
        :type stream_type: str
        :type license_url: str
        :type auth: str
        """
        self.uuid = uuid
        self.url = url
        self.stream_type = stream_type
        self.license_url = license_url
        self.auth = auth

    def __repr__(self):
        return "%r" % self.__dict__
