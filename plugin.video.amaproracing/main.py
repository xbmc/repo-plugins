import sys
import xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import urllib, urllib2
import json
from xml.dom.minidom import Document, parse, parseString
from datetime import datetime, date, timedelta, tzinfo
from supercross import supercross      
from motocross import motocross  
from endurocross import endurocross 
from roadracing import roadracing
from flattrack import flattrack

#import librtmp

addon_handle = int(sys.argv[1])

#Localisation
local_string = xbmcaddon.Addon(id='plugin.video.amaproracing').getLocalizedString

ROOTDIR = xbmcaddon.Addon(id='plugin.video.amaproracing').getAddonInfo('path')

ICON = ROOTDIR+"icon.png"

	
def CATEGORIES():                
    addDir('Endurocross','/ENDUROCROSS',300,ROOTDIR+'/images/icon_endurocross.png',ROOTDIR+'/images/fanart_endurocross.jpg')
    addDir('Motocross','/Motocross',109,ROOTDIR+'/images/icon_motocross.png',ROOTDIR+'/images/fanart_motocross.jpg')
    addDir('Supercross','/SUPERCROSS',200,ROOTDIR+'/images/icon_supercross.png',ROOTDIR+'/images/fanart_supercross.jpg')    
    addDir('Road Racing','/ROADRACING',400,ROOTDIR+'/images/icon_roadracing.png',ROOTDIR+'/images/fanart_roadracing.jpg')    
    addDir('Flat Track','/FLATTRACK',500,ROOTDIR+'/images/icon_flattrack.png',ROOTDIR+'/images/fanart_flattrack.jpg')    
    #addDir('DirtRider.com Videos','http://www.dirtrider.com/videos/',2,'')    



def GET_DIRTRIDER_VIDEO_LINK(url,name):
    print url
    req = urllib2.Request(url)
    req.add_header('User-Agent', ' Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36')
    response = urllib2.urlopen(req)
    video_link=response.read()
    response.close()        
    video_link = video_link.replace('\n',"")   
    
    start = video_link.find('</header>')
    end = video_link.find('<footer>',start)        
    if end < 0:
        end = len(link)    
    video_link = video_link[start:end]       

    video_link.replace(" ","")

    print video_link     
    
    #match = re.compile('<a title="(.+?)" href="(.+?)"><img width="180" height="135" src="(.+?)" class="attachment-thumb-180x135 wp-post-image" alt="').findall(video_link)  
    match = re.compile('<h3><a title="(.+?)" href="(.+?)">').findall(video_link)  
    

    #Go each links page and retrieve the embedcode     
    for title,link in match:                   
        print "LINK ==="+link
        req = urllib2.Request(link)
        req.add_header('User-Agent', ' Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36')
        response = urllib2.urlopen(req)
        video_link=response.read()
        response.close()        
        video_link = video_link.replace('\n',"")        

        ###############################################################################################################################################################
        #Get video image
        #ex. <meta property="og:image" content="http://www.promotocross.com/sites/default/files/images/video/thumbnail/start_450_moto_1_glenhelen_ortiz_49_1280.jpg" />
        ###############################################################################################################################################################
        start_str = '<meta property="og:image" content="'
        start = video_link.index(start_str)        
        end = video_link.index('" />',start)            
        image_link = video_link[start+len(start_str):end]                
        #print "IMAGE LINK =" +image_link
        ###############################################################################################################################################################


        #################################################################################################################################################
        #Get SWF embedcode
        #ex. <meta property="og:video" content="http://player.ooyala.com/player.swf?embedCode=45Mm8xbjpdrkHW1TKb8N-BFXJTTPunCK&amp;keepEmbedCode=true" />
        #################################################################################################################################################
        start = video_link.find('<meta property="og:video" content=')        
        end = video_link.find('keepEmbedCode=true" />',start)            
        swf_link = video_link[start:end]                
        
        start = swf_link.find('swf?embedCode=')        
        end = swf_link.find('&amp;',start) 
        embedcode = swf_link[start+14:end]                
        ##################################################################################################################################################


        app = 'ondemand?_fcs_vhost=cp58064.edgefcs.net'
        swfurl = 'http://player.ooyala.com/static/cacheable/27d91126daacf9df38e10be48dcfa3a5/player_v2.swf'    
        rtmpurl = 'rtmp://63.80.4.116/ondemand?_fcs_vhost=cp58064.edgefcs.net'                    
        pageurl = 'http://www.promotocross.com/sites/all/themes/lucasmoto2013/ooyala.php?embedCode='+embedcode
        playpath = 'mp4:/c/'+embedcode+'/DOcJ-FxaFrRg4gtDEwOjFyazowODE7G_'                           
            
        rtmp = rtmpurl + ' playpath=' + playpath + ' app=' + app + ' pageURL=' + pageurl + ' swfURL=' + swfurl             
        addLink(title,rtmp,title,image_link) 
        ####################################################################################################   

        ####################################################################################################



