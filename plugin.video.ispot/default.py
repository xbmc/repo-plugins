#   Copyright (C) 2016 Lunatixz
#
#
# This file is part of iSpot.
#
# iSpot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iSpot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with iSpot.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, re, sys, time, datetime, requests, string
import urllib, urllib2, base64, HTMLParser
import xbmc, xbmcgui, xbmcplugin, xbmcvfs, xbmcaddon
         
from pyfscache import *
from BeautifulSoup import BeautifulSoup
      
if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json

# Plugin Info
ADDON_ID = 'plugin.video.ispot'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_ID = REAL_SETTINGS.getAddonInfo('id')
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH = (REAL_SETTINGS.getAddonInfo('path').decode('utf-8'))
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
SETTINGS_LOC = REAL_SETTINGS.getAddonInfo('profile')
REQUESTS_LOC = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'requests',''))
ICON = os.path.join(ADDON_PATH, 'icon.png')
FANART = os.path.join(ADDON_PATH, 'fanart.jpg')
DEBUG = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
WEB = int(REAL_SETTINGS.getSetting('Preferred_WEB'))
cache = FSCache(REQUESTS_LOC, days=7, hours=0, minutes=0)
baseurl='http://www.ispot.tv/'

def log(msg, level = xbmc.LOGDEBUG):
    if DEBUG == True:
        xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
        
def uni(string):
    if isinstance(string, basestring):
        if isinstance(string, unicode):
           string = string.encode('utf-8', 'ignore' )
    return string

def open_url(url, userpass=None):
    try:
        request = urllib2.Request(url)
        if userpass:
            user, password = userpass.split(':')
            base64string = base64.encodestring('%s:%s' % (user, password))
            request.add_header("Authorization", "Basic %s" % base64string) 
        else:
            request.add_header('User-Agent','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11')
        page = urllib2.urlopen(request)
        return page
    except urllib2.HTTPError, e:
        log("open_url failed " + str(e))
        
@cache        
def read_url_cached(url, userpass=False):
    log("read_url_cached")
    return open_url(url, userpass).read()

def fillMenu():
    addDir('Browse Commercials','http://www.ispot.tv/browse',1)
    addDir('Event Commercials','http://www.ispot.tv/events',1)
    
def parseDuration(duration):
    duration = 'P'+duration
    print duration
    """ Parse and prettify duration from youtube duration format """
    DURATION_REGEX = r'P(?P<days>[0-9]+D)?T(?P<hours>[0-9]+H)?(?P<minutes>[0-9]+M)?(?P<seconds>[0-9]+S)?'
    NON_DECIMAL = re.compile(r'[^\d]+')
    duration_dict = re.search(DURATION_REGEX, duration).groupdict()
    converted_dict = {}
    # convert all values to ints, remove nones
    for a, x in duration_dict.iteritems():
        if x is not None:
            converted_dict[a] = int(NON_DECIMAL.sub('', x))
    x = time.strptime(str(datetime.timedelta(**converted_dict)).split(',')[0],'%H:%M:%S')
    return int(datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds())

