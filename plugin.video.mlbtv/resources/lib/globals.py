# coding=utf-8
import sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import calendar
import pytz
import urllib, urllib2
import json
import cookielib
import time
import math
from bs4 import BeautifulSoup 
from datetime import date, datetime, timedelta
from urllib2 import URLError, HTTPError
#from PIL import Image
from cStringIO import StringIO


addon_handle = int(sys.argv[1])


#Addon Info
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = xbmc.translatePath(ADDON.getAddonInfo('path'))
ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
XBMC_VERSION = float(re.findall(r'\d{2}\.\d{1}', xbmc.getInfoLabel("System.BuildVersion"))[0])
LOCAL_STRING = ADDON.getLocalizedString
ROOTDIR = ADDON.getAddonInfo('path')

#Settings
settings = xbmcaddon.Addon(id='plugin.video.mlbtv')
USERNAME = str(settings.getSetting(id="username"))
PASSWORD = str(settings.getSetting(id="password"))
OLD_USERNAME = str(settings.getSetting(id="old_username"))
OLD_PASSWORD = str(settings.getSetting(id="old_password"))
ROGERS_SUBSCRIBER = str(settings.getSetting(id="rogers"))
QUALITY = str(settings.getSetting(id="quality"))
NO_SPOILERS = settings.getSetting(id="no_spoilers")
FAV_TEAM = str(settings.getSetting(id="fav_team"))
TEAM_NAMES = settings.getSetting(id="team_names")
TIME_FORMAT = settings.getSetting(id="time_format")
SINGLE_TEAM = str(settings.getSetting(id='single_team'))
#Proxy Settings
PROXY_ENABLED = str(settings.getSetting(id='use_proxy'))
PROXY_SERVER = str(settings.getSetting(id='proxy_server'))
PROXY_PORT = str(settings.getSetting(id='proxy_port'))
PROXY_USER = str(settings.getSetting(id='proxy_user'))
PROXY_PWD = str(settings.getSetting(id='proxy_pwd'))

#Colors
SCORE_COLOR = 'FF00B7EB'
GAMETIME_COLOR = 'FFFFFF66'
#FAV_TEAM_COLOR = 'FFFF0000'
FREE_GAME_COLOR = 'FF43CD80'

#Game Time Colors
UPCOMING = 'FFD2D2D2'
LIVE = 'FFF69E20'
CRITICAL ='FFD10D0D'
FINAL = 'FF666666'
FREE = 'FF43CD80'



#Images
ICON = os.path.join(ROOTDIR,"icon.png")
FANART = os.path.join(ROOTDIR,"fanart.jpg")
PREV_ICON = os.path.join(ROOTDIR,"icon.png")
NEXT_ICON = os.path.join(ROOTDIR,"icon.png")

if SINGLE_TEAM == 'true':
    MASTER_FILE_TYPE = 'master_wired.m3u8'
    PLAYBACK_SCENARIO = 'HTTP_CLOUD_WIRED'
else:
    MASTER_FILE_TYPE = 'master_wired60.m3u8'
    PLAYBACK_SCENARIO = 'HTTP_CLOUD_WIRED_60'


#User Agents
UA_IPHONE = 'AppleCoreMedia/1.0.0.13D15 (iPhone; U; CPU OS 9_2_1 like Mac OS X; en_us)'
UA_IPAD = 'AppleCoreMedia/1.0 ( iPad; compatible; 3ivx HLS Engine/2.0.0.382; Win8; x64; 264P AACP AC3P AESD CLCP HTPC HTPI HTSI MP3P MTKA)'
UA_PC = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36'         
UA_PS4 = 'PS4Application libhttp/1.000 (PS4) libhttp/3.15 (PlayStation 4)'
UA_ATBAT = 'At Bat/13268 CFNetwork/758.2.8 Darwin/15.0.0'

#Playlists
RECAP_PLAYLIST = xbmc.PlayList(0)
EXTENDED_PLAYLIST = xbmc.PlayList(1)



