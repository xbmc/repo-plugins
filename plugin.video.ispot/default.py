#   Copyright (C) 2017 Lunatixz
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
import os, re, sys, time, datetime, traceback
import urllib, urllib2, base64, HTMLParser, socket
import xbmc, xbmcgui, xbmcplugin, xbmcvfs, xbmcaddon

from simplecache import use_cache, SimpleCache

if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json

## GLOBALS ##
baseurl='https://www.ispot.tv/'
TIMEOUT = 15

# Plugin Info
ADDON_ID = 'plugin.video.ispot'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
SETTINGS_LOC = REAL_SETTINGS.getAddonInfo('profile')
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON = os.path.join(ADDON_PATH, 'icon.png')
FANART = os.path.join(ADDON_PATH, 'fanart.jpg')

# User Settings
DEBUG = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
WEB = int(REAL_SETTINGS.getSetting('Preferred_WEB'))

socket.setdefaulttimeout(TIMEOUT)

def log(msg, level=xbmc.LOGDEBUG):
    msg = stringify(msg[:1000])
    if DEBUG == False and level == xbmc.LOGDEBUG:
        return
    if level == xbmc.LOGERROR:
        msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)

def ascii(string):
    if isinstance(string, basestring):
        if isinstance(string, unicode):
           string = string.encode('ascii', 'ignore')
    return string

def uni(string):
    if isinstance(string, basestring):
        if isinstance(string, unicode):
           string = string.encode('utf-8', 'ignore' )
        else:
           string = ascii(string)
    return string

def stringify(string):
    if isinstance(string, list):
        string = stringify(string[0])
    elif isinstance(string, (int, float, long, complex, bool)):
        string = str(string)
    elif isinstance(string, (str, unicode)):
        string = uni(string)
    elif not isinstance(string, (str, unicode)):
        string = ascii(string)
    if isinstance(string, basestring):
        return string
    return ''

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

def chunks(l, n=25):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def get_params():
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

class iSpot():
    def __init__(self):
        log('__init__')
        self.PAGE = 25
        self.cache = SimpleCache()


    def onInit(self):
        log('onInit')
        
        
    def open_url(self, url, userpass=None):
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

            
    '''
        ispot is not updated regularly, no need to burden site. Cache for 14days
    '''
    @use_cache(14)
    def read_url_cached(self, url, userpass=False):
        log("read_url_cached")
        return self.open_url(url, userpass).read()


    def fillMenu(self):
        self.addDir('Browse Commercials','http://www.ispot.tv/browse',1)
        self.addDir('Event Commercials','http://www.ispot.tv/events',1)


    def parseDuration(self, duration):
        duration = 'P'+duration
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


    def PageParse(self, url):
        log('PageParse, url = ' + url)
        link = self.read_url_cached(url)
        if url.startswith('http://www.ispot.tv/events'):
            catlink = re.compile('<a href="/(.+?)">(.+?)</a>').findall(link)
        else:
            catlink = re.compile('<div class="list-grid__item"><a href="/(.+?)">(.+?)</a></div>').findall(link)

        for i in range(len(catlink)):
            # filter unwanted elements
            if not catlink[i][1].startswith(('<','&','Request Trial','Terms &','Most Engaging Ads','Top Spenders')) and url != baseurl + catlink[i][0]:
                self.addDir(catlink[i][1],baseurl + catlink[i][0],1)
        
        self.PAGECNT = 0
        self.LINKLST = []
        self.titleLST =[]
        if url.startswith('http://www.ispot.tv/event'):
            self.LINKLST = re.compile('<a href="/events/(.+?)">').findall(link)
        else:
            self.LINKLST = re.compile('<a href="/ad/(.+?)">').findall(link)
        #parse dir for links
        self.buildLink(self.LINKLST)


    def buildLink(self, lst, pg=False):
        log('buildLink')
        if pg == False:
            catlink = lst
            self.LinkParse(catlink, 0, len(lst))
        else:
            self.PAGEMAX = len(lst)
            self.PAGECNT = self.PAGECNT + self.PAGE
            if self.PAGECNT >= self.PAGEMAX:
                self.PAGECNT = 0
                return
            #page parse dir links in chunks
            catlink = (list(chunks(lst[self.PAGECNT:],self.PAGE))[0])
            self.LinkParse(catlink, self.PAGECNT, self.PAGEMAX)


    def LinkParse(self, catlink, cnt, cntmax):
        log('LinkParse')
        for i in range(len(catlink)):
            try:
                link = catlink[i]
                link = link.split('"')[0]
                link = link.split('"')[0]
                link = baseurl + 'ad/' + link
                link = self.read_url_cached(link)

                if len(link) == 0:
                    link = baseurl + 'events/' + link
                    link = self.read_url_cached(link)

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
                    duration = self.parseDuration((re.compile('<meta itemprop="duration" content="(.+?)" />').findall(link))[0])
                except:
                    duration = 30

                infoList = {}
                infoList['mediatype']     = 'video'
                infoList['Duration']      = int(duration)
                infoList['Title']         = uni(title)
                infoList['Plot']          = uni(description)

                infoArt = {}
                infoArt['thumb']        = (thumburl or ICON)
                infoArt['poster']       = (thumburl or ICON)
                infoArt['fanart']       = (thumburl or ICON)

                # Avoid duplicates
                if title not in self.titleLST:
                    self.titleLST.append(title)
                    self.addLink(title,url, 2, infoList, infoArt, len(catlink))
            except Exception,e:
                log('PageParse, failed ' + str(e))
        #todo pagination?
        # if cnt < cntmax:
            # self.addDir('Next Page','Next',1)

        
    def LinkPlay(self, name, url):
        listitem = xbmcgui.ListItem(name, path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)


    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0):
        name = uncleanString(name)
        log('addLink, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'true')
        if infoList == False:
            liz.setInfo( type="Video", infoLabels={"label":name,"title":name} )
        else:
            liz.setInfo(type="Video", infoLabels=infoList)
            
        if infoArt == False:
            liz.setArt({'thumb':ICON,'fanart':FANART})
        else:
            liz.setArt(infoArt)
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, infoList=False, infoArt=False):
        name = uncleanString(name)
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False:
            liz.setInfo(type="Video", infoLabels={"label":name,"title":name} )
        else:
            liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False:
            liz.setArt({'thumb':ICON,'fanart':FANART})
        else:
            liz.setArt(infoArt)
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
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

if mode==None: iSpot().PageParse('http://www.ispot.tv/browse')
elif mode == 1: iSpot().PageParse(url)
elif mode == 2: iSpot().LinkPlay(name, url)
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE )
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL )
xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)