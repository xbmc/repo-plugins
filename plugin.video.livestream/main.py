from resources.globals import *



def categories():                    
    #addDir('Live & Upcoming','/livestream',100,ICON,FANART)
    addDir('Browse by Category','/livestream',100,ICON,FANART)
    addDir('Search','/search',102,ICON,FANART)
    addDir('Following','/login',150,ICON,FANART)
    addDir('Manually Enter','/manual',160,ICON,FANART)
         

def getCategories():
    live_events = []
    url = 'http://7kjecl120u-1.algolia.io/1/indexes/categories/query'
    req = urllib2.Request(url)
    req.add_header("Accept", "application/json")
    req.add_header("Proxy-Connection", "keep-alive")
    req.add_header("Accept-Language", "en-US,en;q=1")
    req.add_header("Accept-Encoding", "deflate")
    req.add_header("X-Algolia-Application-Id", APP_ID)
    req.add_header("X-Algolia-API-Key", API_KEY)
    req.add_header("Content-type", "application/json; charset=utf-8")
    req.add_header("User-Agent",UA_LIVESTREAM)
        
    
    json_search = '{"params":"attributes=id,name,category_live_events,category_live_viewers,parent_id,parent_name&facetFilters=parent_id:null&hitsPerPage=100&numerics=id%3E0"}'
    #json_search = '{"requests":[{"indexName":"events","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"accounts","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"videos","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"images","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"statuses","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"}],"apiKey":"98f12273997c31eab6cfbfbe64f99d92","appID":"7KJECL120U"}'

    response = urllib2.urlopen(req,json_search)
    json_source = json.load(response)
    #print json_source
    response.close()
    
    for category in json_source['hits']:
        cat_info = json.dumps(category)        
        name = category['name'] + ' (' + str(category['category_live_events']) + ')'              
        live_events.append([name,ICON,FANART,None,None,None,cat_info])

    for event in  sorted(live_events, key=lambda tup: tup[0]): 
        addDir(event[0],'/livestream',106,event[1],event[2],event[3],event[4],event[5],event[6]) 
        #addDir(name,'/livestream',106,ICON,FANART,None,None,None,cat_info)  



