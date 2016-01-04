import sys
import xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
import urllib, urllib2, httplib2
import json
import HTMLParser
import calendar
from datetime import datetime, timedelta
import time
import cookielib
import base64
#import string, random
from resources.globals import *
from resources.providers.adobe import ADOBE
from resources.providers.charter import CHARTER
from resources.providers.comcast import COMCAST
from resources.providers.dish import DISH
from resources.providers.direct_tv import DIRECT_TV
from resources.providers.twc import TWC
from resources.providers.verizon import VERIZON
from resources.providers.cable_one import CABLE_ONE
from resources.providers.optimum import OPTIMUM
from resources.providers.cox import COX
from resources.providers.bright_house import BRIGHT_HOUSE


def CATEGORIES():           
    addDir('Live & Upcoming','/live',1,ICON,FANART)
    addDir('Featured',ROOT_URL+'mcms/prod/nbc-featured.json',2,ICON,FANART)
    addDir('On NBC Sports','/replays',3,ICON,FANART)


def LIVE_AND_UPCOMING():      
    #LIVE        
    SCRAPE_VIDEOS(ROOT_URL+'mcms/prod/nbc-live-ios.json')
    #UPCOMING
    SCRAPE_VIDEOS(ROOT_URL+'mcms/prod/nbc-upcoming-ios.json')


def GET_ALL_SPORTS():    
    req = urllib2.Request(ROOT_URL+'configuration-liveextra-ios.json')    
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
    #print url
    req = urllib2.Request(url)
    #req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36')
    req.add_header('Connection', 'keep-alive')
    req.add_header('Accept', '*/*')
    req.add_header('User-Agent', UA_NBCSN)
    req.add_header('Accept-Language', 'en-us')
    req.add_header('Accept-Encoding', 'gzip, deflate')
    

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
        try:
            if item['videoSources']:
                if 'iosStreamUrl' in item['videoSources'][0]:
                    url =  item['videoSources'][0]['iosStreamUrl']
                    if CDN == 1 and item['videoSources'][0]['backupUrl'] != '':
                        url = item['backupUrl']
        except:
            pass
        pass
    
    #Set quality level based on user settings    
    #url = SET_STREAM_QUALITY(url)                      
    
    
    menu_name = item['title']
    name = menu_name                
    desc = item['info']     
    free = int(item['free'])
    if 'Watch Golf Channel LIVE' in name:
        free = 1

    # Highlight active streams   
    start_time = item['start']
    pattern = "%Y%m%d-%H%M"
    current_time =  datetime.utcnow().strftime(pattern) 
    my_time = int(time.mktime(time.strptime(current_time, pattern)))     

    #string (2008-12-07)
    aired = start_time[0:4]+'-'+start_time[4:6]+'-'+start_time[6:8]
    genre = item['sportName']
    

    length = 0
    try:
        length = int(item['length'])
    except:        
        pass
    

    event_start = int(time.mktime(time.strptime(start_time, pattern)))
    if length != 0:
        event_end = int(event_start + length)
    else:
        #Default to 24 hours if length not provided        
        event_end = int(event_start + 86400)

    #Allow access to stream 10 minutes early
    event_start = event_start - (10*60)

    #Allow access to stream an hour after it's supposed to end
    event_end = event_end + (60*60)
    
    
    #print url
    #print name + str(length) + " " + str(event_start) + " " + str(my_time) + " " + str(event_end) + " " + url + " FREE:" + str(free)
        
    info = {'plot':desc,'tvshowtitle':'NBCSN','title':name,'originaltitle':name,'duration':length,'aired':aired,'genre':genre}
    
    imgurl = "http://hdliveextra-pmd.edgesuite.net/HD/image_sports/mobile/"+item['image']+"_m50.jpg"    
    menu_name = filter(lambda x: x in string.printable, menu_name)
    #and (mode != 1 or (my_time >= event_start and my_time <= event_end) or 'Watch Golf Channel LIVE' in name)
    #if url != '' and (mode != 1 or (my_time >= event_start and my_time <= event_end) or 'Watch Golf Channel LIVE' in name):           
    try:
        start_date = datetime.strptime(start_time, "%Y%m%d-%H%M")
    except TypeError:
        start_date = datetime.fromtimestamp(time.mktime(time.strptime(start_time, "%Y%m%d-%H%M")))

    start_date = datetime.strftime(utc_to_local(start_date),xbmc.getRegion('dateshort')+' '+xbmc.getRegion('time').replace('%H%H','%H').replace(':%S',''))       
    info['plot'] = 'Starting at: '+start_date+'\n\n'+info['plot']

    
    if url != '':
        if free:
            menu_name = '[COLOR='+FREE+']'+menu_name + '[/COLOR]'
            #addLink(menu_name,url,name,imgurl,FANART,info) 
            if str(PLAY_MAIN) == 'true':
                addFreeLink(menu_name,url,imgurl,FANART,None,info)              
            else:
                addDir(menu_name,url,6,imgurl,FANART,None,True,info)             
        elif FREE_ONLY == 'false':                        
            menu_name = '[COLOR='+LIVE+']'+menu_name + '[/COLOR]'
            if str(PLAY_MAIN) == 'true':
                addPremiumLink(menu_name,url,imgurl,FANART,None,info)             
            else:
                addDir(menu_name,url,5,imgurl,FANART,None,True,info)             

    elif my_time < event_start:
        if free:
            menu_name = '[COLOR='+FREE_UPCOMING+']'+menu_name + '[/COLOR]'            
            if str(PLAY_MAIN) == 'true':
                addPremiumLink(menu_name,url,imgurl,FANART,None,info)             
            else:
                addDir(menu_name + ' ' + start_date,'/disabled',999,imgurl,FANART,None,False,info)
            
        elif FREE_ONLY == 'false':
            menu_name = '[COLOR='+UPCOMING+']'+menu_name + '[/COLOR]'            
            addDir(menu_name + ' ' + start_date,'/disabled',999,imgurl,FANART,None,False,info)

        
    

    