def PLAY(url):     
    xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(url)





def addLink(name,url,title,iconimage):
    params=get_params()
    full_name = ''
    try:
        full_name = urllib.unquote_plus(params["full_name"])
    except:
        pass 
    
    if full_name != '':
        title = full_name + ' ' + title

    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage,)
    liz.setProperty('fanart_image',iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
    return ok

def addDir(name,url,mode,iconimage,fanart=None):   
    params=get_params()
    prev_name = ''
    full_name = ''
    try:
        prev_name=urllib.unquote_plus(params["full_name"])
    except:
        pass 
    if mode > 4:
        if prev_name != '':
            full_name = prev_name + ' - ' + name
        else:
            full_name = name

    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&full_name="+urllib.quote_plus(full_name)

    year = ''
    if mode == 4:
        year = name
    else:        
        try:
            year=urllib.unquote_plus(params["year"])
        except:
            pass 

    u = u + "&year="+urllib.quote_plus(year)
    #+'&full_name='+urllib.quote_plus(full_name)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    if fanart == None:
        fanart = ROOTDIR+'/fanart.jpg'

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
year=None

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
    year=urllib.unquote_plus(params["year"])
except:
    pass

print "Mode: "+str(mode)
#print "URL: "+str(url)
print "Name: "+str(name)
print "Year:"+str(year)


if mode==None or url==None or len(url)<1:
        #print ""                
        CATEGORIES()        
 
elif mode==1:
        #print ""+url
        PLAY(url)
 
elif mode==2:
        #print ""+url
        GET_DIRTRIDER_VIDEO_LINK(url,name)

####################
#MOTOCROSS MODES    
####################    
elif mode==100:
		#print "GET_YEAR MODE!"
        motocross = motocross()
        motocross.GET_YEAR()

elif mode==101:
        motocross = motocross()
        motocross.GET_HIGHLIGHTS()

elif mode==102:        
        motocross = motocross()
        motocross.PLAY_LIVE()

elif mode==103:
        motocross = motocross()
        motocross.GET_ON_DEMAND()

elif mode==104:       
        motocross = motocross()
        motocross.GET_RACES(url,name)
elif mode==105:        
        motocross = motocross()
        motocross.GET_RACE_DAY_VIDEOS(url,name,year)
elif mode==106:        
        motocross = motocross()
        motocross.GET_VIDEO_LINK(url,name)

elif mode==107:             
    try:
        proxy_string = params['proxy'][0]
    except:
        pass   
    
    try:
        proxy_use_chunks_temp = params['proxy_for_chunks'][0]
        import json
        proxy_use_chunks=json.loads(proxy_use_chunks_temp)
    except:
        pass
    
    simpleDownloader=False
    try:
        simpleDownloader_temp = params['simpledownloader'][0]
        import json
        simpleDownloader=json.loads(simpleDownloader_temp)
    except:
        pass    
    
    maxbitrate=0
    try:
        maxbitrate =  int(params['maxbitrate'][0])
    except: 
        pass

    proxy = ''
    use_proxy_for_chunks = ''
    maxbitrate = 3450
    simpleDownloader = False      

    #player=f4mProxyHelper()
    #player.playF4mLink(url, name, proxy, use_proxy_for_chunks,maxbitrate,simpleDownloader)    

elif mode==108:
    motocross = motocross()
    endcoded_cookies = motocross.GET_COOKIE(url)
    url = url+'&'+endcoded_cookies
    
    #player=f4mProxyHelper()
    #player.playF4mLink(url, name)

elif mode==109:
    motocross = motocross()
    motocross.CATEGORIES()

####################
#SUPERCROSS MODES
####################
elif mode==200:
    supercross = supercross()
    supercross.CATEGORIES()

elif mode==201:    
    supercross = supercross()
    supercross.SUPERCROSS_YOUTUBE_CHANNEL()    

elif mode==202:    
    supercross = supercross()
    supercross.RACE_DAY_LIVE()

elif mode==203:    
    supercross = supercross()
    supercross.RACE_DAY_ARCHIVE()

####################
#ENDUROCROSS MODES
####################
elif mode==300:
    endurocross = endurocross()
    endurocross.CATEGORIES()

elif mode==301:
    endurocross = endurocross()
    endurocross.ARCHIVE(url)
    
elif mode==400:
    roadracing = roadracing()
    roadracing.ARCHIVE()

elif mode==500:
    flattrack = flattrack()
    flattrack.ARCHIVE()
xbmcplugin.endOfDirectory(addon_handle)
