import urllib2
import re

from xml.dom.minidom import parseString
from datetime import datetime
from dateutil import tz
import time
import pickle
import os
import json
import httplib2

from resources.lib.globals import *
from resources.lib.common import *

def getLiveGames(live):

    #Download live.xml
    downloadedXML =''
    for i in range(1, 2):
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        url = "http://gamecenter.nhl.com/nhlgc/servlets/games"                       
        #1#url = 'http://live.nhl.com/GameData/SeasonSchedule-20142015.json'                
        #2#http://smb.cdnak.neulion.com/fs/nhl/mobile/feed_new/data/streams/2014/ipad/02_0047.json
        #3#http://nlds150.cdnak.neulion.com/nlds_vod/nhl/vod/2014/10/15/47/2_47_bos_det_1415_a_whole_1_ipad.mp4.m3u8
        #4#http://nlds150.cdnak.neulion.com/nlds_vod/nhl/vod/2014/10/15/47/2_47_bos_det_1415_a_whole_1_5000_ipad.mp4.m3u8

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        if live:
            response = opener.open(url, urllib.urlencode({'format':'xml','app':'true'}))
        else:
            response = opener.open(url, urllib.urlencode({'format':'xml'}))
        downloadedXML = response.read()
        #print downloadedXML
        
        #Try to login again if File not accessible
        if "<code>noaccess</code>" in downloadedXML:
            print "No access to XML file"
            checkLogin()
            continue
        else:
            print "Download successful"
            break
    else:
        print "Login failed. Check your login credentials."
    
    
    #Parse the xml file
    xml = parseString(downloadedXML)
    games = xml.getElementsByTagName('game')
    
    if not live:
        games = reversed(games)
    
    #Get teamnames
    teams = getTeams()
        
    #Invert teams dictionary
    teams2 = {}
    for team in teams.keys():
        teams2[teams[team][4]] = team
    
    #List of live games
    gameList = []
   

    json_scoreboard = getScoreBoard(datetime.now().strftime("%Y-%m-%d"))     

    for game in games:
        #Setup variables
        gid = game.getElementsByTagName('gid')[0].childNodes[0].nodeValue
        season = game.getElementsByTagName('season')[0].childNodes[0].nodeValue
        Type = game.getElementsByTagName('type')[0].childNodes[0].nodeValue
        Id = game.getElementsByTagName('id')[0].childNodes[0].nodeValue
        awayTeam = game.getElementsByTagName('awayTeam')[0].childNodes[0].nodeValue
        homeTeam = game.getElementsByTagName('homeTeam')[0].childNodes[0].nodeValue
        date = game.getElementsByTagName('date')[0].childNodes[0].nodeValue
        #startTime = time.strptime(date,"%Y-%m-%d %H:%M:%S.0")
        startTime = time.strptime(date,"%Y-%m-%dT%H:%M:%S.000")


        homeTeamScore = ''
        awayTeamScore = ''
        gameTime = ''
        if SHOWSCORE == 'true':
           
            try:                
                ht = homeTeam
                at = awayTeam      
                json_scoreboard = getScoreBoard(date[0:10])                                       
                #Display Date
               
                for sb_game in json_scoreboard['games']:                                
                    #print homeTeam + " == " + str(sb_game['hta']) + " && " +  awayTeam + " == " + str(sb_game['ata'])
                    if ht == "MON":
                        ht = "MTL"
                    elif at == "MON":
                        at = "MTL"
                    elif ht == "CMB":
                        ht = "CBJ"
                    elif at == "CMB":
                        at = "CBJ"
                    elif ht == "SAN":
                        ht = "SJS"
                    elif at == "SAN":
                        at = "SJS"
                    elif ht == "TAM":
                        ht = "TBL"
                    elif at == "TAM":
                        at = "TBL"
                    elif ht == "LOS":
                        ht = "LAK"
                    elif at == "LOS":
                        at = "LAK"

                    if ht == str(sb_game['hta']) and at == str(sb_game['ata']):
                        #print "WE FOUND A MATCH"
                        homeTeamScore = '[COLOR=FF00B7EB]' + str(sb_game['hts']) +'[/COLOR]'
                        awayTeamScore = '[COLOR=FF00B7EB]' + str(sb_game['ats']) +'[/COLOR]'
                        gameTime = str(sb_game['bs'])                    
            except:
                pass

        
        #Game title
        title = ''
        
        #Check if stream is available
        try:
            if game.getElementsByTagName('hasProgram')[0].childNodes[0].nodeValue == 'true':
                gameStarted = True
            else:
                gameStarted = False
        except:
            gameStarted = False
        
        #Skip games that don't have a stream in 'Latest Games'
        if not live and not gameStarted:
            continue
        
        #Versus string
        versus = 31400 
        if ALTERNATIVEVS == 'true':
            versus = 31401
        
        if gameStarted and live:
            if gameTime == '':
                gameTime = "Live"
            #Displayed titlestring
            if awayTeam in teams and homeTeam in teams:                
                title = gameTime + " - " + teams[awayTeam][TEAMNAME] + " " + awayTeamScore + " " + LOCAL_STRING(versus) + " " + teams[homeTeam][TEAMNAME] + " " + homeTeamScore
            else:
                title = gameTime + " - " + awayTeam + " " + awayTeamScore + " " + LOCAL_STRING(versus) + " " + homeTeam + " " + homeTeamScore
        else:
            #Convert the time to the local timezone
            date = datetime.fromtimestamp(time.mktime(startTime))
            date = date.replace(tzinfo=tz.gettz('America/New_York'))            
            datelocal = date.astimezone(tz.tzlocal()).strftime(xbmc.getRegion('dateshort')+' '+xbmc.getRegion('time').replace('%H%H','%H').replace(':%S',''))           

            #Displayed titlestring
            if awayTeam in teams and homeTeam in teams:
                title = datelocal + ': ' + teams[awayTeam][TEAMNAME] + " " + awayTeamScore + " " + LOCAL_STRING(versus) + " " + teams[homeTeam][TEAMNAME] + " " + homeTeamScore                
            else:
                title = datelocal + ': ' + awayTeam + " " + awayTeamScore + " " + LOCAL_STRING(versus) + " " + homeTeam + " " + homeTeamScore
        
        #Add to the list of live games
        gameList.append([gid, season, Type, Id, gameStarted, title, homeTeam, awayTeam])
    
    
    #Save the gameList
    pickle.dump(gameList, open(os.path.join(ADDON_PATH_PROFILE, 'live'),"wb"))
    
    return gameList
  
    
