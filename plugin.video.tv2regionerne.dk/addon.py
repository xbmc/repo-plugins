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
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import sys
import urlparse

import xbmcgui
import xbmcplugin
import xbmcaddon


REGIONS = {
    30000: 'tv2fyn',
    30001: 'tv2lorry',
    30005: 'tvmidtvest',
    30002: 'tv2nord',
    30003: 'tv2east',
    30004: 'tv2oj'
}

FEEDS = [
    # http://www.tv2oj.dk/artikel/55248:Tjenester--Podcast
    (30100, 'rss://www.tv2oj.dk/podcast/1930', 'tv2oj'),
    (30101, 'rss://www.tv2oj.dk/podcast/2220', 'tv2oj'),
    (30102, 'rss://www.tv2oj.dk/podcast/goaften', 'tv2oj'),

    # http://www.tvmidtvest.dk/node/2407
    (30700, 'rss://podcast.tvmidtvest.dk/feed/3799.aspx', 'tvmidtvest'),

    # http://www.tv2nord.dk/kategori/86
    (30201, 'rss://www.tv2nord.dk/podcast/1930', 'tv2nord'),

    # http://www.tv2fyn.dk/article/41815:TV-2-FYN-med-i-lommen
    (30400, 'rss://www.tv2fyn.dk/podcast/1930', 'tv2fyn'),
    (30401, 'rss://www.tv2fyn.dk/podcast/2220', 'tv2fyn'),

    # http://www.lorry.dk/article/43306
    (30500, 'rss://www.tv2lorry.dk/podcast/1930', 'tv2lorry'),
    (30501, 'rss://www.tv2lorry.dk/podcast/2220', 'tv2lorry'),
    (30502, 'rss://www.tv2lorry.dk/podcast/lounge', 'tv2lorry'),
]

SPECIAL = [
    (30600, 'rss://www.tv2lorry.dk/podcast/dkr', 'danmarkrundt')
]


class TV2Regionerne(object):
    def showRegions(self):
        for stringId in REGIONS:
            slug = REGIONS.get(stringId)
            icon = ADDON.getAddonInfo('path') + "/resources/logos/%s.png" % slug
            item = xbmcgui.ListItem(ADDON.getLocalizedString(stringId), iconImage=icon)
            item.setProperty("Fanart_Image", ADDON.getAddonInfo('path') + "/fanart.jpg")
            url = PATH + '?slug=' + slug
            xbmcplugin.addDirectoryItem(HANDLE, url, item, True)

        if ADDON.getSetting('show.danmark.rundt') == 'true':
            self._addFeeds(SPECIAL)

        xbmcplugin.endOfDirectory(HANDLE)

    def showFeeds(self, slug):
        self._addFeeds(FEEDS, slug)

        if ADDON.getSetting('show.danmark.rundt') == 'true' and not PARAMS.has_key('slug'):
            self._addFeeds(SPECIAL)

        xbmcplugin.endOfDirectory(HANDLE)

    def _addFeeds(self, feeds, region=None):
        for stringId, feedUrl, slug in feeds:
            if region is None or region == slug:
                icon = ADDON.getAddonInfo('path') + "/resources/logos/%s.png" % slug
                item = xbmcgui.ListItem(ADDON.getLocalizedString(stringId), iconImage=icon)
                item.setProperty("Fanart_Image", ADDON.getAddonInfo('path') + "/fanart.jpg")
                xbmcplugin.addDirectoryItem(HANDLE, feedUrl, item, True)


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    regionSlug = None
    regionName = ADDON.getSetting('show.feeds.for')
    for regionStringId in REGIONS:
        if regionName == ADDON.getLocalizedString(regionStringId):
            regionSlug = REGIONS.get(regionStringId)
            break

    tv2r = TV2Regionerne()
    if PARAMS.has_key('slug'):
        tv2r.showFeeds(PARAMS.get('slug')[0])
    elif regionSlug is not None:
        tv2r.showFeeds(regionSlug)
    else:
        tv2r.showRegions()

