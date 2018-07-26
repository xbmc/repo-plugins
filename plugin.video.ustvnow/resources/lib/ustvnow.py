#   Copyright (C) 2018 Lunatixz
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
import os, sys, time, datetime, re, traceback, HTMLParser, calendar
import urlparse, urllib, urllib2, socket, json, collections, net, random
import xbmc, xbmcvfs, xbmcgui, xbmcplugin, xbmcaddon

from simplecache import SimpleCache
# Plugin Info
BRAND         = 'ustvnow'
ADDON_ID      = 'plugin.video.%s'%BRAND
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
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
USER_EMAIL   = REAL_SETTINGS.getSetting('User_Email')
PASSWORD     = REAL_SETTINGS.getSetting('User_Password')
LAST_TOKEN   = REAL_SETTINGS.getSetting('User_Token')
LAST_PASSKEY = REAL_SETTINGS.getSetting('User_Paskey')
DEBUG        = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
PTVL_RUN     = xbmcgui.Window(10000).getProperty('PseudoTVRunning') == 'True'
IMG_PATH     = os.path.join(ADDON_PATH,'resources','images')
COOKIE_JAR   = xbmc.translatePath(os.path.join(SETTINGS_LOC, "cookiejar.lwp"))
URL_TYPE     = {0:'m3u8',1:'mp4'}[int(REAL_SETTINGS.getSetting('URL_Type'))]
URL_QUALITY  = int(REAL_SETTINGS.getSetting('URL_Quality')) + 1
MEDIA_TYPES  = {'SP':'video','SH':'episode','EP':'episode','MV':'movie'}
FREE_CHANS   = ['CW','ABC','FOX','PBS','CBS','NBC','MY9']
BASEURL      = 'http://m.%s.com/'%BRAND
BASEWEB      = 'http://%s.com'%BRAND
BASEVOD      = 'http://watch.ustvnow.com'
PTR_BASE     = 'http://m.poster.static-%s.com'%BRAND
IMG_BASE     = 'http://m.images.static-%s.com'%BRAND
IMG_SOURCE   = PTR_BASE + '/%s/%s/%s/med'
IMG_CHLOGO   = IMG_BASE+'/%s.png'
IMG_URL      = 'http://tvdata.%s.com/'%BRAND
IMG_CHLOGO_C = IMG_URL+'chn-logos/360/%s.png'
IMG_CHLOGO_W = IMG_URL+'inverse-logos/360/%s.png'

USTVNOW_MENU = [("Live"       , '', 0),
                ("Schedules"  , '', 1),
                ("Recordings" , '', 2),
                ("Lineup"     , '', 3),
                ("Movies"     , '', 5),
                ("Highlights" , '', 12),
                ("OnDemand"   , '', 13),
                ("Search"     , '', 11),
                ("Guide"      , '', 20)]
                
uEPG_PARAMS  = {"runtime":"duration","stream_code":"studio","description":"plot","synopsis":"plotoutline","ut_start":"starttime","orig_air_date":"firstaired"}
FILE_PARAMS  = ["title", "artist", "albumartist", "genre", "year", "rating", "album", "track", "duration", "comment", "lyrics", "musicbrainztrackid", "musicbrainzartistid", "musicbrainzalbumid", "musicbrainzalbumartistid", "playcount", "fanart", "director", "trailer", "tagline", "plot", "plotoutline", "originaltitle", "lastplayed", "writer", "studio", "mpaa", "cast", "country", "imdbnumber", "premiered", "productioncode", "runtime", "set", "showlink", "streamdetails", "top250", "votes", "firstaired", "season", "episode", "showtitle", "thumbnail", "file", "resume", "artistid", "albumid", "tvshowid", "setid", "watchedepisodes", "disc", "tag", "art", "genreid", "displayartist", "albumartistid", "description", "theme", "mood", "style", "albumlabel", "sorttitle", "episodeguide", "uniqueid", "dateadded", "size", "lastmodified", "mimetype", "specialsortseason", "specialsortepisode"]
PVR_PARAMS   = ["title","plot","plotoutline","starttime","endtime","runtime","progress","progresspercentage","genre","episodename","episodenum","episodepart","firstaired","hastimer","isactive","parentalrating","wasactive","thumbnail","rating","originaltitle","cast","director","writer","year","imdbnumber","hastimerrule","hasrecording","recording","isseries"]
ART_PARAMS   = ["thumb","poster","fanart","banner","landscape","clearart","clearlogo"]

def uni(string, encoding = 'utf-8'):
    if isinstance(string, basestring):
        if not isinstance(string, unicode): string = unicode(string, encoding)
        elif isinstance(string, unicode): string = string.encode('ascii', 'replace')
    return string

def unescape(string):
    try: return (HTMLParser.HTMLParser().unescape(string))
    except: return string
        
def log(msg, level=xbmc.LOGDEBUG):
    if DEBUG == False and level != xbmc.LOGERROR: return
    if level == xbmc.LOGERROR: msg += ' ,' + traceback.format_exc()
    xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + (msg.encode("utf-8")), level)
        
def inputDialog(heading=ADDON_NAME, default='', key=xbmcgui.INPUT_ALPHANUM, opt=0, close=0):
    retval = xbmcgui.Dialog().input(heading, default, key, opt, close)
    if len(retval) > 0: return retval    
    
def okDialog(str1, str2='', str3='', header=ADDON_NAME):
    xbmcgui.Dialog().ok(header, str1, str2, str3)
    
def yesnoDialog(str1, str2='', str3='', header=ADDON_NAME, yes='', no='', autoclose=0):
    return xbmcgui.Dialog().yesno(header, str1, str2, str3, no, yes, autoclose)
        
