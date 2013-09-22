#
#      Copyright (C) 2013 Tommy Winther
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import os
import sys
import urlparse
import re
import mobileapi

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

import buggalo

REGIONS = ['tv3play.dk', 'tv3play.se', 'tv3play.no', 'tv3play.lt', 'tv3play.lv', 'tv3play.ee', 'tv6play.se',
           'tv8play.se', 'tv10play.se', 'viasat4play.no', 'play.novatv.bg']


class TV3PlayAddon(object):
    def __init__(self):
        if 'region' in PARAMS:
            self.api = mobileapi.TV3PlayMobileApi(PARAMS['region'][0])

    def listRegions(self):
        items = list()
        for region in REGIONS:
            item = xbmcgui.ListItem(region, iconImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            items.append((PATH + '?region=%s' % region, item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def listPrograms(self, region):
        items = list()

        formats = self.api.getAllFormats()
        if not formats:
            xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
            self.displayError(ADDON.getLocalizedString(30205))
            return

        for series in formats:
            fanart = mobileapi.IMAGE_URL % series['image'].replace(' ', '%20')

            infoLabels = {
                'title': series['title'],
                'plot': series['description']
            }

            item = xbmcgui.ListItem(series['title'], iconImage=fanart)
            item.setInfo('video', infoLabels)
            item.setProperty('Fanart_Image', fanart)
            items.append((PATH + '?region=%s&format=%s' % (region, series['id']), item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def listCategories(self, region, formatId):
        detailed = self.api.detailed(formatId)

        for category in detailed['formatcategories']:
            fanart = mobileapi.IMAGE_URL % category['image'].replace(' ', '%20')

            item = xbmcgui.ListItem(category['name'], iconImage=fanart)
            item.setProperty('Fanart_Image', fanart)
            xbmcplugin.addDirectoryItem(HANDLE,
                                        PATH + '?region=%s&format=%s&category=%s' % (region, formatId, category['id']),
                                        item, True)

        xbmcplugin.endOfDirectory(HANDLE)

    def listVideos(self, region, category):
        items = list()

        videos = self.api.getVideos(category)
        for video in videos:
            fanart = mobileapi.IMAGE_URL % video['image'].replace(' ', '%20')

            infoLabels = {
                'title': video['title'],
                'studio': ADDON.getAddonInfo('name'),
                'plot': video['description'],
                'plotoutline': video['summary'],
                'tvshowtitle': video['formattitle']
            }
            if 'length' in video and video['length'] is not None:
                infoLabels['duration'] = int(video['length']) / 60

            if 'airdate' in video:
                airdate = video['airdate']
                infoLabels['date'] = '%s.%s.%s' % (airdate[8:10], airdate[5:7], airdate[0:4])
                infoLabels['year'] = int(airdate[0:4])

            if 'episode' in video and video['episode'] is not None:
                infoLabels['episode'] = int(video['episode'])

            item = xbmcgui.ListItem(video['title'], iconImage=fanart)
            item.setInfo('video', infoLabels)
            item.setProperty('IsPlayable', 'true')
            item.setProperty('Fanart_Image', fanart)
            items.append((PATH + '?region=%s&playVideo=%s' % (region, video['id']), item))

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_EPISODE)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def playVideo(self, videoId):
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        data = self.api.getMobileData(videoId)
        if data is not None and 'adcalls' in data and data['adcalls'][0]['type'] == 'preroll':
            xml = self.api._http_request(data['adcalls'][0]['url'])

            m = re.search('<MediaFile[^>]+><!\[CDATA\[(.*)\]\]></MediaFile>', xml)
            if m:
                item = xbmcgui.ListItem(ADDON.getLocalizedString(30100), iconImage=ICON)
                playlist.add(m.group(1), item)

        url = self.api.getMobileStream(videoId)
        playlist.add(url)

        xbmcplugin.setResolvedUrl(HANDLE, True, playlist[0])

    def displayError(self, message='n/a'):
        heading = buggalo.getRandomHeading()
        line1 = ADDON.getLocalizedString(30200)
        line2 = ADDON.getLocalizedString(30201)
        xbmcgui.Dialog().ok(heading, line1, line2, message)


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    CACHE_PATH = xbmc.translatePath(ADDON.getAddonInfo("Profile"))
    if not os.path.exists(CACHE_PATH):
        os.makedirs(CACHE_PATH)

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    tv3PlayAddon = TV3PlayAddon()
    try:
        if 'playVideo' in PARAMS:
            tv3PlayAddon.playVideo(PARAMS['playVideo'][0])
        elif 'format' in PARAMS and 'category' in PARAMS:
            tv3PlayAddon.listVideos(PARAMS['region'][0], PARAMS['category'][0])
        elif 'format' in PARAMS:
            tv3PlayAddon.listCategories(PARAMS['region'][0], PARAMS['format'][0])
        elif 'region' in PARAMS:
            tv3PlayAddon.listPrograms(PARAMS['region'][0])
        else:
            tv3PlayAddon.listRegions()

    except mobileapi.TV3PlayMobileApiException, ex:
        tv3PlayAddon.displayError(str(ex))

    except Exception:
        buggalo.onExceptionRaised()
