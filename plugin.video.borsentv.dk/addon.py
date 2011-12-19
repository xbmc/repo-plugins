import os
import sys
import urlparse
import urllib2
import re
import datetime
from elementtree import ElementTree

import xbmcgui
import xbmcaddon
import xbmcplugin

CATEGORIES = {
    30100 : '',
    30101 : 'investor.html',
    30102 : 'privatoekonomi.html',
    30103 : 'oekonomi.html',
    30104 : 'politik.html',
    30105 : 'it.html',
    30106 : 'karriere.html',
    30107 : 'weekend.html'
}

URL = 'http://borsentv.dk/%s'
VIDEO_URL = 'http://borsentv.dk/services/frontend/borsentv/mFrontendT2_latestClips.php?%s'
RTMP_URL = 'rtmp://stream.borsentv.dk/arkiv'
RTMP_PATH = 'borsen_tv/mp4:%s.mp4'

class BorsenTVAddon(object):
    def showCategories(self):
        for id, slug in CATEGORIES.items():
            item = xbmcgui.ListItem(ADDON.getLocalizedString(id), iconImage = ICON)
            xbmcplugin.addDirectoryItem(HANDLE, PATH + '?category=%d' % id, item, isFolder = True)

        xbmcplugin.endOfDirectory(HANDLE)

    def showCategory(self, id):
        url = URL % CATEGORIES[int(id)]
        u = urllib2.urlopen(url)
        html = u.read()
        u.close()

        xml = ''
        m = re.search("'(perpage=[^']+)'", html)
        if m:
            url = VIDEO_URL % m.group(1).replace('%26', '&')
            u = urllib2.urlopen(url)
            xml = u.read()
            u.close()


        dom = ElementTree.fromstring(xml)
        for video in dom.find('videos/tab'):
            sThumb = video.findtext('sthumb').replace('_125.jpg', '.jpg')
            date = self._parseDate(video.findtext('hour'))

            item = xbmcgui.ListItem(video.findtext('title'), iconImage = sThumb, thumbnailImage = sThumb)
            item.setProperty('Fanart_Image', sThumb)
            item.setInfo('video', infoLabels = {
                'title' : video.findtext('title'),
                'plot' : video.findtext('description').replace('<br />', ''),
                'date' : date.strftime('%d.%m.%Y'),
                'aired' : date.strftime('%d-%m-%Y'),
                'studio' : ADDON.getAddonInfo('name'),
                'year' : int(date.strftime('%Y'))
            })

            # Parse video id from file_url
            m = re.search('([0-9]+)$', video.findtext('file_url'))
            url = RTMP_PATH % m.group(1)
            xbmcplugin.addDirectoryItem(HANDLE, RTMP_URL + ' playpath=' + url, item)

        xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
        xbmcplugin.endOfDirectory(HANDLE)

    def _parseDate(self, input):
        d = datetime.datetime.now()
        if input.find('/') > 0:
            m = re.search('([0-9]+)/([0-9]+)', input)
            d = datetime.datetime(year = d.year, month = int(m.group(2)), day = int(m.group(1)))

        return d

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id = 'plugin.video.borsentv.dk')
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

    btv = BorsenTVAddon()
    if PARAMS.has_key('category'):
        btv.showCategory(PARAMS['category'][0])
    else:
        btv.showCategories()


