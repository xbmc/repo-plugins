import uuid
import hmac
import hashlib
import string, random
from StringIO import StringIO
import gzip
from urllib2 import URLError, HTTPError
import sys
import xbmc,xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import urllib, urllib2
import json
import HTMLParser
import calendar
from datetime import datetime, timedelta
import time
import cookielib
import base64
import requests, urlparse


addon_handle = int(sys.argv[1])
SCORE_COLOR = 'FF00B7EB'
UPCOMING = 'FFD2D2D2'
CRITICAL ='FFD10D0D'
FINAL = 'FF666666'
FREE = 'FF43CD80'
GAMETIME_COLOR = 'FFFFFF66'
now = datetime.now()
BASE_PATH = 'https://data.ncaa.com/mml/'+str(now.year)+'/mobile'

def colorString(string, color):
    return '[COLOR='+color+']'+string+'[/COLOR]'

def stringToDate(string, date_format):
    try:
        date = datetime.strptime(str(string), date_format)
    except TypeError:
        date = datetime(*(time.strptime(str(string), date_format)[0:6]))                

    return date

def FIND(source,start_str,end_str):    
    start = source.find(start_str)
    end = source.find(end_str,start+len(start_str))

    if start != -1:        
        return source[start+len(start_str):end]
    else:
        return ''


def SET_STREAM_QUALITY(url):
    
    stream_url = {}
    stream_title = []

    #Open master file a get cookie(s)
    cj = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    opener.addheaders = [ ("Accept", "*/*"),
                        ("Accept-Encoding", "deflate"),
                        ("Accept-Language", "en-us"),                                                                                                              
                        ("User-Agent", UA_MMOD)]

    resp = opener.open(url)
    master = resp.read()
    resp.close()  

    cookies = '' 
    for cookie in cj:                    
        if cookies != '':
            cookies = cookies + "; "
        cookies = cookies + cookie.name + "=" + cookie.value
    
    line = re.compile("(.+?)\n").findall(master)  

    for temp_url in line:
        if '#EXT' not in temp_url:
            temp_url = temp_url.rstrip()
            start = 0
            if 'http' not in temp_url:
                if 'master' in url:
                    start = url.find('master')
                elif 'manifest' in url:
                    start = url.find('manifest')                
            
            if url.find('?') != -1:
                replace_url_chunk = url[start:url.find('?')]    
            else:
                replace_url_chunk = url[start:]    
            
            
            temp_url = url.replace(replace_url_chunk,temp_url)              
            temp_url = temp_url.rstrip() + "|User-Agent=" + UA_MMOD
            
            #if cookies != '':                
            #temp_url = temp_url + "&Cookie=" + cookies
            
            stream_title.append(desc)
            stream_url.update({desc:temp_url})
        else:
            desc = ''
            start = temp_url.find('BANDWIDTH=')
            if start > 0:
                start = start + len('BANDWIDTH=')
                end = temp_url.find(',',start)
                desc = temp_url[start:end]
                try:
                    int(desc)
                    desc = str(int(desc)/1000) + ' kbps'
                except:
                    pass            
    
    
    if len(stream_title) > 0:
        ret =-1      
        stream_title.sort(key=natural_sort_key)
        if str(PLAY_BEST) == 'true':
            ret = len(stream_title)-1            
        else:
            dialog = xbmcgui.Dialog() 
            ret = dialog.select('Choose Stream Quality', stream_title)
        if ret >=0:
            url = stream_url.get(stream_title[ret])           
        else:
            sys.exit()
    else:
        msg = "No playable streams found."
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Streams Not Found', msg)


    return url


def natural_sort_key(s):
    _nsre = re.compile('([0-9]+)')
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)] 


def SAVE_COOKIE(cj):
    # Cookielib patch for Year 2038 problem
    # Possibly wrap this in if to check if device is using a 32bit OS
    for cookie in cj:
        # Jan, 1 2038
        if cookie.expires >= 2145916800:
            #Jan, 1 2037
            cookie.expires =  2114380800
    
    cj.save(ignore_discard=True);  




