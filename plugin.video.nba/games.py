import json
import datetime, time
from datetime import timedelta
import urllib,urllib2
import xbmc,xbmcplugin,xbmcgui
from xml.dom.minidom import parseString
import re
import sys, traceback

from utils import *
from common import * 
import vars

def getGameUrl(video_id, video_type, video_ishomefeed):
    log("cookies: %s %s" % (video_type, vars.cookies), xbmc.LOGDEBUG)

    # video_type could be archive, live, condensed or oldseason
    if video_type not in ["live", "archive", "condensed"]:
        video_type = "archive"

    url = 'http://watch.nba.com/nba/servlets/publishpoint'
    headers = { 
        'Cookie': vars.cookies, 
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'iPad' if video_type == "live" 
            else "AppleCoreMedia/1.0.0.8C148a (iPad; U; CPU OS 6_2_1 like Mac OS X; en_us)",
    }
    body = { 
        'id': str(video_id), 
        'gt': video_type + ("away" if not video_ishomefeed else ""), 
        'type': 'game',
        'plid': vars.player_id,
        'nt': '1'
    }
    if video_type != "live":
        body['format'] = 'xml'
    body = urllib.urlencode(body)

    log("the body of publishpoint request is: %s" % body, xbmc.LOGDEBUG)

    try:
        request = urllib2.Request(url, body, headers)
        response = urllib2.urlopen(request)
        content = response.read()
    except urllib2.HTTPError as e:
        log("Failed to get video url. The url was %s, the content was %s" % (url, e.read()))

        littleErrorPopup( xbmcaddon.Addon().getLocalizedString(50020) )
        return ''

    xml = parseString(str(content))
    url = xml.getElementsByTagName("path")[0].childNodes[0].nodeValue
    log(url, xbmc.LOGDEBUG)

    selected_video_url = ''
    if video_type == "live":
        # transform the url
        match = re.search('http://([^:]+)/([^?]+?)\?(.+)$', url)
        domain = match.group(1)
        arguments = match.group(2)
        querystring = match.group(3)

        livecookies = "nlqptid=%s" % (querystring)
        livecookiesencoded = urllib.quote(livecookies)

        log("live cookie: %s %s" % (querystring, livecookies), xbmc.LOGDEBUG)

        url = "http://%s/%s?%s" % (domain, arguments, querystring)
        url = getGameUrlWithBitrate(url, video_type)

        selected_video_url = "%s|Cookie=%s" % (url, livecookiesencoded)
    else:
        # Archive and condensed flow: We now work with HLS. 
        # The cookies are already in the URL and the server will supply them to ffmpeg later.
        selected_video_url = getGameUrlWithBitrate(url, video_type)
        
        
    if selected_video_url:
        log("the url of video %s is %s" % (video_id, selected_video_url), xbmc.LOGDEBUG)

    return selected_video_url

def getHighlightGameUrl(video_id):
    url = 'http://watch.nba.com/nba/servlets/publishpoint'
    headers = {
        'Cookie': vars.cookies, 
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': "AppleCoreMedia/1.0.0.8C148a (iPad; U; CPU OS 6_2_1 like Mac OS X; en_us)",
    }
    
    body = urllib.urlencode({ 
        'id': str(video_id), 
        'gt': "recapf", 
        'type': 'game',
        'plid': vars.player_id,
        'isFlex': "true",
        'bitrate': "1600" # forced bitrate
    })

    log("the body of publishpoint request is: %s" % body, xbmc.LOGDEBUG)

    try:
        request = urllib2.Request(url, body, headers)
        response = urllib2.urlopen(request)
        content = response.read()
    except urllib2.HTTPError:
        return ''

    xml = parseString(str(content))
    url = xml.getElementsByTagName("path")[0].childNodes[0].nodeValue

    # Remove everything after ? otherwise XBMC fails to read the rtpm stream
    url, _,_ = url.partition("?")

    log("highlight video url: %s" % url, xbmc.LOGDEBUG)
    
    return url