def getCategoryEvents(cat_info):
    cat_info = json.loads(cat_info)
    cat_id = str(cat_info['id'])
    live_events = str(cat_info['category_live_events'])   

    url = 'http://7kjecl120u-1.algolia.io/1/indexes/events/query'
    req = urllib2.Request(url)
    req.add_header("Accept", "application/json")
    req.add_header("Proxy-Connection", "keep-alive")
    req.add_header("Accept-Language", "en-US,en;q=1")
    req.add_header("Accept-Encoding", "deflate")
    req.add_header("X-Algolia-Application-Id", APP_ID)
    req.add_header("X-Algolia-API-Key", API_KEY)
    req.add_header("Content-type", "application/json; charset=utf-8")
    req.add_header("User-Agent",UA_LIVESTREAM)
    
    json_search = '{"params":"attributes=id,full_name,tags,description,short_name,owner_account_id,broadcast_id,is_password_protected,is_geo_restricted,likes_count,concurrent_viewers_count,category_name,category_id,subcategory_name,subcategory_id,location_formatted_address,location_name,live_video_post_comments_count,live_chat_enabled,live_video_post_id,post_comments_enabled,viewer_count_visible,owner_account_id,owner_account_full_name,owner_account_features,owner_logo,logo,live_thumbnail,featured_by,start_time,end_time,expires_at&facetFilters=category_id:'+cat_id+'&hitsPerPage='+live_events+'&numerics=broadcast_id%3E0,is_geo_restricted=0,is_password_protected=0"}'

    response = urllib2.urlopen(req,json_search)
    json_source = json.load(response)    
    response.close()    
 
    live_streams = []
    for event in json_source['hits']: 
        #try:           
        event_id = str(event['id'])
        owner_id = str(event['owner_account_id'])

        owner_name = event['owner_account_full_name'].encode('utf-8')
        full_name = event['full_name'].encode('utf-8')
        name = owner_name + ' - ' + full_name      
        
        icon = None
        fanart = FANART
        try:
            icon = event['logo']['large']['url'].encode('utf-8')           
            #fanart = event['background_image']['url']
        except:
            pass

        '''
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
        '''
        #print start_time         
        #aired = start_time[0:4]+'-'+start_time[5:7]+'-'+start_time[8:10]
        print name
        aired = ''        
        length = ''
        desc = ''
        try:
            desc = event['_highlightResult']['description']['value'].encode('utf-8')
        except:
            pass
        #print aired

        info = {'plot':desc, 'tvshowtitle':'Livestream','title':name,'originaltitle':name,'duration':length,'aired':aired}
        
        #if event['in_progress']:
        name = '[COLOR=FF00B7EB]'+name+'[/COLOR]'
        live_streams.append([name,icon,event_id,owner_id,info,fanart])
        #else:
        '''
            if my_time < event_end:                
                start_date = datetime.fromtimestamp(time.mktime(time.strptime(start_time, pattern)))    
                start_date = datetime.strftime(utc_to_local(start_date),xbmc.getRegion('dateshort')+' '+xbmc.getRegion('time').replace('%H%H','%H').replace(':%S',''))
                info['plot'] = "Starting at: "+str(start_date)
                #name = name + ' ' + start_date
                upcoming_streams.append([name,icon,event_id,owner_id,info,fanart])
        '''
        #except:
        #pass

    
    for stream in  sorted(live_streams, key=lambda tup: tup[0]):        
        addDir(stream[0],'/live_now',101,stream[1],stream[5],stream[2],stream[3],stream[4]) 
        #addStream(stream[0],'/live_now',stream[0],stream[1],stream[5],stream[2],stream[3],stream[4])    
        #addStream(name,link_url,title,iconimage,fanart=None,event_id=None,owner_id=None,info=None)        


    #for stream in  sorted(upcoming_streams, key=lambda tup: tup[0]):
    #addDir(stream[0],'/live_now',101,stream[1],stream[5],stream[2],stream[3],stream[4])            
    


def search():    
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
                            ("X-Algolia-Application-Id", APP_ID),
                            ("X-Algolia-API-Key", API_KEY),
                            ("Content-type", "application/json"),
                            ("Connection", "keep-alive"),
                            ("Referer", "http://livestream.com/watch"),
                            ("User-Agent",'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36')]                
        
        
        json_search = '{"requests":[{"indexName":"events","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"accounts","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"videos","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"}],"apiKey":"'+API_KEY+'","appID":"'+APP_ID+'"}'
        #json_search = '{"requests":[{"indexName":"events","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"accounts","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"videos","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"images","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"},{"indexName":"statuses","params":"query='+search_txt+'&hitsPerPage='+SEARCH_HITS+'"}],"apiKey":"98f12273997c31eab6cfbfbe64f99d92","appID":"7KJECL120U"}'

        response = urllib2.urlopen(req,json_search)
        json_source = json.load(response)
        #print json_source
        response.close()


    return json_source


def searchLive():
    json_source = search()
    if json_source != '':
        i = 0
        
        for hits in json_source['results']: 
            i = i + 1
            if i == 1:
                addDir('[B][I][COLOR='+SECTION_COLOR+']Events[/COLOR][/B][/I]','/accounts',999,ICON,FANART)
            elif i == 2:
                addDir('[B][I][COLOR='+SECTION_COLOR+']Accounts[/COLOR][/B][/I]','/accounts',999,ICON,FANART)
            elif i == 3:
                addDir('[B][I][COLOR='+SECTION_COLOR+']Videos[/COLOR][/B][/I]','/accounts',999,ICON,FANART)

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
                        print start_time         
                        aired = start_time[0:4]+'-'+start_time[5:7]+'-'+start_time[8:10]
                        print aired
                        desc = ''
                        try:
                            desc = str(event['description']).encode('utf-8')
                        except:
                            pass

                        info = {'plot':desc,'tvshowtitle':'Livestream','title':name,'originaltitle':name,'duration':duration,'aired':aired}

                        addDir(name,'/live_now',101,icon,FANART,event_id,owner_id,info)
                        #addStream(name,'/live_now',name,icon,FANART,event_id,owner_id)
                    else:
                        #Accounts
                        name = event['full_name'].encode('utf-8') 
                        owner_id = str(event['id'])
                        icon = event['picture']['large']['url']
                        addDir(name,'/accounts',105,icon,FANART,None,owner_id)
                except:
                    pass
            
           
          