def getLiveGameLinks(url):      
    #Load the list of games
    gameList = pickle.load(open(os.path.join(ADDON_PATH_PROFILE, 'live'),"rb"))
    
    #Get the url of the game
    for game in gameList:        
        if game[0] in url:
            #Add teamnames to the list
            homeTeam = game[6]
            awayTeam = game[7]
            linkList = [[homeTeam, awayTeam]]       
            feed_list = [2,4]

            #Add special video streams to list
            if FRENCH_FEED == 'true':
                feed_list.append(8)
            if GOALIE_CAM == 'true':
                feed_list.append(64)
                feed_list.append(128)
            
            for feed in feed_list:
                #Get the m3u8 URL                
                cj = cookielib.LWPCookieJar()
                cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
                publishPointURL = "http://gamecenter.nhl.com/nhlgc/servlets/publishpoint?type=game&id=" + game[1] + game[2].zfill(2) + game[3].zfill(4) + "&gs=live&ft=" + str(feed) + "&nt=1"
                print "publish point == " + publishPointURL
                opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
                if feed in [2,4]:
                    opener.addheaders = [('User-Agent', USERAGENT)]
                else:
                    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (iPad; CPU OS 7_0 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11A465 Safari/9537.53')]
                try:
                    response = opener.open(publishPointURL, urllib.urlencode({'app':'true'}))                
                    downloadedXML = response.read()
                except:
                    continue
                
                #publishPointURL = "http://gamecenter.nhl.com/nhlgc/servlets/publishpoint?type=game&id=%s&gs=%s&ft=%d&nt=1" % (gameID, playType, feedType)                
                #header = [('User-Agent', 'Mozilla/5.0 (iPad; CPU OS 7_0 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11A465 Safari/9537.53')]
                #downloadData, statusCode = downloadURL("publishPoint", publishPointURL, cj, header, urllib.urlencode({'app':'true'}), True)

                xml = parseString(downloadedXML)
                m3u8URL = xml.getElementsByTagName('path')[0].childNodes[0].nodeValue
				

            
                #Quality settings
                if QUALITY == 4 or 'bestquality' in url:
                    if "highlights" not in url:#fix needed to download the key below 
                        m3u8URL = m3u8URL.replace('_ced.', '_5000_ced.')   
                    else:
                        m3u8URL = m3u8URL.replace('_ced.', '_3000_ced.')   

                elif QUALITY == 3 or '5000K' in url:                    
                    if "highlights" not in url:
                        m3u8URL = m3u8URL.replace('_ced.', '_5000_ced.')
                    else:
                        m3u8URL = m3u8URL.replace('_ced.', '_3000_ced.')

                elif QUALITY == 2 or '3000K' in url:
                    m3u8URL = m3u8URL.replace('_ced.', '_3000_ced.')
                elif QUALITY == 1 or '1600K' in url:
                    m3u8URL = m3u8URL.replace('_ced.', '_1600_ced.')
                else:
                    m3u8URL = m3u8URL.replace('_ced.', '_800_ced.')
            
                #
                if 'condensed' in url:
                    m3u8URL = m3u8URL.replace('_whole_', '_condensed_')
                elif 'highlights' in url:
                    m3u8URL = m3u8URL.replace('_whole_', '_continuous_')
                


                #Header for needed for first decryption key
                header = {'Cookie' : 'nlqptid=' +  m3u8URL.split('?', 1)[1], 'User-Agent' : 'Safari/537.36 Mozilla/5.0 AppleWebKit/537.36 Chrome/31.0.1650.57', 'Accept-Encoding' : 'gzip,deflate', 'Connection' : 'Keep-Alive'}

            
                #Live games need additional cookies
                if "live" in url:
                    #Download the m3u8
                    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
                    opener.addheaders = [('Cookie', 'nlqptid=' +  m3u8URL.split('?', 1)[1])]
                    values = {}
                    login_data = urllib.urlencode(values)
                    response = opener.open(m3u8URL, login_data)
                    m3u8File = response.read()
                
                    #Download the keys
                    url2=''
                    for line in m3u8File.split("\n"):
                        searchTerm = "#EXT-X-KEY:METHOD=AES-128,URI="
                        if searchTerm in line:
                            url2=line.strip().replace(searchTerm,'')[1:-1]
                    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
                    values = {}
                    login_data = urllib.urlencode(values)
                    #This line was causing errors for buf/edm game 11/7/2014
                    #Seemed to run fine without a proper response...
                    try:
                        response = opener.open(url2, login_data)
                    except:
                        pass

                    #Remove unneeded cookies
                    remove = []
                    for cookie in cj:
                        if cookie.name != "nlqptid" and "as-live" not in cookie.name:
                            remove.append(cookie)
                    for cookie in remove:
                        cj.clear(cookie.domain, cookie.path, cookie.name)
            
                    #Create header needed for playback
                    cookies = ''
                    for cookie in cj:
                        cookies = cookies + cookie.name + "=" + cookie.value + "; "
            
                    header = {'Cookie' : cookies, 'User-Agent' : 'Safari/537.36 Mozilla/5.0 AppleWebKit/537.36 Chrome/31.0.1650.57', 'Accept-Encoding' : 'gzip,deflate', 'Connection' : 'Keep-Alive'}
                    #header = {'Cookie' : cookies, 'User-Agent' : 'NHL1415/4.1030 CFNetwork/711.1.12 Darwin/14.0.0', 'Accept-Encoding' : 'gzip,deflate', 'Connection' : 'Keep-Alive'}
					
                #Set CDN Server
                m3u8URL = cdnServer(m3u8URL)

                #Get teamnames
                teams = getTeams()
                
                if feed == 2:
                    #Home                    
                    linkList.append(['[B]'+LOCAL_STRING(31320)+"[/B] ("+teams[homeTeam][TEAMNAME]+" feed)", m3u8URL + "|" + urllib.urlencode(header)])      
                elif feed == 4:
                    #Away                    
                    linkList.append(['[B]'+LOCAL_STRING(31330)+"[/B] ("+teams[awayTeam][TEAMNAME]+" feed)", m3u8URL + "|" + urllib.urlencode(header)])
                elif feed == 8:
                    #French
                    linkList.append(['[B]French feed[/B]', m3u8URL + "|" + urllib.urlencode(header)])
                elif feed == 64:
                    #Goalie Cam Left
                    linkList.append(['[B]Goalie Cam 1[/B]', m3u8URL + "|" + urllib.urlencode(header)])      
                elif feed == 128:
                    #Goalie Cam Right
                    linkList.append(['[B]Goalie Cam 2[/B]', m3u8URL + "|" + urllib.urlencode(header)])
                

				
            break
    
    return linkList


def getScoreBoard(date):
    url = "http://live.nhle.com/GameData/GCScoreboard/"+date+".jsonp"
    print url
    http = httplib2.Http()
    http.disable_ssl_certificate_validation = True
    
    response, content = http.request(url, 'GET')
    jsonData = content.strip()

    jsonData = jsonData.replace('loadScoreboard(', '')
    jsonData = jsonData.rstrip(')')

    json_source = json.loads(jsonData)

    return json_source
