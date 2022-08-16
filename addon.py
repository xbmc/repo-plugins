# -*- coding: utf-8 -*-

"""
    Montreal Greek TV Add-on
    Author: greektimes

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import urllib.parse, os
import xbmcvfs, xbmcgui, xbmcplugin, xbmcaddon

addon_id       = 'plugin.video.montreal.greek-tv'
Home           = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))
art            = xbmcvfs.translatePath(Home + '/resources/art/')
icon           = xbmcvfs.translatePath(os.path.join(Home, 'icon.png'))
tv_icon        = xbmcvfs.translatePath(os.path.join(art , 'montreal_tv.png'))
radio_icon     = xbmcvfs.translatePath(os.path.join(art , 'montreal_radio.png'))
radio_fanart   = xbmcvfs.translatePath(os.path.join(art , 'montreal_backround.jpg'))

__handle__     = int(sys.argv[1])

TV_URL = 'http://live.greektv.ca/hls1/greektv.m3u8'
RADIO_URL = 'http://live.greekradio.ca:8000/live'

def Index():
    addDir("Montreal Greek TV", TV_URL, 2, tv_icon, radio_fanart)
    addDir("Montreal Greek Radio", RADIO_URL, 2, radio_icon, radio_fanart)
    xbmcplugin.endOfDirectory(__handle__)

def addDir(name, url, mode, iconimage, fanart):
        u = sys.argv[0]+"?url="+urllib.parse.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.parse.quote_plus(name)+"&iconimage="+urllib.parse.quote_plus(iconimage)+"&fanart="+urllib.parse.quote_plus(fanart)
        liz = xbmcgui.ListItem(name)
        liz.setArt({'thumb': iconimage, "fanart": fanart})
        liz.setInfo(type = "Video", infoLabels = {"Title": name, "Plot": "" } )
        liz.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(handle = __handle__, url = u, listitem = liz,isFolder = False)

def Playlinks(name, url):
        liz = xbmcgui.ListItem(name)
        liz.setProperty('isFolder', 'false')
        liz.setArt({'thumb': radio_icon})
        liz.setInfo('video', {'Title': '', 'Plot': ''})
        liz.setProperty('IsPlayable','true')
        liz.setPath(url)
        xbmcplugin.setResolvedUrl(__handle__, True, liz)
        
def get_params():
        param = []
        paramstring = sys.argv[2]
        if len(paramstring) >= 2 :
                params = sys.argv[2]
                cleanedparams = params.replace('?','')
                if (params[len(params)-1] == '/' ) :
                        params = params[0:len(params)-2]
                pairsofparams = cleanedparams.split('&')
                param = {}
                for i in range(len(pairsofparams)) :
                        splitparams = {}
                        splitparams = pairsofparams[i].split('=')
                        if (len(splitparams)) == 2 :
                                param[splitparams[0]] = splitparams[1]
                                
        return param
        


params = get_params()
url = None
name = None
mode = None
iconimage = None
fanart = None


try:
        url = urllib.parse.unquote_plus(params["url"])
except:
        pass
try:
        name = urllib.parse.unquote_plus(params["name"])
except:
        pass
try:
        iconimage = urllib.parse.unquote_plus(params["iconimage"])
except:
        pass
try:        
        mode = int(params["mode"])
except:
        pass
try:        
        fanart = urllib.parse.unquote_plus(params["fanart"])
except:
        pass


 
if mode == None or url == None or len(url) < 1 : Index()
elif mode == 2 : Playlinks(name, url)

xbmcplugin.endOfDirectory(__handle__)

