# encoding: utf-8
# util class for Hbo Go Kodi add-on
# Copyright (C) 2019-2020 ArvVoid (https://github.com/arvvoid)
# SPDX-License-Identifier: GPL-2.0-or-later

from __future__ import absolute_import, division

import sys

from kodi_six import xbmcplugin  # type: ignore

# import for translate path
if sys.version_info < (3, 0):  # for Kodi 18 use old translatePath
    from kodi_six.xbmc import translatePath  # type: ignore
else:  # for Kodi 19+ use new translatePath
    from kodi_six.xbmcvfs import translatePath  # type: ignore


class KodiUtil(object):

    @staticmethod
    def translatePath(path):
        return translatePath(path)

    @staticmethod
    def addSorting(handle, use_content_type):
        xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_GENRE)
        xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_LASTPLAYED)
        xbmcplugin.setContent(handle, use_content_type)

    @staticmethod
    def endDir(handle, use_content_type, simple=False):
        if not simple:
            KodiUtil.addSorting(handle, use_content_type)
        else:
            xbmcplugin.addSortMethod(handle=handle, sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.endOfDirectory(handle)