def SIGN_STREAM(stream_url, stream_name, stream_icon):   
    print "MSO ID === "+  MSO_ID    
    provider = None
    if MSO_ID == 'Dish':
        provider = DISH()
    elif MSO_ID == 'TWC':
        provider = TWC()
    elif MSO_ID == 'Comcast_SSO':
        provider = COMCAST()
    elif MSO_ID == 'DTV':
        provider = DIRECT_TV()
    elif MSO_ID == 'Charter_Direct':
        provider = CHARTER()
    elif MSO_ID == 'Verizon':
        provider = VERIZON()
    elif MSO_ID == 'auth_cableone_net':
        provider = CABLE_ONE()
    elif MSO_ID == 'Cablevision':
        provider = OPTIMUM()
    elif MSO_ID == 'Cox':
        provider = COX()
    elif MSO_ID == 'Brighthouse':
        provider = BRIGHT_HOUSE()

    #provider = SET_PROVIDER()

    if provider != None:
        #stream_url = AUTHORIZE_STREAM(provider)
        
        adobe = ADOBE()
        expired_cookies = True
        try:
            cj = cookielib.LWPCookieJar()
            cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
            
            for cookie in cj:                
                if cookie.name == 'BIGipServerAdobe_Pass_Prod':
                    print cookie.name
                    print cookie.expires
                    print cookie.is_expired()
                    expired_cookies = cookie.is_expired()
        except:
            pass

        auth_token_file = os.path.join(ADDON_PATH_PROFILE, 'auth.token')  
        last_provider = ''
        fname = os.path.join(ADDON_PATH_PROFILE, 'provider.info')
        if os.path.isfile(fname):                
            provider_file = open(fname,'r') 
            last_provider = provider_file.readline()
            provider_file.close()

        print "Did cookies expire? " + str(expired_cookies)
        print "Does the auth token file exist? " + str(os.path.isfile(auth_token_file))
        print "Does the last provider match the current provider? " + str(last_provider == MSO_ID)
        print "Who was the last provider? " +str(last_provider)
                
        resource_id = GET_RESOURCE_ID()    
        signed_requestor_id = GET_SIGNED_REQUESTOR_ID() 


        #If cookies are expired or auth token is not present run login or provider has changed
        if expired_cookies or not os.path.isfile(auth_token_file) or (last_provider != MSO_ID):
            #saml_request, relay_state, saml_submit_url = adobe.GET_IDP()            
            var_1, var_2, var_3 = provider.GET_IDP()            
            saml_response, relay_state = provider.LOGIN(var_1, var_2, var_3)
            #Error logging in. Abort! Abort!
            print "SAML RESPONSE:"
            print saml_response
            print "RELAY STATE:"
            print relay_state

            if saml_response == '' and relay_state == '':
                msg = "Please verify that your username and password are correct"
                dialog = xbmcgui.Dialog() 
                ok = dialog.ok('Login Failed', msg)
                return
            elif saml_response == 'captcha':
                msg = "Login requires captcha. Please try again later"
                dialog = xbmcgui.Dialog() 
                ok = dialog.ok('Captcha Found', msg)
                return

            adobe.POST_ASSERTION_CONSUMER_SERVICE(saml_response,relay_state)
            adobe.POST_SESSION_DEVICE(signed_requestor_id)    


        authz = adobe.POST_AUTHORIZE_DEVICE(resource_id,signed_requestor_id)      
        

        if 'Authorization failed' in authz or authz == '':
            msg = "Failed to authorize"
            dialog = xbmcgui.Dialog() 
            ok = dialog.ok('Authorization Failed', msg)
            #Delete the invalid auth.token file
            fname = os.path.join(ADDON_PATH_PROFILE, 'auth.token')
            os.remove(fname)
        else:
            media_token = adobe.POST_SHORT_AUTHORIZED(signed_requestor_id,authz)
            stream_url = adobe.TV_SIGN(media_token,resource_id, stream_url)
            #Set quality level based on user settings    
            stream_url = SET_STREAM_QUALITY(stream_url)   
            
            listitem = xbmcgui.ListItem(path=stream_url)
            
            print "PLAY FROM MAIN!!!!"
            print str(PLAY_MAIN)

            if str(PLAY_MAIN) == 'true':
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
            else:
                addLink(stream_name, stream_url, stream_name, stream_icon, FANART) 


