#
#      Copyright (C) 2014 Tommy Winther
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

CHANNELS_URL = 'http://www.dr.dk/radio/external/channels?mediaType=radio'


def showOverview():
    item = xbmcgui.ListItem(ADDON.getLocalizedString(30100), iconImage=ICON)
    item.setProperty('Fanart_Image', FANART)
    xbmcplugin.addDirectoryItem(HANDLE, PATH + '?show=dr', item, True)

    item = xbmcgui.ListItem(ADDON.getLocalizedString(30101), iconImage=ICON)
    item.setProperty('Fanart_Image', FANART)
    xbmcplugin.addDirectoryItem(HANDLE, PATH + '?show=other', item, True)

    xbmcplugin.endOfDirectory(HANDLE)


def showDRChannels():
    try:
        u = urllib2.urlopen(CHANNELS_URL)
        channelList = simplejson.loads(u.read())
        u.close()
    except Exception, ex:
        showError(str(ex))
        return

    for channel in channelList['Data']:
        sourceUrl = channel['SourceUrl']
        logoImage = os.path.join(LOGO_PATH, sourceUrl[sourceUrl.rindex('/') + 1:] + '.png')
        if xbmcvfs.exists(logoImage):
            item = xbmcgui.ListItem(channel['Title'], iconImage=logoImage)
        else:
            item = xbmcgui.ListItem(channel['Title'], iconImage=ICON)

        item.setProperty('IsPlayable', 'true')
        item.setProperty('Fanart_Image', FANART)
        item.setInfo(type='music', infoLabels={
            'title': channel['Title']
        })

        url = None

        if 'StreamingServers' in channel:
            for server in channel['StreamingServers']:
                if 'LinkType' in server and server['LinkType'] == 'Streaming' and 'Qualities' in server:
                    try:
                        url = server['Server'] + '/' + server['Qualities'][0]['Streams'][0]['Stream']
                        break
                    except:
                        pass

        if url:
            xbmcplugin.addDirectoryItem(HANDLE, url + ' live=1', item)

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.endOfDirectory(HANDLE)


def showOtherChannels():
    for channel in channels.CHANNELS:
        logoImage = os.path.join(LOGO_PATH, str(channel.id) + '.png')
        if xbmcvfs.exists(logoImage):
            item = xbmcgui.ListItem(channel.name, iconImage=logoImage)
        else:
            item = xbmcgui.ListItem(channel.name, iconImage=ICON)

        item.setProperty('IsPlayable', 'true')
        item.setProperty('Fanart_Image', FANART)
        item.setInfo(type='music', infoLabels={
            'title': channel.name
        })
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?playOther=%d' % channel.id, item)

    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(HANDLE)


def playOther(idx):
    channel = None
    for c in channels.CHANNELS:
        if c.id == int(idx):
            channel = c
            break

    if channel is None:
        return

    logoImage = os.path.join(LOGO_PATH, str(channel.id) + '.png')
    item = xbmcgui.ListItem(path=channel.url, thumbnailImage=logoImage)
    item.setInfo(type='music', infoLabels={
        'title': channel.name
    })
    xbmcplugin.setResolvedUrl(HANDLE, True, item)


def showError(message):
    heading = buggalo.getRandomHeading()
    line1 = ADDON.getLocalizedString(30900)
    line2 = ADDON.getLocalizedString(30901)
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
        if 'show' in PARAMS and PARAMS['show'][0] == 'dr':
            showDRChannels()
        elif 'show' in PARAMS and PARAMS['show'][0] == 'other':
            showOtherChannels()
        elif 'playOther' in PARAMS:
            playOther(PARAMS['playOther'][0])
        else:
            showOverview()

    except Exception:
        buggalo.onExceptionRaised()

