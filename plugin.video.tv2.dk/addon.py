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
import sys
import os
import re
import urlparse
import urllib
import urllib2
import xml.etree.ElementTree as ET
import datetime
import time

import xbmcgui
import xbmcplugin
import xbmcaddon

import buggalo


def listFeed():
    u = urllib2.urlopen('http://feed.theplatform.com/f/EHsYJC/Q_eFvtpVupQZ')
    data = u.read()
    u.close()

    # strip namespaces
    data = re.sub('<[a-z]+:', '<', data)
    data = re.sub('</[a-z]+:', '</', data)

    items = list()
    doc = ET.fromstring(data)
    for rssItem in doc.findall('channel/item'):
        if not 'video' in rssItem.find('content').get('type'):
            continue

        image = rssItem.findtext('defaultThumbnailUrl')
        if not image:
            image = ICON
        date = parseDate(rssItem.findtext('pubDate'))

        infoLabels = {}
        duration = rssItem.find('content').get('duration')
        if duration:
            infoLabels['duration'] = int(float(duration) / 60) + 1
        infoLabels['date'] = date.strftime('%d.%m.%Y')
        infoLabels['year'] = int(date.strftime('%Y'))

        item = xbmcgui.ListItem(rssItem.findtext('title'), iconImage=image, thumbnailImage=image)
        item.setInfo('video', infoLabels)
        item.setProperty('Fanart_Image', FANART)
        item.setProperty('IsPlayable', 'true')
        items.append((PATH + '?' + urllib.urlencode({'url': rssItem.find('content').get('url')}), item, False))

    xbmcplugin.addDirectoryItems(HANDLE, items)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.endOfDirectory(HANDLE)


def playVideo(url):
    print url
    u = urllib2.urlopen(url)
    smil = u.read()
    u.close()

    # strip namespaces
    smil = re.sub('xmlns=[^>]+', '', smil)

    doc = ET.fromstring(smil)
    src = doc.find('body/seq/switch/video').get('src')
    item = xbmcgui.ListItem(path=src)
    xbmcplugin.setResolvedUrl(HANDLE, True, item)


def parseDate(dateStr):
    try:
        return datetime.datetime.strptime(dateStr[0:-4], '%a, %d %b %Y %H:%M:%S')
    except TypeError:
        return datetime.datetime.fromtimestamp(time.mktime(time.strptime(dateStr[0:-4], '%a, %d %b %Y %H:%M:%S')))

if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    buggalo.SUBMIT_URL = 'http://tommy.winther.nu/exception/submit.php'
    try:
        if 'url' in PARAMS:
            playVideo(PARAMS['url'][0])
        else:
            listFeed()
    except Exception:
        buggalo.onExceptionRaised()


