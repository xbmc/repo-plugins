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


class InitialUI(object):
    """
    The initial grouping model view class

    Args:
        plugin(MediathekView): the plugin object

        sortmethods(array, optional): an array of sort methods
            for the directory representation. Default is
            `[ xbmcplugin.SORT_METHOD_TITLE ]`
    """

    def __init__(self, plugin, sortmethods=None):
        self.plugin = plugin
        self.handle = plugin.addon_handle
        self.sortmethods = sortmethods if sortmethods is not None else [
            xbmcplugin.SORT_METHOD_TITLE]
        self.channelid = 0
        self.initial = ''
        self.count = 0

    def begin(self, channelid):
        """
        Begin a directory containing grouped entries

        Args:
            channelid(id): database id of the channel to group by
        """
        self.channelid = channelid
        for method in self.sortmethods:
            xbmcplugin.addSortMethod(self.handle, method)

    def add(self, altname=None):
        """
        Add the current entry to the directory

        Args:
            altname(str, optional): alternative name for the entry
        """
        if altname is None:
            resultingname = '%s (%d)' % (self.initial if self.initial !=
                                         ' ' and self.initial != '' else ' No Title', self.count)
        else:
            resultingname = altname
        list_item = xbmcgui.ListItem(label=resultingname)
        info_labels = {
            'title': resultingname,
            'sorttitle': resultingname.lower()
        }
        list_item.setInfo(type='video', infoLabels=info_labels)
        xbmcplugin.addDirectoryItem(
            handle=self.handle,
            url=mvutils.build_url({
                'mode': "shows",
                'channel': self.channelid,
                'initial': self.initial,
                'count': self.count
            }),
            listitem=list_item,
            isFolder=True
        )

    def end(self):
        """ Finish a directory containing grouped entries """
        xbmcplugin.endOfDirectory(self.handle)
