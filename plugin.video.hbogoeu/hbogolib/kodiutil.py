# encoding: utf-8
# util class for Hbo Go Kodi add-on
# Copyright (C) 2019 ArvVoid (https://github.com/arvvoid)
# Relesed under GPL version 2
#########################################################

from __future__ import absolute_import, division

from kodi_six import xbmcplugin


class KodiUtil(object):

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
