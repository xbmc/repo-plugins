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
from htmlentitydefs import name2codepoint

import re
import sys
import urlparse
import urllib2
import os
import buggalo

import xbmcgui
import xbmcplugin
import xbmcaddon

BASE_URL = 'http://www.pixel.tv'
PROGRAMS_URL = BASE_URL + '/programmer/'
PROGRAM_SERIE_URL = BASE_URL + '/programserie/%s/page/%d'
CLIP_URL = BASE_URL + '/indslag/%s/'


class PixelTVAddon(object):
    def showPrograms(self):
        u = urllib2.urlopen(PROGRAMS_URL)
        html = u.read()
        u.close()

        for m in re.finditer('<div class="fShowDetails">.*?<img src="([^"]+)".*?<a href="http://www.pixel.tv/'
                             'programserie/([^/]+)/">([^<]+)</a>.*?<p>([^<])+</p>', html, re.DOTALL):
            icon = BASE_URL + m.group(1)
            slug = m.group(2)
            title = m.group(3)
            description = m.group(4)

            item = xbmcgui.ListItem(title, iconImage=icon)
            item.setInfo(type='video', infoLabels={
                'title': self.decodeHtmlEntities(title),
                'plot': description,
                'studio': ADDON.getAddonInfo('name')
            })
            item.setProperty('Fanart_Image', FANART)
            url = PATH + '?slug=' + slug + '&page=1'
            xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        xbmcplugin.endOfDirectory(HANDLE)

    def showProgramSeries(self, slug, page):
        u = urllib2.urlopen(PROGRAM_SERIE_URL % (slug, page))
        html = u.read()
        u.close()

        for m in re.finditer('<article class="fGreen">.*?<img.*?src="([^"]+)".*?href="http://www.pixel.tv/indslag/'
                             '([^/]+)/">([^<]+)</a>.*?<time datetime="([^T]+)T.*?<p>([^<]+)</p>', html, re.DOTALL):
            image = m.group(1).replace('-101x59', '')
            clip = m.group(2)
            title = m.group(3)
            date = m.group(4).replace('-', '.')
            description = m.group(5)

            item = xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
            item.setInfo(type='video', infoLabels={
                'title': self.decodeHtmlEntities(title),
                'plot': self.decodeHtmlEntities(description),
                'date': date,
                'studio': ADDON.getAddonInfo('name')
            })
            item.setProperty('IsPlayable', 'true')
            item.setProperty('Fanart_Image', image)
            url = PATH + '?clip=' + clip
            xbmcplugin.addDirectoryItem(HANDLE, url, item)

        page += 1
        if re.search('/programserie/%s/page/%d' % (slug, page), html):
            item = xbmcgui.ListItem(ADDON.getLocalizedString(30000), iconImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            url = PATH + '?slug=' + slug + '&page=' + str(page)
            xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.endOfDirectory(HANDLE)

    def playClip(self, clip):
        u = urllib2.urlopen(CLIP_URL % clip)
        html = u.read()
        u.close()

        m = re.search('<source src="([^"]+)"', html)
        path = m.group(1)

        item = xbmcgui.ListItem(path=path)
        xbmcplugin.setResolvedUrl(HANDLE, True, item)

    def decodeHtmlEntities(self, string):
        """Decodes the HTML entities found in the string and returns the modified string.

        Both decimal (&#000;) and hexadecimal (&x00;) are supported as well as HTML entities,
        such as &aelig;

        Keyword arguments:
        string -- the string with HTML entities

        """
        if type(string) not in [str, unicode]:
            return string

        string = string.decode('utf-8')

        def substituteEntity(match):
            ent = match.group(3)
            if match.group(1) == "#":
                # decoding by number
                if match.group(2) == '':
                    # number is in decimal
                    return unichr(int(ent))
            elif match.group(2) == 'x':
                # number is in hex
                return unichr(int('0x'+ent, 16))
            else:
                # they were using a name
                cp = name2codepoint.get(ent)
                if cp:
                    return unichr(cp)
                else:
                    return match.group()

        entity_re = re.compile(r'&(#?)(x?)(\w+);')
        return entity_re.subn(substituteEntity, string)[0]


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    try:
        ptv = PixelTVAddon()
        if 'slug' in PARAMS:
            ptv.showProgramSeries(PARAMS['slug'][0], int(PARAMS['page'][0]))
        elif 'clip' in PARAMS:
            ptv.playClip(PARAMS['clip'][0])
        else:
            ptv.showPrograms()
    except:
        buggalo.onExceptionRaised()
