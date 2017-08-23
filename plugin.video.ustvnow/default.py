#   Copyright (C) 2017 Lunatixz
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
import os, sys, datetime, re, traceback, HTMLParser, calendar
import urllib, urllib2, socket, json, collections, net, random
import xbmc, xbmcvfs, xbmcgui, xbmcplugin, xbmcaddon

from simplecache import SimpleCache
# Plugin Info
ADDON_ID      = 'plugin.video.ustvnow'
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
USER_EMAIL   = REAL_SETTINGS.getSetting('User_Email')
PASSWORD     = REAL_SETTINGS.getSetting('User_Password')
LAST_TOKEN   = REAL_SETTINGS.getSetting('User_Token')
LAST_PASSKEY = REAL_SETTINGS.getSetting('User_Paskey')
DEBUG        = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
PTVL_RUN     = xbmcgui.Window(10000).getProperty('PseudoTVRunning') == 'True'
BASEURL      = 'https://m-api.ustvnow.com/'
BASEWEB      = 'https://watch.ustvnow.com/'
BASEMOB      = 'http://mc.ustvnow.com/'
IMG_PATH     = os.path.join(ADDON_PATH,'resources','images')
IMG_HTTP     = BASEMOB + 'gtv/1/live/viewposter?srsid='
IMG_MOVIE    = 'http://tvdata.ustvnow.com/movieposters/'
IMG_TV       = 'http://tvdata.ustvnow.com/tvbanners/'
IMG_POSTER   = 'http://m.poster.static-ustvnow.com/'
IMG_POSTER_RE= 'http://m.reimages.static-ustvnow.com/'
IMG_SNAPSHOT = 'http://m.snapshot.static-ustvnow.com/%s/high'
IMG_CHLOGO   = 'http://m.ustvnow.com/images/%s.png'
COOKIE_JAR   = xbmc.translatePath(os.path.join(SETTINGS_LOC, "cookiejar.lwp"))
MEDIA_TYPES  = {'SP':'video','SH':'episode','EP':'episode','MV':'movie'}
FREE_CHANS   = ['CW','ABC','FOX','PBS','CBS','NBC','MY9']
URL_TYPE     = {0:'m3u8',1:'mp4'}[int(REAL_SETTINGS.getSetting('URL_Type'))]
URL_QUALITY  = int(REAL_SETTINGS.getSetting('URL_Quality')) + 1
CHAN_NAMES   = {'ABC':'ABC','AMC':'AMC','Animal Planet':'Animal Planet','Bravo':'Bravo','CBS':'CBS','CNBC':'CNBC','CW':'CW','Comedy Central':'Comedy Central','Discovery Channel':'Discovery Channel','ESPN':'ESPN',
                'FOX':'FOX','FX':'FX','Fox News Channel':'Fox News','Freeform':'Freeform','MSNBC':'MSNBC','NBC':'NBC','National Geographic Channel':'National Geographic','Nickelodeon':'Nickelodeon','PBS':'PBS',
                'SPIKE TV':'SPIKE TV','SundanceTV':'SundanceTV','Syfy':'Syfy','AE':'A&E','My9':'MY9','BBCA':'BBC America','ESPN2':'ESPN 2','NBCSNHD':'NBCSN','The Learning Channel':'TLC','Universal HD':'Universal',
                'USA':'USA Network','SUNDHD':'SundanceTV'}

USTVNOW_MENU = [("Live"      , '', 0),
                ("Schedules" , '', 1),
                ("Recordings", '', 2),
                ("Guide"     , '', 3),
                ("Featured"  , '', 5)]
                
if xbmc.getCondVisibility('System.HasAddon(script.module.uepg)') == 1:
    USTVNOW_MENU.append(("uEPG Guide", '', 20))

uEPG_PARAMS  = {"stream_code":"studio","description":"plot","synopsis":"plotoutline","ut_start":"starttime","orig_air_date":"firstaired"}
FILE_PARAMS  = ["title", "artist", "albumartist", "genre", "year", "rating", "album", "track", "duration", "comment", "lyrics", "musicbrainztrackid", "musicbrainzartistid", "musicbrainzalbumid", "musicbrainzalbumartistid", "playcount", "fanart", "director", "trailer", "tagline", "plot", "plotoutline", "originaltitle", "lastplayed", "writer", "studio", "mpaa", "cast", "country", "imdbnumber", "premiered", "productioncode", "runtime", "set", "showlink", "streamdetails", "top250", "votes", "firstaired", "season", "episode", "showtitle", "thumbnail", "file", "resume", "artistid", "albumid", "tvshowid", "setid", "watchedepisodes", "disc", "tag", "art", "genreid", "displayartist", "albumartistid", "description", "theme", "mood", "style", "albumlabel", "sorttitle", "episodeguide", "uniqueid", "dateadded", "size", "lastmodified", "mimetype", "specialsortseason", "specialsortepisode"]
PVR_PARAMS   = ["title","plot","plotoutline","starttime","endtime","runtime","progress","progresspercentage","genre","episodename","episodenum","episodepart","firstaired","hastimer","isactive","parentalrating","wasactive","thumbnail","rating","originaltitle","cast","director","writer","year","imdbnumber","hastimerrule","hasrecording","recording","isseries"]
ART_PARAMS   = ["thumb","poster","fanart","banner","landscape","clearart","clearlogo"]


