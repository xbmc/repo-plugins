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
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import sys
import os
import urlparse
import urllib2

import xbmcaddon
import xbmcgui
import xbmcplugin

import buggalo

from channels import CHANNELS, CATEGORIES, QUALITIES

TITLE_OFFSET = 31000


class DanishLiveTV(object):
    def showChannels(self, category=None):
        try:
            quality = QUALITIES[int(ADDON.getSetting('quality'))]
        except ValueError:
            quality = QUALITIES[0]  # fallback for old settings value

        if category is not None:
            channels = CATEGORIES[category]
        else:
            channels = CHANNELS

        for channel in channels:
            icon = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'logos', '%d.png' % channel.get_id())
            if not os.path.exists(icon):
                icon = ICON

            idx = None
            if channel.get_config_key():
                try:
                    idx = int(ADDON.getSetting(channel.get_config_key()))
                except ValueError:
                    idx = 0  # fallback for missing settings

            if channel.get_url(quality, idx):
                title = ADDON.getLocalizedString(TITLE_OFFSET + channel.get_id())
                item = xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=icon)
                item.setInfo('video', infoLabels={
                    'title': title,
                    'studio': ADDON.getLocalizedString(channel.get_category())
                })
                item.setProperty('Fanart_Image', FANART)
                item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(HANDLE, PATH + '?playChannel=%d' % channel.id, item)

        xbmcplugin.endOfDirectory(HANDLE)

    def showCategories(self):
        for id in CATEGORIES:
            title = ADDON.getLocalizedString(id)
            item = xbmcgui.ListItem(title, iconImage=ICON, thumbnailImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            url = PATH + '?category=%d' % id
            xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder=True)

        xbmcplugin.endOfDirectory(HANDLE)

    def playChannel(self, id):
        try:
            quality = QUALITIES[int(ADDON.getSetting('quality'))]
        except ValueError:
            quality = QUALITIES[0]  # fallback for old settings value

        for channel in CHANNELS:
            if str(channel.get_id()) == id:
                idx = None
                if channel.get_config_key():
                    try:
                        idx = int(ADDON.getSetting(channel.get_config_key()))
                    except ValueError:
                        idx = 0 # fallback for missing settings

                url = channel.get_url(quality, idx)
                if url:
                    icon = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'logos', '%d.png' % channel.get_id())
                    if not os.path.exists(icon):
                        icon = ICON

                    title = ADDON.getLocalizedString(TITLE_OFFSET + channel.get_id())
                    item = xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=icon, path=url)
                    item.setProperty('Fanart_Image', FANART)
                    item.setProperty('IsLive', 'true')

                    xbmcplugin.setResolvedUrl(HANDLE, True, item)
                    break

    def imInDenmark(self):
        if ADDON.getSetting('warn.if.not.in.denmark') != 'true':
            return  # Don't bother checking

        try:
            u = urllib2.urlopen('http://www.dr.dk/nu/api/estoyendinamarca.json', timeout=30)
            response = u.read()
            u.close()
            imInDenmark = 'true' == response
        except Exception:
            # If an error occurred assume we are not in Denmark
            imInDenmark = False

        if not imInDenmark:
            heading = ADDON.getLocalizedString(99970)
            line1 = ADDON.getLocalizedString(99971)
            line2 = ADDON.getLocalizedString(99972)
            line3 = ADDON.getLocalizedString(99973)
            nolabel = ADDON.getLocalizedString(99974)
            yeslabel = ADDON.getLocalizedString(99975)
            if xbmcgui.Dialog().yesno(heading, line1, line2, line3, nolabel, yeslabel):
                ADDON.setSetting('warn.if.not.in.denmark', 'false')


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id='plugin.video.dr.dk.live')
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')
    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    try:
        danishTV = DanishLiveTV()
        if 'playChannel' in PARAMS:
            danishTV.playChannel(PARAMS['playChannel'][0])
        elif 'category' in PARAMS:
            danishTV.showChannels(int(PARAMS['category'][0]))
        elif ADDON.getSetting('group.by.category') == 'true':
            danishTV.imInDenmark()
            danishTV.showCategories()
        else:
            danishTV.imInDenmark()
            danishTV.showChannels()
    except Exception:
        buggalo.onExceptionRaised()

