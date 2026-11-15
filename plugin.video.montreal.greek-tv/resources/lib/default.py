# -*- coding: utf-8 -*-

import os, routing, sys
import xbmc, xbmcvfs, xbmcgui, xbmcplugin, xbmcaddon
import urllib.request,urllib.parse,urllib.error

addon_id       = 'plugin.video.montreal.greek-tv'
Home           = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))
icon           = os.path.join(Home, 'icon.png')
fanart         = os.path.join(Home, 'fanart.jpg')
tv_icon        = os.path.join(Home, "resources", "art", 'montreal_tv.png')
radio_icon     = os.path.join(Home, "resources", "art", 'montreal_radio.png')
radio_fanart   = os.path.join(Home, "resources", "art", 'montreal_background.jpg')


TV_URL = 'http://live.greektv.ca/hls1/greektv.m3u8'
RADIO_URL = 'http://live.greekradio.ca:8000/live'

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param


#@plugin.route('/')
def index():
    addLink("Montreal Greek TV", TV_URL, 5,tv_icon, fanart)
    addLink("Montreal Greek Radio", RADIO_URL, 5,radio_icon, fanart)
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

def addLink(name, url, mode, iconimage, fanart, description=''):
    u=sys.argv[0]+"?url="+urllib.parse.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.parse.quote_plus(name)+"&description="+str(description)+"&fanart="+urllib.parse.quote_plus(fanart)
    ok=True   
    liz = xbmcgui.ListItem(name)
    liz.setArt({"icon":"DefaultFolder.png",'thumb': iconimage})
    liz.setProperty('fanart_image', fanart)
    liz.setProperty("IsPlayable","true")
    if 'plugin://' in url:u=url
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    return ok

def addDir(name, url, iconimage, fanart):
        liz = xbmcgui.ListItem(name, offscreen=True)
        liz.setArt({'thumb': iconimage, "fanart": fanart})
        liz.setInfo(type = "Video", infoLabels = {"Title": name, "Plot": "" } )
        liz.setProperty('IsPlayable', 'true')
        '''
        if url == TV_URL :
            url = create_temp_playlist(url)
        '''    
        xbmcplugin.addDirectoryItem(name,url,2,iconimage,fanart, isFolder=False)
                
    
#@plugin.route('/play/<path:url>')
def playlinks(url):
        
        liz = xbmcgui.ListItem(path=url,offscreen=True)
        liz.setProperty('isFolder', 'false')
        if url == RADIO_URL :
            if xbmc.Player().isPlayingVideo() == True : xbmc.executebuiltin("Action(Stop)")
            liz.setArt({'thumb': radio_icon, "fanart": radio_fanart})
        else :
            liz.setArt({'thumb': tv_icon, "fanart": radio_fanart})
            
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
        
        
def addLink(name, url, mode, iconimage, fanart, description=''):
    u=sys.argv[0]+"?url="+urllib.parse.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.parse.quote_plus(name)+"&description="+str(description)+"&fanart="+urllib.parse.quote_plus(fanart)
    ok=True   
    liz = xbmcgui.ListItem(name)
    liz.setArt({"icon":"DefaultFolder.png",'thumb': iconimage})
    liz.setProperty('fanart_image', fanart)
    liz.setProperty("IsPlayable","true")
    if 'plugin://' in url:u=url
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    return ok

params=get_params(); url=None; name=None; mode=None; site=None; iconimage=None
try: site=urllib.parse.unquote_plus(params["site"])
except: pass
try: url=urllib.parse.unquote_plus(params["url"])
except: pass
try: name=urllib.parse.unquote_plus(params["name"])
except: pass
try: mode=int(params["mode"])
except: pass
try: iconimage=urllib.parse.unquote_plus(params["iconimage"])
except: pass
try: fanart=urllib.parse.unquote_plus(params["fanart"])
except: pass
 
if mode==None or url==None or len(url)<1:index()
elif mode==5:playlinks(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
