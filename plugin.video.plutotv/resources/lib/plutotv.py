#   Copyright (C) 2018 Lunatixz
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
import os, sys, time, datetime, net, re, traceback
import urlparse, urllib, socket, json, collections
import xbmc, xbmcgui, xbmcplugin, xbmcvfs, xbmcaddon

from simplecache import SimpleCache
from YDStreamExtractor import getVideoInfo

# Plugin Info
ADDON_ID      = 'plugin.video.plutotv'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

## GLOBALS ##
TIMEOUT      = 15
CONTENT_TYPE = 'files'
USER_EMAIL   = REAL_SETTINGS.getSetting('User_Email')
PASSWORD     = REAL_SETTINGS.getSetting('User_Password')
USER_REGION  = REAL_SETTINGS.getSetting("Select_Country")
FIT_REGION   = False if USER_REGION == 'US' else True
DEBUG        = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
COOKIE_JAR   = xbmc.translatePath(os.path.join(SETTINGS_LOC, "cookiejar.lwp"))
PTVL_RUN     = xbmcgui.Window(10000).getProperty('PseudoTVRunning') == 'True'
HIDE_PLUTO   = True
IGNORE_KEYS  = ['Pluto TV Device Promo 15s prod','Space Station 10s - Promo','Pluto TV Device Promo 15s prod','Exploding Logo 5s','Pluto TV 5 Minute Spot Promo','vibes promo 5s']
YTURL        = 'plugin://plugin.video.youtube/play/?video_id='
VMURL        = 'plugin://plugin.video.vimeo/play/?video_id='
BASE_URL     = 'http://pluto.tv/'#'http://silo.pluto.tv/'
BASE_API     = 'https://api.pluto.tv/v1'
BASE_LINEUP  = 'https://api.pluto.tv/v1/channels.json'
BASE_GUIDE   = 'https://api.pluto.tv/v1/timelines/%s.000Z/%s.000Z/matrix.json'
BASE_CLIPS   = 'https://api.pluto.tv/v2/episodes/%s/clips.json'
PLUTO_MENU   = [("Browse Channels" , BASE_LINEUP, 0),
                ("Browse OnDemand" , BASE_LINEUP, 1),
                ("Channel Guide"   , BASE_LINEUP, 20)]
              
def inputDialog(heading=ADDON_NAME, default='', key=xbmcgui.INPUT_ALPHANUM, opt=0, close=0):
    retval = xbmcgui.Dialog().input(heading, default, key, opt, close)
    if len(retval) > 0:
        return retval    
               
def busyDialog(percent=0, control=None):
    if percent == 0 and not control:
        control = xbmcgui.DialogBusy()
        control.create()
    elif percent == 100 and control: return control.close()
    elif control: control.update(percent)
    return control
     
def yesnoDialog(str1, str2='', str3='', header=ADDON_NAME, yes='', no='', autoclose=0):
    return xbmcgui.Dialog().yesno(header, str1, str2, str3, no, yes, autoclose)
     

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def getParams():
    return dict(urlparse.parse_qsl(sys.argv[2][1:]))
                        
