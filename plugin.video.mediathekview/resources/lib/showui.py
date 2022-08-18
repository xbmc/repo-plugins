# -*- coding: utf-8 -*-
"""
The show model UI module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""

# pylint: disable=import-error
import xbmcgui
import xbmcplugin

import resources.lib.mvutils as mvutils

from resources.lib.show import Show


class ShowUI(Show):
    """
    The show model view class

    Args:
        plugin(MediathekView): the plugin object

        sortmethods(array, optional): an array of sort methods
            for the directory representation. Default is
            `[ xbmcplugin.SORT_METHOD_TITLE ]`
    """

    def __init__(self, plugin, sortmethods=None):
        super(ShowUI, self).__init__()
        self.plugin = plugin
        self.handle = plugin.addon_handle
        self.sortmethods = sortmethods if sortmethods is not None else [
            xbmcplugin.SORT_METHOD_TITLE]
        self.querychannelid = 0

    def begin(self, channelid):
        """
        Begin a directory containing shows

        Args:
            channelid(id): database id of the channel
        """
        self.querychannelid = int(channelid)
        for method in self.sortmethods:
            xbmcplugin.addSortMethod(self.handle, method)
        xbmcplugin.setContent(self.handle, '')

    def add(self, altname=None):
        """
        Add the current entry to the directory

        Args:
            altname(str, optional): alternative name for the entry
        """
        if altname is not None:
            resultingname = altname
        elif self.querychannelid == 0:
            resultingname = self.show + ' [' + self.channel + ']'
        else:
            resultingname = self.show

        info_labels = {
            'title': resultingname,
            'sorttitle': resultingname.lower()
        }

        if self.channel.find(',') == -1:
            icon = 'special://home/addons/' + self.plugin.addon_id + \
                '/resources/icons/' + self.channel.lower() + '-m.png'
        else:
            icon = 'special://home/addons/' + self.plugin.addon_id + \
                '/resources/icons/default-m.png'

        list_item = xbmcgui.ListItem(label=resultingname)
        list_item.setInfo(type='video', infoLabels=info_labels)
        list_item.setArt({
            'thumb': icon,
            'icon': icon
        })

        xbmcplugin.addDirectoryItem(
            handle=self.handle,
            url=mvutils.build_url({
                'mode': "films",
                'show': self.showid
            }),
            listitem=list_item,
            isFolder=True
        )

    def end(self):
        """ Finish a directory containing shows """
        xbmcplugin.endOfDirectory(self.handle)
