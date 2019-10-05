#   Copyright (C) 2017 Lunatixz
#
#
# This file is part of News12.
#
# News12 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# News12 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with News12.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, datetime, re, traceback, feedparser
import urllib, urllib2, socket, json
import xbmc, xbmcgui, xbmcplugin, xbmcvfs, xbmcaddon

from simplecache import SimpleCache
from bs4 import BeautifulSoup

# Plugin Info
ADDON_ID      = 'plugin.video.news12'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

## GLOBALS ##
TIMEOUT = 15
DEBUG   = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
BITRATE = {0:LANGUAGE(30003),1:LANGUAGE(30004),2:LANGUAGE(30005)}[int(REAL_SETTINGS.getSetting('Video_Quality'))]
BASEURL = 'http://news12.com'
RSSURL  = '%s/?clienttype=rss'
BASEIMG = 'http://ftpcontent.worldnow.com/professionalservices/clients/news12/images/regions/selectregion_%i.jpg'
LIVEURL = 'http://adx.news12.com/livevideo/livevideo_iframe.html'
VODURL  = '%s/clip/%s/videoclip?clienttype=mrssjson'
LIVEMAP = {'N12%s':'%s - News','TW%s':'%s - Traffic & Weather','N12%sB2':'%s - Doppler Radar'}
IMGPARM = {'bx':BASEIMG%1,'bk':BASEIMG%2,'ct':BASEIMG%3,'hv':BASEIMG%4,'li':BASEIMG%5,'nj':BASEIMG%6,'wc':BASEIMG%7,'None':ICON,}

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
class News12():
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
        except urllib2.URLError as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
        except socket.timeout as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
        except Exception as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)

            
    def buildRegionMenu(self):
        log('buildRegionMenu')
        soup = BeautifulSoup(self.openURL(BASEURL), "html.parser")
        data = soup('div' , {'class': 'region-links'})[0].find_all('a')
        for idx, region in enumerate(data):
            thumb = IMGPARM[region['class'][0]]
            art   = {"thumb":thumb,"poster":thumb,"icon":ICON,"fanart":FANART}
            self.addDir(region.get_text(),json.dumps({'region_ad':region['class'][0],'url':region.get('href')}),0,infoArt=art)

            
    def buildMenu(self, name, url):
        log('buildMenu')
        self.buildLive(name, url['region_ad'])
        thumb = IMGPARM[url['region_ad']]
        art = {"thumb":thumb,"poster":thumb,"icon":ICON,"fanart":FANART}
        self.addDir('%s - Video Clips'%name,json.dumps(url),1,infoArt=art)


    def buildLive(self, name, url):
        data = self.openURL(LIVEURL).replace(' ','').replace('(','{').replace(')','}')
        live = re.search(r'varstream_url="(.*)"', data.strip(), re.M|re.I).group(1).replace('"+streamname+"','%s')
        for line in data.split('\n'):
            search = re.match( r'if{region=="(.*)"}{region_ad="(.*)";streamname="(.*)";url="(.*)";}.*', line.strip(), re.M|re.I)
            if search and search.group(2).lower() == url:
                region = search.group(1).upper()
                for key in LIVEMAP:
                    if key%url.upper() == region:
                        art = {"thumb":IMGPARM[url],"poster":IMGPARM[url],"icon":ICON,"fanart":FANART}
                        self.addLink(LIVEMAP[key]%name, live%search.group(3),9,infoArt=art,total=len(LIVEMAP))
    
    
    def buildRSS(self, url, end=9):
        log('buildRSS, url = ' + str(url))
        start   = int(url.get('start','0') or '0')
        data    = feedparser.parse(RSSURL%url['url'])['entries']
        start   = 0 if start >= len(data) else start
        count   = 0
        for idx in range(start,len(data)):
            item = data[idx]
            if item and 'summary_detail' in item:
                try:
                    path, duration = self.resolveURL(url['url'], item['links'][0]['href'])
                    thumb = item['links'][1]['href']
                    label = item['title']
                    plot  = item['summary_detail']['value']
                    plot = '%s - %s'%(item['published'], plot)
                    infoLabel  = {"mediatype":"video","label":label,"title":label,"plot":plot,"plotoutline":plot,"genre":"News","duration":duration}                    
                    infoArt    = {"thumb":thumb,"poster":thumb,"icon":ICON,"fanart":FANART}
                    self.addLink(label,path,9,infoLabel,infoArt,len(data[start]))
                    count +=1
                    if count == end:
                        break
                except:
                    pass
        url['start'] = 0 if count == 0 else idx
        self.addDir('>> Next',json.dumps(url), 1)

        
    def resolveURL(self, name, url):
        log('resolveURL, url = ' + str(url))
        try:
            cacheResponse = self.cache.get(ADDON_NAME + '.resolveURL, url = %s.%s'%(url,str(BITRATE)))
            if not cacheResponse:
                data = self.openURL(url).replace(' ','').replace('(','{').replace(')','}')
                try:
                    clip = re.search(r'widgetVideoCanvasDS37.SetVariable{"clipId","(.*)"};', data.strip(), re.M|re.I).group(1)
                except:
                    return
                    
                response = None
                items = json.loads(self.openURL(VODURL%(name,clip)))
                if items and 'channel' in items:
                    for video in items['channel']['item']['media-group']['media-content']:
                        if BITRATE == LANGUAGE(30003) and int(video['@attributes']['bitrate']) > 1200:
                            continue
                        elif BITRATE == LANGUAGE(30004) and int(video['@attributes']['bitrate']) > 2200 and int(video['@attributes']['bitrate']) < 1200:
                            continue
                        elif BITRATE == LANGUAGE(30005) and int(video['@attributes']['bitrate']) < 2200:
                            continue
                        log('resolveURL, using bitrate = ' + str(video['@attributes']['bitrate']))
                        response = video['@attributes']['url'], int(video['@attributes']['duration'])
                        
                    if not response:
                        response = video['@attributes']['url'], int(video['@attributes']['duration'])
                self.cache.set(ADDON_NAME + '.resolveURL, url = %s.%s'%(url,str(BITRATE)), response, expiration=datetime.timedelta(hours=48))
            return self.cache.get(ADDON_NAME + '.resolveURL, url = %s.%s'%(url,str(BITRATE)))
        except Exception as e:
            log("resolveURL Failed! " + str(e), xbmc.LOGERROR)

            
    def playVideo(self, name, url, list=None):
        log('playVideo')
        if not list:
            list = xbmcgui.ListItem(name, path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, list)

           
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

if mode==None:  News12().buildRegionMenu()
elif mode == 0: News12().buildMenu(name, json.loads(url))
elif mode == 1: News12().buildRSS(json.loads(url))
elif mode == 9: News12().playVideo(name, url)

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE )
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL )
xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)