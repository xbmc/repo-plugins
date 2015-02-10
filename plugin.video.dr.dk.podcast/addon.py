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
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import os
import sys
import urlparse

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

import buggalo
import podcastapi


class DrDkPodcast(object):
    def __init__(self, content_type):
        self.content_type = content_type

        if self.content_type == 'audio':
            self.api = podcastapi.PodcastApi(podcastapi.TYPE_RADIO)
        elif self.content_type == 'video':
            self.api = podcastapi.PodcastApi(podcastapi.TYPE_TV)

    def showOverview(self):
        # Show all
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30100), iconImage=ICON)
        item.setProperty('Fanart_Image', FANART)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?content_type=' + self.content_type + '&show=all', item, True)

        # Show channels
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30101), iconImage=ICON)
        item.setProperty('Fanart_Image', FANART)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?content_type=' + self.content_type + '&show=channel', item, True)

        # Show by letters
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30102), iconImage=ICON)
        item.setProperty('Fanart_Image', FANART)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?content_type=' + self.content_type + '&show=letter', item, True)

        # Search
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30103), iconImage=ICON)
        item.setProperty('Fanart_Image', FANART)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?content_type=' + self.content_type + '&show=search', item, True)

        xbmcplugin.endOfDirectory(HANDLE)

    def showChannels(self):
        for channel in self.api.getChannels():
            podcasts = self.api.search(count=1, channel=channel)
            if podcasts['TotalCount'] > 0:
                item = xbmcgui.ListItem(channel, iconImage=ICON)
                item.setProperty('Fanart_Image', FANART)
                xbmcplugin.addDirectoryItem(HANDLE,
                                            PATH + '?content_type=' + self.content_type + '&show=podcasts&channel=' + channel,
                                            item, True)

        xbmcplugin.endOfDirectory(HANDLE)

    def showLetters(self):
        podcasts = self.api.search()
        items = list()

        letter = podcasts['Data'][0]['Title'][0].upper()
        count = 0
        for idx, podcast in enumerate(podcasts['Data']):
            count += 1
            if letter != podcast['Title'][0].upper() or idx == len(podcasts['Data']):
                letter = podcast['Title'][0].upper()
                infoLabels = {'title': letter, 'count': count}

                item = xbmcgui.ListItem(letter, iconImage=ICON)
                item.setInfo(self.content_type, infoLabels)
                item.setProperty('Fanart_Image', FANART)

                url = PATH + '?content_type=' + self.content_type + '&show=podcasts&letter=' + letter
                items.append((url, item, True))
                count = 0

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.endOfDirectory(HANDLE)

    def search(self):
        keyboard = xbmc.Keyboard('', ADDON.getLocalizedString(30200))
        keyboard.doModal()
        if keyboard.isConfirmed():
            query = keyboard.getText()
            self.showPodcasts(query=query)

    def showPodcasts(self, channel=None, letter=None, query=None):
        if letter:
            podcasts = self.api.getByFirstLetter(letter)
        else:
            podcasts = self.api.search(query=query, channel=channel)

        for podcast in podcasts['Data']:
            item = xbmcgui.ListItem(podcast['Title'], iconImage=podcast['ImageLinkScaled'].replace('&amp;', '&'))
            item.setProperty('Fanart_Image', FANART)
            xbmcplugin.addDirectoryItem(HANDLE, podcast['XmlLink'].replace('http://', 'rss://'), item, True)

        xbmcplugin.endOfDirectory(HANDLE)


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    try:
        if 'content_type' in PARAMS:
            addon = DrDkPodcast(PARAMS['content_type'][0])
            if 'show' in PARAMS:
                if PARAMS['show'][0] == 'podcasts':
                    channel = None
                    if 'channel' in PARAMS:
                        channel = PARAMS['channel'][0]
                    letter = None
                    if 'letter' in PARAMS:
                        letter = PARAMS['letter'][0]
                    addon.showPodcasts(channel, letter)

                if PARAMS['show'][0] == 'all':
                    addon.showPodcasts()

                elif PARAMS['show'][0] == 'channel':
                    addon.showChannels()
                elif PARAMS['show'][0] == 'letter':
                    addon.showLetters()
                elif PARAMS['show'][0] == 'search':
                    addon.search()
            else:
                addon.showOverview()

    except podcastapi.PodcastException, ex:
        heading = buggalo.getRandomHeading()
        line1 = ADDON.getLocalizedString(30900)
        line2 = ADDON.getLocalizedString(30901)
        xbmcgui.Dialog().ok(heading, line1, line2, str(ex))

    except Exception:
        buggalo.onExceptionRaised()

