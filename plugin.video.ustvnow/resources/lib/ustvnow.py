#   Copyright (C) 2019 Lunatixz
#
#
# This file is part of USTVnow
#
# USTVnow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# USTVnow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with USTVnow. If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, datetime, re, traceback, HTMLParser, calendar, uuid, collections, inputstreamhelper
import urlparse, urllib, urllib2, requests, socket, json, collections, random
import xbmc, xbmcvfs, xbmcgui, xbmcplugin, xbmcaddon

from simplecache import SimpleCache, use_cache

# Plugin Info
BRAND         = 'ustvnow'
ADDON_ID      = 'plugin.video.%s'%BRAND
REAL_SETTINGS = xbmcaddon.Addon()
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

## GLOBALS ##
TIMEOUT      = 30
CONTENT_TYPE = 'files'
MEDIA_TYPES  = {'SP':'video','SH':'episode','EP':'episode','MV':'movie'}
DEBUG        = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
USER_EMAIL   = REAL_SETTINGS.getSetting('User_Email')
PASSWORD     = REAL_SETTINGS.getSetting('User_Password')
LAST_TOKEN   = REAL_SETTINGS.getSetting('User_Token')
if REAL_SETTINGS.getSetting('User_Device') == "": REAL_SETTINGS.setSetting('User_Device',str(uuid.uuid4()))
BOX_ID       = REAL_SETTINGS.getSetting('User_Device')
DEV_ID       = 5
DEV_TYPE     = 5
IMG_PATH     = os.path.join(ADDON_PATH,'resources','images')
BASEWEB      = 'https://plus.%s.com'%(BRAND)
BASEAPI      = 'https://teleupapi.revlet.net'
BASEIMG      = 'https://d229kpbsb5jevy.cloudfront.net/teleup/320/280/content/common/'

MAIN_MENU    =  [(LANGUAGE(30032), '', 0),
                 (LANGUAGE(30033), '', 3)]

def uni(string, encoding = 'utf-8'):
    if isinstance(string, basestring):
        if not isinstance(string, unicode): string = unicode(string, encoding)
        elif isinstance(string, unicode): string = string.encode('ascii', 'replace')
    return string

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + (msg.encode("utf-8")), level)
        
def notificationDialog(str1):
    xbmcgui.Dialog().notification(ADDON_NAME, str1, ICON, 4000)
    
def inputDialog(heading=ADDON_NAME, default='', key=xbmcgui.INPUT_ALPHANUM, opt=0, close=0):
    retval = xbmcgui.Dialog().input(heading, default, key, opt, close)
    if len(retval) > 0: return retval    
    
def okDialog(str1, str2='', str3='', header=ADDON_NAME):
    xbmcgui.Dialog().ok(header, str1, str2, str3)
    
def yesnoDialog(str1, str2='', str3='', header=ADDON_NAME, yes='', no='', autoclose=0):
    return xbmcgui.Dialog().yesno(header, str1, str2, str3, no, yes, autoclose)
          
