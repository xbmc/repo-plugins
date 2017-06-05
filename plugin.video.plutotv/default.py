#   Copyright (C) 2017 Lunatixz
#
#
# This file is part of PlutoTV.
#
# PlutoTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PlutoTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PlutoTV.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, datetime, net, requests, re, traceback
import urllib, socket, json, urlresolver, collections
import xbmc, xbmcgui, xbmcplugin, xbmcvfs, xbmcaddon

from simplecache import SimpleCache
# Plugin Info
ADDON_ID      = 'plugin.video.plutotv'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')


## GLOBALS ##
TIMEOUT     = 15
USER_EMAIL  = REAL_SETTINGS.getSetting('User_Email')
PASSWORD    = REAL_SETTINGS.getSetting('User_Password')
FIT_REGION  = REAL_SETTINGS.getSetting('Filter_Region') == 'true'
DEBUG       = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
HIDE_PLUTO  = REAL_SETTINGS.getSetting("Hide_Ads") == "true"
COOKIE_JAR  = xbmc.translatePath(os.path.join(SETTINGS_LOC, "cookiejar.lwp"))
PTVL_RUN    = xbmcgui.Window(10000).getProperty('PseudoTVRunning') == 'True'
IGNORE_KEYS = ['pluto.tv','plutotv','pluto tv','promo']
YTURL       = 'plugin://plugin.video.youtube/play/?video_id='
VMURL       = 'plugin://plugin.video.vimeo/play/?video_id='
BASE_URL    = 'http://pluto.tv/'#'http://silo.pluto.tv/'
BASE_API    = 'https://api.pluto.tv/v1'
BASE_LINEUP = 'https://api.pluto.tv/v1/channels.json'
BASE_GUIDE  = 'https://api.pluto.tv/v1/timelines/%s.000Z/%s.000Z/matrix.json'
BASE_CLIPS  = 'https://api.pluto.tv/v2/episodes/%s/clips.json'
USER_REGION = 'US'
PLUTO_MENU  = [("Channel Guide"  , BASE_LINEUP, 0),
               ("Browse Channels", BASE_LINEUP, 1)]
              
def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == True:
        if level == xbmc.LOGERROR:
            msg += ' ,' + traceback.format_exc()
        xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + stringify(msg), level)
        
def stringify(string):
    if isinstance(string, list):
        string = stringify(string[0])
    elif isinstance(string, (int, float, long, complex, bool)):
        string = str(string) 
    if isinstance(string, basestring):
        if not isinstance(string, unicode):
            string = unicode(string, 'utf-8')
        elif isinstance(string, unicode):
            string = string.encode('ascii', 'ignore')
        else:
            string = string.encode('utf-8', 'ignore')
    return string

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

