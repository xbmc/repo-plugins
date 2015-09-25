import sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import re, os, time
from datetime import datetime, timedelta
import urllib, urllib2
import json
import calendar

addon_handle = int(sys.argv[1])

#Localisation
local_string = xbmcaddon.Addon(id='plugin.video.livestream').getLocalizedString
ROOTDIR = xbmcaddon.Addon(id='plugin.video.livestream').getAddonInfo('path')
ICON = ROOTDIR+"/icon.png"
FANART = ROOTDIR+"/fanart.jpg"
IPHONE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12F70 Safari/600.1.4'
SEARCH_HITS = '25'
    
def CATEGORIES():                    
    addDir('Live & Upcoming','/livestream',100,ICON,FANART)
    addDir('Search','/search',102,ICON,FANART)
    #addDir('Search Live','/search',102,ICON,FANART)
    #addDir('Search Archive','/search',103,ICON,FANART)
     

def LIST_STREAMS():
    live_streams = []
    upcoming_streams = []
    url = 'http://api.new.livestream.com/curated_events?page=1&maxItems=500'
    req = urllib2.Request(url)
    req.add_header('User-Agent', IPHONE_UA)              
    response = urllib2.urlopen(req)      
    json_source = json.load(response)
    response.close()

    for event in json_source['data']: 
        try:           
            event_id = str(event['id'])
            owner_id = str(event['owner_account_id'])

            owner_name = name = event['owner']['full_name'].encode('utf-8')
            full_name = event['full_name'].encode('utf-8')
            name = owner_name + ' - ' + full_name
            icon = event['logo']['url']

            #2013-03-26T14:28:00.000Z
            pattern = "%Y-%m-%dT%H:%M:%S.000Z"
            start_time = str(event['start_time'])
            end_time =  str(event['end_time'])
            current_time =  datetime.utcnow().strftime(pattern) 
            my_time = int(time.mktime(time.strptime(current_time, pattern)))             
            event_end = int(time.mktime(time.strptime(end_time, pattern)))

            length = 0
            try:
                length = int(item['duration'])
            except:        
                pass

            print start_time         
            aired = start_time[0:4]+'-'+start_time[5:7]+'-'+start_time[8:10]
            print aired

            info = {'plot':'','tvshowtitle':'Livestream','title':name,'originaltitle':name,'duration':length,'aired':aired}
            
            if event['in_progress']:
                name = '[COLOR=FF00B7EB]'+name+'[/COLOR]'
                live_streams.append([name,icon,event_id,owner_id,info])
            else:

                if my_time < event_end:                
                    start_date = datetime.fromtimestamp(time.mktime(time.strptime(start_time, pattern)))    
                    start_date = datetime.strftime(utc_to_local(start_date),xbmc.getRegion('dateshort')+' '+xbmc.getRegion('time').replace('%H%H','%H').replace(':%S',''))
                    info['plot'] = "Starting at: "+str(start_date)
                    #name = name + ' ' + start_date
                    upcoming_streams.append([name,icon,event_id,owner_id,info])
        except:
            pass

    
    for stream in  sorted(live_streams, key=lambda tup: tup[0]):        
        addStream(stream[0],'/live_now',stream[0],stream[1],FANART,stream[2],stream[3],stream[4])    
        #addStream(name,link_url,title,iconimage,fanart=None,event_id=None,owner_id=None,info=None)        


    for stream in  sorted(upcoming_streams, key=lambda tup: tup[0]):
        addDir(stream[0],'/live_now',101,stream[1],FANART,stream[2],stream[3],stream[4])            
    


def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)

