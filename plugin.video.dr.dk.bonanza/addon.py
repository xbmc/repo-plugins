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
import re
import sys
import simplejson
import urlparse
import urllib2
from htmlentitydefs import name2codepoint
import buggalo

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

BASE_URL = 'http://www.dr.dk/Bonanza/'
VIDEO_TYPES = ['VideoHigh', 'VideoMid', 'VideoLow', 'Audio']

class BonanzaException(Exception):
    pass

class Bonanza(object):
    def search(self):
        keyboard = xbmc.Keyboard('', ADDON.getLocalizedString(30001))
        keyboard.doModal()
        if keyboard.isConfirmed():
            html = self._downloadUrl('http://www.dr.dk/bonanza/search.htm?&type=video&limit=120&needle=' + keyboard.getText().replace(' ', '+'))
            self.addContent(html)
            xbmcplugin.endOfDirectory(HANDLE)


    def showCategories(self):
        items = list()
        html = self._downloadUrl(BASE_URL)

        item = xbmcgui.ListItem(ADDON.getLocalizedString(30001), iconImage = ICON)
        item.setProperty('Fanart_Image', FANART)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?mode=search', item, True)
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30002), iconImage = ICON)
        item.setProperty('Fanart_Image', FANART)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?mode=recommend', item, True)
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30004), iconImage = ICON)
        item.setProperty('Fanart_Image', FANART)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?mode=latest', item, True)

        for m in re.finditer('<a href="(/Bonanza/kategori/.*\.htm)">(.*)</a>', html):
            path = m.group(1)
            title = m.group(2)

            item = xbmcgui.ListItem(title, iconImage = ICON)
            item.setProperty('Fanart_Image', FANART)
            item.setInfo(type = 'video', infoLabels = {
                'title' : title
            })
            url = PATH + '?mode=subcat&url=http://www.dr.dk' + path
            items.append((url, item, True))

        xbmcplugin.addDirectoryItems(HANDLE, items)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(HANDLE)


    def showRecommendations(self):
        html = self._downloadUrl(BASE_URL)
        tab = self._getTab(html, 'redaktionens favoritter')
        self.addSubCategories(tab)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(HANDLE)

    def showLatest(self):
        html = self._downloadUrl(BASE_URL)
        tab = self._getTab(html, 'senest tilf.*?bonanza')
        self.addSubCategories(tab)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(HANDLE)


    def showSubCategories(self, url):
        html = self._downloadUrl(url.replace(' ', '+'))
        tab = self._getTab(html, '') # will return first tab found
        self.addSubCategories(tab)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(HANDLE)

    def showContent(self, url):
        html = self._downloadUrl(url)
        self.addContent(html)

        xbmcplugin.endOfDirectory(HANDLE)

    def addSubCategories(self, html):
        for m in re.finditer('<a href="(http://www\.dr\.dk/bonanza/serie/[^\.]+\.htm)"[^>]+>..<img src="(http://downol\.dr\.dk/download/bonanza/collectionThumbs/[^"]+)"[^>]+>..<b>([^<]+)</b>..<span>([^<]+)</span>..</a>', html, re.DOTALL):
            url = m.group(1)
            image = m.group(2)
            title = m.group(3)
            description = m.group(4)

            item = xbmcgui.ListItem(title, iconImage = image)
            item.setProperty('Fanart_Image', FANART)
            item.setInfo(type = 'video', infoLabels = {
                'title' : title,
                'plot' : description
            })
            url = PATH + '?mode=content&url=' + url
            xbmcplugin.addDirectoryItem(HANDLE, url, item, True)


    def addContent(self, html):
        items = list()
        for m in re.finditer('newPlaylist\(([^"]+)"', html):
            raw = m.group(1)[:-2].replace('&quot;', '"')
            json = simplejson.loads(raw)

            infoLabels = {}
            if json.has_key('Title') and json['Title'] is not None:
                infoLabels['title'] = self._decodeHtmlEntities(json['Title'])
            if json.has_key('Description') and json['Description'] is not None:
                infoLabels['plot'] = self._decodeHtmlEntities(json['Description'])
            if json.has_key('Colophon') and json['Colophon'] is not None:
                infoLabels['writer'] = self._decodeHtmlEntities(json['Colophon'])
            if json.has_key('Actors') and json['Actors'] is not None:
                infoLabels['cast'] = self._decodeHtmlEntities(json['Actors'])
            if json.has_key('Rating') and json['Rating'] is not None:
                infoLabels['rating'] = json['Rating']
            if json.has_key('FirstPublished') and json['FirstPublished'] is not None:
                infoLabels['year'] = int(json['FirstPublished'][:4])
            if json.has_key('Duration') and json['Duration'] is not None:
                infoLabels['duration'] = self._secondsToDuration(int(json['Duration']) / 1000)
            infoLabels['studio'] = ADDON.getAddonInfo('name')

            thumb = self.findFileLocation(json, 'Thumb')
            if thumb is None:
                thumb = ICON
            item = xbmcgui.ListItem(infoLabels['title'], iconImage=thumb, thumbnailImage=thumb)
            item.setProperty('Fanart_Image', FANART)
            item.setProperty('IsPlayable', 'true')
            item.setInfo('video', infoLabels)

            url = '?mode=play'
            for file in json['Files']:
                if file['Type'] in VIDEO_TYPES:
                    url += '&' + file['Type'] + '=' + file['Location']

            items.append((PATH + url, item, False))
        xbmcplugin.addDirectoryItems(HANDLE, items)

    def playContent(self):
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        print PARAMS
        for type in VIDEO_TYPES:
            if PARAMS.has_key(type.lower()):
                url = self.fixRtmpUrl(PARAMS[type.lower()][0])
                item = xbmcgui.ListItem(type, path = url)
                playlist.add(url, item)

        xbmcplugin.setResolvedUrl(HANDLE, True, playlist[0])

    def fixRtmpUrl(self, url):
        if url[0:4] == 'rtmp':
            # patch videoUrl to work with xbmc
            m = re.match('(rtmp://.*?)/(.*)', url)
            url = '%s/bonanza/%s' % (m.group(1), m.group(2))
        return url

    def findFileLocation(self, json, type):
        for file in json['Files']:
            if file['Type'] == type:
                return file['Location']
        return None
    
    def _downloadUrl(self, url):
        try:
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

    def _secondsToDuration(self, input):
        """Formats the seconds to a duration string as used by XBMC.
    
        Keyword arguments:
        input -- the duration in seconds
    
        """
        hours = input / 3600
        minutes = (input % 3600) / 60
        seconds = (input % 3600) % 60 
    
        return "%02d:%02d:%02d" % (hours, minutes, seconds)


    def _getTab(self, html, tabLabel):
        m = re.search('(<div id="tabWrapper" class="tabWrapper"><span class="tabTitle">' + tabLabel + '.*?</div>)', html, re.DOTALL + re.IGNORECASE)
        return m.group(1)

    def showError(self, message):
        heading = buggalo.getRandomHeading()
        line1 = ADDON.getLocalizedString(30900)
        line2 = ADDON.getLocalizedString(30901)
        xbmcgui.Dialog().ok(heading, line1, line2, message)

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id = 'plugin.video.dr.dk.bonanza')
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    b = Bonanza()
    try:
        if PARAMS.has_key('mode') and PARAMS['mode'][0] == 'subcat':
            b.showSubCategories(PARAMS['url'][0])
        elif PARAMS.has_key('mode') and PARAMS['mode'][0] == 'content':
            b.showContent(PARAMS['url'][0])
        elif PARAMS.has_key('mode') and PARAMS['mode'][0] == 'search':
            b.search()
        elif PARAMS.has_key('mode') and PARAMS['mode'][0] == 'recommend':
            b.showRecommendations()
        elif PARAMS.has_key('mode') and PARAMS['mode'][0] == 'latest':
            b.showLatest()
        elif PARAMS.has_key('mode') and PARAMS['mode'][0] == 'play':
            b.playContent()
        else:
            b.showCategories()

    except BonanzaException, ex:
        b.showError(str(ex))

    except Exception:
        buggalo.onExceptionRaised()