socket.setdefaulttimeout(TIMEOUT)
class USTVnow():
    def __init__(self, sysARG):
        log('__init__, sysARG = ' + str(sysARG))
        self.sysARG    = sysARG
        self.net       = net.Net()
        self.cache     = SimpleCache()
        self.reminders = self.loadReminders()
        self.isFree    = REAL_SETTINGS.getSetting('User_isFree') == "True"
        if self.login(USER_EMAIL, PASSWORD) == False: xbmc.executebuiltin("Container.Refresh")
    
    
    def loadReminders(self):
        try: return json.loads(REAL_SETTINGS.getSetting('User_Reminders'))
        except: return {}
        
        
    def mainMenu(self):
        log('mainMenu')
        for item in USTVNOW_MENU:
            if self.highlights and item[0] == "Highlights":
                if len(self.highlights) <= 2: continue
            elif self.recorded and item[0] in ["Schedules","Recordings"]:
                if len(self.recorded) <= 2: continue
            self.addDir(*item)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
        
        
    def buildHeader(self):
        header_dict               = {}
        header_dict['Accept']     = 'application/json, text/javascript, */*; q=0.01'
        header_dict['Connection'] = 'keep-alive'
        header_dict['Referer']    = BASEVOD
        header_dict['Origin']     = BASEVOD
        header_dict['User-Agent'] = 'http://kodi.tv/%s'%ADDON_ID; 
        return header_dict
        
        
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
            header_dict = self.buildHeader()
            qstr = urllib.urlencode({'username':user,'password':password})
            self.net.set_cookies(COOKIE_JAR)
            
            try:
                #check token
                dvrlink  = None
                custlink = json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/getcustomerkey?%s'%(qstr), form_data={'token':LAST_TOKEN}, headers=header_dict).content.encode("utf-8").rstrip())
                '''{u'username': u'', u'ip': u'', u'customerkey': u''}'''
                self.custkey = (custlink.get('customerkey','') or 0)                
                if custlink and 'username' in custlink and user.lower() == custlink['username'].lower():
                    log('login, using existing token, passkey')
                    self.token   = LAST_TOKEN
                    self.passkey = LAST_PASSKEY
                else:
                    #login 
                    loginlink = json.loads(self.net.http_POST(BASEURL + 'iphone/1/live/login?%s'%(qstr), form_data={'username':user,'password':password,'device':'gtv','redir':'0'}, headers=header_dict).content.encode("utf-8").rstrip())
                    '''{u'token': u'', u'result': u'success'}'''
                    if loginlink and 'token' in loginlink and loginlink['result'].lower() == 'success':
                        log('login, creating new token')
                        self.token = loginlink['token']
                        REAL_SETTINGS.setSetting('User_Token',self.token)          
                        
                        #passkey
                        dvrlink = json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/viewdvrlist?%s'%(qstr), form_data={'token':self.token}, headers=header_dict).content.encode("utf-8").rstrip())
                        '''{u'globalparams': {u'passkey': u''}, u'results': []}'''
                        if dvrlink and 'globalparams' in dvrlink:
                            log('login, creating new passkey')
                            self.passkey = dvrlink['globalparams']['passkey']
                            REAL_SETTINGS.setSetting('User_Paskey',self.passkey)
                    else: raise Exception
                            
                    #check user credentials
                    userlink = json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/getuserbytoken?%s'%(qstr), form_data={'token':self.token}, headers=header_dict).content.encode("utf-8").rstrip())
                    '''{u'status': u'success', u'data': {u'username': u'', u'need_account_activation': False, u'plan_id': 1, u'language': u'en', u'plan_free': 1, u'sub_id': u'7', u'lname': u'', u'currency': u'USD', u'points': 1, u'need_account_renew': False, u'fname': u'', u'plan_name': u'Free Plan'}}'''
                    log('login, checking user account')
                    if userlink and 'data' in userlink and userlink['status'].lower() == 'success':
                        REAL_SETTINGS.setSetting('User_Plan'      ,userlink['data']['plan_name'])
                        expires = 'Never' if userlink['data']['plan_name'] == 'Free Plan' else ''
                        REAL_SETTINGS.setSetting('User_Expires'   ,'%s'%expires)
                        self.isFree = userlink['data']['plan_name'] == 'Free Plan'
                        REAL_SETTINGS.setSetting('User_isFree', str(self.isFree))
                        dvrPlan = 2 if 'dvr' in (userlink['data']['plan_name']).lower() else None
                        REAL_SETTINGS.setSetting('User_DVRpoints' ,str(dvrPlan or userlink['data']['points'] or 0))
                        xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30006) + userlink['data']['fname'], ICON, 4000)
                        
                        if userlink['data']['need_account_renew'] == True: xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30016) + userlink['data']['fname'], ICON, 4000)
                        elif userlink['data']['need_account_activation'] == True: xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30022) + userlink['data']['fname'], ICON, 4000)
                        else: 
                            if REAL_SETTINGS.getSetting('User_DVRpoints') != REAL_SETTINGS.getSetting('Last_DVRpoints'):
                                REAL_SETTINGS.setSetting('Last_DVRpoints',REAL_SETTINGS.getSetting('User_DVRpoints'))
                                xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30021) + userlink['data']['fname'], ICON, 4000)
                                
                        #check subscription
                        try:
                            #error prone, isolate and debug.
                            sublink = json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/getaccountsubscription?%s'%(qstr), form_data={'username':user,'customerkey':self.custkey}, headers=header_dict).content.encode("utf-8").rstrip())
                            '''{u'username': u'', u'billingDatetime': u'', u'currency': u'USD', u'cgaccountstatusreason': u'', u'invoicehistory': u'', u'ocaccountstatus': u'Account active', u'ccLastFour': u'', u'lname': u'', u'x-cg-acnt-USD': False, u'fname': u'', u'sub_info': {u'cost': 0, u'plan': {u'sub_group': 4, u'plan_id': 1, u'name': u'Free Plan', u'language': u'en', u'date_expire': u'0000-00-00', u'sub_id': 7, u'price': 0, u'currency': u'USD', u'plan_code': u'7_FREETRIAL', 
                                u'details': u'This plan lets you receive all major US terrestrial stations (ABC, CBS, CW, FOX, NBC, PBS).  You can later upgrade to a paid plan with more channels and DVR.'}, u'packages': []}, u'pendinginvoices': u'', u'cgbillingstatus': u'', u'dvrpoints': 1, u'plans': {u'10': {u'price': 15, u'name': u'1 Week All Channel Plan $15 ($2.14/day)', 
                                u'details': u'1 Week pass for all channels (No DVR)'}, u'23': {u'price': 19, u'name': u'All Channel Promo Plan $19/mo first 3 months', 
                                u'details': u'Monthly subscription for all channels. This promotional price is for the first three months after which it will renew at $29. This plan automatically renews each month but you can cancel anytime and will not be billed again when your current 30 day period has expired. '}, u'31': {u'price': 29, u'name': u'All Channel Promo Plan w/DVR $29/mo first 3 months', 
                                u'details': u'Monthly subscription for all channels. This promotional price is for the first three months after which it will renew at $39. This plan automatically renews each month but you can cancel anytime and will not be billed again when your current 30 day period has expired.'}, u'7': {u'price': 0, u'name': u'Free Plan', 
                                u'details': u'This plan lets you receive all major US terrestrial stations (ABC, CBS, CW, FOX, NBC, PBS).  You can later upgrade to a paid plan with more channels and DVR.'}, u'9': {u'price': 0.00, u'name': u'3 Day All Channel Plan $6.99 ($2.33/day)', 
                                u'details': u'3 Day pass for all channels (No DVR)'}, u'8': {u'price': 2.99, u'name': u'1 Day All Channel Plan $2.99', 
                                u'details': u'24 hour pass for all channels (No DVR)'}}, u'cgredirectUrl': u'', u'cgaccountstatus': False, u'isfacebookuser': False, u'cgkey': u'', u'ocaccountstatuscode': 0, u'packages': [], u'subscription': u'Free Plan', u'language': u'en', u'sub_id': u'7', u'dateopened': u'December 01, 2000', u'canceledDatetime': u'', u'cgbillingmethod': u''}'''
                            if sublink: REAL_SETTINGS.setSetting('User_Expires'   ,'%s'%(sublink['sub_info']['date_expire']))
                        except: pass
                    else: raise Exception
                    self.net.save_cookies(COOKIE_JAR)
                    
                self.channels = self.cache.get(ADDON_NAME + '.channelguide')
                if not self.channels:
                    log('login, refreshing channels')
                    self.channels = sorted(json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/channelguide?%s'%(qstr), form_data={'token':self.token}, headers=header_dict).content.encode("utf-8").rstrip())['results'], key=lambda x: x['displayorder'])
                    '''{u'app_name': u'preview', u'stream': u'00000WXYZustvnow', u'af': u'US', u'dvraction': u'add', u'callsign': u'WHTM', u'event_inprogress': 1, 
                        u'srsid': 3560383, u'guideremainingtime': 3660, u'scheduleid': 9952642, u'favoriteaction': u'remove', u'event_time': u'00:00:00',u'title': u'Shark Tank', 
                        u'timemark': 1498867200, u'recordedon': u'June 30, 2017 20:00', u'prg_img': u'h3/NowShowing/9977826/p9977826_b1t_h3_aa.jpg', u'title_10': u'',
                        u'xcdrappname': u'livehd', u'event_date': u'2017-07-01', u'has_img': 1, u'stream_code': u'ABC', u'updated': u'2017-06-29 11:49:08', 
                        u'description': u'Durable bags made out of the material that protects on the front lines of firefighting; a vibrating mat that helps calm babies;
                        an ointment made from essential oils; a natural snack made with acai.', u'actualremainingtime': 3281, u'content_allowed': False, 
                        u'dvrtimeraction': u'add', u'mediatype': u'EP', u'auth': None, u'stream_origin': u'dne.ustvnow.com', u'dvrtimertype': 0, u'scode': u'whtm', 
                        u'aksid': 1, u'guideheight': 120, u'orig_air_date': u'2017-02-10', u'prgsvcid': 11534, u'runtime': 3660, u'img': u'images/WHTM.png', 
                        u'connectorid': u'SH011581290000', u'ut_start': 1498867200, u'streamname': u'00000WXYZustvnow', u'episode_title': u'', u'synopsis': 
                        u'A vibrating mat that helps calm babies.', u't': 1, u'edgetypes': 7, u'imgmark': u'live', u'content_id': u'EP011581290171', u'order': 1, 
                        u'displayorder': 1}'''
                    self.cache.set(ADDON_NAME + '.channelguide', self.channels, expiration=datetime.timedelta(minutes=5))
                    
                self.upcoming = self.cache.get(ADDON_NAME + '.upcoming')
                if not self.upcoming:
                    log('login, refreshing upcoming')
                    self.upcoming = json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/upcoming?%s'%(qstr), form_data={'token':self.token}, headers=header_dict).content.encode("utf-8").rstrip())
                    '''{u'prgschid': 19479379, u'dvraction': u'add', u'callsign': u'AMC', u'newtimecat': True, u'srsid': 14930, u'timecat': u'Today', u'scheduleid': 9946282, 
                        u'img': u'images/AMC.png', u'title': u'The Fugitive', u'prg_img': u'v5/NowShowing/14930/p14930_p_v5_aa.jpg', u'has_img': 1, u't': 0, u'sname': u'AMC', 
                        u'description': u'U.S. marshal (Tommy Lee Jones) hunts doctor (Harrison Ford) for murder of his wife (Sela Ward).', u'dvrtimeraction': u'add', 
                        u'auth': None, u'orig_air_date': None, u'dvrtimertype': 0, u'scode': u'amchd', u'prgsvcid': 10021, u'runtime': 10800, u'connectorid': u'MV000371790000', 
                        u'episode_title': u'', u'synopsis': u'An innocent man must evade the law as he pursues a killer.', u'event_inprogress': 1, u'ut_start': 1499009400, 
                        u'content_allowed': False, u'imgmark': u'live', u'content_id': u'MV000371790000', u'displayorder': 100}''' 
                    self.cache.set(ADDON_NAME + '.upcoming', self.upcoming, expiration=datetime.timedelta(hours=6))
                    
                self.highlights = self.cache.get(ADDON_NAME + '.highlights')
                if not self.highlights:
                    log('login, refreshing highlights')
                    self.highlights = json.loads(self.net.http_POST(BASEURL + 'api/1/live/highlights?%s'%(qstr), form_data={'token':self.token}, headers=header_dict).content.encode("utf-8").rstrip())
                    '''{u'prgschid': 114059791, u'dvraction': u'add', u'bb_content': u'How would you like having Jim Morrison as a college roommate? ', u'callsign': u'WPSU', u'newtimecat': True,
                        u'srsid': 185479, u'timecat': u'Tomorrow', u'scheduleid': 49826153, u'img': u'images/WPSU.png', u'title': u'Antiques Roadshow', u'prg_img': u'h3/NowShowing/185479/p185479_b_h3_ag.jpg', 
                        u'has_img': 1, u't': 1, u'sname': u'PBS', u'description': u'A French Art Deco diamond and platinum ring; a copy of &quot;The History of Magic&quot; signed by Jim Morrison; four Rembrandt', 
                        u'dvrtimeraction': u'add', u'auth': None, u'orig_air_date': u'2014-02-17', u'dvrtimertype': 0, u'scode': u'wpsu', u'prgsvcid': 11786, u'runtime': 3600, u'connectorid': u'SH002036520000', 
                        u'episode_title': u'Baton Rouge', u'synopsis': u'Diamond and platinum ring.', u'event_inprogress': 2, u'ut_start': 1508216400, u'content_allowed': True, u'imgmark': u'', u'content_id': 
                        u'EP002036520417', u'displayorder': 6}''' 
                    self.cache.set(ADDON_NAME + '.highlights', self.highlights, expiration=datetime.timedelta(hours=6))
                    
                self.recorded = self.cache.get(ADDON_NAME + '.recorded')
                if not self.recorded:
                    log('login, refreshing recorded')
                    '''{u'fn1': u'20170702', u'episode_season': 0, u'filename_smil': u'20170702_213000_220000_utc_SH000000010000_11534_11534_ABC.smil', u'app_name': u'dvrrokuplay', 
                        u'stream': u'2F1ECWHTMUSTVNOW', u'imgmark': u'rem', u'dvrtimeraction': u'add', u'mediatype': u'SH', u'orig_air_date': None, u'content_id': u'SH000000010000', 
                        u'callsign': u'WHTM', u'ut_expires': 1500327000, u'filename_med': u'20170702_213000_220000_utc_SH000000010000_11534_11534_ABC_650.mp4', 
                        u'filename_high': u'20170702_213000_220000_utc_SH000000010000_11534_11534_ABC_950.mp4', u'dvrlocation': u'dvr6', u'episode_number': 0, u'srsid': 459763, 
                        u'runtime': 1800, u'description': u'Paid programming.', u'scheduleid': 9952747, u'has_img': 1, u'fn3': u'220000', u'fn2': u'213000', 
                        u'event_time': u'21:30:00', u'title': u'Paid Programming', u'recordedonmmddyyyy': u'07/02/2017', u'connectorid': u'SH000000010000', 
                        u'recordedon': u'July 2, 2017', u'prg_img': u'h3/NowShowing/459763/p459763_b_h3_ae.jpg', u'filename_low': u'20170702_213000_220000_utc_SH000000010000_11534_11534_ABC_350.mp4', 
                        u'episode_title': u'', u'synopsis': u'Paid programming.', u'dvrtimertype': 0, u'content_allowed': True, u'xcdrappname': u'livehd', u'event_date': u'2017-07-02', 
                        u'event_inprogress': 2, u'prgsvcid': 11534, u'ut_start': 1499031000, u'stream_code': u'ABC'}'''
                    if dvrlink: recorded = dvrlink['results']
                    else: self.recorded = (json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/viewdvrlist?%s'%(qstr), form_data={'token':self.token}, headers=header_dict).content.encode("utf-8").rstrip()))['results']
                    self.cache.set(ADDON_NAME + '.recorded', self.recorded, expiration=datetime.timedelta(minutes=1))
                self.names = self.getChannelNames()
                return True
            except Exception as e:
                log('login, Unable to login ' + str(e), xbmc.LOGERROR)
                REAL_SETTINGS.setSetting('User_Token','')
                REAL_SETTINGS.setSetting('User_Paskey','')
                REAL_SETTINGS.setSetting('User_Activated',str(False))
                xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30007), ICON, 4000)
                return False
        else:
            #firstrun wizard
            if yesnoDialog(LANGUAGE(30008),no=LANGUAGE(30009), yes=LANGUAGE(30010)):
                user     = inputDialog(LANGUAGE(30001))
                password = inputDialog(LANGUAGE(30002),opt=xbmcgui.ALPHANUM_HIDE_INPUT)
                REAL_SETTINGS.setSetting('User_Email'   ,user)
                REAL_SETTINGS.setSetting('User_Password',password)
                return self.login(user, password)
            else:
                okDialog(LANGUAGE(30003))
                return False
        
        
    def qrLogin(self):
        BASEVOD+'/qr/linkcode/%s'%('kodi%s'%ADDON_ID)
        
        
    def grabChannelName(self, sname):
        return sname.strip()
        
        
    def getChannelNames(self):
        collect = []
        if self.channels is None: xbmc.executebuiltin("Container.Refresh")
        for channel in self.channels:
            try:
                name = self.grabChannelName(channel['stream_code'])
                if self.isFree == True and name not in FREE_CHANS: continue
                collect.append(name.strip())
            except: pass
        counter = collections.Counter(collect)
        names   = sorted(list(set(sorted(counter.elements()))))
        log('getChannelNames, names = ' + str(names))
        return names
        
        
    # def browseReminders(self):
    # {'label':'','thumb':'','startime':000000,'info':[{}]}
    # context to delete
        

    def browseLive(self):
        log('browseLive')
        channelCheck = []
        d = datetime.datetime.utcnow()
        now = datetime.datetime.fromtimestamp(calendar.timegm(d.utctimetuple()))  
        if self.channels is None: xbmc.executebuiltin("Container.Refresh")
        for channel in self.channels:
            try:
                name = self.grabChannelName(channel['stream_code'])
                if self.isFree == True and name not in FREE_CHANS: continue
                if name in channelCheck: continue
                else: channelCheck.append(name)
                startime = datetime.datetime.fromtimestamp(channel['ut_start'])
                endtime  = startime + datetime.timedelta(seconds=channel['runtime'])
                if endtime > now and startime <= now:
                    label, url, liz = self.buildChannelListItem(name, channel, opt='Live')
                    self.addLink(label, url, 9, liz, len(self.channels))
            except Exception as e: log('browseLive, failed ' + str(e), xbmc.LOGERROR)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
                
                
    def browseRecordings(self, recorded=False):
        log('browseRecordings')
        found = 0
        d = datetime.datetime.utcnow()
        now = datetime.datetime.fromtimestamp(calendar.timegm(d.utctimetuple()))
        if self.recorded is None: xbmc.executebuiltin("Container.Refresh")
        for channel in self.recorded:
            try:
                startime  = datetime.datetime.fromtimestamp(channel['ut_start'])
                endtime   = startime + datetime.timedelta(seconds=channel['runtime'])
                if recorded == False and channel['event_inprogress'] == 0: continue
                elif recorded == True and channel['event_inprogress'] != 0: continue
                label, url, liz = self.buildRecordedListItem(self.grabChannelName(channel['stream_code']))
                mode = 10 if recorded == True else 21
                if mode == 21: liz.setProperty("IsPlayable","false")
                found += 1
                self.addLink(label, url, mode, liz, len(self.recorded))
            except Exception as e: log('browseRecordings, failed ' + str(e), xbmc.LOGERROR)
        if found == 0: self.addDir(LANGUAGE(30031), '', 1)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
                

    def browseGuide(self, name=None, upcoming=False):
        log('browseGuide')
        d = datetime.datetime.utcnow()
        now = datetime.datetime.fromtimestamp(calendar.timegm(d.utctimetuple()))
        if self.channels is None: xbmc.executebuiltin("Container.Refresh")
        if name is None and upcoming == False:
            for channel in sorted(self.names):
                try: icon = [IMG_CHLOGO_W%(chan['callsign']) for chan in self.channels if channel == chan['stream_code']][0]
                except: icon = (os.path.join(IMG_PATH,'logos','%s.png'%channel) or ICON)
                infoArt  = {"thumb":icon,"poster":icon,"icon":icon,"fanart":FANART}
                self.addDir(channel, channel, 4, infoArt=infoArt)
            xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_LABEL)
        else:
            for channel in self.channels:
                try:
                    if self.isFree == True and name not in FREE_CHANS: continue
                    if name == self.grabChannelName(channel['stream_code']):
                        startime  = datetime.datetime.fromtimestamp(channel['ut_start'])
                        endtime   = startime + datetime.timedelta(seconds=channel['runtime'])
                        if endtime > now and (startime <= now):
                            label, url, liz = self.buildChannelListItem(name, channel)
                            self.addLink(label, url, 9, liz, len(self.channels))
                        elif endtime > now and (startime <= now or startime > now):
                            label, url, liz = self.buildChannelListItem(name, channel)
                            mode = 9 if PTVL_RUN == True else 21
                            if mode == 21: liz.setProperty("IsPlayable","false")
                            self.addLink(label, url, mode, liz, len(self.channels))
                except Exception as e: log('browseGuide, failed ' + str(e), xbmc.LOGERROR)
            xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
                
           
    def browseFeatured(self, hlt=False):
        log('browseFeatured')
        d = datetime.datetime.utcnow()
        now = datetime.datetime.fromtimestamp(calendar.timegm(d.utctimetuple()))
        CONTENT_TYPE = 'movies' if not hlt else 'episodes'
        optLST = self.highlights.get('programs') if hlt else self.upcoming 
        if optLST is None: xbmc.executebuiltin("Container.Refresh")
        for channel in optLST:
            try:
                name      = self.grabChannelName(channel['sname'])
                startime  = datetime.datetime.fromtimestamp(channel['ut_start'])
                endtime   = startime + datetime.timedelta(seconds=channel['runtime'])
                if endtime > now and (startime <= now or startime > now):
                    label, url, liz = self.buildChannelListItem(name, channel, opt='Featured')
                    liz.setProperty("IsPlayable","false")
                    self.addLink(label, url, 21, liz, len(optLST))
            except Exception as e: log('browseFeatured, failed ' + str(e), xbmc.LOGERROR)
        xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)

       
    def browseVOD(self, url=None, limit=24):
        log('browseVOD')
        '''
        {u'paging': {u'current': u'/api/1/live/vod/?role=user&limit=24&status%5B0%5D=5', u'next_query': u'role=user&limit=24&status%5B0%5D=5&page=4954', u'next': u'/api/1/live/vod/?role=user&limit=24&status%5B0%5D=5&page=4954'},
         u'data': [{u'rented': None, u'ratings': [{u'description': u'', u'id': 12585970, u'name': u'TV-Y'}], u'scheduleid': u'V4954', u'description': u"HORSELAND: FIRST LOVE - Tomboyish Alma has a crush on a boy. Chloe .  (CC)", 
         u'language': u'en', u'title': u'Horseland: First Love', u'content_allowed': False, u'price': u'0.99', u'created': 1493301489, u'genres': [], u'licensing_start': 1494475260, u'slug': u'V4954', u'director': None, 
         u'closed_caption': True, u'rent_due': 2, u'actors': [{u'lname': u'Donlan', u'id': 30781624, u'fname': u'Dana'}, {u'lname': u'Hernandez', u'id': 30781625, u'fname': u'Emily'}, {u'lname': u'Heyward', u'id': 30781626, u'fname': 
         u'Bianca'}], u'year': 2006, u'images': {u'posters': {u'small': u'/V4954/USTVNOW/mv/small', u'large': u'/V4954/USTVNOW/mv/large', u'medium': u'/V4954/USTVNOW/mv/medium'}}, u'runtime': u'00:21:15', u'id': 4954, 
         u'licensing_end': 1499745540}]}
        '''
        if url is None: url = BASEVOD + '/vod/all-items'
        items = self.net._json(url, form_data={'limit':limit,'token':self.token})
        if items and len(items) > 0:
            label = '[B]%s[/B]'%LANGUAGE(30029)
            liz = xbmcgui.ListItem(label)
            liz.setArt({"thumb":ICON,"poster":ICON,"fanart":FANART})
            self.addLink(label, '', '', liz, len(items))
            next = (items.get('paging','').get('next','') or '')
            for item in items['data']:
                label, url, liz = self.buildVODListItem(item)
                liz.setProperty("IsPlayable","true")
                liz.addContextMenuItems([('Purchase','')])
                self.addLink(label, url, '', liz, len(items))
            # self.addDir('>> Next', BASEVOD + next, 13)
            xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
                

    def search(self):
        log('search')
        kb = xbmc.Keyboard('', LANGUAGE(30027)%ADDON_NAME)
        xbmc.sleep(1000)
        kb.doModal()
        if kb.isConfirmed():
            try:
                query = kb.getText()
                items = json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/search', form_data={'token':self.token,'q_title':query}, headers=self.buildHeader()).content.encode("utf-8").rstrip())['results']['programs']
                for channel in items:
                    try:
                        name = self.grabChannelName(channel['progs']['sname'])
                        label, url, liz = self.buildChannelListItem(name, channel['progs'], opt='Search')
                        liz.setProperty("IsPlayable","false")
                        self.addLink(label, url, 21, liz, len(items))
                    except Exception as e: log('search, error ' + str(e), xbmc.LOGERROR)
                if len(items) == 0:
                    label = LANGUAGE(30028)%query
                    liz = xbmcgui.ListItem(label)
                    liz.setArt({"thumb":ICON,"poster":ICON,"fanart":FANART})
                    self.addLink(label, '', 0, liz, 1)
                xbmcplugin.addSortMethod(int(self.sysARG[1]) , xbmcplugin.SORT_METHOD_UNSORTED)
            except Exception as e: log('search, failed ' + str(e), xbmc.LOGERROR)
        else: self.mainMenu()
        
           
    def buildVODListItem(self, item):
        url       = ''
        title     = unescape(item['title'])
        price     = item['price']
        year      = item['year']
        h, m, s   = item['runtime'].split(':')
        runtime   = int(h) * 3600 + int(m) * 60 + int(s)
        label     = '%s ($%s)'%(title,price)
        label2    = item['price']
        plot      = unescape(item['description'])
        liz       = xbmcgui.ListItem(label)
        thumb     = PTR_BASE + item['images']['posters']['large']
        infoList  = {"mediatype":'movie',"label":label,"label2":label2,"title":label,"duration":runtime,"plot":plot}
        liz.setInfo(type="Video", infoLabels=infoList)
        liz.setArt({"thumb":thumb,"poster":thumb,"fanart":FANART})
        liz.setProperty("IsPlayable","true")
        liz.setProperty("IsInternetStream","true")
        log('buildVODListItem, label = ' + label + ', url = ' + url)
        return label, url, liz

        
    def buildChannelListItem(self, name, channel=None, opt=''):
        '''{u'app_name': u'preview', u'stream': u'00000WXYZteleup', u'af': u'US', u'dvraction': u'add', u'recordedon': u'May 4, 2018 17:27', u'callsign': u'FOR', 
            u'event_inprogress': 1, u'srsid': 1843, u'guideremainingtime': 5760, u'scheduleid': 173991644, u'favoriteaction': u'add', u'event_time': u'21:27:00', u'title': u'Kansas City Confidential', 
            u'timemark': 1525469400, u'seo_title': u'kansas-city-confidential', u'prg_img': u'v5/NowShowing/1843/p1843_p_v5_aa.jpg', u'title_10': u'Kansas', u'xcdrappname': u'livehd', 
            u'event_date': u'2018-05-04', u'has_img': 1, u'stream_code': u'Films on Reel', u'updated': u'2018-05-04 13:53:34', u'episode_season': 0, u'description': u"Ex-convict (John Payne) ", 
            u'actualremainingtime': 4713, u'content_allowed': False, u'details_uri': u'/info/films-on-reel/kansas-city-confidential/2018-05-04/21-27-00-utc', u'dvrtimeraction': u'add', 
            u'mediatype': u'MV', u'auth': 0, u'stream_origin': u'dne.ustvnow.com', u'seo_name': u'films-on-reel', u'scode': u'flmsrl', u'aksid': 1, u'guideheight': 190, u'episode_number': 0, 
            u'orig_air_date': None, u'prgsvcid': 72510, u'runtime': 5940, u'img': u'images/FOR.png', u'connectorid': u'MV000029920000', u'ut_start': 1525469220, u'streamname': u'00000WXYZteleup', 
            u'episode_title': u'', u'synopsis': u'A robbery suspect tries to find the real mastermind.', u'dvrtimertype': 0, u't': 0, u'edgetypes': 15, u'imgmark': u'live', 
            u'content_id': u'MV000029920000', u'order': 1, u'displayorder': 127}'''                                           
        if channel is None:
            for idx, channel in enumerate(self.channels):
                if name == self.grabChannelName(channel['stream_code']): break
        startime  = datetime.datetime.fromtimestamp(channel['ut_start'])
        endtime   = startime + datetime.timedelta(seconds=channel['runtime'])
        title     = unescape(channel['title'])
        mediatype = (channel.get('mediatype','') or (channel.get('connectorid',''))[:2] or (channel.get('content_id',''))[:2] or 'SP')
        mtype     = MEDIA_TYPES[mediatype.upper()]
        label     = name if PTVL_RUN == True else '%s: %s - %s'%(startime.strftime('%I:%M %p').lstrip('0'),name,title)
        label     = '%s - %s'%(name,title) if opt == 'Live' else label
        label2    = '%s - %s'%(startime.strftime('%I:%M %p').lstrip('0'),endtime.strftime('%I:%M %p').lstrip('0'))
        url       = name
        liz       = xbmcgui.ListItem(label)
        logo      = IMG_CHLOGO_W%(channel['callsign'])
        thumb     = IMG_SOURCE%(str(channel['srsid']),channel['callsign'],mediatype)
        now       = int(time.time())
        rand      = now - (now % 120)
        thumb     = thumb+'/generic?rand=%i'%rand #thumb+'/snapshot?rand=%i'%rand if opt == 'Live' else 
        poster    = (os.path.join(IMG_PATH,'%s.png'%name) or ICON)
        tag       = ''#urllib.quote(json.dumps({"channelname":name,"channelnumber":self.names.index(name)+1,"channellogo":logo,"label":title,"label2":self.isHD(),"starttime":channel['ut_start']}))
        infoList  = {"mediatype":'episode',"label":label,"label2":label2,"title":label,"tagline":tag,
                     "studio":name,"duration":channel['runtime'],"plotoutline":unescape(channel.get('synopsis','')),
                     "plot":unescape(channel['description']),"aired":startime.strftime('%Y-%m-%d')}
        liz.setInfo(type="Video", infoLabels=infoList)
        liz.setArt({"thumb":thumb,"poster":thumb,"fanart":FANART,"clearlogo":logo})
        liz.setProperty("IsPlayable","true")
        liz.setProperty("IsInternetStream","true")
        if channel['dvrtimeraction'] == 'add':
            opt = '@'.join([str(channel['prgsvcid']),(channel.get('event_time','') or str(channel.get('ut_start','')))])#lazy solution rather then create additional url parameters for this single function.
            contextMenu = [('Set single recording'   ,'XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?url="+urllib.quote(str(channel['scheduleid']))+"&mode="+str(6)+"&name="+urllib.quote(opt))),
                           ('Set recurring recording','XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?url="+urllib.quote(str(channel['connectorid']))+"&mode="+str(7)+"&name="+urllib.quote(opt)))]
        else:
            contextMenu = [('Remove recording','XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?url="+urllib.quote(str(channel['scheduleid']))+"&mode="+str(8)+"&name="+urllib.quote(name)))]
        liz.addContextMenuItems(contextMenu)
        log('buildChannelListItem, label = ' + label + ', url = ' + url)
        return label, url, liz
    
    
    def buildRecordedListItem(self, name):
        for channel in self.recorded:
            if name == self.grabChannelName(channel['stream_code']) or name == str(channel['scheduleid']):
                startime  = datetime.datetime.fromtimestamp(channel['ut_start'])
                endtime   = startime + datetime.timedelta(seconds=channel['runtime'])
                title     = unescape(channel['title'])
                label     = '%s - %s: %s - %s'%(startime.strftime('%Y-%m-%d'),startime.strftime('%I:%M %p').lstrip('0'),name,title)
                label2    = '%s-%s'%(startime.strftime('%I:%M %p').lstrip('0'),endtime.strftime('%I:%M %p').lstrip('0'))
                url       = str(channel['scheduleid'])
                liz       = xbmcgui.ListItem(label)
                mediatype = (channel.get('mediatype','') or (channel.get('connectorid',''))[:2] or (channel.get('content_id',''))[:2] or 'SP')
                mtype     = MEDIA_TYPES[mediatype.upper()]
                infoList  = {"mediatype":mtype,"label":label,"label2":label2,"title":label,"studio":self.grabChannelName(channel['stream_code']),
                             "duration":channel['runtime'],"plotoutline":unescape(channel['synopsis']),"plot":unescape(channel['description']),
                             "aired":startime.strftime('%Y-%m-%d')}
                thumb  = IMG_SOURCE%(str(channel['srsid']),channel['callsign'],mediatype)
                liz.setInfo(type="Video", infoLabels=infoList)
                liz.setArt({"thumb":thumb,"poster":thumb,"fanart":FANART})
                liz.setProperty("IsPlayable","true")
                liz.setProperty("IsInternetStream","true")
                contextMenu = []
                # if channel['dvrtimeraction'] == 'add':
                    # opt = '@'.join([str(channel['prgsvcid']),channel['event_time']])#lazy solution rather then create additional url parameters for this single function.
                    # contextMenu = [('Set single recording'   ,'XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?url="+urllib.quote(str(channel['scheduleid']))+"&mode="+str(6)+"&name="+urllib.quote(opt))),
                                   # ('Set recurring recording','XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?url="+urllib.quote(str(channel['connectorid']))+"&mode="+str(7)+"&name="+urllib.quote(opt)))]
                contextMenu.extend([('Remove recording','XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?url="+urllib.quote(str(channel['scheduleid']))+"&mode="+str(8)+"&name="+urllib.quote(name)))])
                liz.addContextMenuItems(contextMenu)
                log('buildRecordedListItem, label = ' + label + ', url = ' + url)
                return label, url, liz
    
    
    def resolveURL(self, url, dvr=False):
        log('resolveURL, url = ' + url + ', dvr = ' + str(dvr))
        if dvr:
            for channel in self.recorded:
                if url == str(channel['scheduleid']):
                    try:
                        urllink = json.loads(self.net.http_POST(BASEURL + 'stream/1/dvr/play', form_data={'token':self.token,'key':self.passkey,'scheduleid':channel['scheduleid']}, headers=self.buildHeader()).content.encode("utf-8").rstrip())
                        '''{u'pr': u'll', u'domain': u'ilvc02.ll.ustvnow.com',u'stream': u'http://ilvc02.ll.ustvnow.com/ilv10/pr/xxl/smil:0B64AWHTMUSTVNOW/playlist.m3u8?', 
                            u'streamname': u'0B64AWHTMUSTVNOW', u'tr': u'', u'up': 1, u'pd': 0, u'pl': u'vjs'}'''
                        stream = urllink['stream']
                        # if URL_TYPE == 'm3u8': stream = urllink['stream']
                        # else: stream = (urllink['stream'].replace('smil:','mp4:').replace('USTVNOW','USTVNOW%d'%URL_QUALITY))
                        log('resolveURL, url = ' + stream)
                        return stream
                    except Exception as e:
                        if channel and channel['scheduleid']: self.replaceToken(url, dvr)
        else:
            for channel in self.channels:
                if url == self.grabChannelName(channel['stream_code']):
                    try:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
                        urllink = json.loads(self.net.http_POST(BASEURL + 'stream/1/live/view', form_data={'token':self.token,'key':self.passkey,'scode':channel['scode']}, headers=self.buildHeader()).content.encode("utf-8").rstrip())
                        '''{u'pr': u'll', u'domain': u'ilvc02.ll.ustvnow.com',u'stream': u'http://ilvc02.ll.ustvnow.com/ilv10/pr/xxl/smil:0B64AWHTMUSTVNOW/playlist.m3u8?', 
                            u'streamname': u'0B64AWHTMUSTVNOW', u'tr': u'', u'up': 1, u'pd': 0, u'pl': u'vjs'}'''
                        if URL_TYPE == 'm3u8': stream = urllink['stream']
                        else: stream = (urllink['stream'].replace('smil:','mp4:').replace('USTVNOW','USTVNOW%d'%URL_QUALITY))
                        log('resolveURL, stream = ' + stream)
                        return stream
                    except Exception as e:
                        if channel and channel['scode']: self.replaceToken(url, dvr)
                    
                    
    def replaceToken(self, url, dvr):
        #generate alternative token using website endpoint rather then googletv.
        try:
            #get CSRF Token
            response = urllib2.urlopen(BASEVOD + "/account/signin").read()
            CSRF = re.findall(r'var csrf_value = "(.*?)"', response, re.DOTALL)[0]
            #get WEB Token
            response = (self.net.http_POST(BASEVOD + '/account/login', form_data={'csrf_ustvnow': CSRF, 'signin_email': USER_EMAIL, 'signin_password':PASSWORD, 'signin_remember':'1'}).content.encode("utf-8").rstrip())
            altToken = re.findall(r'var token(.*?)= "(.*?)";', response, re.DOTALL)[0][1]
            if altToken and altToken != 'null':
                self.token = altToken
                log('replaceToken, replacing existing token')
                REAL_SETTINGS.setSetting('User_Token',altToken)
                self.resolveURL(url, dvr)
        except Exception as e:
            log('replaceToken, Unable to login ' + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30005), ICON, 4000)
            raise SystemExit

            
    def setRecording(self, name, url, remove=False, recurring=False):
        log('setRecording, name = ' + name + ', url = ' + url + ', remove = ' + str(remove))
        if remove == True:
            setlink = (self.net.http_POST(BASEURL + 'gtv/1/dvr/updatedvr', form_data={'scheduleid':url,'token':self.token,'action':'remove'}, headers=self.buildHeader()).content.encode("utf-8").rstrip())
        else:
            if int(REAL_SETTINGS.getSetting('User_DVRpoints')) <= 1: return xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30019), ICON, 4000)
            opt = name.split('@')#lazy solution rather then create additional url parameters for this single function.
            if recurring == True: setlink = (self.net.http_POST(BASEURL + 'gtv/1/dvr/updatedvrtimer', form_data={'connectorid':url,'prgsvcid':opt[0],'eventtime':opt[1],'token':self.token,'action':'add'}, headers=self.buildHeader()).content.encode("utf-8").rstrip())
            else: setlink = (self.net.http_POST(BASEURL + 'gtv/1/dvr/updatedvr', form_data={'scheduleid':url,'token':self.token,'action':'add'}, headers=self.buildHeader()).content.encode("utf-8").rstrip())
        '''<result><status>failure</status><action>add</action></result>'''
        action = re.findall(r'<action>(.*?)</action>', setlink, re.DOTALL)[0]
        status = re.findall(r'<status>(.*?)</status>', setlink, re.DOTALL)[0]
        log('setRecording, action = ' + action + ', status = ' + status)
        if status == 'failure':
            log('setRecording, setlink = ' + str(setlink), xbmc.LOGERROR)
            return xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30023)%action.title(), ICON, 4000)
        self.cache.set(ADDON_NAME + '.recorded', None, expiration=datetime.timedelta(seconds=1))
        xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30024)%action.title(), ICON, 4000)
        # xbmc.sleep(1001)
        # xbmc.executebuiltin("Container.Update(plugin://%s/?mode=1)"%ADDON_ID)
        # xbmc.executebuiltin("Container.Update(plugin://%s/?mode=2)"%ADDON_ID)

    
    def playVideo(self, url, dvr=False):
        log('playVideo, url = ' + url + ', dvr = ' + str(dvr))
        if dvr: label, path, liz = self.buildRecordedListItem(url)
        else: label, path, liz = self.buildChannelListItem(url, opt='Live')
        liz.setPath(self.resolveURL(url,dvr))
        # if url.endswith('m3u8'):
            # liz.setProperty('inputstreamaddon','inputstream.adaptive')
            # liz.setProperty('inputstream.adaptive.manifest_type','hls') 
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
  
  
    def isHD(self):
        if URL_TYPE == 'm3u8': return 'HD'
        elif URL_QUALITY > 2:  return 'HD'
        return ''
        
        
    def hasCC(self):
        if URL_TYPE == 'm3u8': return True
        return False
        
        
    def uEPG(self):
        log('uEPG')
        #support for upcoming uEPG universal epg framework module, module will be available from the Kodi repository.
        #https://github.com/Lunatixz/KODI_Addons/tree/master/script.module.uepg
        collect = []
        if self.channels is None: xbmc.executebuiltin("Container.Refresh")
        for channel in self.channels:
            try:
                name = self.grabChannelName(channel['stream_code'])
                if self.isFree == True and name not in FREE_CHANS: continue
                collect.append(name.strip())
            except: pass
                
        channelNum  = 0
        counter = collections.Counter(collect)
        for key, value in sorted(counter.iteritems()):
            newChannel  = {}
            guidedata   = []
            channelName = key
            channelNum  = channelNum + 1
            isHD        = self.isHD()
            hasCC       = self.hasCC()
            newChannel['channelname']   = channelName
            newChannel['channelnumber'] = channelNum
            for channel in self.channels:
                try:
                    name = self.grabChannelName(channel['stream_code'])
                    if self.isFree == True and name not in FREE_CHANS: continue
                    if name == channelName:
                        tmpdata = {}
                        mediatype = (channel.get('mediatype','') or (channel.get('connectorid',''))[:2] or (channel.get('content_id',''))[:2] or 'SP')
                        mtype     = MEDIA_TYPES[mediatype.upper()]
                        thumb     = IMG_SOURCE%(str(channel['srsid']),channel['callsign'],mediatype)
                        poster    = thumb if mediatype.lower() == 'mv' else ''
                        logo      = IMG_CHLOGO_W%(channel['callsign'])
                        newChannel['channellogo'] = logo
                        
                        for key, value in channel.iteritems():
                            try: tmpdata[uEPG_PARAMS[key]] = unescape(value)
                            except:
                                if key in FILE_PARAMS + PVR_PARAMS: tmpdata[key] = unescape(value)
                                    
                        # contextMenu = [('Schedules' ,'XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?mode="+str(1))),
                                       # ('Recordings','XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?mode="+str(2))),
                                       # ('OnDemand'  ,'XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?mode="+str(13)))]
                                       
                        contextMenu = []
                        if channel['dvrtimeraction'] == 'add':
                            opt = '@'.join([str(channel['prgsvcid']),(channel.get('event_time','') or str(channel.get('ut_start','')))])#lazy solution rather then create additional url parameters for this single function.
                            contextMenu.append(('Set single recording'   ,'XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?url="+urllib.quote(str(channel['scheduleid']))+"&mode="+str(6)+"&name="+urllib.quote(opt))))
                            contextMenu.append(('Set recurring recording','XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?url="+urllib.quote(str(channel['connectorid']))+"&mode="+str(7)+"&name="+urllib.quote(opt))))
                        else: contextMenu.append(('Remove recording','XBMC.RunPlugin(%s)'%(self.sysARG[0]+"?url="+urllib.quote(str(channel['scheduleid']))+"&mode="+str(8)+"&name="+urllib.quote(name))))
                        
                        isNew  = False #todo parse startime and data
                        label2 = isHD
                        tags   = {'isHD':isHD,'hasCC':hasCC,'isNew':isNew}
                        tmpdata['label']   = unescape(channel['title'])
                        tmpdata['label2']  = label2
                        # tmpdata['tagline'] = json.dumps(tags)
                        tmpdata['art'] = {"thumb":thumb,"poster":poster,"clearlogo":logo}
                        tmpdata['mediatype'] = mtype
                        tmpdata['url'] = self.sysARG[0]+'?mode=9&url=%s'%name
                        tmpdata['contextmenu'] = json.dumps(contextMenu)
                        guidedata.append(tmpdata)
                except: pass
                newChannel['guidedata'] = guidedata
            yield newChannel

           
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

        if mode==None:  self.mainMenu()
        elif mode == 0: self.browseLive()
        elif mode == 1: self.browseRecordings()
        elif mode == 2: self.browseRecordings(recorded=True)
        elif mode == 3: self.browseGuide()
        elif mode == 4: self.browseGuide(name)
        elif mode == 5: self.browseFeatured()
        elif mode == 6: self.setRecording(name,url)
        elif mode == 7: self.setRecording(name,url,recurring=True)
        elif mode == 8: self.setRecording(name,url,remove=True)
        elif mode == 9: self.playVideo(url)
        elif mode == 10:self.playVideo(url,dvr=True)
        elif mode == 11:self.search()
        elif mode == 12: self.browseFeatured(True)
        elif mode == 13:self.browseVOD(url)
        elif mode == 19:xbmc.executebuiltin("RunScript(script.module.uepg,listitem=%s&skin_path=%s&refresh_path=%s&refresh_interval=%s&row_count=%s)"%(urllib.quote(self.sysARG[0]+"?mode=3"),urllib.quote(json.dumps(ADDON_PATH)),urllib.quote(json.dumps(self.sysARG[0]+"?mode=19")),urllib.quote(json.dumps("7200")),urllib.quote(json.dumps("7"))))
        elif mode == 20:xbmc.executebuiltin("RunScript(script.module.uepg,json=%s&skin_path=%s&refresh_path=%s&refresh_interval=%s&row_count=%s)"%(urllib.quote(json.dumps(list(self.uEPG()))),urllib.quote(json.dumps(ADDON_PATH)),urllib.quote(json.dumps(self.sysARG[0]+"?mode=20")),urllib.quote(json.dumps("7200")),urllib.quote(json.dumps("7"))))
        elif mode == 21:xbmc.executebuiltin("action(ContextMenu)")
        elif mode == 22:xbmc.executebuiltin('Addon.OpenSettings(script.module.uepg)')

        xbmcplugin.setContent(int(self.sysARG[1])    , CONTENT_TYPE)
        xbmcplugin.endOfDirectory(int(self.sysARG[1]), cacheToDisc=True)