def getJsonFile(url):
    req = urllib2.Request(url) 
    req.add_header('User-Agent', ' Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36')     
    response = urllib2.urlopen(req)            
    json_source = json.load(response)
    response.close()  

    return json_source


def getStream(owner_id,event_id,video_id):    
    
    m3u8_url = ''    
    
    if video_id == None:        
        #url = 'http://api.new.livestream.com/accounts/'+owner_id+'/events/'+event_id+'/viewing_info'
        url = 'https://api.new.livestream.com/accounts/'+owner_id+'/events/'+event_id+'/'                
        req = urllib2.Request(url)       
        req.add_header('User-Agent', UA_IPHONE)        
        try:
            response = urllib2.urlopen(req)                            
        except HTTPError as e:
            print 'The server couldn\'t fulfill the request.'
            print 'Error code: ', e.code    
            print url   
            
            #Error 401 for invalid login
            if e.code == 401:
                msg = "Please check that your username and password are correct"
                dialog = xbmcgui.Dialog() 
                ok = dialog.ok('Invalid Login', msg)

            sys.exit()
        
        json_source = json.load(response)
        response.close()

        if json_source['stream_info'] is not None:            
            event_info = extractEventInfo(json_source['stream_info']['live_video_post'])
            icon = ''
            try:
                icon = json_source['stream_info']['thumbnail_url']
            except:
                pass
            addStream('[COLOR='+LIVE_COLOR+'/]'+event_info['name']+'[/COLOR]','/live_now',event_info['name'],icon,event_info['fanart'],event_id,owner_id,event_info['info'],'LIVE')
       
        #Get the total number of feeds and request all of them to display
        feed_total = str(json_source['feed']['total'])
        url = 'https://api.new.livestream.com/accounts/'+owner_id+'/events/'+event_id+'/feed/?maxItems='+feed_total
        req = urllib2.Request(url)       
        req.add_header('User-Agent', UA_IPHONE)
        response = urllib2.urlopen(req)                    
        json_source = json.load(response)
        response.close()
        for event in json_source['data']:                         
            try:
                event_info = extractEventInfo(event['data'])                    
                addStream(event_info['name'],'/live_now',event_info['name'],event_info['icon'],event_info['fanart'],event_id,owner_id,event_info['info'],event_info['broadcast_id'])
            except:
                pass                    
    else:     
        if video_id == 'LIVE':
            url = 'https://api.new.livestream.com/accounts/'+owner_id+'/events/'+event_id
            req = urllib2.Request(url)
            req.add_header('User-Agent', UA_IPHONE)              
            response = urllib2.urlopen(req)      
            json_source = json.load(response)
            response.close()            
            streamQualitySelect(json_source['stream_info']['m3u8_url'])
        else:
            url = 'https://api.new.livestream.com/accounts/'+owner_id+'/events/'+event_id+'/videos/'+video_id            
            req = urllib2.Request(url)
            req.add_header('User-Agent', UA_IPHONE)              
            response = urllib2.urlopen(req)      
            json_source = json.load(response)
            response.close()
            streamQualitySelect(json_source['m3u8_url'])