def SEARCH():
    '''
    POST http://7kjecl120u-2.algolia.io/1/indexes/*/queries HTTP/1.1
    Host: 7kjecl120u-2.algolia.io
    Connection: keep-alive
    Content-Length: 378
    X-Algolia-Application-Id: 7KJECL120U
    Origin: http://livestream.com
    X-Algolia-API-Key: 98f12273997c31eab6cfbfbe64f99d92
    User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36
    Content-type: application/json
    Accept: */*
    Referer: http://livestream.com/watch
    Accept-Encoding: gzip, deflate
    Accept-Language: en-US,en;q=0.8
    {"requests":[{"indexName":"events","params":"query=summ&hitsPerPage=3"},{"indexName":"accounts","params":"query=summ&hitsPerPage=3"},{"indexName":"videos","params":"query=summ&hitsPerPage=3"},{"indexName":"images","params":"query=summ&hitsPerPage=3"},{"indexName":"statuses","params":"query=summ&hitsPerPage=3"}],"apiKey":"98f12273997c31eab6cfbfbe64f99d92","appID":"7KJECL120U"}

    POST http://7kjecl120u-1.algolia.io/1/indexes/*/queries HTTP/1.1
    Host: 7kjecl120u-1.algolia.io
    Connection: keep-alive
    Content-Length: 258
    X-Algolia-Application-Id: 7KJECL120U
    Origin: http://livestream.com
    X-Algolia-API-Key: 98f12273997c31eab6cfbfbe64f99d92
    User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.93 Safari/537.36
    Content-type: application/json
    Accept: */*
    Referer: http://livestream.com/watch
    Accept-Encoding: gzip, deflate
    Accept-Language: en-US,en;q=0.8

    {"requests":[{"indexName":"events","params":"query=test&hitsPerPage=3"},{"indexName":"accounts","params":"query=test&hitsPerPage=3"},{"indexName":"videos","params":"query=test&hitsPerPage=3"}],"apiKey":"98f12273997c31eab6cfbfbe64f99d92","appID":"7KJECL120U"}
    '''
    search_txt = ''
    dialog = xbmcgui.Dialog()
    search_txt = dialog.input('Enter search text', type=xbmcgui.INPUT_ALPHANUM)

    json_source = ''

    if search_txt != '':

        url = 'http://7kjecl120u-1.algolia.io/1/indexes/*/queries'
        req = urllib2.Request(url)
        req.addheaders = [ ("Accept", "*/*"),
                            ("Origin", "http://livestream.com"),
                            ("Accept-Language", "en-US,en;q=0.8"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("X-Algolia-Application-Id", "7KJECL120U"),
                            ("X-Algolia-API-Key", "98f12273997c31eab6cfbfbe64f99d92"),
                            ("Content-type", "application/json"),
                            ("Connection", "keep-alive"),
                            ("Referer", "http://livestream.com/watch"),
                            ("User-Agent",'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36')]                
        
        
        json_search = '{"requests":[{"indexName":"events","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"accounts","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"videos","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"}],"apiKey":"98f12273997c31eab6cfbfbe64f99d92","appID":"7KJECL120U"}'
        #json_search = '{"requests":[{"indexName":"events","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"accounts","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"videos","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"images","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"statuses","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"}],"apiKey":"98f12273997c31eab6cfbfbe64f99d92","appID":"7KJECL120U"}'

        response = urllib2.urlopen(req,json_search)
        json_source = json.load(response)
        #print json_source
        response.close()


    return json_source


def SEARCH_LIVE():
    json_source = SEARCH()
    if json_source != '':
        i = 0
        
        for hits in json_source['results']: 
            i = i + 1
            if i == 1:
                addDir('[B][I]Events[/B][/I]','/accounts',999,ICON,FANART)
            elif i == 2:
                addDir('[B][I]Accounts[/B][/I]','/accounts',999,ICON,FANART)
            elif i == 3:
                addDir('[B][I]Videos[/B][/I]','/accounts',999,ICON,FANART)

            for event in hits['hits']:                
                try:                                         
                                       
                    #icon = event['logo']['thumbnail']['url']  
                    if i != 2:
                        owner_id = str(event['owner_account_id'])                        

                        if i == 1:
                            #Events
                            name = event['full_name'].encode('utf-8') 
                            name = event['owner_account_full_name'].encode('utf-8') + ' - ' + name
                            event_id = str(event['id'])
                            icon = event['logo']['large']['url']
                            start_time = str(event['start_time'])                        
                        elif i == 3:
                            #Videos
                            name = event['owner_account_full_name'].encode('utf-8') + ' - ' + event['caption'].encode('utf-8')
                            event_id = str(event['owner_event_id'])
                            icon = event['thumbnail']['large']['url']
                            start_time = str(event['publish_at'])                        
                        
                        
                        duration = 0
                        try:
                            duration = int(item['duration'])
                        except:        
                            pass

                        print name
                        #print start_time         
                        aired = start_time[0:4]+'-'+start_time[5:7]+'-'+start_time[8:10]
                        #print aired

                        info = {'plot':'','tvshowtitle':'Livestream','title':name,'originaltitle':name,'duration':duration,'aired':aired}

                        #addDir(name,'/live_now',101,icon,FANART,event_id,owner_id)
                        addStream(name,'/live_now',name,icon,FANART,event_id,owner_id)
                    else:
                        #Accounts
                        name = event['full_name'].encode('utf-8') 
                        owner_id = str(event['id'])
                        icon = event['picture']['large']['url']
                        addDir(name,'/accounts',105,icon,FANART,None,owner_id)
                except:
                    pass
            
           

def SEARCH_ARCHIVE():
    json_source = SEARCH()
    if json_source != '':
        for hits in json_source['results']: 
            for event in hits['hits']:       
                try:         
                    owner_id = str(event['id'])
                    url = 'http://new.livestream.com/api/accounts/'+owner_id
                    json_source = GET_JSON_FILE(url)
                    #Load all past events            
                    for past_event in json_source['past_events']['data']:            
                        name = past_event['full_name']
                        icon = past_event['logo']['url']
                        event_id = str(past_event['id'])

                        start_time = str(past_event['start_time'])                        
                        duration = 0
                        try:
                            duration = int(item['duration'])
                        except:        
                            pass

                        print start_time         
                        aired = start_time[0:4]+'-'+start_time[5:7]+'-'+start_time[8:10]
                        print aired

                        info = {'plot':'','tvshowtitle':'Livestream','title':name,'originaltitle':name,'duration':duration,'aired':aired}
                        
                        addStream(name,'/archive',name,icon,FANART,event_id,owner_id,info)
                except:
                    pass
            

def GET_JSON_FILE(url):
    req = urllib2.Request(url) 
    req.add_header('User-Agent', ' Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36')     
    response = urllib2.urlopen(req)            
    json_source = json.load(response)
    response.close()  

    return json_source


def GET_STREAM(owner_id,event_id,icon): 
    stream_url = []
    stream_title = [] 
    try:
        url = 'http://api.new.livestream.com/accounts/'+owner_id+'/events/'+event_id+'/viewing_info'
        req = urllib2.Request(url)       
        req.add_header('User-Agent', IPHONE_UA)
        try:
            response = urllib2.urlopen(req)                    
            json_source = json.load(response)
            response.close()        
            m3u8_url = json_source['streamInfo']['m3u8_url']            
        except:
            url = 'http://livestream.com/api/accounts/'+owner_id+'/events/'+event_id+'/feed.json?&filter=video'                
            req = urllib2.Request(url)       
            req.add_header('User-Agent', IPHONE_UA)
            response = urllib2.urlopen(req)                    
            json_source = json.load(response)
            response.close()
            m3u8_url = json_source['data'][0]['data']['m3u8_url']
    except:
        pass       

    try:
        print "M3U8!!!" + m3u8_url
        req = urllib2.Request(m3u8_url)
        response = urllib2.urlopen(req)                    
        master = response.read()
        response.close()
        cookie = ''
        try:
            cookie =  urllib.quote(response.info().getheader('Set-Cookie'))
        except:
            pass

        print cookie
        print master        

        line = re.compile("(.+?)\n").findall(master)  

        for temp_url in line:
            if '.m3u8' in temp_url:
                print temp_url
                print desc                  
                temp_url = temp_url+'|User-Agent='+IPHONE_UA              
                if cookie != '':
                    temp_url = temp_url + '&Cookie='+cookie

                stream_url.append(temp_url)
                stream_title.append('('+desc+') '+name)
                #addLink(name +' ('+desc+')',temp_url, name +' ('+desc+')', icon)
            else:
                desc = ''
                start = temp_url.find('RESOLUTION=')
                if start > 0:
                    start = start + len('RESOLUTION=')
                    end = temp_url.find(',',start)
                    desc = temp_url[start:end]
                else:
                    desc = "Audio"
    except:
        pass

    return stream_url, stream_title
    
def STREAM_QUALITY_SELECT(owner_id,event_id,icon):
    stream_url, stream_title = GET_STREAM(owner_id,event_id,icon)

    if len(stream_title) > 0:
        dialog = xbmcgui.Dialog() 
        ret = dialog.select('Choose Stream Quality', stream_title)
        
        if ret >=0:
            listitem = xbmcgui.ListItem(path=stream_url[ret])
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem)
    else:
        msg = "No playable streams found."
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Streams Not Found', msg)

