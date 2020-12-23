# coding: utf-8
from __future__ import print_function, division, absolute_import

from xbmcplugin import getSetting


QUALITY = ["sd", "hd"]
FORMATS = ["mp4", "webm"]


def get_setting_int(plugin, name):
    val = getSetting(plugin.handle, name)
    if not val:
        val = '0'
    return int(val)


def get_quality(plugin):
    return QUALITY[get_setting_int(plugin, 'quality')]


def get_format(plugin):
    return FORMATS[get_setting_int(plugin, 'format')]


def prefer_dash(plugin):
    val = getSetting(plugin.handle, 'dash')
    return val == 'true'
