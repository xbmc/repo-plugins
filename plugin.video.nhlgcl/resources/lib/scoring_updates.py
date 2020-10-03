import xbmc, xbmcplugin, xbmcgui, xbmcaddon
from time import sleep
from datetime import datetime
import urllib, urllib2
import json
import pytz

ADDON = xbmcaddon.Addon(id='plugin.video.nhlgcl')
ADDON_PATH = xbmc.translatePath(ADDON.getAddonInfo('path'))
UA_IPAD = 'Mozilla/5.0 (iPad; CPU OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Mobile/12H143 ipad nhl 5.0925'
nhl_logo = ADDON_PATH+'/resources/lib/nhl_logo.png'

#Colors
SCORE_COLOR = 'FF00B7EB'
GAMETIME_COLOR = 'FFFFFF66'

def local_to_eastern():
    eastern = pytz.timezone('US/Eastern')    
    local_to_utc = datetime.now(pytz.timezone('UTC'))    
    local_to_eastern = local_to_utc.astimezone(eastern).strftime('%Y-%m-%d')
    return local_to_eastern


def getScoreBoard(date):     
    url = 'http://statsapi.web.nhl.com/api/v1/schedule?teamId=&date='+date+'&expand=schedule.teams,schedule.linescore,schedule.game.content.media.epg,schedule.broadcasts,schedule.scoringplays,team.leaders,leaders.person,schedule.ticket,schedule.game.content.highlights.scoreboard,schedule.ticket&leaderCategories=points'         
    req = urllib2.Request(url)    
    req.add_header('Connection', 'keep-alive')
    req.add_header('Accept', 'application/json')
    req.add_header('User-Agent', UA_IPAD)
    req.add_header('Accept-Language', 'en-us')
    req.add_header('Accept-Encoding', 'deflate')

    response = urllib2.urlopen(req)    
    json_source = json.load(response)      
    response.close()

    return json_source


def startScoringUpdatesTEST():
    dialog = xbmcgui.Dialog()  
    title = "Score Notifications"  
    dialog.notification(title, 'Starting...', '', 5000, False)     
   
    wait = 5
    monitor = xbmc.Monitor()    

    while True:        
        xbmc.log("**************Running**********************")     

        if monitor.waitForAbort(wait):       
            xbmc.log("**************Abort Called**********************")     
            break

    sys.exit()