def PageParse(url):
    link = read_url_cached(url)
    soup = BeautifulSoup(link)
    if url.startswith('http://www.ispot.tv/events'):
        catlink = re.compile('<a href="/(.+?)">(.+?)</a>').findall(link)
    else:
        catlink = re.compile('<div class="list-grid__item"><a href="/(.+?)">(.+?)</a></div>').findall(link)
    
    for i in range(len(catlink)):
        if not catlink[i][1].startswith(('<','&','Request Trial','Terms &','Most Engaging Ads','Top Spenders')):
            addDir(catlink[i][1],baseurl + catlink[i][0],1)

    # if url.startswith('http://www.ispot.tv/event'):
        # catlink = re.compile('<a href="/events/(.+?)">').findall(link)
    # else:
    catlink = re.compile('<a href="/ad/(.+?)">').findall(link)
    titleLST = []
    for i in range(len(catlink)):
        try:
            link = catlink[i]
            link = link.split('"')[0]
            link = link.split('"')[0]
            link = baseurl + 'ad/' + link
            link = read_url_cached(link)
            if len(link) == 0:
                link = baseurl + 'events/' + link
                link = read_url_cached(link)
            soup = BeautifulSoup(link)
            
            try:
                if WEB == 1:
                    url = ((re.compile("data-webm="'(.+?)"').findall(link))[0]).replace('https','http').replace('"','')
                else:
                    url = ((re.compile("data-mp4="'(.+?)"').findall(link))[0]).replace('https','http').replace('"','')
            except:
                url = (re.compile("file: '(.+?)'").findall(link))
                
            title = (re.compile('<title>(.+?)</title>').findall(link))[0]
            description = HTMLParser.HTMLParser().unescape((re.compile('<meta name="description" content="(.+?)">').findall(link))[0])
            thumburl = ((re.compile('<meta property="og:image" content="(.+?)" />').findall(link))[0])
            ##adDict = (re.compile("data-ad='(.+?)}'").findall(link))[0] + '}'
            
            try:
                duration = parseDuration((re.compile('<meta itemprop="duration" content="(.+?)" />').findall(link))[0])
            except:                
                duration = 30

            infoList = {}
            infoList['mediatype']     = 'video'
            infoList['Duration']      = int(duration)
            infoList['Title']         = uni(title)
            infoList['Plot']          = uni(description)

            infoArt = {}
            infoArt['thumb']        = thumburl
            infoArt['poster']       = thumburl
            infoArt['fanart']       = FANART
            infoArt['landscape']    = FANART
            
            # Avoid duplicates
            if title not in titleLST:
                titleLST.append(title)
                addLink(title,url,infoList,infoArt,len(catlink))
        except Exception,e:
            log('PageParse, failed ' + str(e))

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

def cleanString(string):
    newstr = uni(string)
    newstr = newstr.replace('&', '&amp;')
    newstr = newstr.replace('>', '&gt;')
    newstr = newstr.replace('<', '&lt;')
    newstr = newstr.replace('"', '&quot;')
    return uni(newstr)

def uncleanString(string):
    newstr = uni(string)
    newstr = newstr.replace('&amp;', '&')
    newstr = newstr.replace('&gt;', '>')
    newstr = newstr.replace('&lt;', '<')
    newstr = newstr.replace('&quot;', '"')
    return uni(newstr)
        
def uni(string):
    if isinstance(string, basestring):
        if isinstance(string, unicode):
           string = string.encode('utf-8', 'ignore' )
    return string
    
def addLink(name,url,infoList=False,infoArt=False,total=0):
    log('addLink')
    name = uncleanString(name)
    liz=xbmcgui.ListItem(name)
    liz.setProperty('IsPlayable', 'true')
    if infoList == False:
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
    else:
        liz.setInfo(type="Video", infoLabels=infoList)
    if infoArt == False:
        liz.setArt({'thumb': ICON, 'fanart': FANART})
    else:
        liz.setArt(infoArt)
    liz.addStreamInfo('video', {})
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,totalItems=total)
        
def addDir(name,url,mode,infoList=False,infoArt=False):
    log('addDir')
    name = '- %s'%uncleanString(name)
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    liz=xbmcgui.ListItem(name)
    liz.setProperty('IsPlayable', 'false')
    if infoList == False:
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
    else:
        liz.setInfo(type="Video", infoLabels=infoList)
    if infoArt == False:
        liz.setArt({'thumb': ICON, 'fanart': FANART})
    else:
        liz.setArt(infoArt)
    liz.addStreamInfo('video', {})
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

params=get_params()
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

if mode==None: PageParse('http://www.ispot.tv/browse')#fillMenu()
elif mode == 1: PageParse(url)

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE )
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL )
xbmcplugin.setContent(int(sys.argv[1]), 'video')
xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True) # End List