# -*- coding: utf-8 -*-
#
# Massengeschmack Kodi add-on
# Copyright (C) 2013-2016 by Janek Bevendorff
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import xbmcplugin
import xbmcgui

from globalvars import *


class Listing(object):
    def __init__(self):
        self.__source = None

    def generate(self, source):
        """
        Generate listing from data source.
        Will return False if the given DataSource does not intend to return a non-empty listing generator,
        i.e. when L{resources.lib.datasource.DataSource.hasListItems} returns False

        @type source: resources.lib.datasource.DataSource
        @param source: the data source object
        @rtype: bool
        @return Whether the given DataSource actually intends to return a non-empty listing
        """
        if not source.hasListItems():
            return False

        self.__source = source
        items         = source.getListItems()

        for i in items:
            self.__addDir(i)

        return True

    def show(self):
        """
        Show the listing after it has been generated.
        You should check the output of L{generate} before trying to show a listing.
        """
        if 'true' == ADDON.getSetting('advanced.viewmodeFix'):
            self.setViewMode(510)
        else:
            self.setViewMode(self.__source.getViewMode())
        xbmcplugin.endOfDirectory(ADDON_HANDLE)

    def setViewMode(self, id):
        """
        Set the view mode of the current listing.

        @type id: int
        @param id: the view mode ID from the current skin
        """
        if 'false' == ADDON.getSetting('advanced.adjustViewModes'):
            return

        xbmcplugin.setContent(ADDON_HANDLE, self.__source.getContentMode())
        xbmc.executebuiltin('Container.SetViewMode(' + str(id) + ')')

    def __addDir(self, listItem):
        xbmcListItem = xbmcgui.ListItem(listItem.getData('name'))
        xbmcListItem.setInfo(type='video', infoLabels=listItem.getData('streamInfo'))

        fanart = listItem.getData('fanart')
        thumb = listItem.getData('thumbnail')

        xbmcListItem.setArt({'thumb' : thumb,
                             'icon'  : thumb,
                             'banner': thumb,
                             'fanart': fanart})

        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url=listItem.getData('url'), listitem=xbmcListItem,
                                    isFolder=listItem.getData('isFolder'))


class ListItem:
    def __init__(self, id=0, name='', url='', thumbnail='', fanart='', streamInfo=None, isFolder=True):
        """
        Generate list item from given parameters.

        @type id         : int
        @param id        : numeric ID of the listed show
        @type name       : str
        @param name      : the display name of the list item
        @type  url       : str
        @param url       : the addon URL this item points to (should not be a real Internet URL)
        @type  thumbnail : str
        @param thumbnail : the path/URL to a thumbnail image
        @type  fanart    : str
        @param fanart    : the path/URL to a fanart image
        @type streamInfo : dict
        @param streamInfo: stream information for passing to xbmcgui.ListeItem.addStreamInfo()
        @type  isFolder  : bool
        @param isFolder  : True if this item is a folder
        """
        if streamInfo is None:
            streamInfo = {}

        self.__data = {
            'id'        : id,
            'name'      : name,
            'url'       : url,
            'thumbnail' : thumbnail,
            'fanart'    : fanart,
            'streamInfo': streamInfo,
            'isFolder'  : isFolder
        }

    def setData(self, key, value):
        """
        Set a value for this list item.

        @type key: str
        @param key: the name of the data record
        @type value: int|str|dict
        @param value: the data (either a string, a dict or a bool)
        """
        self.__data[key] = value

    def getData(self, key):
        """
        Get specific data from this list item.

        @type key: str
        @param key: which data to retrieve (name, url, iconImage, metaData)
        @return mixed: the data or '' if nothing has been set or key is invalid
        """
        if key in self.__data:
            return self.__data[key]

        return ''
