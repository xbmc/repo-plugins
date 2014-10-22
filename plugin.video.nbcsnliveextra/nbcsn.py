import sys
import xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import urllib, urllib2, httplib2
import json
import HTMLParser
import datetime

addon_handle = int(sys.argv[1])
ROOTDIR = xbmcaddon.Addon(id='plugin.video.nbcsnliveextra').getAddonInfo('path')

#Settings
settings = xbmcaddon.Addon(id='plugin.video.nbcsnliveextra')

FANART = ROOTDIR+"/fanart.jpg"
ICON = ROOTDIR+"/icon.png"
ROOT_URL = 'http://stream.nbcsports.com/data/mobile/'


#Main settings
QUALITY = int(settings.getSetting(id="quality"))

def CATEGORIES():                
    addDir('Live & Upcoming','/live',1,ICON,FANART)
    addDir('Featured',ROOT_URL+'featured-2013.json',2,ICON,FANART)
    addDir('On NBC Sports','/replays',3,ICON,FANART)

def LIVE():                
    #LIVE    
    SCRAPE_VIDEOS(ROOT_URL+'live.json')
    #UPCOMING
    SCRAPE_VIDEOS(ROOT_URL+'upcoming.json')

def GET_ALL_SPORTS():
    req = urllib2.Request(ROOT_URL+'configuration-2013.json')
    req.add_header('User-Agent', 'NBCSports/742 CFNetwork/672.0.8 Darwin/14.0.0')
    response = urllib2.urlopen(req)   
    json_source = json.load(response)                       
    response.close()    

    try:
        for item in json_source['sports']:        
            code = item['code']
            name = item['name']                  
            addDir(name,ROOT_URL+code+'.json',4,ICON,FANART,'ALL')
    except:
        pass

def FEATURED():
    addDir('Full Replays',ROOT_URL+'featured-2013.json',4,ICON,FANART,"replay")
    addDir('Showcase',ROOT_URL+'featured-2013.json',4,ICON,FANART,"showCase")
    addDir('Spotlight',ROOT_URL+'featured-2013.json',4,ICON,FANART,"spotlight") 


def SCRAPE_VIDEOS(url,scrape_type=None):            
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'NBCSports/742 CFNetwork/672.0.8 Darwin/14.0.0')
    response = urllib2.urlopen(req)   
    json_source = json.load(response)                       
    response.close()            

    if scrape_type == None:
        #LIVE
        try:       
            for item in json_source:                         
                BUILD_VIDEO_LINK(item)
        except:
            pass

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
    url = item['iosStreamUrl']  
    ##################################################################
    # Inject login cookie - NOT USED CURRENTLY
    ##################################################################
    header = { 'Referer' : 'http://stream.golfchannel.com/?pid=15607',
               'Accept-Encoding' : 'gzip,deflate,sdch',
               'Accept-Language' : 'en-US,en;q=0.8',
               'Cookie' : 'hdntl=exp=1410035727~acl=%2f*~hmac=b3d9c10715e1c34dda7d12ab97b4258388369f094093ef21098a82ba47c92e56'}
    #header_encoded = urllib.urlencode(header)
    #url =  urllib.quote_plus(url+'|')       
    #full_url = url + '|' + header_encoded 
    ##################################################################

    
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
        q_lvl_golf = "4296k"
    
    url = url.replace('manifest(format=m3u8-aapl-v3)','QualityLevels('+q_lvl+')/Manifest(video,format=m3u8-aapl-v3,audiotrack=audio_en_0)')       
    url = url.replace('manifest(format=m3u8-aapl,filtername=vodcut)','QualityLevels('+q_lvl+')/Manifest(video,format=m3u8-aapl,filtername=vodcut)')
    url = url.replace('manifest(format=m3u8-aapl-v3,filtername=vodcut)','QualityLevels('+q_lvl+')/Manifest(video,format=m3u8-aapl-v3,audiotrack=audio_en_0,filtername=vodcut)')                       
    url = url.replace('golfx/master.m3u8','golfx/'+q_lvl_golf+'/prog.m3u8')       
    
    name = item['title']            
    menu_name = name        
    info = item['info'] 
    if info <> "":         
        menu_name = menu_name + " - " + info 
    
    # Highlight active streams
    current_time =  datetime.datetime.utcnow().strftime('%Y%m%d-%H%M')    
    start_time = item['start']
    length = int(item['length'])
    my_time = int(current_time[0:8]+current_time[9:])
    event_start = int(start_time[0:8]+start_time[9:]) 
    event_end = int(current_time[0:8]+current_time[9:])+length

    if my_time >= event_start and my_time <= event_end:
        menu_name = '[COLOR=FF00B7EB]'+menu_name+'[/COLOR]'
    

    imgurl = "http://hdliveextra-pmd.edgesuite.net/HD/image_sports/mobile/"+item['image']+"_m50.jpg"    
    addLink(menu_name,url,name,imgurl,FANART) 


def LOGIN():
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'NBCSports/742 CFNetwork/672.0.8 Darwin/14.0.0')
    response = urllib2.urlopen(req)   
    json_source = json.load(response)                       
    response.close()  

def addLink(name,url,title,iconimage,fanart):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage,)
 
    liz.setProperty('fanart_image',fanart)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    liz.setInfo( type="Video", infoLabels={ "plotoutline": "TEST 123" } )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
    return ok

def addDir(name,url,mode,iconimage,fanart=None,scrape_type=None): 
    params = get_params()      
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&scrape_type="+urllib.quote_plus(str(scrape_type))
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    liz.setProperty('fanart_image', fanart)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)    
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
        FEATURED()
elif mode==3:        
        GET_ALL_SPORTS()
elif mode==4:
        SCRAPE_VIDEOS(url,scrape_type)

xbmcplugin.endOfDirectory(addon_handle)