def addGamesLinks(date = '', video_type = "archive"):
    try:
        schedule = 'http://smb.cdnak.neulion.com/fs/nba/feeds_s2012/schedule/%04d/%d_%d.js?t=%d' % \
            (date.year, date.month, date.day, time.time())

        #Download the scoreboard file for each day of the week
        scoreboards_jsons = {}
        for day_of_week in range(7):
            scoreboard = 'http://data.nba.com/jsonp/5s/json/cms/noseason/scoreboard/%04d%02d%02d/games.json?callback=ciao' % \
                (date.year, date.month, date.day+day_of_week)
            scoreboard_request = urllib2.Request(scoreboard, None);
            scoreboard_response = str(urllib2.urlopen(scoreboard_request).read())
            scoreboard_response = scoreboard_response[scoreboard_response.find("{"):scoreboard_response.rfind("}")+1]

            key = "%04d-%02d-%02d" % (date.year, date.month, date.day+day_of_week)
            scoreboards_jsons[key] = json.loads(scoreboard_response)

        log('Requesting %s' % schedule, xbmc.LOGDEBUG)

        now_datetime_est = nowEST()

        # http://smb.cdnak.neulion.com/fs/nba/feeds_s2012/schedule/2013/10_7.js?t=1381054350000
        schedule_request = urllib2.Request(schedule, None);
        schedule_response = str(urllib2.urlopen(schedule_request).read())
        schedule_json = json.loads(schedule_response[schedule_response.find("{"):])

        for daily_games in schedule_json['games']:
            log(daily_games, xbmc.LOGDEBUG)

            for game in daily_games:
                h = game.get('h', '')
                v = game.get('v', '')
                game_id = game.get('id', '')
                game_start_date_est = game.get('d', '')
                vs = game.get('vs', '')
                hs = game.get('hs', '')
                gs = game.get('gs', '')
                seo_name = game.get("seoName", "")

                video_has_away_feed = False
                video_details = game.get('video', {})
                video_has_away_feed = video_details.get("af", False)

                # Try to convert start date to datetime
                try:
                    game_start_datetime_est = datetime.datetime.strptime(game_start_date_est, "%Y-%m-%dT%H:%M:%S.%f" )
                except:
                    game_start_datetime_est = datetime.datetime.fromtimestamp(time.mktime(time.strptime(game_start_date_est, "%Y-%m-%dT%H:%M:%S.%f")))

                #Set game start date in the past if python can't parse the date
                #so it doesn't get flagged as live or future game and you can still play it
                #if a video is available
                if type(game_start_datetime_est) is not datetime.datetime:
                    game_start_datetime_est = now_datetime_est + timedelta(-30)

                #guess end date by adding 4 hours to start date
                game_end_datetime_est = game_start_datetime_est + timedelta(hours=4)

                #Get playoff game number, if available
                playoff_game_number = 0
                playoff_status = ""
                game_date = game_start_datetime_est.strftime('%Y-%m-%d')
                for game_more_data in scoreboards_jsons[game_date]['sports_content']['games']['game']:
                    if game_more_data['game_url'] == seo_name and game_more_data.get('playoffs', ''):
                        playoff_game_number = int(game_more_data['playoffs']['game_number'])

                        if game_more_data['playoffs'].get('home_wins', None) and game_more_data['playoffs'].get('visitor_wins', None):
                            playoff_status = "%s-%s" % (game_more_data['playoffs']['visitor_wins'], game_more_data['playoffs']['home_wins'])

                if game_id != '':
                    # Get pretty names for the team names
                    if v.lower() in vars.teams:
                        visitor_name = vars.teams[v.lower()]
                    else:
                        visitor_name = v
                    if h.lower() in vars.teams:
                        host_name = vars.teams[h.lower()]
                    else:
                        host_name = h

                    has_video = "video" in game
                    future_video = game_start_datetime_est > now_datetime_est and \
                        game_start_datetime_est.date() == now_datetime_est.date()
                    live_video = game_start_datetime_est < now_datetime_est < game_end_datetime_est

                    # Create the title
                    name = game_start_datetime_est.strftime("%Y-%m-%d")
                    if video_type == "live":
                        name = toLocalTimezone(game_start_datetime_est).strftime("%Y-%m-%d (at %I:%M %p)")

                    #Add the teams' names and the scores if needed
                    name += ' %s vs %s' % (visitor_name, host_name)
                    if playoff_game_number != 0:
                        name += ' (game %d)' % (playoff_game_number)
                    if vars.scores == '1' and not future_video:
                        name += ' %s:%s' % (str(vs), str(hs))

                        if playoff_status:
                            name += " (series: %s)" % playoff_status

                    thumbnail_url = ("http://e1.cdnl3.neulion.com/nba/player-v4/nba/images/teams/%s.png" % h)

                    if video_type == "live":
                        if future_video:
                            name = "UPCOMING: " + name
                        elif live_video:
                            name = "LIVE: " + name

                    add_link = True
                    if video_type == "live" and not (live_video or future_video):
                        add_link = False
                    elif video_type != "live" and (live_video or future_video):
                        add_link = False
                    elif not future_video and not has_video:
                        add_link = False

                    if add_link == True:
                        params = {
                            'video_id': game_id,
                            'video_type': video_type,
                            'video_hasawayfeed': 1 if video_has_away_feed else 0
                        }

                        # Add a directory item that contains home/away/condensed items
                        addListItem(name, url="", mode="gamechoosevideo", 
                            iconimage=thumbnail_url, isfolder=True, customparams=params)

    except Exception, e:
        littleErrorPopup("Error: %s" % str(e))
        log(traceback.format_exc(), xbmc.LOGDEBUG)
        pass