class PlutoTV():
    def __init__(self):
        log('__init__')
        self.net   = net.Net()
        self.cache = SimpleCache()
        self.categoryMenu = self.getCategories()

        
    def login(self):
        log('login')
        header_dict               = {}
        header_dict['Accept']     = 'application/json, text/javascript, */*; q=0.01'
        header_dict['Host']       = 'api.pluto.tv'
        header_dict['Connection'] = 'keep-alive'
        header_dict['Referer']    = 'http://pluto.tv/'
        header_dict['Origin']     = 'http://pluto.tv'
        header_dict['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.2; rv:24.0) Gecko/20100101 Firefox/24.0'

        if len(USER_EMAIL) > 0:
            try:
                #remove COOKIE_JAR Folder
                xbmcvfs.rmdir(COOKIE_JAR)
            except:
                pass
                
            if xbmcvfs.exists(COOKIE_JAR) == False:
                try:
                    xbmcvfs.mkdirs(SETTINGS_LOC)
                    f = xbmcvfs.File(COOKIE_JAR, 'w')
                    f.close()
                except:
                    log('login, Unable to create the storage directory', xbmc.LOGERROR)
            
            form_data = ({'optIn': 'true', 'password': PASSWORD,'synced': 'false', 'userIdentity': USER_EMAIL})
            self.net.set_cookies(COOKIE_JAR)
            try:
                loginlink = self.loadJson(self.net.http_POST(BASE_API + '/auth/local', form_data=form_data, headers=header_dict).content.encode("utf-8").rstrip())
                if loginlink and loginlink['email'].lower() == USER_EMAIL.lower():
                    xbmcgui.Dialog().notification(ADDON_NAME, 'Welcome Back %s' % loginlink['displayName'], ICON, 4000)
                    self.net.save_cookies(COOKIE_JAR)
                    return True
                else:
                    xbmcgui.Dialog().notification(ADDON_NAME, 'Invalid User Credentials', ICON, 4000)
            except Exception,e:
                log('login, Unable to create the storage directory ' + str(e), xbmc.LOGERROR)


    def openURL(self, url):
        log('openURL, url = ' + url)
        try:
            header_dict               = {}
            header_dict['Accept']     = 'application/json, text/javascript, */*; q=0.01'
            header_dict['Host']       = 'api.pluto.tv'
            header_dict['Connection'] = 'keep-alive'
            header_dict['Referer']    = 'http://pluto.tv/'
            header_dict['Origin']     = 'http://pluto.tv'
            header_dict['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.2; rv:24.0) Gecko/20100101 Firefox/24.0'
            self.net.set_cookies(COOKIE_JAR)
            trans_table   = ''.join( [chr(i) for i in range(128)] + [' '] * 128 )
            cacheResponce = self.cache.get(ADDON_NAME + 'openURL, url = %s'%url)
            if not cacheResponce:
                try:
                    req = self.net.http_GET(url, headers=header_dict).content.encode("utf-8", 'ignore')
                except:
                    req = self.net.http_GET(url, headers=header_dict).content.translate(trans_table)
                self.net.save_cookies(COOKIE_JAR)
                self.cache.set(ADDON_NAME + 'openURL, url = %s'%url, json.loads(stringify(req)), expiration=datetime.timedelta(hours=8))
            responce = self.cache.get(ADDON_NAME + 'openURL, url = %s'%url)
            if len(responce) > 0:
                return responce
        except Exception,e:
            log('openURL, Unable to open url ' + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, 'Unable to Connect, Check User Credentials', ICON, 4000)
        

    def mainMenu(self):
        log('mainMenu')
        self.login()
        for item in PLUTO_MENU:
            self.addDir(*item)
            
            
    def browseMenu(self):
        log('browseMenu')
        for item in self.categoryMenu:
            self.addDir(*item)
            

    def getCategories(self):
        log('getCategories')
        collect= []
        lineup = []
        data = self.openURL(BASE_LINEUP)
        for channel in data:
            collect.append(channel['category'])
        counter = collections.Counter(collect)
        for key, value in sorted(counter.iteritems()):
            lineup.append(("%s"%(key), BASE_LINEUP, 2))
        lineup.insert(0,("Featured"  , BASE_LINEUP, 2))
        lineup.insert(2,("All Channels", BASE_LINEUP, 2))
        del collect[:]
        if len(lineup) > 0:
            return lineup
        
            
    def browse(self, chname, url):
        log('browse, chname = ' + chname)
        data = (self.openURL(url))
        for channel in data:
            id     = channel['_id']
            cat    = channel['category']
            number = channel['number']
            region = channel['regionFilter']['exclude']
            name   = channel['name']
            plot   = channel['description']
            feat   = (channel.get('featured','') or 0) == -1

            if FIT_REGION == True and USER_REGION in region:
                continue
            
            thumb = ICON
            if 'thumbnail' in channel:
                thumb = (channel['thumbnail']['path'] or ICON)
            land = FANART
            if 'featuredImage' in channel:
                land = (channel['featuredImage']['path'] or FANART)
            logo = ICON
            if 'logo' in channel:
                logo   = (channel['logo']['path'] or ICON)
            
            if chname == "All Channels":
                title = "%s - %s: %s" % (cat, number, name)
                infoLabels ={"label":title ,"title":title  ,"plot":plot, "code":number, "genre":cat, "imdbnumber":id}
                infoArt    ={"thumb":thumb,"poster":thumb,"fanart":land,"icon":logo,"logo":logo}
                self.addDir(title, id, 8, infoLabels, infoArt)
            elif chname == "Featured" and feat == True:
                title = "%s - %s: %s" % (cat, number, name)
                infoLabels ={"label":title ,"title":title  ,"plot":plot, "code":number, "genre":cat, "imdbnumber":id}
                infoArt    ={"thumb":thumb,"poster":thumb,"fanart":land,"icon":logo,"logo":logo}
                self.addDir(title, id, 8, infoLabels, infoArt)
                    
            elif chname.lower() == cat.lower():
                title = "%s: %s" % (number, name)
                infoLabels ={"label":title ,"title":title  ,"plot":plot, "code":number, "genre":cat, "imdbnumber":id}
                infoArt    ={"thumb":thumb,"poster":thumb,"fanart":land,"icon":logo,"logo":logo}
                self.addDir(title, id, 8, infoLabels, infoArt)
            
            
    def pagination(self, seq, rowlen):
        for start in xrange(0, len(seq), rowlen):
            yield seq[start:start+rowlen]

            
    def browseGuide(self, start=0, end=24):
        log('browseGuide')
        start = 0 if start == BASE_LINEUP else int(start)
        data  = (self.openURL(BASE_LINEUP))
        data  = list(self.pagination(data, end))
        start = 0 if start >= len(data) else start
        for channel in data[start]:
            chid    = channel['_id']
            chcat   = channel['category']
            chnum   = channel['number']
            region  = channel['regionFilter']['exclude']
            chname  = channel['name']
            chplot  = channel['description']
            chthumb = (channel['thumbnail']['path'] or ICON)
            feat    = (channel.get('featured','') or 0) == -1

            if FIT_REGION == True and USER_REGION in region:
                continue

            t1   = datetime.datetime.now().strftime('%Y-%m-%dT%H:00:00')
            t2   = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%dT%H:00:00')
            link = (self.openURL(BASE_GUIDE % (t1,t2)))
            item = link[chid][0]
            epid      = (item['episode']['_id'])
            epname    = item['episode']['name']
            epplot    = item['episode']['description']
            epgenre   = item['episode']['genre']
            epdur     = int(item['episode']['duration'] or '0') // 1000
            live      = item['episode']['liveBroadcast']
            thumb     = chthumb #(item['episode']['thumbnail']['path'] or chthumb) #site doesn't update missing episode thumbs

            title = "%s: %s - %s" % (chnum, chname, epname)
            infoLabels ={"label":title ,"title":title  ,"plot":epplot, "code":epid, "genre":epgenre, "imdbnumber":chid, "duration":epdur}
            infoArt    ={"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
            self.addLink(title, chid, 9, infoLabels, infoArt, end)
        start += 1
        self.addDir('>> Next', '%s'%(start), 0)
    

    def resolveURL(self, provider, url):
        log('resolveURL, provider = ' + provider)
        print url
        if provider == 'jwplatform' or url[-4:] == 'm3u8':
            return url
        elif provider == 'youtube':       
            if len(re.findall('http[s]?://www.youtube.com/watch', url)) > 0:
                return YTURL + url.split('/watch?v=')[1]
            elif len(re.findall('http[s]?://youtu.be/', url)) > 0:
                return YTURL + url.split('/youtu.be/')[1]
        elif provider == 'vimeo':
            if len(re.findall('http[s]?://vimeo.com/', url)) > 0:
                return VMURL + url.split('/vimeo.com/')[1]
        return urlresolver.resolve(url)

    
    def playChannel(self, name, url):
        log('playChannel')
        if PTVL_RUN == True:
            return
            
        origurl  = url
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        
        t1   = datetime.datetime.now().strftime('%Y-%m-%dT%H:00:00')
        t2   = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%dT%H:00:00')
        link = (self.openURL(BASE_GUIDE % (t1,t2)))
        item = link[origurl][0]
        id = item['episode']['_id']
        ch_start = datetime.datetime.fromtimestamp(time.mktime(time.strptime(item["start"].replace('.000Z','').replace('T',' '), "%Y-%m-%d %H:%M:%S")))
        ch_timediff = (datetime.datetime.now() - ch_start).seconds

        data = (self.openURL(BASE_CLIPS %(id)))
        dur_sum  = 0
        for idx, field in enumerate(data):
            url       = (field['url'] or field['code'])
            name      = field['name']
            thumb     = (field['thumbnail'] or ICON)
            provider  = field['provider']
            url       = self.resolveURL(provider, url)
            dur       = int(field['duration'] or '0') // 1000
            dur_start = dur_sum
            dur_sum  += dur

            if HIDE_PLUTO == True and any(k in name.lower() for k in IGNORE_KEYS):
                continue
                
            liz=xbmcgui.ListItem(name, path=url)
            infoList = {"label":name,"title":name,"duration":dur}
            infoArt  = {"thumb":thumb,"poster":thumb,"icon":ICON,"fanart":FANART}
            liz.setInfo(type="Video", infoLabels=infoList)
            liz.setArt(infoArt)
            liz.setProperty("IsPlayable","true")
            liz.setProperty("IsInternetStream",str(field['liveBroadcast']).lower())

            if dur_start < ch_timediff and dur_sum > ch_timediff:
                vid_offset = ch_timediff - dur_start
                liz.setProperty('ResumeTime', str(vid_offset))
            playlist.add(url, liz, idx)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

    
    def playContent(self, name, url):
        log('playContent')
        origurl = url            
        t1   = datetime.datetime.now().strftime('%Y-%m-%dT%H:00:00')
        t2   = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%dT%H:00:00')
        link = (self.openURL(BASE_GUIDE % (t1,t2)))
        item = link[origurl][0]
        id = item['episode']['_id']
        ch_start = datetime.datetime.fromtimestamp(time.mktime(time.strptime(item["start"].replace('.000Z','').replace('T',' '), "%Y-%m-%d %H:%M:%S")))
        ch_timediff = (datetime.datetime.now() - ch_start).seconds
        data = (self.openURL(BASE_CLIPS %(id)))
        dur_sum  = 0
        
        for idx, field in enumerate(data):
            url       = (field['url'] or field['code'])
            name      = field['name']
            thumb     = (field['thumbnail'] or ICON)
            provider  = field['provider']
            url       = self.resolveURL(provider, url)
            dur       = int(field['duration'] or '0') // 1000
            dur_start = dur_sum
            dur_sum  += dur

            if HIDE_PLUTO == True and any(k in name.lower() for k in IGNORE_KEYS):
                continue
                
            liz=xbmcgui.ListItem(name, path=url)
            infoList = {"label":name,"title":name,"duration":dur}
            infoArt  = {"thumb":thumb,"poster":thumb,"icon":ICON,"fanart":FANART}
            liz.setInfo(type="Video", infoLabels=infoList)
            liz.setArt(infoArt)
            liz.setProperty("IsPlayable","true")
            liz.setProperty("IsInternetStream",str(field['liveBroadcast']).lower())

            if dur_start < ch_timediff and dur_sum > ch_timediff:
                vid_offset = ch_timediff - dur_start
                liz.setProperty('ResumeTime', str(vid_offset) )
            self.addLink(name, url, 7, infoList, infoArt, len(data))

    
    def playVideo(self, name, url, list=None):
        log('playVideo')
        if not list:
            list = xbmcgui.ListItem(name, path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, list)

           
    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0):
        name = stringify(name)
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
        name = stringify(name)
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

if mode==None:  PlutoTV().mainMenu()
elif mode == 0: PlutoTV().browseGuide(url)
elif mode == 1: PlutoTV().browseMenu()
elif mode == 2: PlutoTV().browse(name, url)
elif mode == 7: PlutoTV().playVideo(name, url)
elif mode == 8: PlutoTV().playContent(name, url)
elif mode == 9: PlutoTV().playChannel(name, url)

xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE )
xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL )
xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)