socket.setdefaulttimeout(TIMEOUT)
class USTVnow(object):
    def __init__(self, sysARG):
        log('__init__, sysARG = ' + str(sysARG))
        self.sysARG    = sysARG
        self.cache     = SimpleCache()
        self.header    = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
                          'content-type': 'application/json; charset=utf8',
                          'tenant-code': '%s'%BRAND,
                          'session-id': LAST_TOKEN,
                          'box-id': BOX_ID,
                          'origin': BASEWEB,
                          'DNT':'1'}
        
        
    def getURL(self, url, params={}, headers={}, life=datetime.timedelta(minutes=15)):
        log('getURL, url = %s, params = %s, headers = %s'%(url, params, headers))
        cacheresponse = self.cache.get(ADDON_NAME + '.getURL, url = %s.%s.%s'%(url,params,headers))
        if DEBUG: cacheresponse = None
        if not cacheresponse:
            try:
                r = requests.get(url, params, headers=headers)
                self.cache.set(ADDON_NAME + '.getURL, url = %s.%s.%s'%(url,params,headers), r.text, expiration=life)
                return r.json()
            except Exception as e: log("getURL, Failed! %s"%(e), xbmc.LOGERROR)
        else: return json.loads(cacheresponse)
        
        
    def postURL(self, url, params={}, headers={}, life=datetime.timedelta(minutes=15)):
        log('postURL, url = %s, params = %s, headers = %s'%(url, params, headers))
        cacheresponse = self.cache.get(ADDON_NAME + '.postURL, url = %s.%s.%s'%(url,params,headers))
        if DEBUG: cacheresponse = None
        if not cacheresponse:
            try:
                r = requests.post(url, json=params, headers=headers)
                self.cache.set(ADDON_NAME + '.postURL, url = %s.%s.%s'%(url,params,headers), r.text, expiration=life)
                return r.json()
            except Exception as e: log("postURL, Failed! %s"%(e), xbmc.LOGERROR)
        else: return json.loads(cacheresponse)
    

    def loadReminders(self):
        try: return json.loads(REAL_SETTINGS.getSetting('User_Reminders'))
        except: return {}
        
        
    def login(self, user, password):
        log('login, user = %s'%user)
        info = (self.getURL(BASEAPI + '/service/api/auth/user/info', headers=self.header) or {'message':LANGUAGE(30007),'response':''})
        if info['status']:
            # notificationDialog('%s, %s'%(LANGUAGE(30006),info['response']['firstName']))
            return True
        session = self.getURL(BASEAPI + '/service/api/v1/get/token', {'tenant_code':'%s'%BRAND,'product':'%s'%BRAND,'box_id':BOX_ID,'device_id':DEV_ID,'device_sub_type':DEV_TYPE})
        if not session.get('status',False):
            notificationDialog(info.get('error',{}).get('message','') or info.get('message','') or LANGUAGE(30007))
            return False
        token = session['response']['sessionId']
        self.header['session-id'] = token
        REAL_SETTINGS.setSetting('User_Token',token)
        signin = self.postURL(BASEAPI + '/service/api/auth/signin', params={'login_id':user,'login_key':password,'login_mode':1,'manufacturer':'Kodi'}, headers=self.header)
        if not signin.get('status',False):
            notificationDialog(signin.get('error',{}).get('message','') or signin.get('message','') or LANGUAGE(30007))
            return False
        notificationDialog('%s, %s'%(LANGUAGE(30006),signin['response']['firstName']))
        return True
        
    
    def buildMenu(self):
        log('buildMenu')
        for item in MAIN_MENU: self.addDir(*item)

        
    def getcurrentTime(self):
        return int(str(self.getURL(BASEAPI + '/service/api/current/epoch',life=datetime.timedelta(seconds=60)))[:-3])
        
       
    def getChanneldata(self, dtime=3):
        stime = self.getcurrentTime()
        etime = calendar.timegm((datetime.datetime.fromtimestamp(stime) + datetime.timedelta(days=dtime)).timetuple())
        for page in range(20):#todo find channel range
            try: 
                items = self.getURL(BASEAPI + '/service/api/v1/tv/guide', {'page':page,'pagesize':10}, headers=self.header, life=datetime.timedelta(hours=1))['response']['data']
                for item in items: yield item
            except: break
            
            
    def getContent(self, path='movie', count=24, life=datetime.timedelta(hours=1)):
        items = self.getURL(BASEAPI + '/service/api/v1/page/content', {'path':path,'count':count}, headers=self.header, life=life)['response']['data']
        return (item for item in items if len(item.get(item['paneType'],{}).get('sectionData',{}).get('data',{})) > 0)

  
    def resolveURL(self, path):
        stream = self.getURL(path, headers=self.header)
        if not stream.get('status',False): pass
        feeds = stream.get('response',{}).get('streams',{})
        return [feed['url'] for feed in feeds if feed.get('streamType','') == 'akamai'][0]
  
  
    def buildMeta(self, chname, chlogo, item, opt='guide'):
        sview  = item['display']['layout']
        title  = uni(item['display']['title'])
        now    = datetime.datetime.now()
        try: thumb  =  '%s/epgs/%s'%(BASEIMG,item['display']['imageUrl'].split(',')[1])
        except: thumb = chlogo
        try:
            stime  = datetime.datetime.fromtimestamp(float(item['display']['markers'][1]['value'][:-3]))
            etime  = datetime.datetime.fromtimestamp(float(item['display']['markers'][2]['value'][:-3]))
        except: stime  = etime = now
        # if stime < now: return None, None, None
        label  = '%s: %s - %s'%(stime.strftime('%I:%M %p').lstrip('0'),chname,title) if opt == 'guide' else '%s - %s'%(chname,title)
        label2 = ''
        plot   = uni(item['display']['subtitle2'])
        path   = BASEAPI + '/service/api/v1/page/stream?path=%s'%(item['target']['path'])
        liz = xbmcgui.ListItem(label)
        liz.setInfo(type="Video", infoLabels={"mediatype":'episode',"label":label,"label2":label2,"title":label,"plot":plot,"aired":stime.strftime('%Y-%m-%d'),"dateadded":stime.strftime('%Y-%m-%d')})
        liz.setArt({"thumb":thumb,"poster":thumb,"fanart":thumb})
        liz.setProperty("IsPlayable","true")
        liz.setProperty("IsInternetStream","true")
        return label, path, liz
        
        
    def buildLive(self):
        log('buildLive')
        filter   = []
        services = self.getContent('live')
        for service in services:
            section = service[service['paneType']]
            info  = section.get('sectionInfo',{})
            data  = section.get('sectionData',{}).get('data',{})
            provider = info['name']
            for item in data:
                chname = item['display']['parentName']
                if chname in filter: continue
                filter.append(chname)
                chlogo = BASEIMG + item['display']['imageUrl'].split(',')[1]
                chpath = BASEAPI + '/service/api/v1/page/content?path=%s'%(item['display']['subtitle5'])
                label, path, liz = self.buildMeta(chname, chlogo, item, 'live')
                self.addLink(label, path, '9', liz, len(data))
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
                

        
    def buildGuide(self, name=None):
        log('buildGuide, name = %s'%(name))
        channels = self.getChanneldata()
        for channel in channels:
            chname = channel['channel']['display']['title']
            chlogo = BASEIMG + channel['channel']['display']['imageUrl'].split(',')[1]
            chpath = BASEAPI + '/service/api/v1/page/content?path=%s'%(channel['channel']['target']['path'])
            if name is not None:
                if name.lower() == chname.lower():
                    lineup = channel['programs']
                    for item in lineup:
                        label, path, liz = self.buildMeta(chname, chlogo, item)
                        if label is None: continue
                        self.addLink(label, '', '9', liz, len(lineup))
                    xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_DATEADDED)
            else: 
                self.addDir(chname, chname, '3', infoArt={"thumb":chlogo,"poster":chlogo,"fanart":chlogo})
                xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
                    
        
    def buildContent(self, path):
        log('buildContent, path = %s'%(path))
        contents = self.getContent(path)
        for content in contents:
            genre = content['section']['sectionInfo']['name']
            items = content['section']['sectionData']['data']
            for item in items:
                chname = item['display']['title']
                chlogo = BASEIMG + item['display']['imageUrl'].split(',')[1]
                chpath = BASEAPI + '/service/api/v1/page/content?path=%s'%(item['target']['path'])
                label, path, liz = self.buildMeta(chname, chlogo, item)
                self.addLink(label, chpath, '9', liz, len(items))
        
        
    def playVideo(self, name, url):
        log('playVideo')
        url = self.resolveURL(url)
        liz = xbmcgui.ListItem(name, path=url)
        if 'm3u8' in url.lower():
            if not inputstreamhelper.Helper('hls').check_inputstream(): sys.exit()
            liz.setProperty('inputstreamaddon','inputstream.adaptive')
            liz.setProperty('inputstream.adaptive.manifest_type','hls')
        xbmcplugin.setResolvedUrl(int(self.sysARG[1]), True, liz)


    def addLink(self, name, u, mode, liz, total=0):
        log('addLink, name = ' + name)
        u=self.sysARG[0]+"?url="+urllib.quote(u)+"&mode="+str(mode)+"&name="+urllib.quote(uni(name))
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,totalItems=total)

        
    def addDir(self, name, u, mode, infoList=False, infoArt=False):
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name} )
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=self.sysARG[0]+"?url="+urllib.quote(u)+"&mode="+str(mode)+"&name="+urllib.quote(uni(name))
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,isFolder=True)
  
  
    def getParams(self):
        return dict(urlparse.parse_qsl(self.sysARG[2][1:]))

            
    def run(self):  
        params=self.getParams()
        try: url=urllib.unquote(params["url"])
        except: url=None
        try: name=urllib.unquote(params["name"])
        except: name=None
        try: mode=int(params["mode"])
        except: mode=None
        log("Mode: "+str(mode))
        log("URL : "+str(url))
        log("Name: "+str(name))

        if mode==None:  
            if not self.login(USER_EMAIL, PASSWORD): sys.exit()
            self.buildMenu()
        elif mode == 0: self.buildLive()
        elif mode == 3: self.buildGuide(url)
        elif mode == 5: self.buildContent(url)
        elif mode == 9: self.playVideo(name, url)

        xbmcplugin.setContent(int(self.sysARG[1])    , CONTENT_TYPE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=False)