def startScoringUpdates():
    dialog = xbmcgui.Dialog()  
    title = "Score Notifications"  
    dialog.notification(title, 'Starting...', nhl_logo, 5000, False)  
    ADDON.setSetting(id='score_updates', value='true')
        
    FIRST_TIME_THRU = 1  
    OLD_GAME_STATS = []              
    todays_date = local_to_eastern()
    wait = 30
    monitor = xbmc.Monitor()    

    while ADDON.getSetting(id="score_updates") == 'true' and not monitor.abortRequested():        
        video_playing = ''
        if xbmc.Player().isPlayingVideo():
            video_playing = xbmc.Player().getPlayingFile()                                                    
            video_playing = video_playing.lower()
        
        json_source = getScoreBoard(todays_date)   
        NEW_GAME_STATS = []
        #wait = json_source['wait']            
        for game in json_source['dates'][0]['games']:
            #Break out of loop if updates disabled
            if ADDON.getSetting(id="score_updates") == 'false':                                       
                break

            gid = str(game['gamePk'])
            ateam = game['teams']['away']['team']['abbreviation']
            hteam = game['teams']['home']['team']['abbreviation']
            ascore = str(game['linescore']['teams']['away']['goals'])
            hscore = str(game['linescore']['teams']['home']['goals'])
                            
            #Team names (these can be found in the live streams url)
            atcommon = game['teams']['away']['team']['abbreviation']
            htcommon = game['teams']['home']['team']['abbreviation']
            gameclock = game['status']['detailedState']

            current_period = game['linescore']['currentPeriod']            
            try:
                current_period = game['linescore']['currentPeriodOrdinal']                
            except:
                pass
            
            desc = ''
            headshot = ''
            try:
                desc = game['scoringPlays'][-1]['result']['description']
                
                #Remove Assists if there are none
                if ', assists: none' in desc: desc = desc[:desc.find(', assists: none')]

                player_id = game['scoringPlays'][-1]['players'][0]['player']['link']
                #/api/v1/people/8474034
                player_id = player_id[player_id.rfind('/')+1:]                
                headshot = 'http://nhl.bamcontent.com/images/headshots/current/60x60/'+player_id+'@2x.png'                
            except:
                pass

            if 'In Progress' in gameclock:            
                gameclock = game['linescore']['currentPeriodTimeRemaining']+' '+game['linescore']['currentPeriodOrdinal']
            
            
            #Disable spoiler by not showing score notifications for the game the user is currently watching
            if video_playing.find(atcommon.lower()) == -1 and video_playing.find(htcommon.lower()) == -1:
                NEW_GAME_STATS.append([gid,ateam,hteam,ascore,hscore,gameclock,current_period,desc,headshot])
                

        if FIRST_TIME_THRU != 1:
            display_seconds = int(ADDON.getSetting(id="display_seconds"))
            if display_seconds > 60:
                #Max Seconds 60
                display_seconds = 60
            elif display_seconds < 1:
                #Min Seconds 1
                display_seconds = 1

            #Convert to milliseconds
            display_milliseconds = display_seconds * 1000
            all_games_finished = 1
            for new_item in NEW_GAME_STATS:                                    

                if ADDON.getSetting(id="score_updates") == 'false':                                       
                    break
                #Check if all games have finished
                if new_item[5].upper().find('FINAL') == -1:
                    all_games_finished = 0

                for old_item in OLD_GAME_STATS:                    
                    #Break out of loop if updates disabled
                    if ADDON.getSetting(id="score_updates") == 'false':                                       
                        break
                    if new_item[0] == old_item[0]:
                        #--------------------------
                        # Array key
                        #--------------------------
                        # 0 = game id
                        # 1 = away team
                        # 2 = home team
                        # 3 = away score
                        # 4 = home score
                        # 5 = game clock
                        # 6 = current period
                        # 7 = goal description
                        # 8 = headshot img url
                        #--------------------------
                        
                        #If the score for either team has changed and is greater than zero.                                                       #Or if the game has just ended show the final score                  #Or the current peroid has changed
                        if  ((new_item[3] != old_item[3] and int(new_item[3]) != 0) or (new_item[4] != old_item[4] and int(new_item[4]) != 0)) or (new_item[5].upper().find('FINAL') != -1 and old_item[5].upper().find('FINAL') == -1) or (new_item[6] != old_item[6]):
                            #Game variables                                                    
                            ateam = new_item[1]
                            hteam = new_item[2]
                            ascore = new_item[3]
                            hscore = new_item[4]
                            gameclock = new_item[5]             
                            current_period = new_item[6]      
                            desc = new_item[7]
                            headshot = new_item[8]
                            


                            
                            notify_mode = ''
                            if new_item[5].upper().find('FINAL') != -1:
                                #Highlight score of the winning team
                                notify_mode = 'final'
                                title = 'Final Score'
                                if int(ascore) > int(hscore):
                                    message = '[COLOR='+SCORE_COLOR+']' + ateam + ' ' + ascore + '[/COLOR]    ' + hteam + ' ' + hscore + '    [COLOR='+GAMETIME_COLOR+']' + gameclock + '[/COLOR]'
                                else:
                                    message = ateam + ' ' + ascore + '    [COLOR='+SCORE_COLOR+']' + hteam + ' ' + hscore + '[/COLOR]    [COLOR='+GAMETIME_COLOR+']' + gameclock  + '[/COLOR]'

                            elif new_item[6] != old_item[6]:
                                #Notify user that the game has started / period has changed
                                notify_mode = 'game'
                                title = "Game Update"
                                message = ateam + ' ' + ascore + '    ' + hteam + ' ' + hscore + '   [COLOR='+GAMETIME_COLOR+']' + current_period + ' has started[/COLOR]'
                            
                            else:                                                                
                                #Highlight score for the team that just scored a goal
                                notify_mode = 'score'
                                if new_item[3] != old_item[3]: ascore = '[COLOR='+SCORE_COLOR+']'+new_item[3]+'[/COLOR]'                                                                
                                if new_item[4] != old_item[4]: hscore = '[COLOR='+SCORE_COLOR+']'+new_item[4]+'[/COLOR]'
                                                                
                                if ADDON.getSetting(id="goal_desc") == 'false':
                                    title = 'Score Update'
                                    message = ateam + ' ' + ascore + '    ' + hteam + ' ' + hscore + '    [COLOR='+GAMETIME_COLOR+']' + gameclock + '[/COLOR]'
                                else:                                
                                    title = ateam + ' ' + ascore + '    ' + hteam + ' ' + hscore + '    [COLOR='+GAMETIME_COLOR+']' + gameclock + '[/COLOR]'
                                    message = desc

                            if ADDON.getSetting(id="score_updates") != 'false':                                                                                      
                                dialog = xbmcgui.Dialog()
                                img = nhl_logo
                                #Get goal scorers head shot if notification is a score update
                                if ADDON.getSetting(id="goal_desc") == 'true' and notify_mode == 'score' and headshot != '': img = headshot
                                dialog.notification(title, message, img, display_milliseconds, False)
                                sleep(display_seconds+5)

            #if all games have finished for the night kill the thread
            if all_games_finished == 1 and ADDON.getSetting(id="score_updates") == 'true':                    
                ADDON.setSetting(id='score_updates', value='false')
                #If the user is watching a game don't display the all games finished message
                if 'nhl_game_video' not in video_playing:
                    dialog = xbmcgui.Dialog() 
                    title = "Score Notifications"
                    dialog.notification(title, 'All games have ended, good night.', nhl_logo, 5000, False)

        OLD_GAME_STATS = []
        OLD_GAME_STATS = NEW_GAME_STATS 
        
                    
        FIRST_TIME_THRU = 0          
        #sleep(int(60))   
        #sleep(int(wait))
        #If kodi exits break out of loop
        if monitor.waitForAbort(wait):       
            xbmc.log("**************Abort Called**********************")     
            break
   
    
dialog = xbmcgui.Dialog()  
title = "Score Notifications"  
#Toggle the setting
if ADDON.getSetting(id="score_updates") == 'false':        
    ADDON.setSetting(id='score_updates', value='true')   
    dialog.notification(title, 'Starting...', nhl_logo, 5000, False)  
    startScoringUpdates()    
else:    
    ADDON.setSetting(id='score_updates', value='false')    
    dialog.notification(title, 'Stopping...', nhl_logo, 5000, False)