def find(source,start_str,end_str):    
    start = source.find(start_str)
    end = source.find(end_str,start+len(start_str))

    if start != -1:        
        return source[start+len(start_str):end]
    else:
        return ''


def getGameIcon(home,away):
    #Check if game image already exists
    #image_path = ROOTDIR+'/resources/images/'+away+'vs'+home+'.png'
    image_path = os.path.join(ROOTDIR,'resources/images/'+away+'vs'+home+'.png')
    file_name = os.path.join(image_path)
    if not os.path.isfile(file_name): 
        try:
            createGameIcon(home,away,image_path)
        except:
            pass

    return image_path


def createGameIcon(home,away,image_path):    
    #bg = Image.new('RGB', (400,225), (0,0,0))    
    bg = Image.new('RGB', (500,250), (0,0,0)) 
    #http://mlb.mlb.com/mlb/images/devices/240x240/110.png
    #img_file = urllib.urlopen('http://mlb.mlb.com/mlb/images/devices/76x76/'+home+'.png ')
    img_file = urllib.urlopen('http://mlb.mlb.com/mlb/images/devices/240x240/'+home+'.png')
    im = StringIO(img_file.read())
    home_image = Image.open(im)
    #bg.paste(home_image, (267,74), home_image)
    bg.paste(home_image, (255,5), home_image)

    #img_file = urllib.urlopen('http://mlb.mlb.com/mlb/images/devices/76x76/'+away+'.png ')
    img_file = urllib.urlopen('http://mlb.mlb.com/mlb/images/devices/240x240/'+away+'.png')
    im = StringIO(img_file.read())
    away_image = Image.open(im)
    #bg.paste(away_image, (57,74), away_image)    
    bg.paste(away_image, (5,5), away_image)    
    
    bg.save(image_path)        
    

def colorString(string, color):
    return '[COLOR='+color+']'+string+'[/COLOR]'


def stringToDate(string, date_format):
    try:
        date = datetime.strptime(str(string), date_format)
    except TypeError:
        date = datetime(*(time.strptime(str(string), date_format)[0:6]))                

    return date


def easternToLocal(eastern_time):
    utc = pytz.utc
    eastern = pytz.timezone('US/Eastern')    
    eastern_time = eastern.localize(eastern_time)
    # Convert it from Eastern to UTC
    utc_time = eastern_time.astimezone(utc)
    timestamp = calendar.timegm(utc_time.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    # Convert it from UTC to local time
    assert utc_time.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_time.microsecond)

def UTCToLocal(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def localToEastern():    
    eastern = pytz.timezone('US/Eastern')    
    local_to_utc = datetime.now(pytz.timezone('UTC'))  

    eastern_hour = local_to_utc.astimezone(eastern).strftime('%H')    
    eastern_date = local_to_utc.astimezone(eastern)
    #Don't switch to the current day until 4:01 AM est
    if int(eastern_hour) < 3:
        eastern_date = eastern_date - timedelta(days=1)  

    local_to_eastern = eastern_date.strftime('%Y-%m-%d')
    return local_to_eastern

def easternToUTC(eastern_time):    
    utc = pytz.utc
    eastern = pytz.timezone('US/Eastern')    
    eastern_time = eastern.localize(eastern_time)
    # Convert it from Eastern to UTC
    utc_time = eastern_time.astimezone(utc)
    return utc_time



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



def addStream(name,title,event_id,gid,icon=None,fanart=None,info=None,video_info=None,audio_info=None,teams_stream=None,stream_date=None):
    ok=True
    u=sys.argv[0]+"?mode="+str(104)+"&name="+urllib.quote_plus(name)+"&event_id="+urllib.quote_plus(str(event_id))+"&gid="+urllib.quote_plus(str(gid))+"&teams_stream="+urllib.quote_plus(str(teams_stream))+"&stream_date="+urllib.quote_plus(str(stream_date))
    
    #if icon != None:
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=icon) 
    #else:
    #liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=ICON) 
    
    if fanart != None:
        liz.setProperty('fanart_image', fanart)       
    else:
        liz.setProperty('fanart_image', FANART)

    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info)
    if video_info != None:
        liz.addStreamInfo('video', video_info)
    if audio_info != None:
        liz.addStreamInfo('audio', audio_info)

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    xbmcplugin.setContent(addon_handle, 'episodes')
    
    return ok


