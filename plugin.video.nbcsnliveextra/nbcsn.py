import sys
import xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import urllib, urllib2, httplib2
import json
import HTMLParser
import datetime

addon_handle = int(sys.argv[1])

ROOTDIR = xbmcaddon.Addon(id='plugin.video.nbcsnliveextra').getAddonInfo('path')
FANART = ROOTDIR+"/fanart.jpg"
ICON = ROOTDIR+"/icon.png"
ROOT_URL = 'http://stream.nbcsports.com/data/mobile/'

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
            for item in json_source[scrape_type]:        
                BUILD_VIDEO_LINK(item)
        except:
            pass


def BUILD_VIDEO_LINK(item):
    url = item['iosStreamUrl']    
    header = { 'Referer' : 'http://stream.golfchannel.com/?pid=15607',
               'Accept-Encoding' : 'gzip,deflate,sdch',
               'Accept-Language' : 'en-US,en;q=0.8',
               'Cookie' : 'hdntl=exp=1410035727~acl=%2f*~hmac=b3d9c10715e1c34dda7d12ab97b4258388369f094093ef21098a82ba47c92e56'}
    header_encoded = urllib.urlencode(header)
    #url =  urllib.quote_plus(url+'|')       
    #full_url = url + '|' + header_encoded 

    
    url = url.replace('manifest(format=m3u8-aapl-v3)','QualityLevels(3450000)/Manifest(video,format=m3u8-aapl-v3,audiotrack=audio_en_0)')       
    url = url.replace('manifest(format=m3u8-aapl,filtername=vodcut)','QualityLevels(3450000)/Manifest(video,format=m3u8-aapl,filtername=vodcut)')
    url = url.replace('manifest(format=m3u8-aapl-v3,filtername=vodcut)','QualityLevels(3450000)/Manifest(video,format=m3u8-aapl-v3,audiotrack=audio_en_0,filtername=vodcut)')                       
    #url = url.replace('manifest(format=m3u8-aapl,filtername=vodcut','QualityLevels(3450000)/Manifest(video,format=m3u8-aapl-v3,audiotrack=audio_en_0)')
    #http://olystreameast.nbcolympics.com/vod/4e1c7148-6803-46fc-99a4-53f18fe5be22/nbc-sports-live-extra0529140933.ism/manifest(format=m3u8-aapl,filtername=vodcut)
    #/Manifest(video,format=m3u8-aapl,filtername=vodcut)


    #http://link.theplatform.com/s/BxmELC/9oOC_waY8QXZ/file.mp4?mbr=true&manifest=m3u&feed=Mobile_Feed&format=redirect&metafile=false  
    #http://hdliveextra-vh.akamaihd.net/i/HD/video_sports/NBCU_Sports_Group_-_nbcsports/522/694/2014-06-25T00-58-33.933Z--51.934,.,__636916.,__274520.,__117733.,__382099.,mp4.csmil/index_1_av.m3u8?null=
    name = item['title']            
    menu_name = name        
    info = item['info'] 
    if info <> "":
        menu_name = menu_name + " - " + info
    
    #ex. 20140906-1600
    #datetime.datetime.utcnow().strftime('%Y%m%d-%H%M')
    
    #current_date =  datetime.datetime.utcnow().strftime('%Y%m%d-%H%M')
    #video_time = item['start']
    #print str(datetime.datetime.strptime(item['start','%Y%m%d-%H%M'))
    #print item['start']
    #print current_time
    #print video_time
    #print video_time < current_time

    #menu_name = '[COLOR=FF00B7EB]'+menu_name+'[/COLOR]'

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
#print "URL: "+str(url)
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