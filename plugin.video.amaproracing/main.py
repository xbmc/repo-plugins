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
    #addDir('Endurocross','/ENDUROCROSS',300,ROOTDIR+'/images/icon_endurocross.png',ROOTDIR+'/images/fanart_endurocross.jpg')
    addDir('Motocross','/Motocross',109,ROOTDIR+'/images/icon_motocross.png',ROOTDIR+'/images/fanart_motocross.jpg')
    addDir('Supercross','/SUPERCROSS',200,ROOTDIR+'/images/icon_supercross.png',ROOTDIR+'/images/fanart_supercross.jpg')    
    #addDir('Road Racing','/ROADRACING',400,ROOTDIR+'/images/icon_roadracing.png',ROOTDIR+'/images/fanart_roadracing.jpg')    
    #addDir('Flat Track','/FLATTRACK',500,ROOTDIR+'/images/icon_flattrack.png',ROOTDIR+'/images/fanart_flattrack.jpg')    
    #addDir('DirtRider.com Videos','http://www.dirtrider.com/videos/',2,'')    


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
img_url=None

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
try:
    img_url=urllib.unquote_plus(params["img_url"])
except:
    pass


if mode==None or url==None or len(url)<1:               
        CATEGORIES()        

####################
#MOTOCROSS MODES    
####################    
elif mode==100:		
        motocross = motocross()
        motocross.fullMotoYears()        

elif mode==101:
        motocross = motocross()
        motocross.getVideoTypes()

elif mode==102:        
        motocross = motocross()
        motocross.playLive(url)

elif mode==103:
        motocross = motocross()
        stream_url = 'http://www.promotocross.com/media-block-get-results-ajax/ajax/451/16/video/'+url+'/all/all/all/all/'
        motocross.fullMotosOnDemand(stream_url)

elif mode==106:        
        motocross = motocross()        
        url = motocross.scrapeStream(url,'','')
        motocross.playStream(url)

elif mode==107:
        motocross = motocross()
        motocross.getVOD(url)

elif mode==109:
    motocross = motocross()
    motocross.categories()


####################
#SUPERCROSS MODES
####################
elif mode==200:
    supercross = supercross()
    supercross.categories()

elif mode==201:    
    supercross = supercross()
    supercross.getYoutubeChannel()    

elif mode==202:    
    supercross = supercross()
    supercross.raceDayLive()

elif mode==203:    
    supercross = supercross()
    supercross.raceDayArchive()

elif mode==204:      
    event_id=urllib.unquote_plus(params["event_id"])
    owner_id=urllib.unquote_plus(params["owner_id"])

    supercross = supercross()
    supercross.getLiveStream(name,owner_id,event_id)


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
