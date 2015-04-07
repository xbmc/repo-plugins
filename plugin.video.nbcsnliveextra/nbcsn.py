import sys
import xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import urllib, urllib2, httplib2
import json
import HTMLParser
import calendar
from datetime import datetime, timedelta
import time



addon_handle = int(sys.argv[1])
ROOTDIR = xbmcaddon.Addon(id='plugin.video.nbcsnliveextra').getAddonInfo('path')

#Settings file location
settings = xbmcaddon.Addon(id='plugin.video.nbcsnliveextra')

FANART = ROOTDIR+"/fanart.jpg"
ICON = ROOTDIR+"/icon.png"
ROOT_URL = 'http://stream.nbcsports.com/data/mobile/'

#Main settings
QUALITY = int(settings.getSetting(id="quality"))
USER_AGENT = str(settings.getSetting(id="user-agent"))
CDN = int(settings.getSetting(id="cdn"))


def CATEGORIES():                
    addDir('Live & Upcoming','/live',1,ICON,FANART)
    addDir('Featured',ROOT_URL+'mcms/prod/nbc-featured.json',2,ICON,FANART)
    #addDir('On NBC Sports','/replays',3,ICON,FANART)

def LIVE():      
    #LIVE        
    SCRAPE_VIDEOS(ROOT_URL+'mcms/prod/nbc-live.json')
    #UPCOMING
    SCRAPE_VIDEOS(ROOT_URL+'mcms/prod/nbc-upcoming.json')


def GET_ALL_SPORTS():
    # This process has changed drastically
    #Need This 
    #http://link.theplatform.com/s/BxmELC/JYis41t0VJTO?mbr=true&manifest=m3u&feed=Mobile%20App%20-%20NBC%20Sports%20Live%20Extra
    #To get This
    #http://allisports-vh.akamaihd.net/i/HD/video_sports/NBCU_Sports_Group_-_AlliSports/118/775/DT_BK_Skate_Streetstyle_Recap_YT_1411364680363_,140,345,220,90,60,40,20,0k.mp4.csmil/index_1_av.m3u8?null=
    #req = urllib2.Request(ROOT_URL+'configuration-2013.json')
    req = urllib2.Request(ROOT_URL+'configuration-2014-RSN-Sections.json')    
    response = urllib2.urlopen(req)   
    json_source = json.load(response)                       
    response.close()    

    try:
        for item in json_source['sports']:        
            code = item['code']
            name = item['name']                  
            addDir(name,ROOT_URL+'mcms/prod/'+code+'.json',4,ICON,FANART,'ALL')
    except:
        pass


def FEATURED(url):
    addDir('Full Replays',url,4,ICON,FANART,"replay")
    addDir('Showcase',url,4,ICON,FANART,"showCase")
    addDir('Spotlight',url,4,ICON,FANART,"spotlight") 


def SCRAPE_VIDEOS(url,scrape_type=None):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36')
    response = urllib2.urlopen(req)
    json_source = json.load(response)                           
    response.close()                
    
    if scrape_type == None:
        #LIVE
        #try:       
            #Sort By Start Time
            json_source = sorted(json_source,key=lambda x:x['start'])
            for item in json_source:        
                if not item['title'].startswith('CSN'):
                    BUILD_VIDEO_LINK(item)
        #except:
            #pass

    elif scrape_type == "ALL":
        try:
            for item in json_source['replay']:        
                BUILD_VIDEO_LINK(item)
        except:
            pass
        try:
            for item in json_source['showCase']:        
                BUILD_VIDEO_LINK(item)
        except:
            pass
        try:
            for item in json_source['spotlight']:        
                BUILD_VIDEO_LINK(item)
        except:
            pass

    else:
        try:
            if scrape_type == 'replay':
                for item in reversed(json_source[scrape_type]):        
                    BUILD_VIDEO_LINK(item)    
            else:
                for item in json_source[scrape_type]:        
                    BUILD_VIDEO_LINK(item)
        except:
            pass


