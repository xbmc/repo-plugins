import re
import sys
import simplejson
import os
import urlparse
import urllib2
from htmlentitydefs import name2codepoint

import xbmcgui
import xbmcplugin
import xbmcaddon

KEY_TO_TITLE = {
    'beep' : 30001,
    'sport' : 30002,
    'station2' : 30003,
    'zulu' : 30004,
    'tour2009' : 30005,
    'mogensen-kristiansen' : 30006,
    'news-finans' : 30007,
    'nyheder' : 30008,
    'most-viewed' : 30009,
    'go' : 30010,
    'programmer' : 30011,
    'finans' : 30012,
    'musik' : 30013,
    'latest' : 30014
}

BASE_URL = 'http://video.tv2.dk/js/video-list.js.php/index.js'
class TV2VideoAddon(object):
    def showOverview(self):
        json = self._loadJson()

        for key in json.keys():
            if KEY_TO_TITLE.has_key(key):
                title = ADDON.getLocalizedString(KEY_TO_TITLE[key])
                item = xbmcgui.ListItem(title, iconImage=ICON, thumbnailImage=ICON)
            else:
                item = xbmcgui.ListItem(key, iconImage=ICON, thumbnailImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            url = PATH + '?key=' + key
            xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(HANDLE)


    def showCategory(self, key):
        json = self._loadJson()

        for e in json[key]:
            infoLabels = dict()
            if e['headline'] is not None:
                infoLabels['title'] = self._decodeHtmlEntities(e['headline'])
            if e['descr'] is not None:
                infoLabels['plot'] = self._decodeHtmlEntities(e['descr'])
            if e['date'] is not None:
                infoLabels['year'] = int(e['date'][6:])
                infoLabels['date'] = e['date'].replace('-', '.')
            if e['duration'] is not None:
                infoLabels['duration'] = e['duration'][1:9]
            infoLabels['studio'] = ADDON.getAddonInfo('name')

            item = xbmcgui.ListItem(infoLabels['title'], iconImage = e['img'], thumbnailImage=e['img'])
            item.setInfo('video', infoLabels)
            item.setProperty('Fanart_Image', FANART)
            item.setProperty('IsPlayable', 'true')
            url = PATH + '?id=' + str(e['id'])

            xbmcplugin.addDirectoryItem(HANDLE, url, item)

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.endOfDirectory(HANDLE)


    def playVideo(self, id):
        # retrieve masquarade playlist
        u = urllib2.urlopen('http://common.tv2.dk/flashplayer/playlistSimple.xml.php/clip-' + id + '.xml')
        playlist = u.read()
        u.close()
        m = re.search('video="([^"]+)" materialId="([^"]+)"', playlist)

        # retrive crossdomain to setup next request for geocheck
        u = urllib2.urlopen('http://common-dyn.tv2.dk/crossdomain.xml')
        u.read()
        u.close()

        # retrieve real playlist
        u = urllib2.urlopen('http://common-dyn.tv2.dk/flashplayer/geocheck.php?id=' + m.group(2) + '&file=' + m.group(1))
        playlist = u.read()
        u.close()

        item = xbmcgui.ListItem(path = playlist)
        xbmcplugin.setResolvedUrl(HANDLE, True, item)

    def _loadJson(self):
        u = urllib2.urlopen(BASE_URL)
        json = u.read()
        u.close()

        # get json part of js file
        m = re.search('data = (\{.*)\}', json, re.DOTALL)
        # fixup json parsing with simplejson, ie. replace ' with "
        json = re.sub(r'\'([\w-]+)\':', r'"\1":', m.group(1))

        return simplejson.loads(json)

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


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id = 'plugin.video.tv2.dk')
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    tv2 = TV2VideoAddon()
    if PARAMS.has_key('key'):
        tv2.showCategory(PARAMS['key'][0])
    elif PARAMS.has_key('id'):
        tv2.playVideo(PARAMS['id'][0])
    else:
        tv2.showOverview()

