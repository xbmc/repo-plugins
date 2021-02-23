# -*- coding: utf-8 -*-
"""
The show model UI module

Copyright 2017-2018, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""

# pylint: disable=import-error
import time
import resources.lib.appContext as appContext
import os
import xbmcgui
import xbmcplugin
import resources.lib.mvutils as mvutils
from resources.lib.model.letter import Letter


class LetterUi(object):
    """
    The show model view class

    Args:
        plugin(MediathekView): the plugin object
    """

    def __init__(self, plugin):
        self.logger = appContext.MVLOGGER.get_new_logger('ShowUI')
        self.plugin = plugin
        self.handle = plugin.addon_handle
        self.startTime = 0

    def generate(self, databaseRs):
        #
        # 0 - letter
        # 1 - cnt
        #
        self.startTime = time.time()
        #
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.setContent(self.handle, 'movies')
        #
        letterModel = Letter()
        listOfElements = []
        for element in databaseRs:
            #
            letterModel.init(element[0], element[1])

            nameLabel = letterModel.letter + " (" + str(letterModel.count) + ")" ;
            #
            if self.plugin.get_kodi_version() > 17:
                list_item = xbmcgui.ListItem(label=nameLabel, offscreen=True)
            else:
                list_item = xbmcgui.ListItem(label=nameLabel)
            #
            icon = os.path.join(
                self.plugin.path,
                'resources',
                'icons',
                'letter',
                'letter-' + letterModel.letter + '-m.png'
            )
            list_item.setArt({
                'thumb': icon,
                'icon': icon,
                'banner': icon,
                'fanart': icon,
                'clearart': icon,
                'clearlogo': icon
            })
            #
            info_labels = {
                'title': nameLabel,
                'sorttitle': nameLabel.lower()
            }
            list_item.setInfo(type='video', infoLabels=info_labels)
            #
            targetUrl = mvutils.build_url({
                'mode': 'shows',
                'initial': letterModel.letter
            })
            #
            listOfElements.append((targetUrl, list_item, True))
        #
        xbmcplugin.addDirectoryItems(
            handle=self.handle,
            items=listOfElements,
            totalItems=len(listOfElements)
        )
        #
        xbmcplugin.endOfDirectory(self.handle, cacheToDisc=False)
        self.plugin.setViewId(self.plugin.resolveViewId('THUMBNAIL'))
        #
        self.logger.debug('generated: {} sec', time.time() - self.startTime)