def GET_ACCOUNT_STREAMS(owner_id):    
    url = 'https://api.new.livestream.com/accounts/'+owner_id    
    json_source = GET_JSON_FILE(url)
    

    addDir('[B][I]Upcoming Events[/B][/I]','/accounts',999,ICON,FANART)
    for event in json_source['upcoming_events']['data']:         
        name = event['full_name'].encode('utf-8')
        icon = event['logo']['url'].encode('utf-8')
        event_id = str(event['id'])

        start_time = str(event['start_time'])                        
        duration = 0
        try:
            duration = int(item['duration'])
        except:        
            pass

        print start_time         
        aired = start_time[0:4]+'-'+start_time[5:7]+'-'+start_time[8:10]
        print aired

        info = {'plot':'','tvshowtitle':'Livestream','title':name,'originaltitle':name,'duration':duration,'aired':aired}
        addStream(name,'/live_now',name,icon,FANART,event_id,owner_id,info)

    addDir('[B][I]Past Events[/B][/I]','/accounts',999,ICON,FANART)
    for event in json_source['past_events']['data']:         
        name = event['full_name'].encode('utf-8')
        icon = event['logo']['url'].encode('utf-8')
        event_id = str(event['id'])

        start_time = str(event['start_time'])                        
        duration = 0
        try:
            duration = int(item['duration'])
        except:        
            pass

        print start_time         
        aired = start_time[0:4]+'-'+start_time[5:7]+'-'+start_time[8:10]
        print aired

        info = {'plot':'','tvshowtitle':'Livestream','title':name,'originaltitle':name,'duration':duration,'aired':aired}
        addStream(name,'/live_now',name,icon,FANART,event_id,owner_id,info)


