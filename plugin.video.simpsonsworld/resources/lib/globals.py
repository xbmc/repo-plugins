import sys, os
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import urllib, urllib2
import json
import base64
from adobepass.adobe import ADOBE



addon_handle = int(sys.argv[1])
ADDON = xbmcaddon.Addon()
ROOTDIR = ADDON.getAddonInfo('path')

FANART = os.path.join(ROOTDIR,"resources/media/fanart.jpg")
ICON = os.path.join(ROOTDIR,"resources/media/icon.png")


#Addon Settings 
RATIO = str(ADDON.getSetting(id="ratio"))
COMMENTARY = str(ADDON.getSetting(id="commentary"))
LOCAL_STRING = ADDON.getLocalizedString

RESOURCE_ID = "<rss version='2.0'><channel><title>fx</title></channel></rss>"
UA_FX = 'FXNOW/562 CFNetwork/711.4.6 Darwin/14.0.0'

#Add-on specific Adobepass variables
SERVICE_VARS = {'app_version': 'Fire TV',
                'device_type':'firetv',             
                'private_key':'B081JNlGKn1ZqpQH',
                'public_key':'Dy1OhW3HrWk03QJrMMIULAmUdPQqk2Ds',
                'registration_url':'fxnetworks.com/activate',
                'requestor_id':'fx',
                'resource_id':urllib.quote(RESOURCE_ID)
               }

art_root = 'http://thetvdb.com/banners/seasons/'
season_art = {'1':'71663-1-16.jpg',
            '2':'71663-2-15.jpg',
            '3':'71663-3-15.jpg',
            '4':'71663-4-16.jpg',
            '5':'71663-5-16.jpg',
            '6':'71663-6-15.jpg',
            '7':'71663-7-14.jpg',
            '8':'71663-8-14.jpg',
            '9':'71663-9-15.jpg',
            '10':'71663-10-15.jpg',
            '11':'71663-11-14.jpg',
            '12':'71663-12-10.jpg',
            '13':'71663-13-13.jpg',
            '14':'71663-14-13.jpg',
            '15':'71663-15-10.jpg',
            '16':'71663-16-11.jpg',
            '17':'71663-17-11.jpg',
            '18':'71663-18-10.jpg',
            '19':'71663-19-8.jpg',
            '20':'71663-20-11.jpg',
            '21':'71663-21-11.jpg',
            '22':'71663-22-9.jpg',
            '23':'71663-23-9.jpg',
            '24':'71663-24-4.jpg',
            '25':'71663-25-3.jpg',
            '26':'71663-26.jpg',
            '27':'71663-27-2.jpg',
            '28':'71663-28.jpg',
            }


def listSeasons():       
    for x in range(1, 29):
        title = "Season "+str(x)
        url = str(x)
        #icon = 'http://thetvdb.com/banners/seasons/71663-'+str(x)+'-15.jpg'
        #icon = 'http://thetvdb.com/banners/seasonswide/71663-'+str(x)+'.jpg'        
        #icon = 'http://thetvdb.com/banners/seasons/71663-'+str(x)+'.jpg'
        icon = art_root+season_art[str(x)]

        addSeason(title,url,101,icon,FANART)


def listEpisodes(season):    
    url = "http://fapi2.fxnetworks.com/androidtv/videos?filter%5Bfapi_show_id%5D=9aad7da1-093f-40f5-b371-fec4122f0d86&filter%5Bseason%5D="+season+"&limit=500&filter%5Btype%5D=episode"    
    req = urllib2.Request(url)
    req.add_header("Connection", "keep-alive")
    req.add_header("Accept", "*/*")
    req.add_header("Accept-Encoding", "deflate")
    req.add_header("Accept-Language", "en-us")
    req.add_header("Connection", "keep-alive")
    req.add_header("Authentication", "androidtv:a4y4o0e01jh27dsyrrgpvo6d1wvpravc2c4szpp4")
    req.add_header("User-Agent", UA_FX)
    response = urllib2.urlopen(req)   
    json_source = json.load(response)                       
    response.close() 
    
    #for episode in reversed(json_source['videos']):            
    for episode in sorted(json_source['videos'], key=lambda k: k['episode']):
        title = episode['name']
        #Default video type is 16x9
        url = episode['video_urls']['16x9']['en_US']['video_url']         
        try: url = episode['video_urls'][RATIO]['en_US']['video_url']
        except: pass
        if COMMENTARY == 'true':
            try: url = episode['video_urls'][RATIO]['en_US']['video_url_commentary']
            except: pass
        icon = episode['img_url']
        desc = episode['description']
        duration = episode['duration']
        aired = episode['airDate']
        season = str(episode['season']).zfill(2) 
        episode = str(episode['episode']).zfill(2)         

        info = {'plot':desc,'tvshowtitle':LOCAL_STRING(30000), 'season':season, 'episode':episode, 'title':title,'originaltitle':title,'duration':duration,'aired':aired,'genre':LOCAL_STRING(30002)}
        
        addEpisode(title,url,title,icon,FANART,info)



def getStream(url):
    adobe = ADOBE(SERVICE_VARS)            
    if adobe.checkAuthN():
        if adobe.authorize():
            media_token = adobe.mediaToken()       
            url = url + "&auth="+urllib.quote(base64.b64decode(media_token))
            req = urllib2.Request(url)
            req.add_header("Accept", "*/*")
            req.add_header("Accept-Encoding", "deflate")
            req.add_header("Accept-Language", "en-us")
            req.add_header("Connection", "keep-alive")        
            req.add_header("User-Agent", UA_FX)
            response = urllib2.urlopen(req)              
            response.close() 

            #get the last url forwarded to
            stream_url = response.geturl()
            stream_url = stream_url + '|User-Agent=okhttp/3.4.1'            
            listitem = xbmcgui.ListItem(path=stream_url)
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem)
        else:
            sys.exit()
    else:
        #msg = 'Your device\'s is not currently authorized to view the selected content.\n Would you like to authorize this device now?'
        dialog = xbmcgui.Dialog() 
        answer = dialog.yesno(LOCAL_STRING(30911), LOCAL_STRING(30910))
        if answer:
            adobe.registerDevice()
            getStream(url)
        else:
            sys.exit()


def deauthorize():
    adobe = ADOBE(SERVICE_VARS)
    adobe.deauthorizeDevice()
    dialog = xbmcgui.Dialog()      
    dialog.notification(LOCAL_STRING(30900), LOCAL_STRING(30901), '', 5000, False)  
        

def addEpisode(name,link_url,title,iconimage,fanart,info=None):
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(link_url)+"&mode="+str(102)
    liz=xbmcgui.ListItem(name)
    liz.setArt({'icon': ICON, 'thumb': iconimage, 'fanart': fanart})    
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title, 'mediatype': 'episode' } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info) 
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    xbmcplugin.setContent(addon_handle, 'tvshows')    
    return ok


def addSeason(name,url,mode,iconimage,fanart=None,info=None): 
    params = get_params()      
    ok=True    
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    liz=xbmcgui.ListItem(name)
    liz.setArt({'icon': ICON, 'thumb': iconimage, 'fanart': fanart})
    liz.setInfo( type="Video", infoLabels={ 'Title': name, 'tvdb_id': '71663', 'mediatype': 'season' } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info)     
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)    
    xbmcplugin.setContent(addon_handle, 'tvshows')
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