def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def addLink(name,url,title,iconimage,fanart,info=None):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage,)
 
    liz.setProperty('fanart_image',fanart)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info) 
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok

def addFreeLink(name,link_url,iconimage,fanart=None,scrape_type=None,info=None): 
    params = get_params()      
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(link_url)+"&mode=6&icon_image="+urllib.quote_plus(iconimage)
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info)        

    liz.setProperty('fanart_image', fanart)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)    
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok

def addPremiumLink(name,link_url,iconimage,fanart=None,scrape_type=None,info=None): 
    params = get_params()      
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(link_url)+"&mode=5&icon_image="+urllib.quote_plus(iconimage)
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info)        

    liz.setProperty('fanart_image', fanart)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)    
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return ok


def addDir(name,url,mode,iconimage,fanart=None,scrape_type=None,isFolder=True,info=None): 
    params = get_params()      
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&scrape_type="+urllib.quote_plus(str(scrape_type))+"&icon_image="+urllib.quote_plus(str(iconimage))
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info)        

    liz.setProperty('fanart_image', fanart)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isFolder)    
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
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
icon_image = None

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
try:
    icon_image=urllib.unquote_plus(params["icon_image"])
except:
    pass


print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)
print "scrape_type:"+str(scrape_type)
print "icon image:"+str(icon_image)


if mode==None or url==None or len(url)<1:        
        CATEGORIES()        
elif mode==1:        
        LIVE_AND_UPCOMING()                     
elif mode==2:        
        FEATURED(url)
elif mode==3:        
        GET_ALL_SPORTS()
elif mode==4:
        SCRAPE_VIDEOS(url,scrape_type)
elif mode==5:
        if USERNAME != '' and PASSWORD != '':
            SIGN_STREAM(url, name, icon_image)
        else:
            msg = "A valid username and password is required to view premium content"
            dialog = xbmcgui.Dialog() 
            ok = dialog.ok('Credentials Missing', msg)
            #sys.exit("Credentials not provided")
elif mode==6:
    #Set quality level based on user settings    
    stream_url = SET_STREAM_QUALITY(url) 
    listitem = xbmcgui.ListItem(path=stream_url)

    if str(PLAY_MAIN) == 'true':
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)
    else:
        addLink(name, stream_url, name, icon_image, FANART)


#Don't cache live and upcoming list
if mode==1:
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)
else:
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