def addLink(name,url,title,iconimage,info=None,video_info=None,audio_info=None,fanart=None):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)    
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    liz.setProperty('fanart_image', FANART)
    #if iconimage != None:
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage) 
    #else:
    #liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=ICON) 

    if info != None:
        liz.setInfo( type="Video", infoLabels=info)
    if video_info != None:
        liz.addStreamInfo('video', video_info)
    if audio_info != None:
        liz.addStreamInfo('audio', audio_info)

    if fanart != None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
    xbmcplugin.setContent(addon_handle, 'episodes')
    return ok




def addDir(name,mode,iconimage,fanart=None,game_day=None):       
    ok=True    
    
    #Set day to today if none given
    #game_day = time.strftime("%Y-%m-%d")
    #game_day = localToEastern()
    #game_day = '2016-01-27'

    u=sys.argv[0]+"?mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&icon="+urllib.quote_plus(iconimage)
    if game_day != None:
        u = u+"&game_day="+urllib.quote_plus(game_day)

    if iconimage != None:
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage) 
    else:
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=ICON) 

    liz.setInfo( type="Video", infoLabels={ "Title": name } )

    if fanart != None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)


    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)    
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok


def addPlaylist(name,game_day,mode,iconimage,fanart=None):       
    ok=True    
    u=sys.argv[0]+"?mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&icon="+urllib.quote_plus(iconimage)+"&stream_date="+urllib.quote_plus(str(game_day))

    if iconimage != None:
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage) 
    else:
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=ICON) 

    liz.setInfo( type="Video", infoLabels={ "Title": name } )

    if fanart != None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)

    
    info = {'plot':'Watch all the days highlights for '+game_day,'tvshowtitle':'MLB','title':name,'originaltitle':name,'aired':game_day,'genre':LOCAL_STRING(700),'mediatype':'video'}
    audio_info, video_info = getAudioVideoInfo()

    if info != None:
        liz.setInfo( type="Video", infoLabels=info)
    if video_info != None:
        liz.addStreamInfo('video', video_info)
    if audio_info != None:
        liz.addStreamInfo('audio', audio_info)
    

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)    
    #xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok


def scoreUpdates():
    #http://gdx.mlb.com/components/game/mlb/year_2016/month_03/day_08/miniscoreboard.json
    #grid.poll=15
    #s = ScoreThread()
    t = threading.Thread(target = scoringUpdates)
    t.start() 

def getFavTeamColor():
    #Hex code taken from http://teamcolors.arc90.com/    
    team_colors = {'Arizona Diamondbacks':'FFA71930',
                'Atlanta Braves':'FFCE1141',
                'Baltimore Orioles':'FFDF4601',
                'Boston Red Sox':'FFBD3039',
                'Chicago Cubs':'FFCC3433',
                'Chicago White Sox':'FFC4CED4',
                'Cincinnati Reds':'FFC6011F',
                'Cleveland Indians':'FFE31937',
                'Colorado Rockies':'FFC4CED4',
                'Detroit Tigers':'FF0C2C56',
                'Houston Astros':'FFEB6E1F',
                'Kansas City Royals':'FFC09A5B',
                'Los Angeles Angels':'FFBA0021',
                'Los Angeles Dodgers':'FFEF3E42',
                'Miami Marlins':'FFFF6600',
                'Milwaukee Brewers':'FFB6922E',
                'Minnesota Twins':'FFD31145',
                'New York Mets':'FFFF5910',
                'New York Yankees':'FFE4002B',
                'Oakland Athletics':'FFEFB21E',
                'Philadelphia Phillies':'FFE81828',
                'Pittsburgh Pirates':'FFFDB827',
                'St. Louis Cardinals':'FFC41E3A',
                'San Diego Padres':'FF05143F',
                'San Francisco Giants':'FFFD5A1E',
                'Seattle Mariners':'FFC4CED4',
                'Tampa Bay Rays':'FF8FBCE6',
                'Texas Rangers':'FFC0111F',
                'Toronto Blue Jays':'FFE8291C',
                'Washington Nationals':'FFAB0003'}

    
    fav_team_color = team_colors[FAV_TEAM]
    
    return  fav_team_color