def getTournamentInfo():
    now = datetime.now()
    url = 'http://data.ncaa.com/mml/'+str(now.year)+'/mobile/tournament.json'
    req = urllib2.Request(url)
    #req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36')
    req.add_header('Connection', 'keep-alive')
    req.add_header('Accept', '*/*')
    req.add_header('User-Agent', UA_MMOD)
    req.add_header('Accept-Language', 'en-us')
    req.add_header('Accept-Encoding', 'deflate')

    response = urllib2.urlopen(req)    
    json_source = json.load(response)                           
    response.close() 

    teams = json.dumps(json_source['tournament']['teams']['team'])

    return teams

def getTeamInfo(teams, team_id):    
    all_teams = json.loads(teams)
    team_name = ''
    link_name = ''
    
    for team in all_teams:        
        if str(team['id']) == str(team_id):
            #team_name = team['school']
            #link_name = team['link']
            break

    return team

def getCurrentInfo():
    now = datetime.now()
    url = 'http://data.ncaa.com/mml/'+str(now.year)+'/mobile/current.json'
    req = urllib2.Request(url)
    #req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36')
    req.add_header('Connection', 'keep-alive')
    req.add_header('Accept', '*/*')
    req.add_header('User-Agent', UA_MMOD)
    req.add_header('Accept-Language', 'en-us')
    req.add_header('Accept-Encoding', 'deflate')

    response = urllib2.urlopen(req)    
    json_source = json.load(response)                           
    response.close() 

    current_games = ''
    
    try:
        current_games = json.dumps(json_source['current']['game'])
    except:
        pass

    return current_games


def getGameClock(current_games, game_id):  
    games = json.loads(current_games)
    clock = 'Final'    
    ordinal_indicator = ''

    for game in games:        
        if str(game['id']) == str(game_id):
            clock = str(game['clock'])
            per = str(game['per'])
            state = str(game['state'])
            if state != '4' and per != '':
                if per == '1' and clock == '00:00':
                    clock = 'HALF'
                else:
                    if per == '1':
                        ordinal_indicator = "st"
                    elif per == '2':
                        ordinal_indicator = "nd"                                                
                    clock = clock + ' ' + per + ordinal_indicator
                break
                

    return clock
    

def getAppConfig():
    #https://data.ncaa.com/mml/2017/mobile/appConfig_iPhone.json    
    now = datetime.now()
    url = 'https://data.ncaa.com/mml/'+str(now.year)+'/mobile/appConfig_iPhone.json'
    req = urllib2.Request(url)    
    req.add_header('Accept', '*/*')
    req.add_header('User-Agent', UA_IPHONE)
    req.add_header('Accept-Language', 'en-us')
    req.add_header('Accept-Encoding', 'deflate')

    response = urllib2.urlopen(req)   
    json_source = json.load(response)                       
    response.close()  
    
    api = json_source['api']    
    #BASE_PATH = api['base']['sche']


def tokenTurner(media_token, stream_url, mvpd):
    url = ('https://token.ncaa.com/token/token_spe_mml?profile=mml&path=%s&format=json&accessTokenType=adobe&accessToken=%s') % \
          (urlparse.urlparse(stream_url).path, urllib.quote_plus(str(base64.b64decode(media_token))))

    headers = {'app-id': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBJZCI6Im5jYWEtbW1sLWlvcy1ncnJjZWwiLCJuZXR3b3JrIj'
                         'oibmNhYSIsInBsYXRmb3JtIjoiaW9zIiwicHJvZHVjdCI6Im1tbCIsImlhdCI6MTUxNTcwMDExM30.NLuTO5WIGNKd7Y'
                         'XGIEK0LVawhw68mawSQqnGAsRUs80',
               'User-Agent': 'MML%20iOS/166 CFNetwork/976 Darwin/18.2.0'
               }
    r = requests.get(url, headers=headers)
    stream_url += '?hdnts=' + r.json()['auth']['token'] + '|User-Agent=MML%20iOS/166 CFNetwork/976 Darwin/18.2.0'
    return stream_url


def fetchStream(game_id,archive=None):    
    now = datetime.now()
    url = 'http://data.ncaa.com/mml/'+str(now.year)+'/mobile/video/'+game_id+'_pr.json'
    if archive == 'archive': url = 'http://data.ncaa.com/mml/'+str(now.year)+'/mobile/game/game_'+game_id+'.json'
    now = datetime.now()
    req = urllib2.Request(url)    
    req.add_header('Accept', '*/*')
    req.add_header('User-Agent', UA_MMOD)
    req.add_header('Accept-Language', 'en-us')
    req.add_header('Accept-Encoding', 'deflate')

    response = urllib2.urlopen(req)   
    json_source = json.load(response)                       
    response.close()  
    
    if archive == 'archive':
        stream_url = json_source['game']['videos']['video'][0]['connected']
    else:
        stream_url = json_source['connected1']

    return stream_url


