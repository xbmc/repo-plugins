from resources.globals import *
from resources.adobepass import ADOBE

#Add-on specific Adobepass variables
SERVICE_VARS = {'requestor_id':'MML',
                'public_key':'XfId78vskMBegCUx9fuiNQL3XvxP3SzN',
                'private_key':'60OKORsYmOkUMgDm',
                'activate_url':'ncaa.com/activate'
               }

def categories():               
    addDir('Today\'s Games','/live',1,ICON,FANART)
    addDir('Archive Games','/live',2,ICON,FANART)
    addDir('Classic Games','/classic',3,ICON,FANART)
    addDir('Deauthorize this Device','/deauth',4,ICON,FANART)    


def todaysGames(archive=None):   
    now = datetime.now()
    url = 'http://data.ncaa.com/mml/'+str(now.year)+'/mobile/bracket.json'
    
    req = urllib2.Request(url)    
    req.add_header('Connection', 'keep-alive')
    req.add_header('Accept', '*/*')
    req.add_header('User-Agent', UA_MMOD)
    req.add_header('Accept-Language', 'en-us')
    req.add_header('Accept-Encoding', 'deflate')

    response = urllib2.urlopen(req)    
    json_source = json.load(response)                           
    response.close() 

    tourn_day = json_source['bracket']['tournDay'] 
    teams = getTournamentInfo()         

    
    if not archive:
        setTodaysStream(tourn_day, json_source, teams)
    else:
        setArchiveStreams(tourn_day, json_source, teams)

    
def setTodaysStream(tourn_day, json_source, teams):
    tomorrow = str(int(tourn_day) + 86400)            
    try:
        current_games = getCurrentInfo()
    except:
        pass

    #Sort By Start Time
    json_source = sorted(json_source['bracket']['game'],key=lambda x:x['time'])
    
    for game in json_source:
        if game['time'] >= tourn_day and  game['time'] < tomorrow:        
            if game['tmH'] != '' and game['tmV'] != '':                
                game_id = game['id']                
                hTeam = getTeamInfo(teams, game['tmH'])
                vTeam = getTeamInfo(teams,game['tmV'])    
                game_time = time.strftime('%I:%M %p', time.localtime(int(game['time']))).lstrip('0')    
                state = game['state']
                archive_video = game['rcpV']                
                
                title = vTeam['school'] + ' vs ' + hTeam['school']

                if NO_SPOILERS == '1' or NO_SPOILERS == '2':
                    name =  title
                else:
                    name =  '#'+ vTeam['seed']+ ' ' + vTeam['school'] + ' ' + colorString(game['ptsV'], SCORE_COLOR) + ' vs #'+ hTeam['seed']+ ' ' + hTeam['school'] + ' ' + colorString(game['ptsH'], SCORE_COLOR)

                if state == "1":                    
                    name =  colorString(game_time, UPCOMING) + ' ' + name
                elif state == "4":
                    name =  colorString("FINAL", FINAL) + ' ' + name
                else:
                    clock = getGameClock(current_games, game_id)
                    if clock == '':
                        clock = 'LIVE'
                    name =  colorString(clock,GAMETIME_COLOR) + ' ' + name

                
                link_url = ''             
                addStream(name,link_url,title,game_id)


def classicGames():
    now = datetime.now()    
    url = 'http://data.ncaa.com/mml/'+str(now.year)+'/mobile/vod/classic_games.json'    
    req = urllib2.Request(url)    
    req.add_header('Connection', 'keep-alive')
    req.add_header('Accept', '*/*')
    req.add_header('User-Agent', UA_MMOD)
    req.add_header('Accept-Language', 'en-us')
    req.add_header('Accept-Encoding', 'deflate')

    response = urllib2.urlopen(req)    
    json_source = json.load(response)                           
    response.close() 

    for game in json_source['videos']:
        title = game['title']
        url = game['connected'] + '|User-Agent='+UA_MMOD
        icon = game['thumbnails']['large']
        fanart = game['thumbnails']['raw']
        addLink(title,url,icon,fanart)



def setArchiveStreams(tourn_day, json_source, teams):
    json_source = sorted(json_source['bracket']['game'],key=lambda x:x['time'], reverse=True)
    for game in json_source:        
        if game['time'] < tourn_day:
            if game['tmH'] != '' and game['tmV'] != '':                
                game_id = game['id']                
                hTeam = getTeamInfo(teams, game['tmH'])
                vTeam = getTeamInfo(teams,game['tmV'])     
                game_time = time.strftime('%I:%M %p', time.localtime(int(game['time']))).lstrip('0')
                live_video = game['video']
                archive_video = game['rcpV']
                
                title = vTeam['school'] + ' vs ' + hTeam['school']

                if NO_SPOILERS == '1' or NO_SPOILERS == '3':
                    name =  title
                else:                    
                    name =  '#'+ vTeam['seed']+ ' ' + vTeam['school'] + ' ' + colorString(game['ptsV'], SCORE_COLOR) + ' vs ' + '#'+ hTeam['seed']+ ' ' + hTeam['school'] + ' ' + colorString(game['ptsH'], SCORE_COLOR)
                
                name =  colorString('FINAL ',FINAL) + name               
                link_url = 'archive'
                addStream(name,link_url,title,game_id)


def startStream(game_id):
    stream_url = fetchStream(game_id,addon_url)
    
    if addon_url == 'archive':        
        playable_stream = stream_url + '|User-Agent='+UA_MMOD
    else:
        adobe = ADOBE(SERVICE_VARS)        
        resource_id = 'truTV'
        mvpd = adobe.authorizeDevice(resource_id)        
        media_token = adobe.mediaToken(resource_id)          
        playable_stream = tokenTurner(media_token,stream_url,mvpd)        

    listitem = xbmcgui.ListItem(path=playable_stream)        
    xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=listitem)



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
addon_url=None
name=None
mode=None
game_id=None
icon_image = None

try:
    addon_url=urllib.unquote_plus(params["url"])
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
    game_id=urllib.unquote_plus(params["game_id"])
except:
    pass
try:
    icon_image=urllib.unquote_plus(params["icon_image"])
except:
    pass


if mode==None:        
    categories()        
elif mode==1:        
    todaysGames() 
elif mode==2:
    todaysGames(archive=True)
elif mode==3:
    classicGames()
elif mode==4:
    msg = 'Are you sure you wish to deauthorize this device?'
    dialog = xbmcgui.Dialog() 
    answer = dialog.yesno('Deauthorize Devices', msg)
    if answer:
        adobe = ADOBE(SERVICE_VARS)
        adobe.deauthorizeDevice()
    sys.exit()

elif mode==104:        
    startStream(game_id)
    

#Don't cache todays games
if mode==1:
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)
else:
    xbmcplugin.endOfDirectory(addon_handle)