def getFavTeamId():
    #possibly use the xml file in the future
    #http://mlb.mlb.com/shared/properties/mlb_properties.xml  
    team_ids = {'Arizona Diamondbacks':'109',
                'Atlanta Braves':'144',
                'Baltimore Orioles':'110',
                'Boston Red Sox':'111',
                'Chicago Cubs':'112',
                'Chicago White Sox':'145',
                'Cincinnati Reds':'113',
                'Cleveland Indians':'114',
                'Colorado Rockies':'115',
                'Detroit Tigers':'116',
                'Houston Astros':'117',
                'Kansas City Royals':'118',
                'Los Angeles Angels':'108',
                'Los Angeles Dodgers':'119',
                'Miami Marlins':'146',
                'Milwaukee Brewers':'158',
                'Minnesota Twins':'142',
                'New York Mets':'121',
                'New York Yankees':'147',
                'Oakland Athletics':'133',
                'Philadelphia Phillies':'143',
                'Pittsburgh Pirates':'134',
                'St. Louis Cardinals':'138',
                'San Diego Padres':'135',
                'San Francisco Giants':'137',
                'Seattle Mariners':'136',
                'Tampa Bay Rays':'139',
                'Texas Rangers':'140',
                'Toronto Blue Jays':'141',
                'Washington Nationals':'120'}
    
    fav_team_id = team_ids[FAV_TEAM]

    return  fav_team_id

def getAudioVideoInfo():
    #SD (800 kbps)|SD (1600 kbps)|HD (3000 kbps)|HD (5000 kbps)
    if QUALITY == 'SD (800 kbps)':        
        video_info = { 'codec': 'h264', 'width' : 512, 'height' : 288, 'aspect' : 1.78 }        
    elif QUALITY == 'SD (1200 kbps)':
        video_info = { 'codec': 'h264', 'width' : 640, 'height' : 360, 'aspect' : 1.78 }        
    else:
        #elif QUALITY == 'HD (2500 kbps)' or QUALITY == 'HD (3500 kbps)' or QUALITY == 'HD (5000 kbps)':
        video_info = { 'codec': 'h264', 'width' : 1280, 'height' : 720, 'aspect' : 1.78 }        

    audio_info = { 'codec': 'aac', 'language': 'en', 'channels': 2 }
    return audio_info, video_info

def getConfigFile():
    '''
    GET http://lwsa.mlb.com/partner-config/config?company=sony-tri&type=nhl&productYear=2015&model=PS4&firmware=default&app_version=1_0 HTTP/1.0
    Host: lwsa.mlb.com
    User-Agent: PS4Application libhttp/1.000 (PS4) libhttp/3.15 (PlayStation 4)
    Connection: close
    '''
    url = 'http://lwsa.mlb.com/partner-config/config?company=sony-tri&type=nhl&productYear=2015&model=PS4&firmware=default&app_version=1_0'
    req = urllib2.Request(url)       
    req.add_header("Connection", "close")
    req.add_header("User-Agent", UA_PS4)

    response = urllib2.urlopen(req, '')
    json_source = json.load(response)   
    response.close()
    