def uni(string, encoding = 'utf-8'):
    if isinstance(string, basestring):
        if not isinstance(string, unicode):
            string = unicode(string, encoding)
        elif isinstance(string, unicode):
            string = string.encode('ascii', 'replace')
    return string

def unescape(string):
    try:
        parser = HTMLParser.HTMLParser()
        return (parser.unescape(string))
    except:
        return string
        
def log(msg, level=xbmc.LOGDEBUG):
    msg = msg.encode("utf-8")
    if DEBUG == True:
        if level == xbmc.LOGERROR:
            msg += ' ,' + traceback.format_exc()
        xbmc.log(ADDON_ID + '-' + ADDON_VERSION + '-' + msg, level)
        
def inputDialog(heading=ADDON_NAME, default='', key=xbmcgui.INPUT_ALPHANUM, opt=0, close=0):
    retval = xbmcgui.Dialog().input(heading, default, key, opt, close)
    if len(retval) > 0:
        return retval    
    
def okDialog(str1, str2='', str3='', header=ADDON_NAME):
    xbmcgui.Dialog().ok(header, str1, str2, str3)
    
def yesnoDialog(str1, str2='', str3='', header=ADDON_NAME, yes='', no='', autoclose=0):
    return xbmcgui.Dialog().yesno(header, str1, str2, str3, no, yes, autoclose)
     
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
class USTVnow():
    def __init__(self):
        log('__init__')
        self.net   = net.Net()
        self.cache = SimpleCache()
        if self.login(USER_EMAIL, PASSWORD) == False:
            raise SystemExit
        
        
    def mainMenu(self):
        log('mainMenu')
        for item in USTVNOW_MENU:
            self.addDir(*item)
        
        
    def buildHeader(self):
        header_dict               = {}
        header_dict['Accept']     = 'application/json, text/javascript, */*; q=0.01'
        header_dict['Host']       = 'm-api.ustvnow.com'
        header_dict['Connection'] = 'keep-alive'
        header_dict['Referer']    = 'http://watch.ustvnow.com'
        header_dict['Origin']     = 'http://watch.ustvnow.com'
        header_dict['User-Agent'] = 'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.127 Large Screen Safari/533.4 GoogleTV/162671'
        return header_dict
        
        
    def login(self, user, password):
        log('login')
        if len(user) > 0:
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
            header_dict = self.buildHeader()
            self.net.set_cookies(COOKIE_JAR)
            
            try:
                #check token
                dvrlink  = None
                custlink = json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/getcustomerkey', form_data={'token':LAST_TOKEN}, headers=header_dict).content.encode("utf-8").rstrip())
                '''{u'username': u'', u'ip': u'', u'customerkey': u''}'''
                self.custkey = (custlink.get('customerkey','') or 0)                
                if custlink and 'username' in custlink and user.lower() == custlink['username'].lower():
                    log('login, using existing token, passkey')
                    self.token   = LAST_TOKEN
                    self.passkey = LAST_PASSKEY
                else:
                    #login
                    loginlink = json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/login', form_data={'username':user,'password':password,'device':'gtv','redir':'0'}, headers=header_dict).content.encode("utf-8").rstrip())
                    '''{u'token': u'', u'result': u'success'}'''
                    if loginlink and 'token' in loginlink and loginlink['result'].lower() == 'success':
                        log('login, creating new token')
                        self.token = loginlink['token']
                        REAL_SETTINGS.setSetting('User_Token',self.token)          
                        
                        #passkey
                        dvrlink = json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/viewdvrlist', form_data={'token':self.token}, headers=header_dict).content.encode("utf-8").rstrip())
                        '''{u'globalparams': {u'passkey': u''}, u'results': []}'''
                        if dvrlink and 'globalparams' in dvrlink:
                            log('login, creating new passkey')
                            self.passkey = dvrlink['globalparams']['passkey']
                            REAL_SETTINGS.setSetting('User_Paskey',self.passkey)
                    else:
                        raise Exception
                            
                    #check user credentials
                    userlink = json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/getuserbytoken', form_data={'token':self.token}, headers=header_dict).content.encode("utf-8").rstrip())            
                    '''{u'status': u'success', u'data': {u'username': u'', u'need_account_activation': False, u'plan_id': 1, u'language': u'en', u'plan_free': 1, u'sub_id': u'7', u'lname': u'', u'currency': u'USD', u'points': 1, u'need_account_renew': False, u'fname': u'', u'plan_name': u'Free Plan'}}'''
                    log('login, checking user account')
                    if userlink and 'data' in userlink and userlink['status'].lower() == 'success':
                        REAL_SETTINGS.setSetting('User_Plan'      ,userlink['data']['plan_name'])
                        expires = 'Never' if userlink['data']['plan_name'] == 'Free Plan' else ''
                        REAL_SETTINGS.setSetting('User_Expires'   ,'%s'%expires)
                        REAL_SETTINGS.setSetting('User_isFree'    ,str(userlink['data']['plan_name'] == 'Free Plan'))
                        dvrPlan = 2 if 'dvr' in (userlink['data']['plan_name']).lower() else None
                        REAL_SETTINGS.setSetting('User_DVRpoints' ,str(dvrPlan or userlink['data']['points'] or 0))
                        xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30006) + userlink['data']['fname'], ICON, 4000)
                        
                        if userlink['data']['need_account_renew'] == True:
                            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30016) + userlink['data']['fname'], ICON, 4000)
                        elif userlink['data']['need_account_activation'] == True:
                            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30022) + userlink['data']['fname'], ICON, 4000)
                        else: 
                            if REAL_SETTINGS.getSetting('User_DVRpoints') != REAL_SETTINGS.getSetting('Last_DVRpoints'):
                                REAL_SETTINGS.setSetting('Last_DVRpoints',REAL_SETTINGS.getSetting('User_DVRpoints'))
                                xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30021) + userlink['data']['fname'], ICON, 4000)
                                
                        #check subscription
                        try:
                            #error prone, isolate and debug.
                            sublink = json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/getaccountsubscription', form_data={'username':user,'customerkey':self.custkey}, headers=header_dict).content.encode("utf-8").rstrip())
                            '''{u'username': u'', u'billingDatetime': u'', u'currency': u'USD', u'cgaccountstatusreason': u'', u'invoicehistory': u'', u'ocaccountstatus': u'Account active', u'ccLastFour': u'', u'lname': u'', u'x-cg-acnt-USD': False, u'fname': u'', u'sub_info': {u'cost': 0, u'plan': {u'sub_group': 4, u'plan_id': 1, u'name': u'Free Plan', u'language': u'en', u'date_expire': u'0000-00-00', u'sub_id': 7, u'price': 0, u'currency': u'USD', u'plan_code': u'7_FREETRIAL', 
                                u'details': u'This plan lets you receive all major US terrestrial stations (ABC, CBS, CW, FOX, NBC, PBS).  You can later upgrade to a paid plan with more channels and DVR.'}, u'packages': []}, u'pendinginvoices': u'', u'cgbillingstatus': u'', u'dvrpoints': 1, u'plans': {u'10': {u'price': 15, u'name': u'1 Week All Channel Plan $15 ($2.14/day)', 
                                u'details': u'1 Week pass for all channels (No DVR)'}, u'23': {u'price': 19, u'name': u'All Channel Promo Plan $19/mo first 3 months', 
                                u'details': u'Monthly subscription for all channels. This promotional price is for the first three months after which it will renew at $29. This plan automatically renews each month but you can cancel anytime and will not be billed again when your current 30 day period has expired. '}, u'31': {u'price': 29, u'name': u'All Channel Promo Plan w/DVR $29/mo first 3 months', 
                                u'details': u'Monthly subscription for all channels. This promotional price is for the first three months after which it will renew at $39. This plan automatically renews each month but you can cancel anytime and will not be billed again when your current 30 day period has expired.'}, u'7': {u'price': 0, u'name': u'Free Plan', 
                                u'details': u'This plan lets you receive all major US terrestrial stations (ABC, CBS, CW, FOX, NBC, PBS).  You can later upgrade to a paid plan with more channels and DVR.'}, u'9': {u'price': 0.00, u'name': u'3 Day All Channel Plan $6.99 ($2.33/day)', 
                                u'details': u'3 Day pass for all channels (No DVR)'}, u'8': {u'price': 2.99, u'name': u'1 Day All Channel Plan $2.99', 
                                u'details': u'24 hour pass for all channels (No DVR)'}}, u'cgredirectUrl': u'', u'cgaccountstatus': False, u'isfacebookuser': False, u'cgkey': u'', u'ocaccountstatuscode': 0, u'packages': [], u'subscription': u'Free Plan', u'language': u'en', u'sub_id': u'7', u'dateopened': u'December 01, 2000', u'canceledDatetime': u'', u'cgbillingmethod': u''}'''
                            if sublink:
                                REAL_SETTINGS.setSetting('User_Expires'   ,'%s'%(sublink['sub_info']['date_expire']))
                        except:
                            pass
                    else:
                        raise Exception
                    self.net.save_cookies(COOKIE_JAR)
                    
                self.channels = channels = self.cache.get(ADDON_NAME + '.channelguide')
                if not self.channels:
                    log('login, refreshing channels')
                    channels = sorted(json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/channelguide', form_data={'token':self.token}, headers=header_dict).content.encode("utf-8").rstrip())['results'], key=lambda x: x['displayorder'])
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
                    self.cache.set(ADDON_NAME + '.channelguide', channels, expiration=datetime.timedelta(minutes=5))
                    self.channels = self.cache.get(ADDON_NAME + '.channelguide')
                    
                self.upcoming = self.cache.get(ADDON_NAME + '.upcoming')
                if not self.upcoming:
                    log('login, refreshing upcoming')
                    upcoming = json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/upcoming', form_data={'token':self.token}, headers=header_dict).content.encode("utf-8").rstrip())           
                    '''{u'prgschid': 19479379, u'dvraction': u'add', u'callsign': u'AMC', u'newtimecat': True, u'srsid': 14930, u'timecat': u'Today', u'scheduleid': 9946282, 
                        u'img': u'images/AMC.png', u'title': u'The Fugitive', u'prg_img': u'v5/NowShowing/14930/p14930_p_v5_aa.jpg', u'has_img': 1, u't': 0, u'sname': u'AMC', 
                        u'description': u'U.S. marshal (Tommy Lee Jones) hunts doctor (Harrison Ford) for murder of his wife (Sela Ward).', u'dvrtimeraction': u'add', 
                        u'auth': None, u'orig_air_date': None, u'dvrtimertype': 0, u'scode': u'amchd', u'prgsvcid': 10021, u'runtime': 10800, u'connectorid': u'MV000371790000', 
                        u'episode_title': u'', u'synopsis': u'An innocent man must evade the law as he pursues a killer.', u'event_inprogress': 1, u'ut_start': 1499009400, 
                        u'content_allowed': False, u'imgmark': u'live', u'content_id': u'MV000371790000', u'displayorder': 100}''' 
                    self.cache.set(ADDON_NAME + '.upcoming', upcoming, expiration=datetime.timedelta(hours=6))
                    self.upcoming = self.cache.get(ADDON_NAME + '.upcoming')

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
                    if dvrlink:
                        recorded = dvrlink['results']
                    else:
                        recorded = (json.loads(self.net.http_POST(BASEURL + 'gtv/1/live/viewdvrlist', form_data={'token':self.token}, headers=header_dict).content.encode("utf-8").rstrip()))['results']
                    self.cache.set(ADDON_NAME + '.recorded', recorded, expiration=datetime.timedelta(minutes=1))
                    self.recorded = self.cache.get(ADDON_NAME + '.recorded')
                return True
            except Exception,e:
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
        

    def browseLive(self):
        log('browseLive')
        d = datetime.datetime.utcnow()
        now = datetime.datetime.fromtimestamp(calendar.timegm(d.utctimetuple()))  
        isFree = REAL_SETTINGS.getSetting('User_isFree') == "True"
        if self.channels is None:
            xbmc.executebuiltin("Container.Refresh")
        for channel in self.channels:
            try:
                name = CHAN_NAMES[channel['stream_code']]
                if isFree == True and name not in FREE_CHANS:
                    continue
                startime = datetime.datetime.fromtimestamp(channel['ut_start'])
                endtime  = startime + datetime.timedelta(seconds=channel['runtime'])
                if endtime > now and startime <= now:
                    label, url, liz = self.buildChannelListItem(name, channel)
                    self.addLink(label, url, 9, liz, len(self.channels))
            except Exception,e:
                log('browseLive, failed ' + str(e), xbmc.LOGERROR)
                
                
    def browseRecordings(self, recorded=False):
        log('browseRecordings')
        d = datetime.datetime.utcnow()
        now = datetime.datetime.fromtimestamp(calendar.timegm(d.utctimetuple()))
        if self.recorded is None:
            xbmc.executebuiltin("Container.Refresh")
        for channel in self.recorded:
            try:
                startime  = datetime.datetime.fromtimestamp(channel['ut_start'])
                endtime   = startime + datetime.timedelta(seconds=channel['runtime'])
                if endtime > now and (startime <= now or startime > now) and recorded == True:
                    continue
                elif endtime < now and (startime <= now or startime > now) and recorded == False:
                    continue
                label, url, liz = self.buildRecordedListItem(CHAN_NAMES[channel['stream_code']])
                mode = 10 if recorded == True else 21
                if mode == 21:
                    liz.setProperty("IsPlayable","false")
                self.addLink(label, url, mode, liz, len(self.recorded))
            except Exception,e:
                log('browseRecordings, failed ' + str(e), xbmc.LOGERROR)
                

    def browseGuide(self, name=None, upcoming=False):
        log('browseGuide')
        d = datetime.datetime.utcnow()
        now = datetime.datetime.fromtimestamp(calendar.timegm(d.utctimetuple()))  
        isFree = REAL_SETTINGS.getSetting('User_isFree') == "True"
        if self.channels is None:
            xbmc.executebuiltin("Container.Refresh")
        if name is None and upcoming == False:
            collect = []
            for channel in self.channels:
                try:
                    name = CHAN_NAMES[channel['stream_code']]
                    if isFree == True and name not in FREE_CHANS:
                        continue
                    collect.append(name)
                except:
                    xbmc.executebuiltin("Container.Refresh")
            counter = collections.Counter(collect)
            for key, value in sorted(counter.iteritems()):
                icon = (os.path.join(IMG_PATH,'logos','%s.png'%key) or ICON)
                infoArt  = {"thumb":icon,"poster":icon,"icon":icon,"fanart":FANART}
                self.addDir("%s"%(key), key, 4, infoArt=infoArt)
        else:
            for channel in self.channels:
                try:
                    if isFree == True and name not in FREE_CHANS:
                        continue
                    if name == CHAN_NAMES[channel['stream_code']]:
                        startime  = datetime.datetime.fromtimestamp(channel['ut_start'])
                        endtime   = startime + datetime.timedelta(seconds=channel['runtime'])
                        if endtime > now and (startime <= now):
                            label, url, liz = self.buildChannelListItem(name, channel)
                            self.addLink(label, url, 9, liz, len(self.channels))
                        elif endtime > now and (startime <= now or startime > now):
                            label, url, liz = self.buildChannelListItem(name, channel)
                            mode = 9 if PTVL_RUN == True else 21
                            if mode == 21:
                                liz.setProperty("IsPlayable","false")
                            self.addLink(label, url, mode, liz, len(self.channels))
                except Exception,e:
                    log('browseGuide, failed ' + str(e), xbmc.LOGERROR)
                
           
    def browseFeatured(self):
        log('browseFeatured')
        d = datetime.datetime.utcnow()
        now = datetime.datetime.fromtimestamp(calendar.timegm(d.utctimetuple()))  
        isFree = REAL_SETTINGS.getSetting('User_isFree') == "True"
        if self.upcoming is None:
            xbmc.executebuiltin("Container.Refresh")
        for channel in self.upcoming:
            try:
                name = CHAN_NAMES[channel['sname']]
                startime  = datetime.datetime.fromtimestamp(channel['ut_start'])
                endtime   = startime + datetime.timedelta(seconds=channel['runtime'])
                if endtime > now and (startime <= now or startime > now):
                    label, url, liz = self.buildChannelListItem(name, channel, feat=True)
                    liz.setProperty("IsPlayable","false")
                    self.addLink(label, url, 21, liz, len(self.upcoming))
            except Exception,e:
                log('browseFeatured, failed ' + str(e), xbmc.LOGERROR)

                
    def buildChannelListItem(self, name, channel=None, feat=False):
        if channel is None:
            for channel in self.channels:
                if name == CHAN_NAMES[channel['stream_code']]:
                    break
        startime  = datetime.datetime.fromtimestamp(channel['ut_start'])
        endtime   = startime + datetime.timedelta(seconds=channel['runtime'])
        title     = unescape(channel['title'])
        mediatype = (channel.get('mediatype','') or (channel.get('connectorid',''))[:2] or (channel.get('content_id',''))[:2] or 'SP')
        mtype     = MEDIA_TYPES[mediatype.upper()]
        if PTVL_RUN == True:
            label = name
        elif feat == True:
            label     = '%s %s-%s: %s - %s'%(startime.strftime('%m/%d/%Y'),startime.strftime('%I:%M').lstrip('0'),endtime.strftime('%I:%M %p').lstrip('0'),name,title)       
        else:
            label = '%s: %s - %s'%(startime.strftime('%I:%M %p').lstrip('0'),name,title)
        label2    = '%s - %s'%(startime.strftime('%I:%M %p').lstrip('0'),endtime.strftime('%I:%M %p').lstrip('0'))
        scode     = (channel.get('stream_code','') or channel.get('sname','') or '')
        url       = CHAN_NAMES[scode]
        liz       = xbmcgui.ListItem(label)
        infoList  = {"mediatype":mtype,"label":label,"label2":label2,"title":label,
                     "studio":CHAN_NAMES[scode],"duration":channel['runtime'],"plotoutline":unescape(channel['synopsis']),
                     "plot":unescape(channel['description']),"aired":(channel['orig_air_date'] or startime.strftime('%Y-%m-%d'))}
                     
        # if mediatype.startswith('MV'):
            # poster = IMG_MOVIE+channel['prg_img']
        # elif mediatype.startswith(('SH','EP')):
            # poster = IMG_TV+channel['prg_img']
        # else:
        thumb  = IMG_HTTP + str(channel['srsid']) + '&cs=' + channel['callsign'] + '&tid=' + mediatype
        poster = (os.path.join(IMG_PATH,'%s.png'%name) or ICON)
        liz.setInfo(type="Video", infoLabels=infoList)
        liz.setArt({"thumb":thumb,"poster":poster,"fanart":FANART})
        liz.setProperty("IsPlayable","true")
        liz.setProperty("IsInternetStream","true")
        if channel['dvrtimeraction'] == 'add':
            opt = '@'.join([str(channel['prgsvcid']),(channel.get('event_time','') or str(channel.get('ut_start','')))])#lazy solution rather then create additional url parameters for this single function.
            contextMenu = [('Set single recording'   ,'XBMC.RunPlugin(%s)'%(sys.argv[0]+"?url="+urllib.quote_plus(str(channel['scheduleid']))+"&mode="+str(6)+"&name="+urllib.quote_plus(opt))),
                           ('Set recurring recording','XBMC.RunPlugin(%s)'%(sys.argv[0]+"?url="+urllib.quote_plus(str(channel['connectorid']))+"&mode="+str(7)+"&name="+urllib.quote_plus(opt)))]
        else:
            contextMenu = [('Remove recording','XBMC.RunPlugin(%s)'%(sys.argv[0]+"?url="+urllib.quote_plus(str(channel['scheduleid']))+"&mode="+str(8)+"&name="+urllib.quote_plus(name)))]
        liz.addContextMenuItems(contextMenu)
        log('buildChannelListItem, label = ' + label + ', url = ' + url)
        return label, url, liz
    
    
    def buildRecordedListItem(self, name):
        for channel in self.recorded:
            if name == CHAN_NAMES[channel['stream_code']] or name == str(channel['scheduleid']):
                startime  = datetime.datetime.fromtimestamp(channel['ut_start'])
                endtime   = startime + datetime.timedelta(seconds=channel['runtime'])
                title     = unescape(channel['title'])
                label     = '%s %s-%s: %s - %s'%(startime.strftime('%m/%d/%Y'),startime.strftime('%I:%M').lstrip('0'),endtime.strftime('%I:%M %p').lstrip('0'),name,title)
                label2    = '%s %s-%s'%(startime.strftime('%m/%d/%Y'),startime.strftime('%I:%M').lstrip('0'),endtime.strftime('%I:%M %p').lstrip('0'))
                url       = str(channel['scheduleid'])
                liz       = xbmcgui.ListItem(label)
                mediatype = (channel.get('mediatype','') or (channel.get('connectorid',''))[:2] or (channel.get('content_id',''))[:2] or 'SP')
                mtype     = MEDIA_TYPES[mediatype.upper()]
                infoList  = {"mediatype":mtype,"label":label,"label2":label2,"title":label,"studio":CHAN_NAMES[channel['stream_code']],
                             "duration":channel['runtime'],"plotoutline":unescape(channel['synopsis']),"plot":unescape(channel['description']),
                             "aired":(channel['orig_air_date'] or startime.strftime('%Y-%m-%d'))}
                # if mediatype.startswith('MV'):
                    # poster = IMG_MOVIE+channel['prg_img']
                # elif mediatype.startswith(('SH','EP')):
                    # poster = IMG_TV+channel['prg_img']
                # else:
                thumb  = IMG_HTTP + str(channel['srsid']) + '&cs=' + channel['callsign'] + '&tid=' + mediatype
                poster = (os.path.join(IMG_PATH,'%s.png'%name) or ICON)
                liz.setInfo(type="Video", infoLabels=infoList)
                liz.setArt({"thumb":thumb,"poster":poster,"fanart":FANART})
                liz.setProperty("IsPlayable","true")
                liz.setProperty("IsInternetStream","true")
                print channel['dvrtimeraction']
                if channel['dvrtimeraction'] == 'add':
                    opt = '@'.join([str(channel['prgsvcid']),channel['event_time']])#lazy solution rather then create additional url parameters for this single function.
                    contextMenu = [('Set single recording'   ,'XBMC.RunPlugin(%s)'%(sys.argv[0]+"?url="+urllib.quote_plus(str(channel['scheduleid']))+"&mode="+str(6)+"&name="+urllib.quote_plus(opt))),
                                   ('Set recurring recording','XBMC.RunPlugin(%s)'%(sys.argv[0]+"?url="+urllib.quote_plus(str(channel['connectorid']))+"&mode="+str(7)+"&name="+urllib.quote_plus(opt)))]
                contextMenu.extend([('Remove recording','XBMC.RunPlugin(%s)'%(sys.argv[0]+"?url="+urllib.quote_plus(str(channel['scheduleid']))+"&mode="+str(8)+"&name="+urllib.quote_plus(name)))])
                liz.addContextMenuItems(contextMenu)
                log('buildRecordedListItem, label = ' + label + ', url = ' + url)
                return label, url, liz
    
    
    def resolveURL(self, url, dvr=False):
        log('resolveURL, url = ' + url + ', dvr = ' + str(dvr))
        isFree  = REAL_SETTINGS.getSetting('User_isFree') == "True"
        if dvr:
            for channel in self.recorded:
                if url == str(channel['scheduleid']):
                    try:
                        urllink = json.loads(self.net.http_POST(BASEURL + 'stream/1/dvr/play', form_data={'token':self.token,'key':self.passkey,'scheduleid':channel['scheduleid']}, headers=self.buildHeader()).content.encode("utf-8").rstrip())
                        '''{u'pr': u'll', u'domain': u'ilvc02.ll.ustvnow.com',u'stream': u'http://ilvc02.ll.ustvnow.com/ilv10/pr/xxl/smil:0B64AWHTMUSTVNOW/playlist.m3u8?', 
                            u'streamname': u'0B64AWHTMUSTVNOW', u'tr': u'', u'up': 1, u'pd': 0, u'pl': u'vjs'}'''
                        if URL_TYPE == 'm3u8':
                            stream = urllink['stream']
                        else:
                            stream = (urllink['stream'].replace('smil:','mp4:').replace('USTVNOW','USTVNOW%d'%URL_QUALITY))
                        log('resolveURL, url = ' + stream)
                        return stream
                    except Exception,e:
                        if channel and channel['scheduleid']:
                            self.replaceToken(url, dvr)
        else:
            for channel in self.channels:
                if url == CHAN_NAMES[channel['stream_code']]:
                    try:
                        urllink = json.loads(self.net.http_POST(BASEURL + 'stream/1/live/view', form_data={'token':self.token,'key':self.passkey,'scode':channel['scode']}, headers=self.buildHeader()).content.encode("utf-8").rstrip())
                        '''{u'pr': u'll', u'domain': u'ilvc02.ll.ustvnow.com',u'stream': u'http://ilvc02.ll.ustvnow.com/ilv10/pr/xxl/smil:0B64AWHTMUSTVNOW/playlist.m3u8?', 
                            u'streamname': u'0B64AWHTMUSTVNOW', u'tr': u'', u'up': 1, u'pd': 0, u'pl': u'vjs'}'''
                        if URL_TYPE == 'm3u8':
                            stream = urllink['stream']
                        else:
                            stream = (urllink['stream'].replace('smil:','mp4:').replace('USTVNOW','USTVNOW%d'%URL_QUALITY))
                        log('resolveURL, stream = ' + stream)
                        return stream
                    except Exception,e:
                        if channel and channel['scode']:
                            self.replaceToken(url, dvr)
                    
                    
    def replaceToken(self, url, dvr):
        #generate alternative token using website endpoint rather then googletv.
        try:
            #get CSRF Token
            responce = urllib2.urlopen(BASEWEB + "account/signin").read()
            CSRF = re.findall(r'var csrf_value = "(.*?)"', responce, re.DOTALL)[0]
            #get WEB Token
            responce = (self.net.http_POST(BASEWEB + 'account/login', form_data={'csrf_ustvnow': CSRF, 'signin_email': USER_EMAIL, 'signin_password':PASSWORD, 'signin_remember':'1'}).content.encode("utf-8").rstrip())
            altToken = re.findall(r'var token(.*?)= "(.*?)";', responce, re.DOTALL)[0][1]
            if altToken and altToken != 'null':
                self.token = altToken
                log('replaceToken, replacing existing token')
                REAL_SETTINGS.setSetting('User_Token',altToken)
                self.resolveURL(url, dvr)
        except Exception,e:
            log('replaceToken, Unable to login ' + str(e), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30005), ICON, 4000)
            raise SystemExit

            
    def setRecording(self, name, url, remove=False, recurring=False):
        log('setRecording, name = ' + name + ', url = ' + url + ', remove = ' + str(remove))
        if remove == True:
            setlink = (self.net.http_POST(BASEURL + 'gtv/1/dvr/updatedvr', form_data={'scheduleid':url,'token':self.token,'action':'remove'}, headers=self.buildHeader()).content.encode("utf-8").rstrip())
        else:
            if int(REAL_SETTINGS.getSetting('User_DVRpoints')) <= 1:
                xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30019), ICON, 4000)
                return
            opt = name.split('@')#lazy solution rather then create additional url parameters for this single function.
            if recurring == True:
                setlink = (self.net.http_POST(BASEURL + 'gtv/1/dvr/updatedvrtimer', form_data={'connectorid':url,'prgsvcid':opt[0],'eventtime':opt[1],'token':self.token,'action':'add'}, headers=self.buildHeader()).content.encode("utf-8").rstrip())
            else:
                setlink = (self.net.http_POST(BASEURL + 'gtv/1/dvr/updatedvr'     , form_data={'scheduleid':url,'token':self.token,'action':'add'}, headers=self.buildHeader()).content.encode("utf-8").rstrip())
        '''<result><status>failure</status><action>add</action></result>'''
        action = re.findall(r'<action>(.*?)</action>', setlink, re.DOTALL)[0]
        status = re.findall(r'<status>(.*?)</status>', setlink, re.DOTALL)[0]
        log('setRecording, action = ' + action + ', status = ' + status)
        if status == 'failure':
            xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30023)%action.title(), ICON, 4000)
            return
        xbmcgui.Dialog().notification(ADDON_NAME, LANGUAGE(30024)%action.title(), ICON, 4000)
        xbmc.executebuiltin("Container.Refresh")

    
    def playVideo(self, url, dvr=False):
        log('playVideo, url = ' + url + ', dvr = ' + str(dvr))
        if dvr:
            label, path, liz = self.buildRecordedListItem(url)
        else:
            label, path, liz = self.buildChannelListItem(url)
        liz.setPath(self.resolveURL(url,dvr)) 
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

           
    def addLink(self, name, u, mode, liz, total=0):
        log('addLink, name = ' + name)
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(uni(name))
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=total)

        
    def addDir(self, name, u, mode, infoList=False, infoArt=False):
        log('addDir, name = ' + name)
        liz=xbmcgui.ListItem(name)
        liz.setProperty('IsPlayable', 'false')
        if infoList == False:
            liz.setInfo(type="Video", infoLabels={"mediatype":"video","label":name,"title":name} )
        else:
            liz.setInfo(type="Video", infoLabels=infoList)
        if infoArt == False:
            liz.setArt({'thumb':ICON,'fanart':FANART})
        else:
            liz.setArt(infoArt)
        u=sys.argv[0]+"?url="+urllib.quote_plus(u)+"&mode="+str(mode)+"&name="+urllib.quote_plus(uni(name))
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
  
  
    def uEPG(self):
        log('uEPG')
        #support for upcoming uEPG universal epg framework module, module will be available from the Kodi repository.
        #https://github.com/Lunatixz/XBMC_Addons/tree/master/script.module.uepg
        isFree = REAL_SETTINGS.getSetting('User_isFree') == "True"
        collect = []
        for channel in self.channels:
            try:
                name = CHAN_NAMES[channel['stream_code']]
                if isFree == True and name not in FREE_CHANS:
                    continue
                collect.append(name)
            except:
                xbmc.executebuiltin("Container.Refresh")
        
        channelNum  = 0
        channelList = []
        counter = collections.Counter(collect)
        for key, value in sorted(counter.iteritems()):
            guidedata   = []
            newChannel  = {}
            channelName = key
            channelNum  = channelNum + 1
            newChannel['channelname']   = channelName
            newChannel['channelnumber'] = channelNum
            for channel in self.channels:
                try:
                    name = CHAN_NAMES[channel['stream_code']]
                    if isFree == True and name not in FREE_CHANS:
                        continue
                    if name == channelName:
                        tmpdata = {}
                        mediatype = (channel.get('mediatype','') or (channel.get('connectorid',''))[:2] or (channel.get('content_id',''))[:2] or 'SP')
                        mtype     = MEDIA_TYPES[mediatype.upper()]
                        thumb  = IMG_HTTP + str(channel['srsid']) + '&cs=' + channel['callsign'] + '&tid=' + mediatype
                        logo   = (os.path.join(IMG_PATH,'%s.png'%name) or ICON)
                        
                        for key, value in channel.iteritems():
                            try:
                                tmpdata[uEPG_PARAMS[key]] = unescape(value)
                            except:
                                if key in FILE_PARAMS + PVR_PARAMS:
                                    tmpdata[key] = unescape(value)
                        tmpdata['art'] = {"thumb":thumb,"logo":logo}
                        tmpdata['mediatype'] = mtype
                        tmpdata['url'] = sys.argv[0]+'?mode=9&name=%s'%name
                        guidedata.append(tmpdata)
                except:
                    pass
                newChannel['guidedata'] = guidedata
            channelList.append(newChannel)
        return channelList
        
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

