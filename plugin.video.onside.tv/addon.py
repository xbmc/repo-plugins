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
import simplejson
import buggalo

BASE_URL = 'http://onside.dk'
VIDEO_URL = 'http://video.onside.dk/api/photo/list?raw&format=json&photo_id=%s&source=embed&player_id=0'

class OnsideException(Exception):
    pass

class OnsideTV(object):
    def listVideos(self, page = 0):
        url = BASE_URL + '/onside_tv/arkiv'
        if page > 0:
            url += '?page=%d' % page

        html = self.downloadUrl(url)
        for m in re.finditer('field-created">(.*?)<a href="([^"]+)"><span class="Video">([^<]+)<', html, re.DOTALL):
            path = m.group(2)
            title = m.group(3).replace('&#039;', "'")

            item = xbmcgui.ListItem(title, iconImage = ICON, thumbnailImage = ICON)
            item.setProperty('IsPlayable', 'true')
            item.setProperty('Fanart_Image', FANART)
            item.setInfo(type = 'video', infoLabels = {
                'studio' : ADDON.getAddonInfo('name'),
                'title' : title,
            })
            xbmcplugin.addDirectoryItem(HANDLE, PATH + '?play=' + path, item)

        if ADDON.getSetting('show.load.next.page') == 'true':
            if -1 != html.find('<a href="/onside_tv/arkiv?page=' + str(page + 1) + '"'):
                item = xbmcgui.ListItem(ADDON.getLocalizedString(30000), iconImage=ICON)
                item.setProperty('Fanart_Image', FANART)
                xbmcplugin.addDirectoryItem(HANDLE, PATH + '?page=' + str(page + 1), item, True)

        xbmcplugin.endOfDirectory(HANDLE)

    def playProgram(self, path):
        url = BASE_URL + path
        html = self.downloadUrl(url)
        m = re.search('photo_id=(\d+)', html)
        photoId = m.group(1)
        json = simplejson.loads(self.downloadUrl(VIDEO_URL % photoId))
        path = 'http://video.onside.dk' + json['photos'][0]['video_hd_download']
        item = xbmcgui.ListItem(path = path)
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

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    otv = OnsideTV()
    try:
        if PARAMS.has_key('play'):
            otv.playProgram(PARAMS['play'][0])
        elif PARAMS.has_key('page'):
            otv.listVideos(int(PARAMS['page'][0]))
        else:
            otv.listVideos()

    except OnsideException, ex:
        otv.showError(str(ex))
    except Exception:
        buggalo.onExceptionRaised()
