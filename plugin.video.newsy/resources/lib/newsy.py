#   Copyright (C) 2017 Lunatixz
#
#
# This file is part of Newsy.
#
# Newsy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Newsy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Newsy.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, datetime, traceback, feedparser
import urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

from simplecache import SimpleCache
from bs4 import BeautifulSoup

# Plugin Info
ADDON_ID      = 'plugin.video.newsy'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

## GLOBALS ##
TIMEOUT   = 15
DEBUG     = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
LIVEURL   = 'http://www.newsy.com/live/'
RSSURL    = 'http://feeds.feedburner.com/newsy-allvideos/'
VID_TYPE  = ['M3U8','MP4'][int(REAL_SETTINGS.getSetting('Video_Type'))]

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == True:
        if level == xbmc.LOGERROR:
            msg += ' ,' + traceback.format_exc()
        xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + (msg), level)
   
def getParams():
    param=[]
    if len(sys.argv[2])>=2:
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
                 
socket.setdefaulttimeout(TIMEOUT)
class Newsy(object):
    def __init__(self):
        log('__init__')
        self.cache = SimpleCache()

            
    def openURL(self, url):
        log('openURL, url = ' + str(url))
        try:
            cacheResponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheResponse:
                request = urllib2.Request(url)
                request.add_header('User-Agent','Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)')
                response = urllib2.urlopen(request, timeout=TIMEOUT).read()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, response, expiration=datetime.timedelta(hours=6))
            return self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
        except urllib2.URLError, e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
        except socket.timeout, e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
        except Exception, e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
             

    def buildMainMenu(self):
        self.addLink('Live'     ,'' ,0)
        self.addDir('Browse'    ,'0',1)
        
        
    def buildLiveLink(self):
        soup = BeautifulSoup(self.openURL(LIVEURL), "html.parser")
        link = 'http:' + soup('div' , {'class': 'live-player'})[0].find('script').get('src')
        item = json.loads('{'+self.openURL(link).split('}; // end config')[0].split('var jwConfig = {')[1]+'}')
        self.playVideo('Newsy Live',item['playlist'][0]['sources'][0]['file'])
            
                         
    def pagination(self, seq, rowlen):
        for start in xrange(0, len(seq), rowlen):
            yield seq[start:start+rowlen]

            
    def buildRSS(self, start=0, end=14):
        data    = feedparser.parse(RSSURL)['entries']
        data    = list(self.pagination(data, end))
        start   = 0 if start >= len(data) else start
        for item in data[start]:
            if item and 'summary_detail' in item:
                try:
                    path, duration, plot = self.resolveURL(item['links'][0]['href'])
                    thumb = item['summary_detail']['value'].encode("utf-8").split('<img alt="" src="')[1].split('.jpg')[0]+'.jpg'
                    label = item['title']
                    date  = item['published']
                    plot  = '%s - %s'%(date, plot)
                    aired = (datetime.datetime.strptime(date[0:16], '%a, %d %b %Y')).strftime('%Y-%m-%d') 
                    infoLabel  = {"mediatype":"video","label":label,"title":label,"plot":plot,"plotoutline":plot,"genre":"News","duration":duration,"aired":aired}
                    infoArt    = {"thumb":thumb,"poster":thumb,"icon":ICON,"fanart":FANART}
                    self.addLink(label,path,9,infoLabel,infoArt,end)
                except:
                    log("buildRSS, no video found")
        start += 1
        self.addDir('>> Next', '%s'%(start), 1)
                    
                    
    def resolveURL(self, url):
        log('resolveURL, url = ' + str(url))
        try:
            soup = BeautifulSoup(self.openURL(url), "html.parser")
            link = soup('div' , {'class': 'video-container'})[0]
            item = json.loads(link('div' , {'class': 'video-container'})[0].get('data-video-player'))
            url = item['file'] if VID_TYPE == 'MP4' else 'http:'+item['stream']
            return url, item['duration']//1000, item['headline']
        except Exception, e:
            log("resolveURL Failed! " + str(e), xbmc.LOGERROR)
        
        
    def playVideo(self, name, url, liz=None):
        log('playVideo')
        if not liz:
            liz = xbmcgui.ListItem(name, path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

           
    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0):
        name = name.encode("utf-8")
        log('addLink, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'true')
        if infoList == False:
            liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name,"genre":"News"})
        else:
            liz.setInfo(type="Video", infoLabels=infoList)
            
        if infoArt == False:
            liz.setArt({'thumb':ICON,'fanart':FANART})
        else:
            liz.setArt(infoArt)
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, infoList=False, infoArt=False):
        name = name.encode("utf-8")
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False:
            liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name,"genre":"News"})
        else:
            liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False:
            liz.setArt({'thumb':ICON,'fanart':FANART})
        else:
            liz.setArt(infoArt)
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

params=getParams()
try:
    url=urllib.unquote_plus(params["url"])
except:
    url=None
try:
    name=urllib.unquote_plus(params["name"])
except:
    name=None
try:
    mode=int(params["mode"])
except:
    mode=None
    
log("Mode: "+str(mode))
log("URL : "+str(url))
log("Name: "+str(name))

if mode==None:  Newsy().buildMainMenu()
elif mode == 0: Newsy().buildLiveLink()
elif mode == 1: Newsy().buildRSS(int(url))
elif mode == 9: Newsy().playVideo(name, url)

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE )
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL )
xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)