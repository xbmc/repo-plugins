#   Copyright (C) 2018 Lunatixz
#
#
# This file is part of Transponder.tv.
#
# Transponder.tv is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Transponder.tv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Transponder.tv.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import os, sys, time, _strptime, datetime, re, traceback, pytz, calendar
import urlparse, urllib, urllib2, socket, json, requests, mechanize, cookielib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs

from bs4 import BeautifulSoup
from simplecache import SimpleCache, use_cache

try:
    from multiprocessing import cpu_count 
    from multiprocessing.pool import ThreadPool 
    ENABLE_POOL = True
except: ENABLE_POOL = False

# Plugin Info
ADDON_ID      = 'plugin.video.transpondertv'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path').decode('utf-8')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

## GLOBALS ##
TIMEOUT       = 60
CONTENT_TYPE  = 'episodes'
MAX_LINEUP    = [1,2,3][int(REAL_SETTINGS.getSetting('Max_Lineup'))]
CACHE_DAYS    = (MAX_LINEUP - 1) if MAX_LINEUP > 1 else 1
USER_EMAIL    = REAL_SETTINGS.getSetting('User_Email')
PASSWORD      = REAL_SETTINGS.getSetting('User_Password')
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
COOKIE_JAR    = xbmc.translatePath(os.path.join(SETTINGS_LOC, "cookiejar.lwp"))
BASE_URL      = 'https://transponder.tv'
LOGIN_URL     = BASE_URL + '/login'
LIVE_URL      = BASE_URL + '/channels'
GUIDE_URL     = BASE_URL + '/guide%s?category=all' #%202018-10-11
RECORD_URL    = BASE_URL + '/recording'
NOWNEXT_URL   = BASE_URL + '/nownext'
CHANNEL_URL   = BASE_URL + '/watch'
LOGO          = os.path.join(SETTINGS_LOC,'%s.png')

MAIN_MENU     = [(LANGUAGE(30003), '' , 1),
                 (LANGUAGE(30004), '' , 2),
                 (LANGUAGE(30013), '' , 3),
                 (LANGUAGE(30002), '' , 4),
                 (LANGUAGE(30005), '' , 20)]

def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
    
def uni(string1, encoding = 'utf-8'):
    if isinstance(string1, basestring):
        if not isinstance(string1, unicode): string1 = unicode(string1, encoding)
        elif isinstance(string1, unicode): string1 = string1.encode('ascii', 'replace')
    return string1  
    
def inputDialog(heading=ADDON_NAME, default='', key=xbmcgui.INPUT_ALPHANUM, opt=0, close=0):
    retval = xbmcgui.Dialog().input(heading, default, key, opt, close)
    if len(retval) > 0: return retval    
    
def okDialog(str1, str2='', str3='', header=ADDON_NAME):
    xbmcgui.Dialog().ok(header, str1, str2, str3)

def yesnoDialog(str1, str2='', str3='', header=ADDON_NAME, yes='', no='', autoclose=0):
    return xbmcgui.Dialog().yesno(header, str1, str2, str3, no, yes, autoclose)
    
def notificationDialog(message, header=ADDON_NAME, sound=False, time=1000, icon=ICON):
    try: xbmcgui.Dialog().notification(header, message, icon, time, sound)
    except: xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % (header, message, time, icon))

def cleanString(string1):
    return string1.strip(' \t\n\r\b')
              
def trimString(string1):
    return re.sub('[\s+]', '', string1.strip(' \t\n\r\b'))

def retrieveURL(url, dest):
    try: urllib.urlretrieve(url, dest)
    except Exception as e: log("retrieveURL, Failed! " + str(e), xbmc.LOGERROR)
    return True
    