def getStreamQuality(m3u8_url):
    stream_url = []
    stream_title = [] 
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
                temp_url = temp_url+'|User-Agent='+UA_IPHONE              
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

    
def streamQualitySelect(m3u8_url):    
    
    stream_url, stream_title = getStreamQuality(m3u8_url)

    if len(stream_title) > 0:
        ret = 0
        if AUTO_PLAY == 'true':            
            temp_qlty = 0
            i = 0
            for stream in stream_title:
                stream = stream.partition("x")[0]
                print stream
                print stream[1:]
                try:
                    if int(stream[1:]) > temp_qlty:
                        temp_qlty = int(stream[1:])
                        ret = i
                except:
                    pass
                    
                i=i+1
        else:            
            dialog = xbmcgui.Dialog() 
            ret = dialog.select('Choose Stream Quality', stream_title)
        
        if ret >=0:
            listitem = xbmcgui.ListItem(path=stream_url[ret])
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem)
        else:
            sys.exit()
    else:
        msg = "No playable streams found."
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Streams Not Found', msg)



def getAccountStreams(owner_id):    
    url = 'https://api.new.livestream.com/accounts/'+owner_id    
    json_source = getJsonFile(url)
    
    ###########################################################
    # Live & Upcoming
    ###########################################################    
    addDir('[B][I][COLOR='+SECTION_COLOR+']Live & Upcoming Events[/COLOR][/B][/I]','/accounts',999,ICON,FANART)
    event_list = []
    for event in json_source['upcoming_events']['data']:
         event_info = extractEventInfo(event)
         event_list.append(event_info)

    #Reversed order so upcoming videos are displayed by date ascending
    for event in reversed(event_list):        
        addDir(event['name'],'/videos',101,event['icon'],event['fanart'],event['event_id'],owner_id,event['info'])            


    ###########################################################
    # Archived
    ###########################################################
    addDir('[B][I][COLOR='+SECTION_COLOR+']Archived Events[/COLOR][/B][/I]','/accounts',999,ICON,FANART)
    event_list = []
    for event in json_source['past_events']['data']:
         event_info = extractEventInfo(event)
         event_list.append(event_info)

    #Past videos are displayed by date descending
    for event in event_list:        
        addDir(event['name'],'/videos',101,event['icon'],event['fanart'],event['event_id'],owner_id,event['info'])            



def extractEventInfo(event):
    
    event_info = {}             
    try:
        event_id = str(event['event_id'])
    except:
        event_id = str(event['id'])

    broadcast_id = None
    try:
        broadcast_id = str(event['id'])        
    except:
        broadcast_id = str(event['broadcast_id'])        

    try:
        name = event['full_name'].encode('utf-8')        
    except:
        name = event['caption'].encode('utf-8')

    icon = None
    fanart = None
    try:
        icon = event['logo']['url'].encode('utf-8')           
        fanart = event['background_image']['url'].encode('utf-8')        
    except:
        try:            
            icon = event['thumbnail_url'].encode('utf-8')  
        except:
            pass         

    try:
        start_time = str(event['start_time'])   
    except:
        try:
            start_time = str(event['streamed_at'])
        except:
            start_time = str(event['publish_at'])

    duration = 0
    try:
        duration = int(item['duration'])
    except:        
        pass

    desc = ''
    try:
        desc = str(event['description']).encode('utf-8')
    except:
        pass
    
    aired = start_time[0:4]+'-'+start_time[5:7]+'-'+start_time[8:10]
    info = {'plot': desc,'tvshowtitle':'Livestream','title':name,'originaltitle':name,'duration':duration,'aired':aired}
    event_info = {'name':name, 'event_id':event_id, 'icon':icon, 'fanart':fanart, 'info':info, 'broadcast_id':broadcast_id}

    return event_info


def login():
    #Check if username and password are provided
    global USERNAME
    if USERNAME == '':        
        dialog = xbmcgui.Dialog()
        USERNAME = dialog.input('Please enter your username', type=xbmcgui.INPUT_ALPHANUM)        
        settings.setSetting(id='username', value=USERNAME)

    global PASSWORD
    if PASSWORD == '':        
        dialog = xbmcgui.Dialog()
        PASSWORD = dialog.input('Please enter your password', type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
        settings.setSetting(id='password', value=PASSWORD)

    if USERNAME != '' and PASSWORD != '':
        
        url = 'https://oauth.new.livestream.com/oauth/access_token/'
        req = urllib2.Request(url)
        req.add_header("Accept", "*/*")
        req.add_header("Origin", "http://livestream.com")
        req.add_header("Accept-Language", "en-US,en;q=0.8")
        req.add_header("Accept-Encoding", "gzip, deflate")
        req.add_header("X-Algolia-Application-Id", APP_ID)
        req.add_header("X-Algolia-API-Key", API_KEY)
        req.add_header("Content-type", "application/x-www-form-urlencoded; charset=utf-8")
        req.add_header("Connection", "keep-alive")
        req.add_header("User-Agent", UA_LIVESTREAM)                
        
        
        body = urllib.urlencode({'grant_type' : 'password',
                                 'username' : USERNAME,
                                 'password' : PASSWORD,
                                 'client_id' : '289ef33f7caa0c346c3025ff518ada99',
                                 'client_secret' : '511901d55797644f2bf78716518adaa3'
                                 })

        response = urllib2.urlopen(req, body)
        json_source = json.load(response)    
        response.close()

        access_token = json_source['access_token']
        user_id = str(json_source['user_data']['id'])

        ########################
        #Get Accounts Following
        ########################
        req = urllib2.Request('https://api.new.livestream.com/accounts/'+user_id+'/')
        req.add_header("Accept", "*/*")
        req.add_header("Accept-Language", "en-US,en;q=1")
        req.add_header("Accept-Encoding", "gzip, deflate")
        #('If-None-Match', 'W/"xyKvCBoIJXQ9Tu6ij5hL1g=='),                                                
        #("Connection", "keep-alive"),
        req.add_header("Authorization", "Bearer "+access_token)
        req.add_header("User-Agent", UA_LIVESTREAM)

        response = urllib2.urlopen(req)                    
        json_source = json.load(response)    
        response.close()

        for account in json_source['following']['data']:
            name = account['full_name'].encode('utf-8') 
            owner_id = str(account['id'])
            icon = ICON
            fanart = FANART
            try:
                icon = account['picture']['url']            
                fanart = account['background_image']['url']
            except:
                pass

            print name
            print icon
            addDir(name,'/accounts',105,icon,fanart,None,owner_id)
        

def manualEvent():
    dialog = xbmcgui.Dialog()
    owner_id = dialog.input('Please enter the account id', type=xbmcgui.INPUT_ALPHANUM)        
    event_id = dialog.input('Please enter the event id', type=xbmcgui.INPUT_ALPHANUM)        
    if owner_id != '' and event_id != '':
        getStream(owner_id,event_id,None)


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
video_id=None
icon = None
cat_info = None

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
try:
    video_id=urllib.unquote_plus(params["video_id"])
except:
    pass
try:
    cat_info=urllib.unquote_plus(params["cat_info"])
except:
    pass

print "Mode: "+str(mode)
#print "URL: "+str(url)
print "Name: "+str(name)
print "Event ID:"+str(event_id)
print "Owner ID:"+str(owner_id)
print "Video ID:"+str(video_id)



if mode==None or url==None or len(url)<1:    
    categories()          
elif mode==100:                
    getCategories()
elif mode==101:        
    getStream(owner_id,event_id,video_id)
elif mode==102:
    searchLive()
elif mode==104:
    getStream(owner_id,event_id,video_id)
elif mode==105:
    getAccountStreams(owner_id)

elif mode==106:
    getCategoryEvents(cat_info)

elif mode==150:
    login()
elif mode==160:
    manualEvent()
elif mode==999:
    sys.exit()

if mode == 100:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
else:
    xbmcplugin.endOfDirectory(addon_handle)