if mode==None:  USTVnow().mainMenu()
elif mode == 0: USTVnow().browseLive()
elif mode == 1: USTVnow().browseRecordings()
elif mode == 2: USTVnow().browseRecordings(recorded=True)
elif mode == 3: USTVnow().browseGuide()
elif mode == 4: USTVnow().browseGuide(name)
elif mode == 5: USTVnow().browseFeatured()
elif mode == 6: USTVnow().setRecording(name,url)
elif mode == 7: USTVnow().setRecording(name,url,recurring=True)
elif mode == 8: USTVnow().setRecording(name,url,remove=True)
elif mode == 9: USTVnow().playVideo(url)
elif mode == 10:USTVnow().playVideo(url,dvr=True)
elif mode == 20:xbmc.executebuiltin("RunScript(script.module.uepg,json=%s&refresh_path=%s&refresh_interval=%s)"%(urllib.quote_plus(json.dumps(USTVnow().uEPG())),urllib.quote_plus(json.dumps(sys.argv[0]+"?mode=20")),urllib.quote_plus(json.dumps("hours=2"))))
elif mode == 21:xbmc.executebuiltin("action(ContextMenu)")

xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_NONE )
xbmcplugin.addSortMethod(int(sys.argv[1]) , xbmcplugin.SORT_METHOD_LABEL )
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)