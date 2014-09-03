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
import urllib2
import xbmcgui
import xbmcplugin
import xbmcaddon
import buggalo

BASE_URL = 'http://www.gamereactor.dk'
GRTV_URL = BASE_URL + '/grtv/'
PLAYLIST_URL = GRTV_URL + 'embed/sliderlist.php?id='
USER_AGENT = 'Mozilla/5.0 (compatible, XBMC addon)'


class GRTVAddon(object):
    def showCategories(self):
        html = self._downloadUrl(GRTV_URL)
        for m in re.finditer("'list_20latest.php\?l=(.*?)', '20latest'\);\">([^<]+)<", html):
            slug = m.group(1)
            title = m.group(2)

            item = xbmcgui.ListItem(title, iconImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            item.setInfo(type='video', infoLabels={
                'title': title
            })

            url = PATH + '?slug=' + slug
            xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder=True)

        xbmcplugin.endOfDirectory(HANDLE)

    def showCategory(self, slug):
        html = self._downloadUrl(GRTV_URL + 'list_20latest.php?l=' + slug.replace(' ', '%20'))
        for m in re.finditer('<a href="\?id=([0-9]+).*?url\(\'([^\']+)\'\).*?<h4>(.*?)</h4><span class="publishDate">([0-9]+)-([0-9]+)-([0-9]+)</span><p>(.*?</p>)', html, re.DOTALL):
            clipId = m.group(1)
            icon = BASE_URL + m.group(2).replace('_w184.jpg', '_w926.jpg')
            title = m.group(3)
            year = m.group(4)
            month = m.group(5)
            date = m.group(6)
            description = m.group(7)

            item = xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=icon)
            item.setProperty('Fanart_Image', icon)
            item.setProperty('IsPlayable', 'true')
            item.setInfo(type='video', infoLabels={
                'title': title,
                'plot': description,
                'studio': ADDON.getAddonInfo('name'),
                'date': '%s.%s.%s' % (date, month, year),
                'aired': '%s-%s-%s' % (date, month, year),
                'year': int(year)
            })

            url = PATH + '?id=' + clipId
            xbmcplugin.addDirectoryItem(HANDLE, url, item)

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.endOfDirectory(HANDLE)

    def playVideo(self, clipId):
        xml = self._downloadUrl(PLAYLIST_URL + clipId)
        m = re.search('<location>([^<]+)</location>', xml)
        item = xbmcgui.ListItem(path=m.group(1))
        xbmcplugin.setResolvedUrl(HANDLE, True, item)

    def _downloadUrl(self, url):
        r = urllib2.Request(url)
        r.add_header('User-Agent', USER_AGENT)
        u = urllib2.urlopen(r)
        contents = u.read()
        u.close()

        return contents


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    try:
        grtv = GRTVAddon()
        if 'id' in PARAMS:
            grtv.playVideo(PARAMS['id'][0])
        elif 'slug' in PARAMS:
            grtv.showCategory(PARAMS['slug'][0])
        else:
            grtv.showCategories()
    except Exception:
        buggalo.onExceptionRaised()