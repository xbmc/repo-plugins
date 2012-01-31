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
import os
import sys
import urlparse
import urllib2
import re
import buggalo
import xbmcgui
import xbmcaddon
import xbmcplugin
import random

VIDEO_LIST_URL = 'http://news.tv2.dk/js/video-list.js.php/video.js'
PLAYLIST_URL = 'http://common-dyn.tv2.dk/flashplayer/playlist.xml.php/alias-player_news/autoplay-1/clipid-%s/keys-NEWS,PLAYER.xml'

class TV2NewsAddon(object):
    def listCategories(self):
        data = self._loadJson()
        if data:
            m = re.match('.*sections: \[(.*?)\]', data, re.DOTALL)
            for idx, m in enumerate(re.finditer('title: "([^"]+)"', m.group(1))):
                title = m.group(1)

                item = xbmcgui.ListItem(title, iconImage = ICON)
                item.setProperty('Fanart_Image', FANART)
                url = PATH + '?idx=' + str(idx)
                xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder = True)

            xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)

        xbmcplugin.endOfDirectory(HANDLE, succeeded=data is not None)

    def listCategory(self, idx):
        data = self._loadJson()
        if data:
            clips = list()
            for m in re.finditer('sources: \[(.*?)\] \}', data, re.DOTALL):
                clips.append(m.group(1))

            for m in re.finditer('id: ([0-9]+),\s+title:"(.*?)",\s+image:"([^"]+)",\s+description: "(.*?)",\s+.*?date: "([^"]+)"', clips[idx], re.DOTALL):
                id = m.group(1)
                title = m.group(2).replace("\\'", "'").replace('\\"', '"')
                image = m.group(3)
                description = m.group(4)
                date = m.group(5)

                item = xbmcgui.ListItem(title, iconImage = image)
                item.setInfo('video', {
                    'title' : title,
                    'studio' : ADDON.getAddonInfo('name'),
                    'plot' : description,
                    'date' : date[6:].replace('-', '.')
                })
                item.setProperty('IsPlayable', 'true')
                item.setProperty('Fanart_Image', FANART)
                url = PATH + '?clip=' + str(id)
                xbmcplugin.addDirectoryItem(HANDLE, url, item)

            xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.endOfDirectory(HANDLE, succeeded=data is not None)

    def playClip(self, clipId):
        try:
            u = urllib2.urlopen(PLAYLIST_URL % clipId)
            playlist = u.read()
            u.close()
        except Exception as ex:
            heading = ADDON.getLocalizedString(random.randint(99980, 99985))
            line1 = ADDON.getLocalizedString(30900)
            line2 = ADDON.getLocalizedString(30901)
            xbmcgui.Dialog().ok(heading, line1, line2, str(ex))

            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
            return

        m = re.match('.*video="([^"]+)" splash="([^"]+)"', playlist, re.DOTALL)
        if m:
            item = xbmcgui.ListItem(path = m.group(1), thumbnailImage=m.group(2))
            xbmcplugin.setResolvedUrl(HANDLE, True, item)

    def _loadJson(self):
        try:
            u = urllib2.urlopen(VIDEO_LIST_URL)
            data = u.read()
            u.close()
            return data.decode('iso-8859-1')
        except Exception as ex:
            heading = ADDON.getLocalizedString(random.randint(99980, 99985))
            line1 = ADDON.getLocalizedString(30900)
            line2 = ADDON.getLocalizedString(30901)
            xbmcgui.Dialog().ok(heading, line1, line2, str(ex))

            return None


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')
    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

    try:
        tv2News = TV2NewsAddon()
        if PARAMS.has_key('idx'):
            tv2News.listCategory(int(PARAMS['idx'][0]))
        elif PARAMS.has_key('clip'):
            tv2News.playClip(PARAMS['clip'][0])
        else:
            tv2News.listCategories()
    except Exception:
        buggalo.onExceptionRaised()
