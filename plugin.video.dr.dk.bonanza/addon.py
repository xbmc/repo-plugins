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
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import os
import re
import sys
import urlparse
import urllib2
from htmlentitydefs import name2codepoint
import buggalo

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

try:
    import json
except:
    import simplejson as json

BASE_URL = 'http://www.dr.dk/bonanza/'


class BonanzaException(Exception):
    pass


class Bonanza(object):
    def search(self):
        keyboard = xbmc.Keyboard('', ADDON.getLocalizedString(30001))
        keyboard.doModal()
        if keyboard.isConfirmed():
            html = self._downloadUrl('http://www.dr.dk/bonanza/sog?q=' + keyboard.getText().replace(' ', '+'))

            items = list()
            pattern = '<a href="/bonanza/(serie/.*?)".*?' \
                      '<img src="(//asset\.dr\.dk/[^"]+)".*?' \
                      '<h3.*?>([^<]+)</h3>.*?<p>([^<]+)</p>'

            for m in re.finditer(pattern, html, re.DOTALL):
                url = BASE_URL + m.group(1)
                image = 'http:' + m.group(2)
                title = self._decodeHtmlEntities(m.group(3).decode('utf-8'))
                description = self._decodeHtmlEntities(m.group(4).decode('utf-8'))

                infoLabels = {
                    'title': title,
                    'plot': description,
                    'studio': ADDON.getAddonInfo('name')}

                item = xbmcgui.ListItem(infoLabels['title'], iconImage=image, thumbnailImage=image)
                item.setProperty('Fanart_Image', FANART)
                item.setProperty('IsPlayable', 'true')
                item.setInfo('video', infoLabels)

                url = '?mode=play&url=' + url
                items.append((PATH + url, item, False))
            xbmcplugin.addDirectoryItems(HANDLE, items)

            xbmcplugin.endOfDirectory(HANDLE)

    def showCategories(self):
        items = list()
        html = self._downloadUrl(BASE_URL)

        item = xbmcgui.ListItem(ADDON.getLocalizedString(30001), iconImage=ICON)
        item.setProperty('Fanart_Image', FANART)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?mode=search', item, True)

        pattern = '<a href="(/bonanza/kategori/.*)">(.*)</a>'
        for m in re.finditer(pattern, html):
            path = m.group(1)
            title = m.group(2)

            item = xbmcgui.ListItem(title, iconImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            item.setInfo('video', infoLabels={
                'title': title
            })
            url = PATH + '?mode=subcat&url=http://www.dr.dk' + path
            items.append((url, item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(HANDLE)

    def showSubCategories(self, url):
        html = self._downloadUrl(url.replace(' ', '+'))
        self.addSubCategories(html)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(HANDLE)

    def showContent(self, url):
        html = self._downloadUrl(url)
        self.addContent(html)

        xbmcplugin.endOfDirectory(HANDLE)

    def addSubCategories(self, html):
        pattern = '<a href="/bonanza/(serie/.*?)".*?' \
                  '<img src="(//asset\.dr\.dk/[^"]+)".*?' \
                  '<h3>([^<]+)</h3>.*?<p>([^<]+)</p>'
        for m in re.finditer(pattern, html, re.DOTALL):
            url = BASE_URL + m.group(1)
            image = 'http:' + m.group(2)
            title = self._decodeHtmlEntities(m.group(3).decode('utf-8'))
            description = self._decodeHtmlEntities(m.group(4).decode('utf-8'))

            item = xbmcgui.ListItem(title, iconImage=image)
            item.setProperty('Fanart_Image', FANART)
            item.setInfo('video', infoLabels={
                'title': title,
                'plot': description
            })
            url = PATH + '?mode=content&url=' + url
            xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

    def addContent(self, html):
        items = list()
        pattern = '<a href="/bonanza/(serie/.*?)" title="([^"]+)".*?' \
                  '<img src="(//asset\.dr\.dk/[^"]+)".*?' \
                  '<h3>([^<]+)</h3>'

        for m in re.finditer(pattern, html, re.DOTALL):
            url = BASE_URL + m.group(1)
            description = self._decodeHtmlEntities(m.group(2).decode('utf-8'))
            image = 'http:' + m.group(3)
            title = self._decodeHtmlEntities(m.group(4).decode('utf-8'))

            infoLabels = {
                'title': title,
                'plot': description,
                'studio': ADDON.getAddonInfo('name')}

            item = xbmcgui.ListItem(infoLabels['title'], iconImage=image, thumbnailImage=image)
            item.setProperty('Fanart_Image', FANART)
            item.setProperty('IsPlayable', 'true')
            item.setInfo('video', infoLabels)

            url = '?mode=play&url=' + url
            items.append((PATH + url, item, False))
        xbmcplugin.addDirectoryItems(HANDLE, items)


    def playContent(self, url):
        html = self._downloadUrl(url)
        pattern = '<source.*?src="([^"]+)"'
        m = re.search(pattern, html, re.DOTALL)
        if m is not None:
            item = xbmcgui.ListItem(path=m.group(1))
            xbmcplugin.setResolvedUrl(HANDLE, True, item)
        else:
            xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())

    def _downloadUrl(self, url):
        try:
            xbmc.log(url)
            u = urllib2.urlopen(url)
            data = u.read()
            u.close()
            return data
        except Exception, ex:
            raise BonanzaException(ex)

    def _decodeHtmlEntities(self, string):
        """Decodes the HTML entities found in the string and returns the modified string.

        Both decimal (&#000;) and hexadecimal (&x00;) are supported as well as HTML entities,
        such as &aelig;

        Keyword arguments:
        string -- the string with HTML entities

        """
        if type(string) not in [str, unicode]:
            return string

        def substituteEntity(match):
            ent = match.group(3)
            if match.group(1) == "#":
                # decoding by number
                if match.group(2) == '':
                    # number is in decimal
                    return unichr(int(ent))
            elif match.group(2) == 'x':
                # number is in hex
                return unichr(int('0x' + ent, 16))
            else:
                # they were using a name
                cp = name2codepoint.get(ent)
                if cp:
                    return unichr(cp)
                else:
                    return match.group()

        entity_re = re.compile(r'&(#?)(x?)(\w+);')
        return entity_re.subn(substituteEntity, string)[0]

    def showError(self, message):
        heading = buggalo.getRandomHeading()
        line1 = ADDON.getLocalizedString(30900)
        line2 = ADDON.getLocalizedString(30901)
        xbmcgui.Dialog().ok(heading, line1, line2, message)


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    b = Bonanza()
    try:
        if 'mode' in PARAMS:
            if PARAMS['mode'][0] == 'subcat':
                b.showSubCategories(PARAMS['url'][0])
            elif PARAMS['mode'][0] == 'content':
                b.showContent(PARAMS['url'][0])
            elif PARAMS['mode'][0] == 'search':
                b.search()
            elif PARAMS['mode'][0] == 'play':
                b.playContent(PARAMS['url'][0])
        else:
            b.showCategories()

    except BonanzaException, ex:
        b.showError(str(ex))

    except Exception:
        buggalo.onExceptionRaised()