def getAuthCookie():
    mediaAuth = ''    
    try:
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))     
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)    

        #If authorization cookie is missing or stale, perform login    
        for cookie in cj:            
            if cookie.name == "mediaAuth" and not cookie.is_expired():            
                mediaAuth = 'mediaAuth='+cookie.value 
    except:
        pass

    return mediaAuth


def addStream(name,link_url,title,game_id,icon=None,fanart=None):
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(link_url)+"&mode="+str(104)+"&name="+urllib.quote_plus(name)+"&game_id="+urllib.quote_plus(str(game_id))

    liz = xbmcgui.ListItem(name)
    liz.setArt({'icon': ICON, 'thumb': ICON })

    if fanart != None:
        liz.setArt({'fanart': fanart})
    else:
        liz.setArt({'fanart': FANART})

    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )    

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    xbmcplugin.setContent(addon_handle, 'episodes')    
    return ok

def addDir(name,url,mode,iconimage,fanart=None):       
    ok=True    
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)

    liz = xbmcgui.ListItem(name)
    if iconimage is not None:
        liz.setArt({'icon': iconimage, 'thumb': iconimage})
    else:
        liz.setArt({'icon': ICON, 'thumb': ICON})

    liz.setInfo( type="Video", infoLabels={ "Title": name } )

    if fanart != None:
        liz.setArt({'fanart': fanart})
    else:
        liz.setArt({'fanart': FANART})


    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)    
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok


def addLink(name,url,iconimage,fanart=None):
    ok=True
    liz = xbmcgui.ListItem(name)

    if iconimage is not None:
        liz.setArt({'icon': iconimage, 'thumb': iconimage})
    else:
        liz.setArt({'icon': ICON, 'thumb': ICON})

    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    liz.setProperty("IsPlayable", "true")

    if fanart is not None:
        liz.setArt({'fanart': fanart})
    else:
        liz.setArt({'fanart': FANART})

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)    
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok


# KODI ADDON GLOBALS
ADDON_HANDLE = int(sys.argv[1])
ROOTDIR = xbmcaddon.Addon(id='plugin.video.mmlive').getAddonInfo('path')
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = xbmc.translatePath(ADDON.getAddonInfo('path'))
ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
KODI_VERSION = float(re.findall(r'\d{2}\.\d{1}', xbmc.getInfoLabel("System.BuildVersion"))[0])
LOCAL_STRING = ADDON.getLocalizedString
FANART = ROOTDIR+"/fanart.jpg"
ICON = ROOTDIR+"/icon.png"

#Settings file location
settings = xbmcaddon.Addon(id='plugin.video.mmlive')

#Main settings
NO_SPOILERS = str(settings.getSetting(id="no_spoilers"))

#User Agents
UA_IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Mobile/12H143'
UA_PC = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
UA_ADOBE_PASS = 'AdobePassNativeClient/1.9.4 (iPhone; U; CPU iPhone OS 9.2.1 like Mac OS X; en-us)'
UA_MMOD = 'MML iOS/73 CFNetwork/808.3 Darwin/16.3.0'



#Create Random Device ID and save it to a file
fname = os.path.join(ADDON_PATH_PROFILE, 'device.id')
if not os.path.isfile(fname):
    if not os.path.exists(ADDON_PATH_PROFILE):
        os.makedirs(ADDON_PATH_PROFILE)
    new_device_id = ''.join([random.choice('0123456789abcdef') for x in range(64)])
    device_file = open(fname,'w')   
    device_file.write(new_device_id)
    device_file.close()

fname = os.path.join(ADDON_PATH_PROFILE, 'device.id')
device_file = open(fname,'r') 
DEVICE_ID = device_file.readline()
device_file.close()


#Event Colors
FREE = 'FF43CD80'
LIVE = 'FF00B7EB'
UPCOMING = 'FFFFB266'
FREE_UPCOMING = 'FFCC66FF'