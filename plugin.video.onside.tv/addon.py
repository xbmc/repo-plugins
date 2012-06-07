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
import xbmcgui, xbmcplugin, xbmcaddon
import urllib2
import re
import os
import sys
import urlparse
import buggalo

BASE_URL = 'http://onside.dk'
buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'

class OnsideException(Exception):
    pass

class OnsideTV(object):
    def listCategories(self):
        html = self.downloadUrl(BASE_URL + '/onsidetv')
        for m in re.finditer('<a href="/onsidetv/([^/]+)/[^<]+>([^<]+)</a>', html, re.DOTALL):
            slug = m.group(1)
            name = m.group(2)

            item = xbmcgui.ListItem(name[5:], iconImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            xbmcplugin.addDirectoryItem(HANDLE, PATH + '?slug='+ slug + '&page=1', item, True)

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(HANDLE)

    def listPrograms(self, slug, page):
        html = self.downloadUrl(BASE_URL + '/onsidetv/' + slug + '/' + str(page))
        for m in re.finditer('<a href="/fodbold-video/([^"]+)".*?<img src="(.*?)".*?class="video-title">(.*?)</div>.*?class="desc">(.*?)</div>.*?class="date">(.*?)</div>', html, re.DOTALL):
            slug = m.group(1)
            image = m.group(2)
            title = m.group(3)
            description = m.group(4)
            dateStr = m.group(5)

            icon = BASE_URL + image
            icon = icon.replace('136x91', 'onsidetv_658x366')
            item = xbmcgui.ListItem(title, iconImage = icon, thumbnailImage = icon)
            item.setProperty('IsPlayable', 'true')
            item.setProperty('Fanart_Image', icon)
            item.setInfo(type = 'video', infoLabels = {
                'studio' : ADDON.getAddonInfo('name'),
                'title' : title,
                'plot' : description,
                'date' : dateStr[0:10]
            })
            xbmcplugin.addDirectoryItem(HANDLE, PATH + '?play=' + slug, item)

        if ADDON.getSetting('show.load.next.page') == 'true':
            m = re.search('<a href="/onsidetv/([^/]+)/\d+">&gt;&gt;', html)
            if m:
                item = xbmcgui.ListItem(ADDON.getLocalizedString(30000), iconImage=ICON)
                item.setProperty('Fanart_Image', FANART)
                xbmcplugin.addDirectoryItem(HANDLE, PATH + '?slug='+ m.group(1) + '&page=' + str(page + 1), item, True)

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.endOfDirectory(HANDLE)

    def playProgram(self, slug):
        url = BASE_URL + '/fodbold-video/' + slug
        html = self.downloadUrl(url)
        m = re.search('id="onside_video_player" href="(.*?)"', html)

        videoUrl = m.group(1)
        if videoUrl[0:7] != 'http://':
            videoUrl = BASE_URL + videoUrl

        item = xbmcgui.ListItem(path = videoUrl)
        xbmcplugin.setResolvedUrl(HANDLE, True, item)

    def downloadUrl(self, url):
        try:
            u = urllib2.urlopen(url)
            data = u.read()
            u.close()
            return data
        except Exception, ex:
            raise OnsideException(ex)

    def showError(self, message):
        heading = buggalo.getRandomHeading()
        line1 = ADDON.getLocalizedString(30900)
        line2 = ADDON.getLocalizedString(30901)
        xbmcgui.Dialog().ok(heading, line1, line2, message)

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id = 'plugin.video.onside.tv')
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')
    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

    otv = OnsideTV()
    try:
        if PARAMS.has_key('slug'):
            otv.listPrograms(PARAMS['slug'][0], int(PARAMS['page'][0]))
        elif PARAMS.has_key('play'):
            otv.playProgram(PARAMS['play'][0])
        else:
            otv.listCategories()
    except OnsideException, ex:
        otv.showError(str(ex))
    except Exception:
        buggalo.onExceptionRaised()
