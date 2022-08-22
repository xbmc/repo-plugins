# -*- coding: utf-8 -*-

import os, routing
import xbmcvfs, xbmcgui, xbmcplugin, xbmcaddon

addon_id       = 'plugin.video.montreal.greek-tv'
Home           = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))
icon           = os.path.join(Home, 'icon.png')
tv_icon        = os.path.join(Home, "resources", "art", 'montreal_tv.png')
radio_icon     = os.path.join(Home, "resources", "art", 'montreal_radio.png')
radio_fanart   = os.path.join(Home, "resources", "art", 'montreal_backround.jpg')

plugin = routing.Plugin()

TV_URL = 'http://live.greektv.ca/hls1/greektv.m3u8'
RADIO_URL = 'http://live.greekradio.ca:8000/live'

@plugin.route('/')
def index():
    addDir("Montreal Greek TV", TV_URL, tv_icon, radio_fanart)
    addDir("Montreal Greek Radio", RADIO_URL, radio_icon, radio_fanart)
    xbmcplugin.endOfDirectory(plugin.handle)

def addDir(name, url, iconimage, fanart):
        liz = xbmcgui.ListItem(name, offscreen=True)
        liz.setArt({'thumb': iconimage, "fanart": fanart})
        liz.setInfo(type = "Video", infoLabels = {"Title": name, "Plot": "" } )
        liz.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(plugin.handle, plugin.url_for(playlinks, url), liz, isFolder=False)

@plugin.route('/play/<path:url>')
def playlinks(url):
        liz = xbmcgui.ListItem(offscreen=True)
        liz.setProperty('isFolder', 'false')
        if url == RADIO_URL :
            liz.setArt({'thumb': radio_icon, "fanart": radio_fanart})
        liz.setProperty('IsPlayable','true')
        liz.setPath(url)
        xbmcplugin.setResolvedUrl(plugin.handle, True, liz)
        
if __name__ == '__main__':
    plugin.run()