def hour_rounder(dt):
    return (dt.replace(second=0, microsecond=0, minute=0, hour=dt.hour) + datetime.timedelta(hours=dt.minute//30))
    
socket.setdefaulttimeout(TIMEOUT)  
class Transponder(object):
    def __init__(self, sysARG):
        log('__init__')
        self.chnum   = 0
        self.sysARG  = sysARG
        self.cache   = SimpleCache()
        self.mechze  = mechanize.Browser()
        self.cj      = cookielib.LWPCookieJar()
        if self.login(USER_EMAIL, PASSWORD) == False: sys.exit()  
        self.channels   = self.getChannels()
        self.recordings = self.getRecordings()
        
        
    def login(self, user, password):
        log('login')
        if len(user) > 0:
            try: xbmcvfs.rmdir(COOKIE_JAR)
            except: pass
            
            if xbmcvfs.exists(COOKIE_JAR) == False:
                try:
                    xbmcvfs.mkdirs(SETTINGS_LOC)
                    f = xbmcvfs.File(COOKIE_JAR, 'w')
                    f.close()
                except: log('login, Unable to create the storage directory', xbmc.LOGERROR)
                
            try:
                login = self.mechze
                login.set_handle_robots(False)
                login.set_cookiejar(self.cj)
                login.addheaders = [('User-Agent','Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)')]
                login.open(LOGIN_URL)
                if '/myaccount' in login.response().read(): return True 
                # login.open(LOGIN_URL)
                login.select_form(nr=0)
                login.form['email'] = user
                login.form['password'] = password
                login.submit()
                login.open(LOGIN_URL)
                if '/myaccount' not in login.response().read(): 
                    notificationDialog(LANGUAGE(30024))
                    return False
                self.cj.save(COOKIE_JAR, ignore_discard=True)  
                return True
            except Exception as e: 
                log("login, failed! " + str(e), xbmc.LOGERROR)
                notificationDialog(LANGUAGE(30001))
                return False
        else:
            #firstrun wizard
            if yesnoDialog(LANGUAGE(30010),no=LANGUAGE(30008), yes=LANGUAGE(30009)):
                user     = inputDialog(LANGUAGE(30006))
                password = inputDialog(LANGUAGE(30007),opt=xbmcgui.ALPHANUM_HIDE_INPUT)
                REAL_SETTINGS.setSetting('User_Email'   ,user)
                REAL_SETTINGS.setSetting('User_Password',password)
                return self.login(user, password)
            else: 
                okDialog(LANGUAGE(30012))
                return False
        
        
    def getDuration(self, timeString):
        starttime, endtime = timeString.split('-')
        try: endtime = datetime.datetime.strptime(endtime, '%H:%M') 
        except TypeError: endtime = datetime.datetime(*(time.strptime(endtime, '%H:%M')[0:6]))
        try: starttime = datetime.datetime.strptime(starttime, '%H:%M') 
        except TypeError: starttime = datetime.datetime(*(time.strptime(starttime, '%H:%M')[0:6]))
        durtime = (endtime - starttime)
        return durtime.seconds
        
        
    def getLocalNow(self, offset=0):
        ltz = pytz.timezone('Europe/London')
        return datetime.datetime.now(ltz) + datetime.timedelta(days=offset)
        
        
    def getLocaltime(self, timeString, dst=False, offset=0):
        ltz   = pytz.timezone('Europe/London')
        try: ltime = datetime.datetime.strptime(timeString, '%H:%M').time()
        except TypeError: ltime = datetime.datetime(*(time.strptime(timeString, '%H:%M')[0:6])).time()
        ldate = self.getLocalNow(offset).date()
        ltime = ltz.localize((datetime.datetime.combine(ldate, ltime)))
        ltime = ltime.astimezone(pytz.timezone('UTC')).replace(tzinfo=None)
        if dst: return ltime - ((datetime.datetime.utcnow() - datetime.datetime.now()) +  datetime.timedelta(hours=time.daylight))
        else: return ltime - (datetime.datetime.utcnow() - datetime.datetime.now())
        
        
    def openURL(self, url, life=datetime.timedelta(minutes=15)):
        log('openURL, url = ' + str(url))
        try:
            cacheresponse = self.cache.get(ADDON_NAME + '.openURL, url = %s'%url)
            if not cacheresponse:
                results = self.mechze
                results.set_handle_robots(False)
                results.set_handle_refresh(True)
                results.set_cookiejar(self.cj)
                results.addheaders = [('Connection','keep-alive'),('User-Agent','Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)')]
                results.open(url)
                cacheresponse = results.response().read()
                self.cache.set(ADDON_NAME + '.openURL, url = %s'%url, cacheresponse, expiration=life)
            return cacheresponse
        except Exception as e:
            log("openURL Failed! " + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return ''
            
            
    def buildMenu(self, items):
        for item in items:
            if len(self.recordings['Schedules']) == 0 and item[0] == LANGUAGE(30013): continue
            elif len(self.recordings['Recordings']) == 0 and item[0] == LANGUAGE(30002): continue
            self.addDir(*item)
            
        
    @use_cache(1)
    def getChannels(self):
        log('getChannels')
        channels = {}
        soup     = BeautifulSoup(self.openURL(LIVE_URL), "html.parser")
        results  = soup('div' , {'class': 'channelBox'})
        for idx, channel in enumerate(results):
            link   = channel.find_all('a')[0].attrs['href']
            chname = channel.find_all('img')[0].attrs['alt']
            logo   = '%s/%s'%(BASE_URL,channel.find_all('img')[0].attrs['src'])
            channels[link.replace('/watch/','')] = {'name':chname,'logo':logo,'url':link,'number':idx + 1}
        return (channels or {})
        
        
    def getRecordings(self):
        log('getRecordings')
        record  = {}
        soup    = BeautifulSoup(self.openURL(RECORD_URL,life=datetime.timedelta(seconds=5)), "html.parser")
        record['Recordings'] = (soup('div' , {'id': 'savedRecordings'})[0]('div' , {'class': 'recordingBox'}))
        record['Schedules']  = (soup('div' , {'id': 'scheduledRecordings'})[0]('div' , {'class': 'secondaryBubble'}))
        return (record or {})
        
        
    def buildSchedules(self):
        log('buildSchedules')
        items = self.recordings['Schedules']
        if len(items) == 0: self.addLink(LANGUAGE(30018), '', None)
        for item in items:
            chlogo = '%s/%s'%(BASE_URL,item.find_all('img')[0].attrs['src'])
            link   = item.find_all('a')[0].attrs['href']
            chname = cleanString(self.channels[re.compile('/images/channelicons/(.+?).png').findall(item.find_all('img')[0].attrs['src'])[0]]['name'])
            label  = cleanString('%s - %s'%(chname,cleanString(item.find_all('br')[0].get_text())))
            infoLabels  = {"mediatype":"episode","label":label,"title":label}
            infoArt     = {"thumb":chlogo,"poster":chlogo,"fanart":FANART,"icon":chlogo,"clearlogo":chlogo}
            contextMenu = [(LANGUAGE(30016),'XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?url="+urllib.quote(link.replace('/watch/','/delete/'))+"&mode="+str(6)+"&name="+urllib.quote(label)))]
            self.addLink(label, link, 21, infoLabels, infoArt, len(items), contextMenu)
        

    def buildRecordings(self):
        log('buildRecordings')
        items = self.recordings['Recordings']
        if len(items) == 0: self.addLink(LANGUAGE(30019), '', None)
        for item in items:
            chlogo = '%s/%s'%(BASE_URL,item.find_all('img')[0].attrs['src'])
            link   = item.find_all('a')[0].attrs['href']
            chname = cleanString(self.channels[re.compile('/images/channelicons/(.+?).png').findall(item.find_all('img')[0].attrs['src'])[0]]['name'])
            label  = cleanString('%s - %s'%(chname,cleanString(item.find_all('p')[0].get_text())))
            infoLabels  = {"mediatype":"episode","label":label,"title":label}
            infoArt     = {"thumb":chlogo,"poster":chlogo,"fanart":FANART,"icon":chlogo,"clearlogo":chlogo}
            contextMenu = [(LANGUAGE(30017),'XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?url="+urllib.quote(link.replace('/watch/','/delete/'))+"&mode="+str(6)+"&name="+urllib.quote(label)))]
            self.addLink(label, link, 9, infoLabels, infoArt, len(items), contextMenu)
        
        
    def setRecording(self, name, href):
        log('setRecording, href = ' + href)
        try: 
            soup    = BeautifulSoup(self.openURL(BASE_URL + href, datetime.timedelta(seconds=1)))
            message = '%s, %s'%(cleanString(soup('p' , {'class': 'floatLeft'})[0].get_text()),cleanString(soup('p' , {'class': 'floatRight'})[0].get_text()))
            notificationDialog(message, time=20000)
        except: pass
        
        
    def delRecording(self, name, href):
        log('delRecording, href = ' + href)
        try: 
            soup    = BeautifulSoup(self.openURL(BASE_URL + href, datetime.timedelta(seconds=1)))
            message = '%s, %s'%(cleanString(soup('p' , {'class': 'floatLeft'})[0].get_text()),cleanString(soup('p' , {'class': 'floatRight'})[0].get_text()))
            notificationDialog(message, time=20000)
            xbmc.executebuiltin("Container.Refresh")
        except: pass
        
        
    def buildProgram(self, href):
        log('buildProgram, href = ' + href)
        soup     = BeautifulSoup(self.openURL(BASE_URL + href,datetime.timedelta(days=28)), "html.parser")
        results  = soup('div' , {'id': 'programmeGrid'})[0]
        thumb    = results('div' , {'id': 'programmeImg'})[0].find_all('img')[0].attrs['src']
        plot     = cleanString(results('div' , {'id': 'programmeMain'})[0].find_all('p')[0].get_text())
        genre    = cleanString(results('div' , {'id': 'programmeAside'})[0].find_all('p')[0].get_text().split(' - '))
        return thumb, plot, genre 
        
        
    def buildLive(self):
        soup    = BeautifulSoup(self.openURL(NOWNEXT_URL), "html.parser")
        results = soup('div' , {'class': 'nowNextChannel'})
        for channel in results:
            chlogo = '%s/%s'%(BASE_URL,channel.find_all('img')[0].attrs['src'])
            link   = channel.find_all('a')[0].attrs['href']
            chname = self.channels[link.replace('/watch/','')]['name']
            now    = channel('div' , {'class': 'now programme'})
            label  = '%s - %s'%(chname,now[0].find_all('a')[0].get_text())
            thumb  = chlogo
            plot   = label
            genre  = 'Live'
            # try: thumb, plot, genre = self.buildProgram(channel.find_all('a')[1].attrs['href'])
            # except: pass
            infoLabels = {"mediatype":"episode","label":label,"title":label,"plot":plot,"genre":genre}
            infoArt    = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":chlogo,"clearlogo":chlogo}
            self.addLink(label, link, 9, infoLabels, infoArt, len(results))
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        
        
    def buildLineups(self, days=1):
        log('buildLineups, days = ' + str(days))
        progs = []
        for i in range(days):
            if i == 0: offset = ''
            else: offset = '/%'+ str(self.getLocalNow(i).date())
            soup = BeautifulSoup(self.openURL(GUIDE_URL%(offset),datetime.timedelta(days=(i+1))), "html.parser")
            items = (soup('div' , {'class': 'tvguideChannelListings noselect'}))
            progs.append(items)
        return progs
        
        
    def buildLineup(self, name=None, url=None):
        log('buildLineup, name = ' + str(name))
        if url is None:
            soup = BeautifulSoup(self.openURL(GUIDE_URL%('')), "html.parser")
            for channel in self.channels:
                link   = self.channels[channel]['url']
                chname = self.channels[channel]['name']
                chlogo = self.channels[channel]['logo']
                infoLabels = {"mediatype":"episode","label":chname ,"title":chname,"tracknumber":self.channels[channel]['number']}
                infoArt    = {"thumb":chlogo,"poster":chlogo,"fanart":FANART,"icon":chlogo,"clearlogo":chlogo}
                self.addDir(chname, link, 2, infoLabels, infoArt)
            xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_TRACKNUM	)
        else:
            datas = (self.buildLineups(MAX_LINEUP))
            for idx, data in enumerate(datas):
                now = datetime.datetime.now() + datetime.timedelta(days=idx)
                for item in data:
                    if name.lower().replace('  1',' +1') == item.find_all('h3')[0].get_text().lower():
                        listings = (item('div' , {'class': re.compile(r'programme\s')}))
                        for listing in listings:
                            mode   = 9
                            stime  = listing.find_all('p')
                            if not stime: continue
                            stime  = trimString(stime[0].get_text())
                            dur    = self.getDuration(stime)
                            start  = self.getLocaltime(stime.split('-')[0], offset=idx)
                            end    = start + datetime.timedelta(seconds=dur)
                            try: title  = cleanString(listing.find_all('h3')[0].find_all('a')[0].get_text())
                            except: title = cleanString(item.find_all('h3')[0].get_text())
                            if idx == 0 and now > end: continue
                            if idx == 0 and now >= start and now < end: title = '[B]%s[/B]'%title
                            # if now < end: mode = 21 # call contextMenu
                            aired  = start.strftime('%Y-%m-%d')
                            start  = start.strftime('%I:%M %p')
                            label  = cleanString('%s: %s'%(start,title))
                            chlogo = self.channels[url.replace('/watch/','')]['logo']
                            thumb  = chlogo
                            plot   = label
                            genre  = 'Live'
                            contextMenu = []
                            # try: thumb, plot, genre = self.buildProgram(listing.find_all('a')[0].attrs['href'])
                            # except: pass
                            try:
                                contextMenu = [(LANGUAGE(30011),'XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?url="+urllib.quote(listing.find_all('a')[2].attrs['href'])+"&mode="+str(5)+"&name="+urllib.quote(title)))]
                                plot = '%s [CR]%s'%(plot,LANGUAGE(30023))
                            except: pass
                            infoLabels  = {"mediatype":"episode","label":label ,"title":label,"plot":plot,"duration":dur,"aired":aired,"genre":genre}
                            infoArt     = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":chlogo,"clearlogo":chlogo}
                            self.addLink(label, url, mode, infoLabels, infoArt, len(listings), contextMenu)
                        break
            xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        

    def uEPG(self):
        log('uEPG')
        #support for uEPG universal epg framework module available from the Kodi repository. https://github.com/Lunatixz/KODI_Addons/tree/master/script.module.uepg
        lineup = (self.buildLineups(MAX_LINEUP))
        return self.poolList(self.buildGuide, [(self.channels[channel]['number'], self.channels[channel], lineup) for channel in self.channels])
        
        
    def buildGuide(self, data):
        chnum, channel, datas = data
        chname     = channel['name']
        link       = channel['url']
        chlogo     = channel['logo']
        isFavorite = False 
        newChannel = {}
        guidedata  = []
        newChannel['channelname']   = chname
        newChannel['channelnumber'] = chnum
        newChannel['channellogo']   = chlogo
        newChannel['isfavorite']    = isFavorite
        for idx, data in enumerate(datas):
            now = datetime.datetime.now() + datetime.timedelta(days=idx)
            for item in data:
                if chname.lower().replace('  1',' +1') == item.find_all('h3')[0].get_text().lower():
                    listings = (item('div' , {'class': re.compile(r'programme\s')}))
                    for listing in listings:
                        stime = listing.find_all('p')
                        if not stime: continue
                        stime  = trimString(stime[0].get_text())
                        dur    = self.getDuration(stime)
                        start  = self.getLocaltime(stime.split('-')[0], offset=idx)
                        end    = start + datetime.timedelta(seconds=dur)
                        aired  = start.strftime('%Y-%m-%d')
                        try: label  = listing.find_all('h3')[0].find_all('a')[0].get_text()
                        except: label = item.find_all('h3')[0].get_text()
                        if idx == 0 and now > end: continue
                        thumb  = chlogo
                        plot   = label
                        genre  = 'Live'
                        contextMenu = []
                        # try: thumb, plot, genre = self.buildProgram(listing.find_all('h3')[0].attrs['href'])
                        # except: pass
                        try:
                            contextMenu = [(LANGUAGE(30011),'XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?url="+urllib.quote(listing.find_all('h3')[2].attrs['href'])+"&mode="+str(5)+"&name="+urllib.quote(label)))]
                            plot = '%s [CR]%s'%(plot,LANGUAGE(30023))
                        except: pass
                        tmpdata = {"mediatype":"episode","label":label ,"title":label,"plot":plot,"duration":dur,"aired":aired,"genre":genre}
                        tmpdata['starttime'] = time.mktime(start.timetuple())
                        tmpdata['url'] = self.sysARG[0]+'?mode=9&name=%s&url=%s'%(label,link)
                        tmpdata['art'] = {"thumb":thumb,"poster":thumb,"fanart":FANART,"icon":chlogo,"clearlogo":chlogo}
                        tmpdata['contextmenu'] = json.dumps(contextMenu)
                        guidedata.append(tmpdata)
                    break
        newChannel['guidedata'] = guidedata
        return newChannel
        
        
    def poolList(self, method, items):
        results = []
        if ENABLE_POOL:
            pool = ThreadPool(cpu_count())
            results = pool.imap_unordered(method, items)
            pool.close()
            pool.join()
        else: results = [method(item) for item in items]
        results = filter(None, results)
        return results
        
        
    def resolverURL(self, url):
        return 'https://' + re.compile('<source src="https://(.+?)" type="application/x-mpegURL">').findall(self.openURL(BASE_URL + url))[0]

        
    def playVideo(self, name, url, liz=None):
        log('playVideo')
        liz  = xbmcgui.ListItem(name, path=self.resolverURL(url))
        liz.setMimeType('application/x-mpegURL')
        if url.startswith(BASE_URL):
            liz.setProperty('inputstreamaddon','inputstream.adaptive')
            liz.setProperty('inputstream.adaptive.manifest_type','hls')
        xbmcplugin.setResolvedUrl(int(self.sysARG[1]), True, liz)


    def addLink(self, name, u, mode, infoList=False, infoArt=False, total=0, contextMenu=None):
        name = name.encode("utf-8")
        log('addLink, name = ' + name)
        liz=xbmcgui.ListItem(name)
        if mode == 21: liz.setProperty("IsPlayable","false")
        else: liz.setProperty('IsPlayable', 'true')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        if contextMenu is not None: liz.addContextMenuItems(contextMenu)
        u=self.sysARG[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,totalItems=total)


    def addDir(self, name, u, mode, infoList=False, infoArt=False):
        name = name.encode("utf-8")
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False: liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name})
        else: liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False: liz.setArt({'thumb':ICON,'fanart':FANART})
        else: liz.setArt(infoArt)
        u=self.sysARG[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(handle=int(self.sysARG[1]),url=u,listitem=liz,isFolder=True)


    def getParams(self):
        return dict(urlparse.parse_qsl(self.sysARG[2][1:]))

            
    def run(self):  
        params=self.getParams()
        try: url=urllib.unquote_plus(params["url"])
        except: url=None
        try: name=urllib.unquote_plus(params["name"])
        except: name=None
        try: mode=int(params["mode"])
        except: mode=None
        log("Mode: "+str(mode))
        log("URL : "+str(url))
        log("Name: "+str(name))

        if mode==None:  self.buildMenu(MAIN_MENU)
        elif mode == 1: self.buildLive()
        elif mode == 2: self.buildLineup(name, url)
        elif mode == 3: self.buildSchedules()
        elif mode == 4: self.buildRecordings()
        elif mode == 5: self.setRecording(name, url)
        elif mode == 6: self.delRecording(name, url)
        elif mode == 9: self.playVideo(name, url)
        elif mode == 20:xbmc.executebuiltin("RunScript(script.module.uepg,json=%s&refresh_path=%s&refresh_interval=%s&row_count=%s)"%(urllib.quote(json.dumps(list(self.uEPG()))),urllib.quote(json.dumps(self.sysARG[0]+"?mode=20")),urllib.quote(json.dumps("10800")),urllib.quote(json.dumps("7"))))
        elif mode == 21:xbmc.executebuiltin("action(ContextMenu)")
        
        xbmcplugin.setContent(int(self.sysARG[1])    , CONTENT_TYPE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=True)