def BUILD_VIDEO_LINK(item):
    url = ''    
    try:        
        url = item['iosStreamUrl']  
        if CDN == 1 and item['backupUrl'] != '':
            url = item['backupUrl']
    except:
        pass
    
    #Set quality level based on user settings
    if QUALITY == 0:
        q_lvl = "200000"
        q_lvl_golf = "296k"
    elif QUALITY == 1:
        q_lvl = "400000"
        q_lvl_golf = "496k"
    elif QUALITY == 2:
        q_lvl = "600000"
        q_lvl_golf = "796k"
    elif QUALITY == 3:
        q_lvl = "900000"
        q_lvl_golf = "1296k"
    elif QUALITY == 4:
        q_lvl = "1400000"
        q_lvl_golf = "1896k"
    elif QUALITY == 5:
        q_lvl = "2200000"
        q_lvl_golf = "2596k"
    else:
        q_lvl = "3450000"
        #q_lvl = "4296000"
        q_lvl_golf = "4296k"
    
    
    url = url.replace('master.m3u8',q_lvl_golf+'/prog.m3u8')       
    url = url.replace('manifest(format=m3u8-aapl-v3)','QualityLevels('+q_lvl+')/Manifest(video,format=m3u8-aapl-v3,audiotrack=audio_en_0)')       
    url = url.replace('manifest(format=m3u8-aapl,filtername=vodcut)','QualityLevels('+q_lvl+')/Manifest(video,format=m3u8-aapl,filtername=vodcut)')
    url = url.replace('manifest(format=m3u8-aapl-v3,filtername=vodcut)','QualityLevels('+q_lvl+')/Manifest(video,format=m3u8-aapl-v3,audiotrack=audio_en_0,filtername=vodcut)')                       
    
    
    menu_name = item['title']
    name = menu_name                
    info = item['info']     
    # Highlight active streams   
    start_time = item['start']
    current_time =  datetime.utcnow().strftime('%Y%m%d-%H%M')   

    length = 0
    try:     
        length = int(item['length'])
    except:
        pass

    my_time = int(current_time[0:8]+current_time[9:])
    event_start = int(start_time[0:8]+start_time[9:]) 
    event_end = int(current_time[0:8]+current_time[9:])+length
    
    imgurl = "http://hdliveextra-pmd.edgesuite.net/HD/image_sports/mobile/"+item['image']+"_m50.jpg"    
   
    if url != '' and my_time >= event_start and my_time <= event_end:           
        url = url + "|User-Agent=" + USER_AGENT
        menu_name = '[COLOR=FF00B7EB]'+menu_name+'[/COLOR]'
        addLink(menu_name,url,name,imgurl,FANART) 
    else:
        try:
            start_date = datetime.strptime(start_time, "%Y%m%d-%H%M")
        except TypeError:
            start_date = datetime.fromtimestamp(time.mktime(time.strptime(start_time, "%Y%m%d-%H%M")))
        
        start_date = datetime.strftime(utc_to_local(start_date),xbmc.getRegion('dateshort')+' '+xbmc.getRegion('time').replace('%H%H','%H').replace(':%S',''))       
        addDir('[COLOR=FFFFB266]'+menu_name + '[/COLOR] ' + start_date,'/disabled',999,imgurl,FANART,None,False)


def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def addLink(name,url,title,iconimage,fanart):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage,)
 
    liz.setProperty('fanart_image',fanart)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    liz.setInfo( type="Video", infoLabels={ "plotoutline": "TEST 123" } )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
    return ok


def addDir(name,url,mode,iconimage,fanart=None,scrape_type=None,isFolder=True): 
    params = get_params()      
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&scrape_type="+urllib.quote_plus(str(scrape_type))
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    liz.setProperty('fanart_image', fanart)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isFolder)    
    return ok


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


params=get_params()
url=None
name=None
mode=None
scrape_type=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass
try:
    scrape_type=urllib.unquote_plus(params["scrape_type"])
except:
    pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)
print "scrape_type:"+str(scrape_type)


if mode==None or url==None or len(url)<1:
        #print ""                
        CATEGORIES()        
elif mode==1:        
        LIVE()
elif mode==2:        
        FEATURED(url)
elif mode==3:        
        GET_ALL_SPORTS()
elif mode==4:
        SCRAPE_VIDEOS(url,scrape_type)

xbmcplugin.endOfDirectory(addon_handle)