socket.setdefaulttimeout(TIMEOUT)
class PlutoTV():
    def __init__(self):
        log('__init__')
        self.net   = net.Net()
        self.cache = SimpleCache()
        self.categoryMenu = self.getCategories()
        self.mediaType = self.getMediaTypes()
        
        
    def login(self):
        log('login')
        #ignore guest login
        if USER_EMAIL == LANGUAGE(30009): return
            
        if len(USER_EMAIL) > 0:
            header_dict               = {}
            header_dict['Accept']     = 'application/json, text/javascript, */*; q=0.01'
            header_dict['Host']       = 'api.pluto.tv'
            header_dict['Connection'] = 'keep-alive'
            header_dict['Referer']    = 'http://pluto.tv/'
            header_dict['Origin']     = 'http://pluto.tv'
            header_dict['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.2; rv:24.0) Gecko/20100101 Firefox/24.0'
            
            try: xbmcvfs.rmdir(COOKIE_JAR)
            except: pass
                
            if xbmcvfs.exists(COOKIE_JAR) == False:
                try:
                    xbmcvfs.mkdirs(SETTINGS_LOC)
                    f = xbmcvfs.File(COOKIE_JAR, 'w')
                    f.close()
                except: log('login, Unable to create the storage directory', xbmc.LOGERROR)
            
            form_data = ({'optIn': 'true', 'password': PASSWORD,'synced': 'false', 'userIdentity': USER_EMAIL})
            self.net.set_cookies(COOKIE_JAR)
            try:
                loginlink = json.loads(self.net.http_POST(BASE_API + '/auth/local', form_data=form_data, headers=header_dict).content.encode("utf-8").rstrip())
                if loginlink and loginlink['email'].lower() == USER_EMAIL.lower():
                    xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30006) + loginlink['displayName'], ICON, 4000)
                    self.net.save_cookies(COOKIE_JAR)
                else: xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30007), ICON, 4000)
            except Exception as e: log('login, Unable to create the storage directory ' + str(e), xbmc.LOGERROR)
        
        else:
            #firstrun wizard
            if yesnoDialog(LANGUAGE(30008),no=LANGUAGE(30009), yes=LANGUAGE(30010)):
                REAL_SETTINGS.setSetting('User_Email',inputDialog(LANGUAGE(30001)))
                REAL_SETTINGS.setSetting('User_Password',inputDialog(LANGUAGE(30002)))
            else: REAL_SETTINGS.setSetting('User_Email',LANGUAGE(30009))
            xbmc.executebuiltin('RunScript("' + ADDON_PATH + '/country.py' + '")')
            
            
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
            cacheResponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheResponse:
                try: req = self.net.http_GET(url, headers=header_dict).content.encode("utf-8", 'ignore')
                except: req = (self.net.http_GET(url, headers=header_dict).content.translate(trans_table)).encode("utf-8")
                self.net.save_cookies(COOKIE_JAR)
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, req, expiration=datetime.timedelta(hours=1))
            response = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if isinstance(response, basestring): response = json.loads(response)
            return response
        except Exception as e:
            log('openURL, Unable to open url ' + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, 'Unable to Connect, Check User Credentials', ICON, 4000)
            return []
            

    def mainMenu(self):
        log('mainMenu')
        self.login()
        for item in PLUTO_MENU: self.addDir(*item)
            
            
    def browseMenu(self):
        log('browseMenu')
        for item in self.categoryMenu: self.addDir(*item)

           
    def getCategories(self):
        log('getCategories')
        collect= []
        lineup = []
        data = self.openURL(BASE_LINEUP)
        for channel in data: collect.append(channel['category'])
        counter = collections.Counter(collect)
        for key, value in sorted(counter.iteritems()): lineup.append(("%s"%(key)  , BASE_LINEUP, 2))
        lineup.insert(0,("Featured"    , BASE_LINEUP, 2))
        lineup.insert(2,("All Channels", BASE_LINEUP, 2))
        return lineup
        
        
    def getMediaTypes(self):
        mediaType = {}
        for type in self.categoryMenu:
            type = type[0]
            if type == 'Movies': mediaType[type] = 'movie'
            elif type == 'TV': mediaType[type] = 'episodes'
            elif type == 'Music + Radio': mediaType[type] = 'musicvideo'
            else: mediaType[type] = 'video'
        return mediaType
            
            
    def browse(self, chname, url):
        log('browse, chname = ' + chname)
        geowarn = False
        data    = (self.openURL(url))
        for channel in data:
            id      = channel['_id']
            cat     = channel['category']
            number  = channel['number']
            region  = channel['regionFilter']['include']
            exclude = channel['regionFilter']['exclude']
            name    = channel['name']
            plot    = channel['description']
            feat    = (channel.get('featured','') or 0) == -1
     
            if FIT_REGION == True and (USER_REGION in exclude or USER_REGION not in region):
                if geowarn == False:
                    geowarn = True
                    xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30004), ICON, 4000)
                continue
            
            thumb = ICON
            if 'thumbnail' in channel: thumb = (channel['thumbnail'].get('path',ICON) or ICON)
            land = FANART
            if 'featuredImage' in channel: land = (channel['featuredImage'].get('path',FANART) or FANART)
            logo = ICON
            if 'logo' in channel: logo   = (channel['logo']['path'] or ICON)
            if chname == "All Channels":
                title = "%s - %s: %s" % (cat, number, name)
                infoLabels ={"mediatype":self.mediaType[cat],"label":title ,"title":title  ,"plot":plot, "code":number, "genre":cat, "imdbnumber":id}
                infoArt    ={"thumb":thumb,"poster":thumb,"fanart":land,"icon":logo,"logo":logo}
                self.addDir(title, id, 8, infoLabels, infoArt)
            elif chname == "Featured" and feat == True:
                title = "%s - %s: %s" % (cat, number, name)
                infoLabels ={"mediatype":self.mediaType[cat],"label":title ,"title":title  ,"plot":plot, "code":number, "genre":cat, "imdbnumber":id}
                infoArt    ={"thumb":thumb,"poster":thumb,"fanart":land,"icon":logo,"logo":logo}
                self.addDir(title, id, 8, infoLabels, infoArt)
            elif chname.lower() == cat.lower():
                title = "%s: %s" % (number, name)
                infoLabels ={"mediatype":self.mediaType[cat],"label":title ,"title":title  ,"plot":plot, "code":number, "genre":cat, "imdbnumber":id}
                infoArt    ={"thumb":thumb,"poster":thumb,"fanart":land,"icon":logo,"logo":logo}
                self.addDir(title, id, 8, infoLabels, infoArt)
            
            
    def pagination(self, seq, rowlen):
        for start in xrange(0, len(seq), rowlen): yield seq[start:start+rowlen]

            
    def browseGuide(self, start=0, end=14):
        log('browseGuide')
        geowarn = False
        start   = 0 if start == BASE_LINEUP else int(start)
        data    = (self.openURL(BASE_LINEUP))
        data    = list(self.pagination(data, end))
        start   = 0 if start >= len(data) else start
        
        for channel in data[start]:
            chid    = channel['_id']
            chcat   = channel['category']
            chnum   = channel['number']
            region  = channel['regionFilter']['include']
            exclude = channel['regionFilter']['exclude']
            chname  = channel['name']
            chplot  = channel['description']
            chthumb = ICON
            if 'thumbnail' in channel: chthumb = (channel['thumbnail'].get('path',ICON) or ICON)
            feat = (channel.get('featured','') or 0) == -1
            
            if FIT_REGION == True and (USER_REGION in exclude or USER_REGION not in region):
                if geowarn == False:
                    geowarn = True
                    xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30004), ICON, 4000)
                continue

            t1   = datetime.datetime.now().strftime('%Y-%m-%dT%H:00:00')
            t2   = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%dT%H:00:00')
            link = (self.openURL(BASE_GUIDE % (t1,t2)))
            item = link[chid]
            
            if len(item) == 0: continue
            item      = item[0]
            epid      = (item['episode']['_id'])
            epname    = item['episode']['name']
            epplot    = (item['episode'].get('description',epname) or epname)
            epgenre   = (item['episode'].get('genre',chcat) or chcat)
            epdur     = int(item['episode'].get('duration','0') or '0') // 1000
            live      = item['episode']['liveBroadcast']
            thumb     = chthumb #(item['episode']['thumbnail']['path'] or chthumb) #site doesn't update missing episode thumbs
            title     = "%s: %s - %s" % (chnum, chname, epname)
            if any(k.lower().startswith(title.lower()) for k in IGNORE_KEYS): continue
            infoLabels ={"mediatype":self.mediaType[chcat],"label":title ,"title":title  ,"plot":epplot, "code":epid, "genre":epgenre, "imdbnumber":chid, "duration":epdur}
            infoArt    ={"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":ICON,"logo":ICON}
            self.addLink(title, chid, 9, infoLabels, infoArt, end)
        start += 1
        self.addDir('>> Next', '%s'%(start), 0)
    

    def resolveURL(self, provider, url):
        log('resolveURL, provider = ' + provider + ', url = ' + url)
        if provider == 'jwplatform' or url[-4:] == 'm3u8': return url
        elif provider == 'youtube':
            url = url.replace('feature=player_embedded&','')
            if len(re.findall('http[s]?://www.youtube.com/watch', url)) > 0: return YTURL + url.split('/watch?v=')[1]
            elif len(re.findall('http[s]?://youtu.be/', url)) > 0: return YTURL + url.split('/youtu.be/')[1]
        elif provider == 'vimeo':
            if len(re.findall('http[s]?://vimeo.com/', url)) > 0: return VMURL + url.split('/vimeo.com/')[1]
        else:
            info = getVideoInfo(url,3,True)
            if info is None: return YTURL + 'W6FjQgmtt0k'
            info = info.streams()
            return info[0]['xbmc_url']

     
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
        ch_start = datetime.datetime.fromtimestamp(time.mktime(time.strptime((item["start"].split('.')[0]), "%Y-%m-%dT%H:%M:%S")))
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

            liz=xbmcgui.ListItem(name, path=url)
            infoList = {"mediatype":"video","label":name,"title":name,"duration":dur}
            infoArt  = {"thumb":thumb,"poster":thumb,"icon":ICON,"fanart":FANART}
            liz.setInfo(type="Video", infoLabels=infoList)
            liz.setArt(infoArt)
            liz.setProperty("IsPlayable","true")
            liz.setProperty("IsInternetStream",str(field['liveBroadcast']).lower())
            if dur_start < ch_timediff and dur_sum > ch_timediff:
                vid_offset = ch_timediff - dur_start
                liz.setProperty('ResumeTime', str(vid_offset))
            if len(data) > 1: playlist.add(url, liz, idx)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
        xbmc.executebuiltin('ActivateWindow(fullscreenvideo)')
     
     
    def playContent(self, name, url):
        log('playContent')
        origurl = url
        t1   = datetime.datetime.now().strftime('%Y-%m-%dT%H:00:00')
        t2   = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%dT%H:00:00')
        link = (self.openURL(BASE_GUIDE % (t1,t2)))
        try: item = link[origurl][0]
        except Exception as e: return log('playContent, failed! ' + str(e), xbmc.LOGERROR)
        id = item['episode']['_id']
        ch_start = datetime.datetime.fromtimestamp(time.mktime(time.strptime((item["start"].split('.')[0]), "%Y-%m-%dT%H:%M:%S")))
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
            if any(k.lower().startswith(name.lower()) for k in IGNORE_KEYS): continue
            liz=xbmcgui.ListItem(name, path=url)
            infoList = {"mediatype":"video","label":name,"title":name,"duration":dur}
            infoArt  = {"thumb":thumb,"poster":thumb,"icon":ICON,"fanart":FANART}
            liz.setInfo(type="Video", infoLabels=infoList)
            liz.setArt(infoArt)
            liz.setProperty("IsPlayable","true")
            liz.setProperty("IsInternetStream",str(field['liveBroadcast']).lower())

            if dur_start < ch_timediff and dur_sum > ch_timediff:
                vid_offset = ch_timediff - dur_start
                liz.setProperty('ResumeTime', str(vid_offset) )
            self.addLink(name, url, 7, infoList, infoArt, len(data))
            
           
    def playVideo(self, name, url, liz=None):
        log('playVideo')
        if liz is None: liz = xbmcgui.ListItem(name, path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

           
    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0):
        name = name.encode("utf-8")
        log('addLink, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'true') 
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=sys.argv[0]+"?url="+urllib.quote(u)+"&mode="+str(mode)+"&name="+urllib.quote(name)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, infoList=False, infoArt=False):
        name = name.encode("utf-8")
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name} )
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=sys.argv[0]+"?url="+urllib.quote(u)+"&mode="+str(mode)+"&name="+urllib.quote(name)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

        
    def uEPG(self):
        log('uEPG')
        #support for upcoming uEPG universal epg framework module, module will be available from the Kodi repository.
        #https://github.com/Lunatixz/KODI_Addons/tree/master/script.module.uepg
        data = (self.openURL(BASE_LINEUP))
        prog = busyDialog(0)
        for cnt, channel in enumerate(data):
            chthumb    = ''
            chlogo     = ''
            chid       = channel['_id']
            chcat      = channel['category']
            chnum      = channel['number']
            region     = channel['regionFilter']['include']
            exclude    = channel['regionFilter']['exclude']
            chname     = channel['name']
            chplot     = channel['description']
            isFavorite = False #(channel.get('featured','') or 0) == -1
            
            if FIT_REGION == True and (USER_REGION in exclude or USER_REGION not in region):
                continue
            if 'thumbnail' in channel:
                chthumb = (channel['thumbnail'].get('path','') or '')
            if 'logo' in channel:
                chlogo = (channel['logo'].get('path','') or '')
                
            newChannel = {}
            guidedata  = []
            newChannel['channelname']   = chname
            newChannel['channelnumber'] = chnum
            newChannel['channellogo']   = chlogo
            newChannel['isfavorite']    = isFavorite
            
            t1   = datetime.datetime.now().strftime('%Y-%m-%dT%H:00:00')
            t2   = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%dT%H:00:00')
            link = (self.openURL(BASE_GUIDE % (t1,t2)))

            for i in range(len(link.get(chid,[]))):
                item      = link[chid][i]
                epname    = item['episode']['name']
                epid      = (item['episode']['_id'])
                epplot    = (item['episode'].get('description',epname) or epname)
                epgenre   = (item['episode'].get('genre',chcat)        or chcat)
                epsubgenre= (item['episode'].get('subGenre','')        or '')
                genre     = '%s + %s'%(epgenre, epsubgenre) if len(epsubgenre) > 0 else epgenre
                epdur     = int(item['episode'].get('duration','0') or '0') // 1000
                live      = item['episode']['liveBroadcast'] == "true"
                thumb     = chthumb
                poster    = (item['episode'].get('thumbnail','').get('path',chthumb) or chthumb)
                clips     = link[chid]
                
                if len(clips) == 0: continue
                clips   = clips[0]
                id      = clips['episode']['_id']
                data    = (self.openURL(BASE_CLIPS %(id)))
                tmpdata = {}
                for idx, field in enumerate(data):
                    url       = (field['url'] or field['code'])
                    name      = field['name']
                    thumb     = (field['thumbnail'] or ICON)
                    provider  = field['provider']
                    url       = self.resolveURL(provider, url)
                    dur       = int(field['duration'] or '0') // 1000
                    title     = "%s: %s" %(chname, epname)
                    if any(k.lower().startswith(title.lower()) for k in IGNORE_KEYS): continue
                    # #remove promos
                    # if any(k.lower().startswith(name.lower()) for k in IGNORE_KEYS):
                        # continue
                        
                    tmpdata            = {"mediatype":self.mediaType[chcat],"label":title,"title":chname,"originaltitle":epname,"plot":epplot, "code":epid, "genre":chcat, "imdbnumber":chid, "duration":dur}
                    #remove duplicates
                    # if any(x['code'] in epid for x in guidedata):
                        # continue
                    
                    tmpdata['starttime'] = time.time() #int(time.mktime(time.strptime((item["start"].split('.')[0]), "%Y-%m-%dT%H:%M:%S")))
                    tmpdata['url']       = sys.argv[0]+'?mode=7&name=%s&url=%s'%(title,url)
                    tmpdata['art']       ={"thumb":thumb,"clearart":poster,"fanart":FANART,"icon":chthumb,"clearlogo":chlogo}
                    guidedata.append(tmpdata)
                busyDialog(int(cnt + 1 * 100 // 100), prog)
            newChannel['guidedata'] = guidedata
            yield newChannel

params=getParams()
try: url=urllib.unquote(params["url"])
except: url=None
try: name=urllib.unquote(params["name"])
except: name=None
try: mode=int(params["mode"])
except: mode=None
    
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
elif mode == 20:xbmc.executebuiltin("RunScript(script.module.uepg,json=%s&skin_path=%s&refresh_path=%s&refresh_interval=%s&row_count=%s)"%(urllib.quote(json.dumps(list(PlutoTV().uEPG()))),urllib.quote(json.dumps(ADDON_PATH)),urllib.quote(json.dumps(sys.argv[0]+"?mode=20")),urllib.quote(json.dumps("7200")),urllib.quote(json.dumps("5"))))

xbmcplugin.setContent(int(sys.argv[1])    , CONTENT_TYPE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_TITLE)
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)