def playGame():
    # Authenticate
    if vars.cookies == '':
        vars.cookies = login()
    if not vars.cookies:
        return

    currentvideo_id = vars.params.get("video_id")
    currentvideo_type  = vars.params.get("video_type")
    currentvideo_ishomefeed = vars.params.get("video_ishomefeed", "1")
    currentvideo_ishomefeed = currentvideo_ishomefeed == "1"

    # Get the video url. 
    # Authentication is needed over this point!
    currentvideo_url = getGameUrl(currentvideo_id, currentvideo_type, currentvideo_ishomefeed)
    if currentvideo_url:
        item = xbmcgui.ListItem(path=currentvideo_url)
        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=item) 

def chooseGameVideoMenu():
    currentvideo_id = vars.params.get("video_id")
    currentvideo_type  = vars.params.get("video_type")
    currentvideo_hasawayfeed = vars.params.get("video_hasawayfeed", "0")
    currentvideo_hasawayfeed = currentvideo_hasawayfeed == "1"

    if currentvideo_hasawayfeed:
        # Create the "Home" and "Away" list items
        for ishomefeed in [True, False]:
            listitemname = "Full game, " + ("away feed" if not ishomefeed else "home feed")
            params = {
                'video_id': currentvideo_id,
                'video_type': currentvideo_type,
                'video_ishomefeed': 1 if ishomefeed else 0
            }
            addListItem(listitemname, url="", mode="playgame", iconimage="", customparams=params)
    else:
        #Add a "Home" list item
        params = {
            'video_id': currentvideo_id,
            'video_type': currentvideo_type
        }
        addListItem("Full game", url="", mode="playgame", iconimage="", customparams=params)

    # Create the "Condensed" list item
    if currentvideo_type != "live":
        params = {
            'video_id': currentvideo_id,
            'video_type': 'condensed'
        }
        addListItem("Condensed game", url="", mode="playgame", iconimage="", customparams=params)

        # Get the highlights video if available
        highlights_url = getHighlightGameUrl(currentvideo_id)
        if highlights_url:
            addVideoListItem("Highlights", highlights_url, iconimage="")

    xbmcplugin.endOfDirectory(handle = int(sys.argv[1]) )

def chooseGameMenu(mode, video_type, date2Use = None):
    try:
        if mode == "selectdate":
            date = getDate()
        elif mode == "oldseason":
            date = date2Use
        else:
            date = nowEST()
            log("current date (america timezone) is %s" % str(date), xbmc.LOGDEBUG)
        
        # starts on mondays
        day = date.isoweekday()
        date = date - timedelta(day-1)
        if mode == "lastweek":
            date = date - timedelta(7)
            
        addGamesLinks(date, video_type)

        # Can't sort the games list correctly because XBMC treats file items and directory
        # items differently and puts directory first, then file items (home/away feeds
        # require a directory item while only-home-feed games is a file item)
        #xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_DATE )
    except:
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),succeeded=False)
        return None