def addStream(name,link_url,title,iconimage,fanart=None,event_id=None,owner_id=None,info=None):
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(link_url)+"&mode="+str(104)+"&name="+urllib.quote_plus(name)+"&icon="+urllib.quote_plus(iconimage)
    if event_id != None:
        u = u+"&event_id="+urllib.quote_plus(event_id)
    if owner_id != None:
        u = u+"&owner_id="+urllib.quote_plus(owner_id) 
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage,) 
    liz.setProperty('fanart_image',fanart)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    if info != None:
        liz.setInfo( type="Video", infoLabels=info) 
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    xbmcplugin.setContent(addon_handle, 'episodes')
    
    return ok

def addLink(name,url,title,iconimage,fanart=None):
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setProperty('fanart_image',FANART)
    liz.setProperty("IsPlayable", "true")
    liz.setInfo( type="Video", infoLabels={ "Title": title } )
    if fanart != None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
    return ok


def addDir(name,url,mode,iconimage,fanart=None,event_id=None,owner_id=None,info=None):       
    ok=True
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&icon="+urllib.quote_plus(iconimage)
    if event_id != None:
        u = u+"&event_id="+urllib.quote_plus(event_id)
    if owner_id != None:
        u = u+"&owner_id="+urllib.quote_plus(owner_id)
    liz=xbmcgui.ListItem(name, iconImage=ICON, thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    if fanart != None:
        liz.setProperty('fanart_image', fanart)
    else:
        liz.setProperty('fanart_image', FANART)

    if info != None:
        liz.setInfo( type="Video", infoLabels=info)

    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)    
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
event_id=None
owner_id=None
icon = None

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
    event_id=urllib.unquote_plus(params["event_id"])
except:
    pass
try:
    owner_id=urllib.unquote_plus(params["owner_id"])
except:
    pass
try:
    icon=urllib.unquote_plus(params["icon"])
except:
    pass

print "Mode: "+str(mode)
#print "URL: "+str(url)
print "Name: "+str(name)
print "Event ID:"+str(event_id)
print "Owner ID:"+str(owner_id)



if mode==None or url==None or len(url)<1:
        #print ""                
        CATEGORIES()  
elif mode==100:        
        LIST_STREAMS()
elif mode==101:        
        GET_STREAM(owner_id,event_id,icon)
elif mode==102:
        SEARCH_LIVE()
elif mode==103:
        SEARCH_ARCHIVE()
elif mode==104:
        STREAM_QUALITY_SELECT(owner_id,event_id,icon)
elif mode==105:
    GET_ACCOUNT_STREAMS(owner_id)

if mode == 100:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
else:
    xbmcplugin.endOfDirectory(addon_handle)