import sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
from datetime import datetime, timedelta
import urllib, urllib2
import json
import calendar
from urllib2 import URLError, HTTPError

addon_handle = int(sys.argv[1])

#App Variables
API_KEY = '98f12273997c31eab6cfbfbe64f99d92'
APP_ID = '7KJECL120U'

#Settings
settings = xbmcaddon.Addon(id='plugin.video.livestream')
USERNAME = str(settings.getSetting(id="username"))
PASSWORD = str(settings.getSetting(id="password"))
AUTO_PLAY = str(settings.getSetting(id="auto_play"))

#Localisation
local_string = xbmcaddon.Addon(id='plugin.video.livestream').getLocalizedString
ROOTDIR = xbmcaddon.Addon(id='plugin.video.livestream').getAddonInfo('path')
ICON = ROOTDIR+"/icon.png"
FANART = ROOTDIR+"/fanart.jpg"

SEARCH_HITS = '25'
LIVE_COLOR = 'FF00B7EB'
SECTION_COLOR = 'FFFFFF66'

#User-Agents
UA_IPHONE = 'AppleCoreMedia/1.0.0.13E233 (iPhone; U; CPU OS 9_3 like Mac OS X; en_us)'
UA_LIVESTREAM = 'Livestream/4.0.2 (iPhone; iOS 9.3; Scale/2.00)'



def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def addStream(name,link_url,title,iconimage,fanart=None,event_id=None,owner_id=None,info=None,video_id=None):
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(link_url)+"&mode="+str(104)+"&name="+urllib.quote_plus(name)
    if iconimage != None:
        u = u+"&icon="+urllib.quote_plus(iconimage)        
    if event_id != None:
        u = u+"&event_id="+urllib.quote_plus(event_id)
    if owner_id != None:
        u = u+"&owner_id="+urllib.quote_plus(owner_id) 
    if video_id != None:
        u = u+"&video_id="+urllib.quote_plus(video_id) 

    if iconimage != None:
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage) 
    else:
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=ICON) 
    
    if fanart != None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)

    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info) 
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    xbmcplugin.setContent(addon_handle, 'episodes')
    
    return ok

def addLink(name,url,title,iconimage,fanart=None):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)    
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    if iconimage != None:
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage) 
    else:
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=ICON) 

    if fanart != None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
    return ok


def addDir(name,url,mode,iconimage,fanart=None,event_id=None,owner_id=None,info=None,cat_info=None):       
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)

    if event_id != None:
        u = u+"&event_id="+urllib.quote_plus(event_id)
    if owner_id != None:
        u = u+"&owner_id="+urllib.quote_plus(owner_id)

    if iconimage != None:
        u = u+"&icon="+urllib.quote_plus(iconimage)

    if cat_info != None:
        u = u+"&cat_info="+urllib.quote_plus(cat_info)

    if iconimage != None:
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage) 
    else:
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=ICON) 

    liz.setInfo( type="Video", infoLabels={ "Title": name } )

    if fanart != None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)

    if info != None:
        liz.setInfo( type="Video", infoLabels=info)

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)    
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok
