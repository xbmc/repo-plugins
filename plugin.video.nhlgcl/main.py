
from resources.lib.globals import *


def categories():      
    addDir('Today\'s Games','/live',100,ICON,FANART)
    addDir('Yesterday\'s Games','/live',105,ICON,FANART)     
    if FAV_TEAM != 'None' and FAV_TEAM != '':
        #'https://www.nhl.com/site-core/images/team/logo/current/'+FAV_TEAM_ID+'_light.svg'
        addFavToday(FAV_TEAM+'\'s Game Today', 'Today\'s ' +  FAV_TEAM + ' Game', FAV_TEAM_LOGO, FANART)
        addDir(FAV_TEAM+'\'s Recent Games','favteam',500, FAV_TEAM_LOGO,FANART)
    addDir('Goto Date','/date',200,ICON,FANART)
    addDir('Featured Videos','/qp',300,ICON,FANART)
    

def todaysGames(game_day):    
    if game_day == None:
        game_day = localToEastern()

    xbmc.log("GAME DAY = " + str(game_day))
    settings.setSetting(id='stream_date', value=game_day)    

    display_day = stringToDate(game_day, "%Y-%m-%d")            
    prev_day = display_day - timedelta(days=1)                

    addDir('[B]<< Previous Day[/B]','/live',101,PREV_ICON,FANART,prev_day.strftime("%Y-%m-%d"))

    date_display = '[B][I]'+ colorString(display_day.strftime("%A, %m/%d/%Y"),GAMETIME_COLOR)+'[/I][/B]'
    addPlaylist(date_display,display_day,'/playhighlights',900,ICON,FANART)

    #url = 'https://statsapi.web.nhl.com/api/v1/schedule?teamId=&startDate=2016-02-09&endDate=2016-02-09&expand=schedule.teams,schedule.linescore,schedule.game.content.media.epg,schedule.broadcasts,schedule.scoringplays,team.leaders,leaders.person,schedule.ticket,schedule.game.content.highlights.scoreboard,schedule.ticket&leaderCategories=points'
    url = 'http://statsapi.web.nhl.com/api/v1/schedule?expand=schedule.teams,schedule.linescore,schedule.scoringplays,schedule.game.content.media.epg&date='+game_day+'&site=en_nhl&platform='+PLATFORM
    req = urllib2.Request(url)    
    req.add_header('Connection', 'close')
    req.add_header('User-Agent', UA_PS4)

    try:    
        response = urllib2.urlopen(req)            
        json_source = json.load(response)                           
        response.close()                
    except HTTPError as e:
        xbmc.log('The server couldn\'t fulfill the request.')
        xbmc.log('Error code: ', e.code)
        sys.exit()

    global RECAP_PLAYLIST
    global EXTENDED_PLAYLIST
    RECAP_PLAYLIST.clear()
    EXTENDED_PLAYLIST.clear()
    try:
        for game in json_source['dates'][0]['games']:        
            createGameListItem(game, game_day)
    except:
        pass
    
    next_day = display_day + timedelta(days=1)
    addDir('[B]Next Day >>[/B]','/live',101,NEXT_ICON,FANART,next_day.strftime("%Y-%m-%d"))    


def createGameListItem(game, game_day):
    away = game['teams']['away']['team']
    home = game['teams']['home']['team']
    #http://nhl.cdn.neulion.net/u/nhlgc_roku/images/HD/NJD_at_BOS.jpg
    #icon = 'http://nhl.cdn.neulion.net/u/nhlgc_roku/images/HD/'+away['abbreviation']+'_at_'+home['abbreviation']+'.jpg'
    #icon = 'http://raw.githubusercontent.com/eracknaphobia/game_images/master/square_black/'+away['abbreviation']+'vs'+home['abbreviation']+'.png'    
    icon = getGameIcon(home['abbreviation'],away['abbreviation'])    


    
    if TEAM_NAMES == "1":
        away_team = away['teamName']
        home_team = home['teamName']
    elif TEAM_NAMES == "2":
        away_team = away['name']
        home_team = home['name']
    elif TEAM_NAMES == "3":
        away_team = away['abbreviation']
        home_team = home['abbreviation']
    else:
        away_team = away['locationName']
        home_team = home['locationName']


    if away_team == "New York":
        away_team = away['name']

    if home_team == "New York":
        home_team = home['name']


    fav_game = False
    if FAV_TEAM_ID == str(away['id']):
        fav_game = True        
        away_team = colorString(away_team,FAV_TEAM_COLOR)           
    
    if FAV_TEAM_ID == str(home['id']):
        fav_game = True        
        home_team = colorString(home_team,FAV_TEAM_COLOR)


    game_time = ''
    if game['status']['detailedState'] == 'Scheduled':
        game_time = game['gameDate']
        game_time = stringToDate(game_time, "%Y-%m-%dT%H:%M:%SZ")
        game_time = UTCToLocal(game_time)
       
        if TIME_FORMAT == '0':
             game_time = game_time.strftime('%I:%M %p').lstrip('0')
        else:
             game_time = game_time.strftime('%H:%M')

        game_time = colorString(game_time,UPCOMING)            

    else:
        game_time = game['status']['detailedState']

        if game_time == 'Final':
            #if (NO_SPOILERS == '1' and game_time[:5] == "Final") or (NO_SPOILERS == '2' and game_time[:5] == "Final" and fav_game):
            #game_time = game_time[:5]                     
            game_time = colorString(game_time,FINAL)
        elif 'In Progress' in game_time:
            color = LIVE
            if 'Critical' in game_time:
                color = CRITICAL
            game_time = game['linescore']['currentPeriodTimeRemaining']+' '+game['linescore']['currentPeriodOrdinal']
            game_time = colorString(game_time,color)
        else:            
            game_time = colorString(game_time,LIVE)
        
        
    game_id = str(game['gamePk'])

    #live_video = game['gameLiveVideo']
    epg = ''
    try:
        epg = json.dumps(game['content']['media']['epg'])
    except:
        pass
    live_feeds = 0
    archive_feeds = 0
    teams_stream = away['abbreviation'] + home['abbreviation']    
    stream_date = str(game['gameDate'])


    desc = ''       
    hide_spoilers = 0
    if NO_SPOILERS == '1' or (NO_SPOILERS == '2' and fav_game) or (NO_SPOILERS == '3' and game_day == localToEastern()) or (NO_SPOILERS == '4' and game_day < localToEastern()) or game['status']['detailedState'] == 'Scheduled':
        name = game_time + ' ' + away_team + ' at ' + home_team    
        hide_spoilers = 1
    else:
        name = game_time + ' ' + away_team + ' ' + colorString(str(game['teams']['away']['score']),SCORE_COLOR) + ' at ' + home_team + ' ' + colorString(str(game['teams']['home']['score']),SCORE_COLOR)         
        

    fanart = None   
    try:        
        if game_day < localToEastern():
            fanart = str(game['content']['media']['epg'][3]['items'][0]['image']['cuts']['1136x640']['src'])
            if hide_spoilers == 0:
                soup = BeautifulSoup(str(game['content']['editorial']['recap']['items'][0]['preview']))
                desc = soup.get_text()
        else:  
            if PREVIEW_INFO == 'true':          
                url = 'http://statsapi.web.nhl.com/api/v1/game/'+str(game['gamePk'])+'/content?site=en_nhl'
                req = urllib2.Request(url)    
                req.add_header('Connection', 'close')
                req.add_header('User-Agent', UA_PS4)

                try:    
                    response = urllib2.urlopen(req)            
                    json_source = json.load(response)     
                    fanart = str(json_source['editorial']['preview']['items'][0]['media']['image']['cuts']['1284x722']['src'])                                      
                    soup = BeautifulSoup(str(json_source['editorial']['preview']['items'][0]['preview']))
                    desc = soup.get_text()
                    response.close()                
                except HTTPError as e:
                    xbmc.log('The server couldn\'t fulfill the request.')
                    xbmc.log('Error code: ', e.code)            
    except:
        pass

    name = name.encode('utf-8')
    if fav_game:
        name = '[B]'+name+'[/B]'
    
    title = away_team + ' at ' + home_team
    title = title.encode('utf-8')

    #Label free game of the day
    try:
        if bool(game['content']['media']['epg'][0]['items'][0]['freeGame']):
            name = colorString(name,FREE)
    except:
        pass
    
    #Set audio/video info based on stream quality setting
    audio_info, video_info = getAudioVideoInfo()
    #'duration':length
    info = {'plot':desc,'tvshowtitle':'NHL','title':title,'originaltitle':title,'aired':game_day,'genre':'Sports'}

    #Create Playlist for all highlights    
    try:
        global RECAP_PLAYLIST    
        temp_recap_stream_url = createHighlightStream(game['content']['media']['epg'][3]['items'][0]['playbacks'][3]['url'])   
        listitem = xbmcgui.ListItem(title, thumbnailImage=icon)    
        listitem.setInfo( type="Video", infoLabels={ "Title": title })
        RECAP_PLAYLIST.add(temp_recap_stream_url, listitem)

        global EXTENDED_PLAYLIST
        temp_extended_stream_url = createHighlightStream(game['content']['media']['epg'][2]['items'][0]['playbacks'][3]['url'])   
        listitem = xbmcgui.ListItem(title, thumbnailImage=icon)      
        listitem.setInfo( type="Video", infoLabels={ "Title": title } )
        EXTENDED_PLAYLIST.add(temp_extended_stream_url, listitem)
    except:
        pass


    addStream(name,'',title,game_id,epg,icon,fanart,info,video_info,audio_info,teams_stream,stream_date)



def streamSelect(game_id, epg, teams_stream, stream_date):
    #print epg
    #0 = NHLTV
    #1 = Audio
    #2 = Extended Highlights
    #3 = Recap
    
    try:
        epg = json.loads(epg)    
    except:
        msg = "No playable streams found."
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Streams Not Found', msg)        
        sys.exit()

    full_game_items = epg[0]['items']
    audio_items = epg[1]['items']
    highlight_items = epg[2]['items']
    recap_items = epg[3]['items']

    stream_title = []
    content_id = []
    event_id = []
    free_game = []
    media_state = []
    archive_type = ['Recap','Extended Highlights','Full Game']    
    
    multi_angle = 0
    multi_cam = 0
    if len(full_game_items) > 0:
        for item in full_game_items:
            media_state.append(item['mediaState'])

            if item['mediaFeedType'].encode('utf-8') == "COMPOSITE":
                multi_cam += 1
                stream_title.append("Multi-Cam " + str(multi_cam))
            elif item['mediaFeedType'].encode('utf-8') == "ISO":
                multi_angle += 1
                stream_title.append("Multi-Angle " + str(multi_angle))
            else:
                temp_item = item['mediaFeedType'].encode('utf-8').title()                
                if item['callLetters'].encode('utf-8') != '':
                    temp_item = temp_item+' ('+item['callLetters'].encode('utf-8')+')'

                stream_title.append(temp_item)

            content_id.append(item['mediaPlaybackId'])
            event_id.append(item['eventId'])
            free_game.append(item['freeGame'])

    else:
        msg = "No playable streams found."
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Streams Not Found', msg)        
        sys.exit()
    
    #Reverse Order for display purposes
    #stream_title.reverse()
    #ft.reverse()

    stream_url = ''
    media_auth = ''

    if media_state[0] == 'MEDIA_ARCHIVE':
        dialog = xbmcgui.Dialog() 
        a = dialog.select('Choose Archive', archive_type)
        if a < 2:
            if a == 0:
                #Recap                 
                try:            
                    stream_url = createHighlightStream(recap_items[0]['playbacks'][3]['url'])                
                except:
                    pass
            elif a == 1:
                #Extended Highlights                
                try:
                    stream_url = createHighlightStream(highlight_items[0]['playbacks'][3]['url'])
                except:
                    pass
        elif a == 2:
            dialog = xbmcgui.Dialog() 
            n = dialog.select('Choose Stream', stream_title)
            if n > -1:                
                stream_url, media_auth = fetchStream(game_id, content_id[n],event_id[n])
                xbmc.log(stream_url)                
                stream_url = createFullGameStream(stream_url,media_auth,media_state[n])           
    else:
        dialog = xbmcgui.Dialog() 
        n = dialog.select('Choose Stream', stream_title)
        if n > -1:            
            stream_url, media_auth = fetchStream(game_id, content_id[n],event_id[n])
            stream_url = createFullGameStream(stream_url,media_auth,media_state[n])           
       
    
    listitem = xbmcgui.ListItem(path=stream_url)

    if stream_url != '':            
        listitem.setMimeType("application/x-mpegURL")
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem)
    else:        
        xbmcplugin.setResolvedUrl(addon_handle, False, listitem)        


def playAllHighlights():
    stream_title = ['Recap','Extended Highlights'] 
    dialog = xbmcgui.Dialog() 
    n = dialog.select('View All', stream_title)

    if n == 0:
        xbmc.Player().play(RECAP_PLAYLIST)
    elif n == 1:
        xbmc.Player().play(EXTENDED_PLAYLIST)


def createHighlightStream(stream_url):
    bandwidth = ''
    bandwidth = find(QUALITY,'(',' kbps)') 
    #Switch to ipad master file
    stream_url = stream_url.replace('master_wired.m3u8', MASTER_FILE_TYPE)
    xbmc.log("bandwidth")
    xbmc.log(str(bandwidth))
    if bandwidth != '':
        stream_url = stream_url.replace(MASTER_FILE_TYPE, 'asset_'+bandwidth+'k.m3u8')

    stream_url = stream_url + '|User-Agent='+UA_IPAD

    xbmc.log(stream_url)
    return stream_url


def createFullGameStream(stream_url, media_auth, media_state):
    #SD (800 kbps)|SD (1600 kbps)|HD (3000 kbps)|HD (5000 kbps)        
    bandwidth = ''
    bandwidth = find(QUALITY,'(',' kbps)')

    #Only set bandwidth if it's explicitly set
    if bandwidth != '':
        #Reduce convert bandwidth if composite video selected   
        if ('COMPOSITE' in stream_url or 'ISO' in stream_url) :
            if int(bandwidth) == 5000:
                bandwidth = '3500'
            elif int(bandwidth) == 1200:
                bandwidth = '1500'
        
        if media_state == 'MEDIA_ARCHIVE':                
            #ARCHIVE
            if checkArchiveType(stream_url,media_auth) == 'asset':
                stream_url = stream_url.replace(MASTER_FILE_TYPE, 'asset_'+bandwidth+'k.m3u8') 
            else:
                stream_url = stream_url.replace(MASTER_FILE_TYPE, bandwidth+'K/'+bandwidth+'_complete-trimmed.m3u8') 

        elif media_state == 'MEDIA_ON':
            #LIVE    
            #5000K/5000_slide.m3u8 OR #3500K/3500_complete.m3u8
            # Slide = Live, Complete = Watch from beginning?
            stream_url = stream_url.replace(MASTER_FILE_TYPE, bandwidth+'K/'+bandwidth+'_complete.m3u8') 
                
    
    cj = cookielib.LWPCookieJar()
    cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
    try:
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
    except:
        pass

    cookies = ''
    for cookie in cj:            
        if cookie.name == "Authorization":
            cookies = cookies + cookie.name + "=" + cookie.value + "; "
    #stream_url = stream_url + '|User-Agent='+UA_PS4+'&Cookie='+cookies+media_auth
    stream_url = stream_url + '|User-Agent='+UA_IPAD+'&Cookie='+cookies+media_auth

    xbmc.log("STREAM URL: "+stream_url)
    return stream_url
    
                
def getAuthCookie():
    authorization = ''    
    try:
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))     
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)    

        #If authorization cookie is missing or stale, perform login    
        for cookie in cj:            
            if cookie.name == "Authorization" and not cookie.is_expired():            
                authorization = cookie.value 
    except:
        pass

    return authorization


def checkArchiveType(stream_url, media_auth):
    xbmc.log('test--------------------------------------------------------')
    xbmc.log(stream_url)
    req = urllib2.Request(stream_url)       
    req.add_header("Accept", "*/*")
    req.add_header("Accept-Encoding", "deflate")
    req.add_header("Accept-Language", "en-US,en;q=0.8")                       
    req.add_header("Connection", "keep-alive")    
    req.add_header("User-Agent", UA_NHL)
    req.add_header("Cookie", media_auth) 


    response = urllib2.urlopen(req)
    playlist = response.read()
    response.close()

    stream_type = 'complete-trimmed'
    if 'asset_' in playlist:
        stream_type = 'asset'

    return stream_type


def fetchStream(game_id, content_id,event_id):        
    stream_url = ''
    media_auth = ''    
   
    authorization = getAuthCookie()            
    
    if authorization == '':  
        login()
        authorization = getAuthCookie()   
        if authorization == '':
            return stream_url, media_auth

    cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')) 
    cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)         
    session_key = getSessionKey(game_id,event_id,content_id,authorization)    
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))   
        

    if session_key == '':
        return stream_url, media_auth
    elif session_key == 'blackout':
        msg = "The game you are trying to access is not currently available due to local or national blackout restrictions.\n Full game archives will be available 48 hours after completion of this game."
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Game Blacked Out', msg) 
        return stream_url, media_auth

    
    #Get user set CDN
    if CDN == 'Akamai':
        cdn_url = 'akc.med2.med.nhl.com'
    else:
        cdn_url = 'l3c.med2.med.nhl.com'

    i=0
    for i in range (0,9):
        #Org
        url = 'https://mf.svc.nhl.com/ws/media/mf/v2.4/stream?contentId='+content_id+'&playbackScenario=HTTP_CLOUD_TABLET_60&platform='+PLATFORM+'&sessionKey='+urllib.quote_plus(session_key)        
        req = urllib2.Request(url)       
        req.add_header("Accept", "*/*")
        req.add_header("Accept-Encoding", "deflate")
        req.add_header("Accept-Language", "en-US,en;q=0.8")                       
        req.add_header("Connection", "keep-alive")
        req.add_header("Authorization", authorization)
        req.add_header("User-Agent", UA_NHL)
        req.add_header("Proxy-Connection", "keep-alive")  
        response = opener.open(req)    
        json_source = json.load(response)       
        response.close()

        try:
            #Update session key to prevent sign-on a restriction in subsequent calls
            session_key = json_source['session_key']
            stream_url = json_source['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['url'] 
            if cdn_url in stream_url: break
            elif json_source['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['blackout_status']['status'] == 'BlackedOutStatus': break
            elif CDN == 'No Preference': break
        except:
            i = i + 1
            pass
       

    if json_source['status_code'] == 1:
        if json_source['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['blackout_status']['status'] == 'BlackedOutStatus':
            msg = "You do not have access to view this content. To watch live games and learn more about blackout restrictions, please visit NHL.TV"
            dialog = xbmcgui.Dialog() 
            ok = dialog.ok('Game Blacked Out', msg) 
        elif json_source['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['auth_status'] == 'NotAuthorizedStatus':
            msg = "You do not have an active NHL.TV subscription. To access this content please purchase at www.NHL.TV or call customer support at 800-559-2333"
            dialog = xbmcgui.Dialog() 
            ok = dialog.ok('Account Not Authorized', msg) 
        else:
            stream_url = json_source['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['url']    
            media_auth = str(json_source['session_info']['sessionAttributes'][0]['attributeName']) + "=" + str(json_source['session_info']['sessionAttributes'][0]['attributeValue'])
            session_key = json_source['session_key']
            settings.setSetting(id='media_auth', value=media_auth) 
            #Update Session Key
            settings.setSetting(id='session_key', value=session_key)   
    else:
        msg = json_source['status_message']
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Error Fetching Stream', msg)
       
    
    return stream_url, media_auth    
   


def getSessionKey(game_id,event_id,content_id,authorization):    
    #session_key = ''
    session_key = str(settings.getSetting(id="session_key"))

    if session_key == '':        
        epoch_time_now = str(int(round(time.time()*1000)))    

        url = 'https://mf.svc.nhl.com/ws/media/mf/v2.4/stream?eventId='+event_id+'&format=json&platform='+PLATFORM+'&subject=NHLTV&_='+epoch_time_now        
        req = urllib2.Request(url)       
        req.add_header("Accept", "application/json")
        req.add_header("Accept-Encoding", "deflate")
        req.add_header("Accept-Language", "en-US,en;q=0.8")                       
        req.add_header("Connection", "keep-alive")
        req.add_header("Authorization", authorization)
        req.add_header("User-Agent", UA_PC)
        req.add_header("Origin", "https://www.nhl.com")
        req.add_header("Referer", "https://www.nhl.com/tv/"+game_id+"/"+event_id+"/"+content_id)
        
        response = urllib2.urlopen(req)
        json_source = json.load(response)   
        response.close()
        
        xbmc.log("REQUESTED SESSION KEY")
        if json_source['status_code'] == 1:      
            if json_source['user_verified_event'][0]['user_verified_content'][0]['user_verified_media_item'][0]['blackout_status']['status'] == 'BlackedOutStatus':
                msg = "You do not have access to view this content. To watch live games and learn more about blackout restrictions, please visit NHL.TV"
                session_key = 'blackout'
            else:    
                session_key = str(json_source['session_key'])
                settings.setSetting(id='session_key', value=session_key)                              
        else:
            msg = json_source['status_message']
            dialog = xbmcgui.Dialog() 
            ok = dialog.ok('Error Fetching Stream', msg)            
    
    return session_key  
    

def login():    
    #Check if username and password are provided    
    global USERNAME
    if USERNAME == '':        
        dialog = xbmcgui.Dialog()
        USERNAME = dialog.input('Please enter your username', type=xbmcgui.INPUT_ALPHANUM)        
        settings.setSetting(id='username', value=USERNAME)
        USERNAME = json.dumps(USERNAME)

    global PASSWORD
    if PASSWORD == '':        
        dialog = xbmcgui.Dialog()
        PASSWORD = dialog.input('Please enter your password', type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
        settings.setSetting(id='password', value=PASSWORD)
        PASSWORD = json.dumps(PASSWORD)
   
    if USERNAME != '' and PASSWORD != '':        
        cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')) 
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))   

        try:
            cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        except:
            pass

        #Get Token
        url = 'https://user.svc.nhl.com/oauth/token?grant_type=client_credentials'
        req = urllib2.Request(url)       
        req.add_header("Accept", "application/json")
        req.add_header("Accept-Encoding", "gzip, deflate, sdch")
        req.add_header("Accept-Language", "en-US,en;q=0.8")                                           
        req.add_header("User-Agent", UA_PC)
        req.add_header("Origin", "https://www.nhl.com")
        #from https:/www.nhl.com/tv?affiliated=NHLTVLOGIN
        req.add_header("Authorization", "Basic d2ViX25obC12MS4wLjA6MmQxZDg0NmVhM2IxOTRhMThlZjQwYWM5ZmJjZTk3ZTM=")

        response = opener.open(req, '')
        json_source = json.load(response)   
        authorization = getAuthCookie()
        if authorization == '':
            authorization = json_source['access_token']
        response.close()
 
        if ROGERS_SUBSCRIBER == 'true':                        
            url = 'https://activation-rogers.svc.nhl.com/ws/subscription/flow/rogers.login'            
            login_data = '{"rogerCredentials":{"email":'+USERNAME+',"password":'+PASSWORD+'}}'
            #referer = "https://www.nhl.com/login/rogers"              
        else:                               
            url = 'https://user.svc.nhl.com/v2/user/identity'            
            login_data = '{"email":{"address":'+USERNAME+'},"type":"email-password","password":{"value":'+PASSWORD+'}}'            


        req = urllib2.Request(url, data=login_data, headers=
            {"Accept": "*/*",
             "Accept-Encoding": "gzip, deflate",
             "Accept-Language": "en-US,en;q=0.8",
             "Content-Type": "application/json", 
             "Authorization": authorization,
             "Connection": "keep-alive",
             "User-Agent": UA_PC})     
       
        try:
            response = opener.open(req) 
        except HTTPError as e:
            xbmc.log('The server couldn\'t fulfill the request.')
            xbmc.log('Error code: ', e.code)
            xbmc.log(url)
            
            #Error 401 for invalid login
            if e.code == 401:
                msg = "Please check that your username and password are correct"
                dialog = xbmcgui.Dialog() 
                ok = dialog.ok('Invalid Login', msg)

        #response = opener.open(req)              
        #user_data = response.read()
        response.close()
      

        cj.save(ignore_discard=True); 


def logout(display_msg=None):    
    from resources.lib.globals import *
    cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))   
    try:  
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
    except:
        pass
        
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))                
    url = 'https://account.nhl.com/ui/rest/logout'
    
    req = urllib2.Request(url, data='',
          headers={"Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "en-US,en;q=0.8",
                    "Content-Type": "application/x-www-form-urlencoded",                            
                    "Origin": "https://account.nhl.com/ui/SignOut?lang=en",
                    "Connection": "close",
                    "User-Agent": UA_PC})

    try:
        response = opener.open(req) 
    except HTTPError as e:
        xbmc.log('The server couldn\'t fulfill the request.')
        xbmc.log('Error code: ', e.code)
        xbmc.log(url)

    response.close()

    #Delete cookie file
    try: os.remove(ADDON_PATH_PROFILE+'cookies.lwp')
    except: pass

    if display_msg == 'true':
        settings.setSetting(id='session_key', value='') 
        dialog = xbmcgui.Dialog() 
        title = "Logout Successful" 
        dialog.notification(title, 'Logout completed successfully', ICON, 5000, False) 


def myTeamsGames():    
    if FAV_TEAM != 'None':
        end_day = localToEastern()
        end_date = stringToDate(end_day, "%Y-%m-%d")            
        start_date = end_date - timedelta(days=30) 
        start_day = start_date.strftime("%Y-%m-%d")
        

        url = 'http://statsapi.web.nhl.com/api/v1/schedule?teamId='+FAV_TEAM_ID+'&startDate='+start_day+'&endDate='+end_day+'&expand=schedule.teams,schedule.linescore,schedule.scoringplays,schedule.game.content.media.epg'
        #${expand},schedule.ticket&${optionalParams}'
        req = urllib2.Request(url)   
        req.add_header('User-Agent', UA_IPAD)
        response = urllib2.urlopen(req)    
        json_source = json.load(response)                           
        response.close()

        for date in reversed(json_source['dates']):        
            #temp_date = stringToDate(date['date'], "%Y-%m-%d") 
            #date_display = '[B][I]'+ colorString(temp_date.strftime("%A, %m/%d/%Y"),GAMETIME_COLOR)+'[/I][/B]'
            #addDir(date_display,'/nothing',999,ICON,FANART)
            for game in date['games']:        
                createGameListItem(game, date['date'])  

        
    else:
        msg = "Please select your favorite team from the addon settings"
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Favorite Team Not Set', msg)


def playTodaysFavoriteTeam():   

    if FAV_TEAM != 'None':
        end_day = localToEastern()        
        start_day = end_day
        

        url = 'http://statsapi.web.nhl.com/api/v1/schedule?teamId='+FAV_TEAM_ID+'&startDate='+start_day+'&endDate='+end_day+'&expand=schedule.game.content.media.epg,schedule.teams'
        req = urllib2.Request(url)   
        req.add_header('User-Agent', UA_IPAD)
        response = urllib2.urlopen(req)    
        json_source = json.load(response)                           
        response.close()

        stream_url = ''
        if json_source['dates']:
            todays_game = json_source['dates'][0]['games'][0]

            # Determine if favorite team is home or away
            fav_team_homeaway = ''

            away = todays_game['teams']['away']['team']
            home = todays_game['teams']['home']['team']

            if FAV_TEAM_ID == str(away['id']):
                fav_team_homeaway = 'AWAY'

            if FAV_TEAM_ID == str(home['id']):
                fav_team_homeaway = 'HOME'


            # Grab the correct feed (home/away/national)
            epg = todays_game['content']['media']['epg']
            streams = epg[0]['items']
            local_stream = {}
            natl_stream = {}
            for stream in streams:
                feedType = stream['mediaFeedType']
                if feedType == fav_team_homeaway:
                    local_stream = stream
                    break
                elif feedType == 'NATIONAL':
                    natl_stream = stream
            if not local_stream:
                local_stream = natl_stream
       
            game_id = str(todays_game['gamePk'])

            # Create the stream url
            stream_url, media_auth = fetchStream(str(game_id), local_stream['mediaPlaybackId'], local_stream['eventId'])
            stream_url = createFullGameStream(stream_url, media_auth, local_stream['mediaState'])

        else:
            dialog = xbmcgui.Dialog()
            dialog.ok('No Game Today', FAV_TEAM + " doesn't play today")

        listitem = xbmcgui.ListItem(path=stream_url)
        if stream_url != '':
            listitem.setMimeType("application/x-mpegURL")
            xbmcplugin.setResolvedUrl(addon_handle, True, listitem)
        else:
            xbmcplugin.setResolvedUrl(addon_handle, False, listitem)


    else:
        msg = "Please select your favorite team from the addon settings"
        dialog = xbmcgui.Dialog() 
        ok = dialog.ok('Favorite Team Not Set', msg)


def gotoDate():
    #Goto Date
    search_txt = ''
    dialog = xbmcgui.Dialog()
    #game_day = dialog.input('Enter date (yyyy-mm-dd)', type=xbmcgui.INPUT_ALPHANUM)    
    game_day = ''
    
    #Year
    year_list = []
    #year_item = datetime.now().year
    year_item = 2015
    while year_item <= datetime.now().year:
        year_list.insert(0,str(year_item))
        year_item = year_item + 1
    
    ret = dialog.select('Choose Year', year_list)

    if ret > -1:
        year = year_list[ret]    

        #Month
        #mnth_name = ['September','October','November','December','Janurary','February','March','April','May','June'] 
        #mnth_num = ['9','10','11','12','1','2','3','4','5','6']        

        mnth_name = ['Janurary','February','March','April','May','June','September','October','November','December'] 
        mnth_num = ['1','2','3','4','5','6','9','10','11','12']        
        
        ret = dialog.select('Choose Month', mnth_name)

        if ret > -1:
            mnth = mnth_num[ret]    

            #Day
            day_list = []
            day_item = 1
            last_day = calendar.monthrange(int(year), int(mnth))[1]
            while day_item <= last_day:                
                day_list.append(str(day_item))
                day_item = day_item + 1
            
            ret = dialog.select('Choose Day', day_list)

            if ret > -1:
                day = day_list[ret]
                game_day = year+'-'+mnth.zfill(2)+'-'+day.zfill(2)                
                
    
    if game_day != '':        
        todaysGames(game_day)
    else:
        sys.exit()

def nhlVideos():    
    url = 'http://nhl.bamcontent.com/nhl/en/section/v1/video/nhl/ios-tablet-v1.json'    
    req = urllib2.Request(url)   
    req.add_header('User-Agent', UA_IPAD)
    
    try:    
        response = urllib2.urlopen(req)    
        json_source = json.load(response)                           
        response.close()                
    except HTTPError as e:
        xbmc.log('The server couldn\'t fulfill the request.')
        xbmc.log('Error code: ', e.code)
        sys.exit()
    
    for video in json_source['videosLongList']:
        title = video['headline']
        name = title
        icon = video['image']['1136x640']
        url = video['mediaPlaybackURL']
        desc = video['blurb']
        release_date = video['date'][0:10]
        duration = video['duration']

        bandwidth = find(QUALITY,'(',' kbps)')
        if bandwidth != '':
            url = url.replace('master_tablet60.m3u8', 'asset_'+bandwidth+'k.m3u8')
        url = url + '|User-Agent='+UA_IPAD

        audio_info, video_info = getAudioVideoInfo()
        info = {'plot':desc,'tvshowtitle':'NHL','title':name,'originaltitle':name,'duration':'','aired':release_date}
        addLink(name,url,title,icon,info,video_info,audio_info,icon)

    
params=get_params()
url=None
name=None
mode=None
game_day=None
game_id=None
epg=None
teams_stream=None
stream_date=None

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
    game_day=urllib.unquote_plus(params["game_day"])
except:    
    pass
try:
    game_id=urllib.unquote_plus(params["game_id"])
except:
    pass
try:
    epg=urllib.unquote_plus(params["epg"])
except:
    pass
try:
    teams_stream=urllib.unquote_plus(params["teams_stream"])
except:
    pass
try:
    stream_date=urllib.unquote_plus(params["stream_date"])
except:
    pass


xbmc.log("Mode: "+str(mode))
#xbmc.log("URL: "+str(url))
xbmc.log("Name: "+str(name))



if mode==None or url==None:        
    categories()  

elif mode == 100:      
    #Todays Games            
    todaysGames(None)

elif mode == 101:
    #Prev and Next 
    todaysGames(game_day)    

elif mode == 104:    
    streamSelect(game_id, epg, teams_stream, stream_date)

elif mode == 105:
    #Yesterday's Games
    game_day = localToEastern()
    display_day = stringToDate(game_day, "%Y-%m-%d")            
    prev_day = display_day - timedelta(days=1)                
    todaysGames(prev_day.strftime("%Y-%m-%d"))

elif mode == 200:    
    gotoDate()

elif mode == 300:
    nhlVideos()

elif mode == 400:    
    logout('true')

elif mode == 500:
    myTeamsGames()

elif mode == 510:
    playTodaysFavoriteTeam()

elif mode == 515:
    getThumbnails()

elif mode == 900:
    playAllHighlights()
    

elif mode == 999:
    sys.exit()

xbmc.log(str(mode))
if mode==100 or mode==101 or mode==104 or mode==105 or mode==200 or mode==300 or mode==500 or mode==510: 
    setViewMode()
elif mode==None:
    getViewMode()
    
xbmc.log("My view mode " + VIEW_MODE)

if mode == 100:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
elif mode == 101:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False, updateListing=True)
else:
    xbmcplugin.endOfDirectory(addon_handle)
