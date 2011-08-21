import sys
import cgi as urlparse

import xbmcgui
import xbmcplugin
import xbmcaddon


REGIONS = {
    30000: 'tv2fyn',
    30001: 'tv2lorry',
    30002: 'tv2nord',
    30003: 'tv2east',
    30004: 'tv2oj'
}

FEEDS = [
        (30100, 'rss://www.tv2oj.dk/podcast/1930', 'tv2oj'),
        (30101, 'rss://www.tv2oj.dk/podcast/2220', 'tv2oj'),
        (30102, 'rss://www.tv2oj.dk/podcast/goaften', 'tv2oj'),

        (30200, 'rss://www.tv2nord.dk/podcast/1210', 'tv2nord'),
        (30201, 'rss://www.tv2nord.dk/podcast/1930', 'tv2nord'),
        (30202, 'rss://www.tv2nord.dk/podcast/2220', 'tv2nord'),
        (30203, 'rss://www.tv2nord.dk/podcast/plus', 'tv2nord'),

        (30300, 'rss://podcast.tv2east.dk/podcaster?channel=nyheder', 'tv2east'),
        (30301, 'rss://podcast.tv2east.dk/podcaster?channel=nyheder&subchannel=1210', 'tv2east'),
        (30302, 'rss://podcast.tv2east.dk/podcaster?channel=nyheder&subchannel=1610', 'tv2east'),
        (30303, 'rss://podcast.tv2east.dk/podcaster?channel=nyheder&subchannel=1810', 'tv2east'),
        (30304, 'rss://podcast.tv2east.dk/podcaster?channel=nyheder&subchannel=1930', 'tv2east'),
        (30305, 'rss://podcast.tv2east.dk/podcaster?channel=nyheder&subchannel=2220', 'tv2east'),

        (30400, 'rss://www.tv2fyn.dk/podcast/1930', 'tv2fyn'),
        (30401, 'rss://www.tv2fyn.dk/podcast/2220', 'tv2fyn'),
        (30402, 'rss://www.tv2fyn.dk/podcast/plus', 'tv2fyn'),

        (30500, 'rss://www.tv2lorry.dk/podcast/1930', 'tv2lorry'),
        (30501, 'rss://www.tv2lorry.dk/podcast/2220', 'tv2lorry'),
        (30502, 'rss://www.tv2lorry.dk/podcast/lounge', 'tv2lorry'),
        (30503, 'rss://www.tv2lorry.dk/podcast/dervarengang', 'tv2lorry')
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
    ADDON = xbmcaddon.Addon(id='plugin.video.tv2regionerne.dk')
    PATH = sys.argv[0]
    HANDLE= int(sys.argv[1])
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

