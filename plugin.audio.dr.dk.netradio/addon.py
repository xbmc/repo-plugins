#
#      Copyright (C) 2012 Tommy Winther
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
#  along with this Program; see the file LICENSE.txt. If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import os
import sys
import simplejson
import urllib2
import urlparse

import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

import channels
import buggalo

CHANNELS_URL = 'http://www.dr.dk/radio/channels/channels.json.drxml'

class DkNetradio(object):

    def showOverview(self):
        item = xbmcgui.ListItem(ADDON.getLocalizedString(100), iconImage = ICON)
        item.setProperty('Fanart_Image', FANART)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?show=dr', item, True)

        item = xbmcgui.ListItem(ADDON.getLocalizedString(101), iconImage = ICON)
        item.setProperty('Fanart_Image', FANART)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?show=other', item, True)

        xbmcplugin.endOfDirectory(HANDLE)

    def showDRChannels(self):
        try:
            u = urllib2.urlopen(CHANNELS_URL)
            channelList = simplejson.loads(u.read())
            u.close()
        except Exception, ex:
            self.showError(str(ex))
            return

        for channel in channelList:
            logoImage = os.path.join(LOGO_PATH, channel['source_url'] + '.png')
            if xbmcvfs.exists(logoImage):
                item = xbmcgui.ListItem(channel['title'], iconImage = logoImage)
            else:
                item = xbmcgui.ListItem(channel['title'], iconImage = ICON)

            item.setProperty('IsPlayable', 'true')
            item.setProperty('Fanart_Image', FANART)
            item.setInfo(type = 'music', infoLabels = {
                    'title' : channel['title']
            })

            if type(channel['mediaFile']) is list:
                url = channel['mediaFile'][0]
            else:
                url = channel['mediaFile']
            xbmcplugin.addDirectoryItem(HANDLE, url + ' live=1', item)

        xbmcplugin.endOfDirectory(HANDLE)


    def showOtherChannels(self):
        for channel in channels.CHANNELS:
            logoImage = os.path.join(LOGO_PATH, str(channel.id) + '.png')
            if xbmcvfs.exists(logoImage):
                item = xbmcgui.ListItem(channel.name, iconImage = logoImage)
            else:
                item = xbmcgui.ListItem(channel.name, iconImage = ICON)

            item.setProperty('IsPlayable', 'true')
            item.setProperty('Fanart_Image', FANART)
            item.setInfo(type = 'music', infoLabels = {
                'title' : channel.name
            })
            xbmcplugin.addDirectoryItem(HANDLE, PATH + '?playOther=%d' % channel.id, item)

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(HANDLE)

    def playOther(self, idx):
        channel = None
        for c in channels.CHANNELS:
            if c.id == int(idx):
                channel = c
                break

        if channel is None:
            return

        logoImage = os.path.join(LOGO_PATH, str(channel.id) + '.png')
        item = xbmcgui.ListItem(path = channel.url, thumbnailImage = logoImage)
        item.setInfo(type = 'music', infoLabels = {
            'title' : channel.name
        })
        xbmcplugin.setResolvedUrl(HANDLE, True, item)

    def showError(self, message):
        heading = buggalo.getRandomHeading()
        line1 = ADDON.getLocalizedString(900)
        line2 = ADDON.getLocalizedString(901)
        xbmcgui.Dialog().ok(heading, line1, line2, message)

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    LOGO_PATH = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'logos')
    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    try:
        netradio = DkNetradio()
        if PARAMS.has_key('show') and PARAMS['show'][0] == 'dr':
            netradio.showDRChannels()
        elif PARAMS.has_key('show') and PARAMS['show'][0] == 'other':
            netradio.showOtherChannels()
        elif PARAMS.has_key('playOther'):
            netradio.playOther(PARAMS['playOther'][0])
        else:
            netradio.showOverview()

    except Exception:
        buggalo.onExceptionRaised()

