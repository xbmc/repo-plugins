# -*- coding: utf-8 -*-
"""
The film model UI module

Copyright 2017-2019, Leo Moll and Dominik Schlösser
SPDX-License-Identifier: MIT
"""

import time
import os
from datetime import datetime
from datetime import timedelta
# pylint: disable=import-error
import xbmcgui
import xbmcplugin
import resources.lib.appContext as appContext
from resources.lib.model.film import Film


class FilmlistUi(object):
    """
    The filmui which generates a film list from data

    Args:
        plugin(MediathekView): the plugin object
    """

    def __init__(self, plugin, pLongTitle=True):
        self.logger = appContext.MVLOGGER.get_new_logger('FilmlistUI')
        self.plugin = plugin
        self.handle = plugin.addon_handle
        self.settings = appContext.MVSETTINGS
        self.useLongTitle = pLongTitle
        # define sortmethod for films
        # all av. sort method and put the default sortmethod on first place to be used by UI
        allSortMethods = [
            xbmcplugin.SORT_METHOD_UNSORTED,
            xbmcplugin.SORT_METHOD_TITLE,
            xbmcplugin.SORT_METHOD_DATE,
            xbmcplugin.SORT_METHOD_DATEADDED,
            xbmcplugin.SORT_METHOD_DURATION
        ]
        method = allSortMethods[0]
        allSortMethods[0] = allSortMethods[self.settings.getFilmSortMethod()]
        allSortMethods[self.settings.getFilmSortMethod()] = method
        self.sortmethods = allSortMethods
        #
        self.startTime = 0
        self.tzDiff = datetime.now() - datetime.utcnow()
        self.tzBase = datetime.fromtimestamp(0)

    def generate(self, databaseRs):
        #
        # 0 - idhash, 1 - title, 2 - showname, 3 - channel,
        # 4 - description, 5 - duration, 6 - aired,
        # 7- url_sub, 8- url_video, 9 - url_video_sd, 10 - url_video_hd
        #
        self.startTime = time.time()
        #
        xbmcplugin.setContent(self.handle, self.settings.getContentType())
        for method in self.sortmethods:
            xbmcplugin.addSortMethod(self.handle, method)
        #
        aFilm = Film()
        listOfElements = []
        for element in databaseRs:
            #
            aFilm.init(element[0], element[1], element[2], element[3], element[4], element[5],
                        element[6], element[7], element[8], element[9], element[10])
            #
            (targetUrl, list_item) = self._generateListItem(aFilm)
            #
            list_item.addContextMenuItems(self._generateContextMenu(aFilm))
            #
            if self.settings.getAutoSub() and aFilm.url_sub:
                targetUrl = self.plugin.build_url({
                    'mode': "playwithsrt",
                    'id': aFilm.filmid
                })
            #
            listOfElements.append((targetUrl, list_item, False))
        #
        xbmcplugin.addDirectoryItems(
            handle=self.handle,
            items=listOfElements,
            totalItems=len(listOfElements)
        )
        #
        xbmcplugin.endOfDirectory(self.handle, cacheToDisc=False)
        self.plugin.setViewId(self.plugin.resolveViewId('LIST'))
        #
        self.logger.debug('generated: {} sec', time.time() - self.startTime)

    def _generateListItem(self, pFilm):
        #
        videohds = ""
        if (pFilm.url_video_hd != "" and self.settings.getPreferHd()):
            videourl = pFilm.url_video_hd
            videohds = " (HD)"
        elif (pFilm.url_video_sd != ""):
            videourl = pFilm.url_video_sd
        else:
            videourl = pFilm.url_video

        # exit if no url supplied
        if videourl == "":
            return None

        videourl = videourl + self.settings.getUserAgentString()

        if self.useLongTitle:
            resultingtitle = pFilm.show + ': ' + pFilm.title + videohds
        else:
            resultingtitle = pFilm.title + videohds

        info_labels = {
            'title': resultingtitle,
            'sorttitle': resultingtitle.lower(),
            'tvshowtitle': pFilm.show,
            'plot': pFilm.description
        }

        if pFilm.seconds is not None and pFilm.seconds > 0:
            info_labels['duration'] = pFilm.seconds

        if pFilm.aired is not None and pFilm.aired != 0:
            ndate = self.tzBase + timedelta(seconds=(pFilm.aired))
            airedstring = ndate.isoformat().replace('T', ' ')
            info_labels['date'] = airedstring[:10]
            info_labels['aired'] = airedstring[:10]
            info_labels['dateadded'] = airedstring
            info_labels['plot'] = self.plugin.language(30990).format(airedstring) + info_labels['plot']

        icon = os.path.join(
            self.plugin.path,
            'resources',
            'icons',
            'sender',
            pFilm.channel.lower() + '-c.png'
        )

        #
        if self.plugin.get_kodi_version() > 17:
            listitem = xbmcgui.ListItem(label=resultingtitle, path=videourl, offscreen=True)
        else:
            listitem = xbmcgui.ListItem(label=resultingtitle, path=videourl)
        #
        listitem.setInfo(type='video', infoLabels=info_labels)
        listitem.setProperty('IsPlayable', 'true')
        listitem.setArt({
            'thumb': icon,
                'icon': icon,
                'banner': icon,
                'fanart': icon,
                'clearart': icon,
                'clearlogo': icon
        })
        return (videourl, listitem)

    def _generateContextMenu(self, pFilm):
        contextmenu = []

        if pFilm.url_sub != '':
            contextmenu.append((
                self.plugin.language(30921),
                'PlayMedia({})'.format(
                    self.plugin.build_url({
                        'mode': "playwithsrt",
                        'id': pFilm.filmid
                    })
                )
            ))

        # Download movie
        contextmenu.append((
            self.plugin.language(30922),
            'RunPlugin({})'.format(
                self.plugin.build_url({
                    'mode': "downloadmv",
                    'id': pFilm.filmid,
                    'quality': 1
                })
            )
        ))
        if pFilm.url_video_hd:
            # Download HD movie
            contextmenu.append((
                self.plugin.language(30923),
                'RunPlugin({})'.format(
                    self.plugin.build_url({
                        'mode': "downloadmv",
                        'id': pFilm.filmid,
                        'quality': 2
                    })
                )
            ))
        # Download TV episode
        contextmenu.append((
            self.plugin.language(30924),
            'RunPlugin({})'.format(
                self.plugin.build_url({
                    'mode': "downloadep",
                    'id': pFilm.filmid,
                    'quality': 1
                })
            )
        ))
        if pFilm.url_video_hd:
            # Download HD TV episode
            contextmenu.append((
                self.plugin.language(30925),
                'RunPlugin({})'.format(
                    self.plugin.build_url({
                        'mode': "downloadep",
                        'id': pFilm.filmid,
                        'quality': 2
                    })
                )
            ))
        return contextmenu