def convertSubtitles(suburl):
    #suburl = subtitles url
    #xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = url))

    #if ((addon.getSetting('sub_enable') == "true"):    
    subfile = xbmc.translatePath(os.path.join(ADDON_PATH_PROFILE, 'game_subtitles.srt'))
    prodir  = xbmc.translatePath(os.path.join(ADDON_PATH_PROFILE))
    if not os.path.isdir(prodir):
        os.makedirs(prodir)

    #pg = getRequest(suburl)
    response = urllib.urlopen(suburl)
    pg = response.read()    
    response.close()    
    if pg != "":
        ofile = open(subfile, 'w+')
        #need to adjust for subtitles not starting until 18 hours into the stream
        #<p begin='18:00:08;29' end='18:00:35;23'>&gt;&gt;&gt;</p>
        captions = re.compile("<p begin='(.+?)' end='(.+?)'>(.+?)</p>").findall(pg)
        idx = 1
        for cstart, cend, caption in captions:            
            cstart = cstart.replace('.',',')
            cend   = cend.replace('.',',').split('"',1)[0]
            caption = caption.replace('<br/>','\n').replace('&gt;','>')
            ofile.write( '%s\n%s --> %s\n%s\n\n' % (idx, cstart, cend, caption))
            idx += 1
        ofile.close()

    return subfile


def getStreamQuality(stream_url):    
    stream_title = []         
    req = urllib2.Request(stream_url)
    response = urllib2.urlopen(req)                    
    master = response.read()
    response.close()
            
    line = re.compile("(.+?)\n").findall(master)  

    for temp_url in line:
        if '.m3u8' in temp_url:
            temp_url = temp_url
            match = re.search(r'(\d.+?)K', temp_url)
            if match:
                bandwidth = match.group()
                if 0 < len(bandwidth) < 6:
                    bandwidth = bandwidth.replace('K',' kbps')                    
                    stream_title.append(bandwidth)                           
    

    stream_title.sort(key=natural_sort_key,reverse=True) 
    dialog = xbmcgui.Dialog() 
    ret = dialog.select('Choose Stream Quality', stream_title)    
    if ret >=0:        
        bandwidth = find(stream_title[ret],'',' kbps')
    else:
        sys.exit()

    return bandwidth

def natural_sort_key(s):
    _nsre = re.compile('([0-9]+)')
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)] 

def getBlackoutLiftTime(url):
    #"http://mediadownloads.mlb.com/ttml/2016/04/14/584182283.ttml"
    #url = 'http://mediadownloads.mlb.com/ttml/2016/04/14/584182283.ttml'    
    req = urllib2.Request(url)    
    req.add_header('Connection', 'close')
    req.add_header('User-Agent', UA_IPAD)
    try:    
        response = urllib2.urlopen(req)            
        xml_data = response.read()                                 
        response.close()                
    except HTTPError as e:
        xbmc.log('The server couldn\'t fulfill the request.')
        xbmc.log('Error code: ', e.code)
        sys.exit()
    
    
    #<p begin="19:59:16;28" end="19:59:20;06">PRESENTED BY THE ALLEGHENY HEALTH NETWORK.</p>
    #match = re.compile("<p begin='(.+?)' end='(.+?)'>",re.DOTALL).findall(xml_data)       
    match = re.compile('<inningTime type="SCAST" start="(.+?)" end="(.+?)"/>',re.DOTALL).findall(xml_data) 
    
    last_end_time = ''
    for begin_time, end_time in match:        
        last_end_time = end_time


    #ex 19:59:20;06
    game_end_time = datetime.strptime(last_end_time,'%H:%M:%S')
    blackout_lift_time = game_end_time + timedelta(minutes = 90)
    now = datetime.strptime(datetime.utcnow().strftime('%H:%M:%S'),'%H:%M:%S')
    
    minutes_until_lift = int(math.ceil((blackout_lift_time - now).total_seconds() / 60))
    lift_time = datetime.utcnow() + timedelta(minutes = minutes_until_lift)
    local_lift_time = UTCToLocal(lift_time)

    if TIME_FORMAT == '0':
         local_lift_time = local_lift_time.strftime('%I:%M %p').lstrip('0')
    else:
         local_lift_time = local_lift_time.strftime('%H:%M')
    
    return minutes_until_lift, local_lift_time
    