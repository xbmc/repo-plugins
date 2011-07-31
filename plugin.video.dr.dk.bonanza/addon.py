import os
import re
import sys
import simplejson
import cgi as urlparse
import urllib2
from htmlentitydefs import name2codepoint

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

BASE_URL = 'http://www.dr.dk/Bonanza/'

class Bonanza(object):
    def search(self):
        keyboard = xbmc.Keyboard('', ADDON.getLocalizedString(30001))
        keyboard.doModal()
        if keyboard.isConfirmed():
            html = self._downloadUrl('http://www.dr.dk/bonanza/search.htm?&type=video&limit=120&needle=' + keyboard.getText().replace(' ', '+'))
            self.addContent(html)
            xbmcplugin.endOfDirectory(HANDLE)


    def showCategories(self):
        html = self._downloadUrl(BASE_URL)

        item = xbmcgui.ListItem(ADDON.getLocalizedString(30001), iconImage = ICON)
        item.setProperty('Fanart_Image', FANART)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?mode=search', item, True)
        item = xbmcgui.ListItem(ADDON.getLocalizedString(30002), iconImage = ICON)
        item.setProperty('Fanart_Image', FANART)
        xbmcplugin.addDirectoryItem(HANDLE, PATH + '?mode=recommend', item, True)

        for m in re.finditer('<a href="(/Bonanza/kategori/.*\.htm)">(.*)</a>', html):
            path = m.group(1)
            title = m.group(2)

            item = xbmcgui.ListItem(title, iconImage = ICON)
            item.setProperty('Fanart_Image', FANART)
            item.setInfo(type = 'video', infoLabels = {
                'title' : title
            })
            url = PATH + '?mode=subcat&url=http://www.dr.dk' + path
            xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(HANDLE)


    def showRecommendations(self):
        html = self._downloadUrl(BASE_URL)

        # remove anything but 'Redaktionens favoritter'
        html = html[html.find('<span class="tabTitle">Redaktionens Favoritter</span>'):]
        self.addSubCategories(html)
        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(HANDLE)


    def showSubCategories(self, url):
        html = self._downloadUrl(url.replace(' ', '+'))

        # remove 'Redaktionens favoritter' as they are located on every page
        html = html[:html.find('<span class="tabTitle">Redaktionens Favoritter</span>')]

        self.addSubCategories(html)
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

            item = xbmcgui.ListItem(infoLabels['title'], iconImage = self.findFileLocation(json, 'Thumb'))
            item.setProperty('Fanart_Image', FANART)
            item.setInfo('video', infoLabels)

            rtmp_url = self.findFileLocation(json, 'VideoHigh')
            if rtmp_url is None:
                rtmp_url = self.findFileLocation(json, 'VideoMid')
            if rtmp_url is None:
                rtmp_url = self.findFileLocation(json, 'VideoLow')

            # patch rtmp_url to work with mplayer
            m = re.match('(rtmp://.*?)/(.*)', rtmp_url)
            rtmp_url = '%s/bonanza/%s' % (m.group(1), m.group(2))
            xbmcplugin.addDirectoryItem(HANDLE, rtmp_url, item, False)

    def findFileLocation(self, json, type):
        for file in json['Files']:
            if file['Type'] == type:
                return file['Location']
        return None
    
    def _downloadUrl(self, url):
        u = urllib2.urlopen(url)
        data = u.read()
        u.close()
        return data

    def _decodeHtmlEntities(self, string):
        """Decodes the HTML entities found in the string and returns the modified string.

        Both decimal (&#000;) and hexadecimal (&x00;) are supported as well as HTML entities,
        such as &aelig;

        Keyword arguments:
        string -- the string with HTML entities

        """
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


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id = 'plugin.video.dr.dk.bonanza')
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    b = Bonanza()
    if PARAMS.has_key('mode') and PARAMS['mode'][0] == 'subcat':
        b.showSubCategories(PARAMS['url'][0])
    elif PARAMS.has_key('mode') and PARAMS['mode'][0] == 'content':
        b.showContent(PARAMS['url'][0])
    elif PARAMS.has_key('mode') and PARAMS['mode'][0] == 'search':
        b.search()
    elif PARAMS.has_key('mode') and PARAMS['mode'][0] == 'recommend':
        b.showRecommendations()
    else:
        b.showCategories()

