import sys
import os
import cgi as urlparse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from channels import CHANNELS, CATEGORIES, QUALITIES

TITLE_OFFSET = 31000
DESCRIPTION_OFFSET = 32000

class DanishLiveTV(object):
    def showChannels(self, category = None):
        try:
            quality = QUALITIES[int(ADDON.getSetting('quality'))]
        except ValueError:
            quality = QUALITIES[0] # fallback for old settings value

        if category is not None:
            channels = CATEGORIES[category]
        else:
            channels = CHANNELS

        for channel in channels:
            icon = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'logos', '%d.png' % channel.get_id())
            if not os.path.exists(icon):
                icon = ICON

            url = channel.get_url(quality)
            if url:
                title = ADDON.getLocalizedString(TITLE_OFFSET + channel.get_id())
                description = ADDON.getLocalizedString(DESCRIPTION_OFFSET + channel.get_id())
                item = xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=icon)
                item.setInfo('video', infoLabels={
                    'title': title,
                    'plot' : description,
                    'studio' : ADDON.getLocalizedString(channel.get_category())
                })
                item.setProperty('Fanart_Image', FANART)
                item.setProperty('IsLive', 'true')
                xbmcplugin.addDirectoryItem(HANDLE, url, item)

        xbmcplugin.endOfDirectory(HANDLE)

    def showCategories(self):
        for id in CATEGORIES:
            title = ADDON.getLocalizedString(id)
            item = xbmcgui.ListItem(title, iconImage=ICON, thumbnailImage=ICON)
            item.setProperty('Fanart_Image', FANART)
            url = PATH + '?category=%d' % id
            xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder = True)

        xbmcplugin.endOfDirectory(HANDLE)


    def playChannel(self, name):
        try:
            quality = QUALITIES[int(ADDON.getSetting('quality'))]
        except ValueError:
            quality = QUALITIES[0] # fallback for old settings value

        for channel in CHANNELS:
            if channel.get_name() == name:
                url = channel.get_url(quality)
                if url:
                    icon = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'logos', channel.get_logo())
                    item = xbmcgui.ListItem(channel.get_name(), iconImage=icon, thumbnailImage=icon)
                    item.setProperty('Fanart_Image', FANART)
                    item.setProperty('IsLive', 'true')

                    p = xbmc.Player()
                    p.play(url, item)


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id='plugin.video.dr.dk.live')
    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')
    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')

    danishTV = DanishLiveTV()
    if PARAMS.has_key('playChannel'):
        danishTV.playChannel(PARAMS['playChannel'][0])
    elif PARAMS.has_key('category'):
        danishTV.showChannels(int(PARAMS['category'][0]))
    elif ADDON.getSetting('group.by.category') == 'true':
        danishTV.showCategories()
    else:
        danishTV.showChannels()


