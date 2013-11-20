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
import sys
import os
import urlparse
import urllib2
import platform

import xbmcaddon
import xbmcgui
import xbmcplugin

import buggalo

from channels import CHANNELS, CATEGORIES, QUALITIES, Q_BEST, Q_RASPBERRY_PI

TITLE_OFFSET = 30500


class DanishLiveTV(object):
    def showChannels(self, category=None):
        try:
            quality = QUALITIES[int(ADDON.getSetting('quality'))]
        except ValueError:
            quality = QUALITIES[Q_BEST]  # fallback for old settings value

        if category is not None:
            channels = CATEGORIES[category]
        else:
            channels = CHANNELS

        for channel in channels:
            icon = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'logos', '%d.png' % channel.category_id)
            if not os.path.exists(icon):
                icon = ICON

            idx = None
            if channel.config_key:
                try:
                    idx = int(ADDON.getSetting(channel.config_key))
                except ValueError:
                    idx = 0  # fallback for missing settings

            if channel.get_url(quality, idx):
                title = ADDON.getLocalizedString(TITLE_OFFSET + channel.category_id)
                item = xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=icon)
                item.setInfo('video', infoLabels={
                    'title': title,
                    'studio': ADDON.getLocalizedString(channel.category)
                })
                item.setProperty('Fanart_Image', FANART)
                item.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(HANDLE, PATH + '?playChannel=%d' % channel.category_id, item)

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
            quality = QUALITIES[Q_BEST]  # fallback for old settings value

        for channel in CHANNELS:
            if str(channel.category_id) == id:
                idx = None
                if channel.config_key:
                    try:
                        idx = int(ADDON.getSetting(channel.config_key))
                    except ValueError:
                        idx = 0  # fallback for missing settings

                url = channel.get_url(quality, idx)
                if url:
                    icon = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'logos', '%d.png' % channel.category_id)
                    if not os.path.exists(icon):
                        icon = ICON

                    title = ADDON.getLocalizedString(TITLE_OFFSET + channel.category_id)
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
            heading = ADDON.getLocalizedString(30970)
            line1 = ADDON.getLocalizedString(30971)
            line2 = ADDON.getLocalizedString(30972)
            line3 = ADDON.getLocalizedString(30973)
            nolabel = ADDON.getLocalizedString(30974)
            yeslabel = ADDON.getLocalizedString(30975)
            if xbmcgui.Dialog().yesno(heading, line1, line2, line3, nolabel, yeslabel):
                ADDON.setSetting('warn.if.not.in.denmark', 'false')

    def isRaspberryPi(self):
        # inspired by plugin.image.xzen
        try:
            uname = platform.uname()
        except:
            uname = os.uname()

        return 'raspbmc' in uname or 'armv6l' in uname

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')
    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    try:
        danishTV = DanishLiveTV()
        if ADDON.getSetting('quality') == '':
            # set default value based on what we are able to detect
            if danishTV.isRaspberryPi():
                ADDON.setSetting('quality', str(Q_RASPBERRY_PI))
            else:
                ADDON.setSetting('quality', str(Q_BEST))

        if 'playChannel' in PARAMS:
            danishTV.playChannel(PARAMS['playChannel'][0])
        elif 'category' in PARAMS:
            danishTV.showChannels(int(PARAMS['category'][0]))
        elif ADDON.getSetting('group.by.category') == 'true' and ADDON.getSetting('raspberry.pi.compatible.streams') == 'false':
            danishTV.imInDenmark()
            danishTV.showCategories()
        else:
            danishTV.imInDenmark()
            danishTV.showChannels()
    except Exception:
        buggalo.onExceptionRaised()

