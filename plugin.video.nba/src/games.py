import json
import datetime, time
from datetime import timedelta
import urllib,urllib2
import xbmc,xbmcplugin,xbmcgui
from xml.dom.minidom import parseString
import re
import sys, traceback
import calendar
from utils import *
from common import *
from request import Request
import vars

def getGameUrl(video_id, video_type, video_ishomefeed, start_time, duration):
    log("cookies: %s %s" % (video_type, vars.cookies), xbmc.LOGDEBUG)

    # video_type could be archive, live, condensed or oldseason
    if video_type not in ["live", "archive", "condensed"]:
        video_type = "archive"
    gt = 1
    if not video_ishomefeed:
        gt = 4
    if video_type == "condensed":
        gt = 8

    url = vars.config['publish_endpoint']
    headers = {
        'Cookie': vars.cookies,
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'iPad' if video_type == "live"
            else "AppleCoreMedia/1.0.0.8C148a (iPad; U; CPU OS 6_2_1 like Mac OS X; en_us)",
    }
    body = {
        'extid': str(video_id),
        'format': "xml",
        'gt': gt,
        'gs': vars.params.get("game_state", "3"),
        'type': 'game',
        'plid': vars.player_id,
    }

    if video_type == "live":
        line1 = "Start from Beginning"
        line2 = "Go LIVE"
        ret = xbmcgui.Dialog().select("Game Options", [line1, line2])
        if ret == -1:
            return
        elif ret == 0:
            if start_time:
                body['st'] = str(start_time)
                if duration:
                    body['dur'] = str(duration)
                else:
                    log("No end time, can't start from beginning", xbmc.LOGERROR)
            else:
                log("No start time can't start from beginning", xbmc.LOGERROR)
    else:
        if start_time:
            body['st'] = str(start_time)
            log("start_time: %s" % start_time, xbmc.LOGDEBUG)

            if duration:
                body['dur'] = str(duration)
                log("Duration: %s"% str(duration), xbmc.LOGDEBUG)
            else:
                log("No end time for game", xbmc.LOGDEBUG)
        else:
            log("No start time, can't start from beginning", xbmc.LOGERROR)

    if vars.params.get("camera_number"):
        body['cam'] = vars.params.get("camera_number")
    if video_type != "live":
        body['format'] = 'xml'
    body = urllib.urlencode(body)

    log("the body of publishpoint request is: %s" % body, xbmc.LOGDEBUG)

    try:
        request = urllib2.Request(url, body, headers)
        response = urllib2.urlopen(request)
        content = response.read()
    except urllib2.HTTPError as e:
        logHttpException(e, url)
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

        selected_video_url = "%s&Cookie=%s" % (url, livecookiesencoded)
    else:
        # Archive and condensed flow: We now work with HLS.
        # The cookies are already in the URL and the server will supply them to ffmpeg later.
        selected_video_url = getGameUrlWithBitrate(url, video_type)
        
        
    if selected_video_url:
        log("the url of video %s is %s" % (video_id, selected_video_url), xbmc.LOGDEBUG)

    return selected_video_url

def getHighlightGameUrl(video_id):
    url = 'https://watch.nba.com/service/publishpoint'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': "AppleCoreMedia/1.0.0.8C148a (iPad; U; CPU OS 6_2_1 like Mac OS X; en_us)",
    }
    
    body = urllib.urlencode({
        'extid': str(video_id),
        'plid': vars.player_id,
        'gt': "64",
        'type': 'game',
        'bitrate': "1600"
    })

    log("the body of publishpoint request is: %s" % body, xbmc.LOGDEBUG)

    try:
        request = urllib2.Request(url, body, headers)
        response = urllib2.urlopen(request)
        content = response.read()
    except urllib2.HTTPError as ex:
        log("Highlight url not found. Error: %s - body: %s" % (str(ex), ex.read()), xbmc.LOGERROR)
        return ''

    xml = parseString(str(content))
    url = xml.getElementsByTagName("path")[0].childNodes[0].nodeValue

    # Remove everything after ? otherwise XBMC fails to read the rtpm stream
    url, _,_ = url.partition("?")

    log("highlight video url: %s" % url, xbmc.LOGDEBUG)
    
    return url

def addGamesLinks(date = '', video_type = "archive"):
    try:
        now_datetime_est = nowEST()

        #example: http://smb.cdnak.neulion.com/fs/nba/feeds_s2012/schedule/2013/10_7.js?t=1381054350000
        schedule = 'http://smb.cdnak.neulion.com/fs/nba/feeds_s2012/schedule/%04d/%d_%d.js?t=%d' % \
            (date.year, date.month, date.day, time.time())
        log('Requesting %s' % schedule, xbmc.LOGDEBUG)

        schedule_request = urllib2.Request(schedule, None);
        schedule_response = str(urllib2.urlopen(schedule_request).read())
        schedule_json = json.loads(schedule_response[schedule_response.find("{"):])
        for index,daily_games in enumerate(schedule_json['games']):
            log("daily games for day %d are %s" % (index, daily_games), xbmc.LOGDEBUG)

            for game in daily_games:
                h = game.get('h', '')
                v = game.get('v', '')
                game_id = game.get('id', '')
                game_start_date_est = game.get('d', '')
                vs = game.get('vs', '')
                hs = game.get('hs', '')
                name = game.get('name', '')
                image = game.get('image', '')
                seo_name = game.get("seoName", "")
                has_condensed_video = game.get("video", {}).get("c", False)

                has_away_feed = False
                video_details = game.get('video', {})
                has_away_feed = bool(video_details.get("af", {}))

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

                if 'playoff' in game:
                    playoff_home_wins = int(game['playoff']['hr'].split("-")[0])
                    playoff_visitor_wins = int(game['playoff']['vr'].split("-")[0])
                    playoff_status = "%d-%d" % (playoff_visitor_wins, playoff_home_wins)
                    playoff_game_number = playoff_home_wins + playoff_visitor_wins

                if game_id != '':
                    # Get pretty names for the team names
                    if v.lower() in vars.config['teams']:
                        visitor_name = vars.config['teams'][v.lower()]
                    else:
                        visitor_name = v
                    if h.lower() in vars.config['teams']:
                        host_name = vars.config['teams'][h.lower()]
                    else:
                        host_name = h

                    has_video = "video" in game
                    future_video = game_start_datetime_est > now_datetime_est and \
                        game_start_datetime_est.date() == now_datetime_est.date()
                    live_video = game_start_datetime_est < now_datetime_est < game_end_datetime_est

                    # Create the title
                    if host_name and visitor_name:
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

                        thumbnail_url = ("http://i.cdn.turner.com/nba/nba/.element/img/1.0/teamsites/logos/teamlogos_500x500/%s.png" % h.lower())
                    elif image:
                        thumbnail_url = "https://neulionmdnyc-a.akamaihd.net/u/nba/nba/thumbs/%s" % image

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
                            'seo_name': seo_name,
                            'has_away_feed': 1 if has_away_feed else 0,
                            'has_condensed_game': 1 if has_condensed_video else 0,
                        }

                        if 'st' in game:
                            start_time = calendar.timegm(time.strptime(game['st'], '%Y-%m-%dT%H:%M:%S.%f')) * 1000
                            params['start_time'] = start_time
                            if 'et' in game:
                                end_time = calendar.timegm(time.strptime(game['et'], '%Y-%m-%dT%H:%M:%S.%f')) * 1000
                                params['end_time'] = end_time
                                params['duration'] = end_time - start_time
                            else:
                                # create my own et for game (now)
                                end_time = str(datetime.datetime.now()).replace(' ', 'T')
                                end_time = calendar.timegm(time.strptime(end_time, '%Y-%m-%dT%H:%M:%S.%f')) * 1000
                                params['end_time'] = end_time
                                params['duration'] = end_time - start_time

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
    start_time = vars.params.get("start_time")
    duration = vars.params.get("duration")
    currentvideo_ishomefeed = vars.params.get("video_ishomefeed", "1")
    currentvideo_ishomefeed = currentvideo_ishomefeed == "1"

    # Get the video url.
    # Authentication is needed over this point!
    currentvideo_url = getGameUrl(currentvideo_id, currentvideo_type, currentvideo_ishomefeed, start_time, duration)
    if currentvideo_url:
        item = xbmcgui.ListItem(path=currentvideo_url)
        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=item)

def chooseGameVideoMenu():
    video_id = vars.params.get("video_id")
    video_type = vars.params.get("video_type")
    seo_name = vars.params.get("seo_name")
    has_away_feed = vars.params.get("has_away_feed", "0") == "1"
    has_condensed_game = vars.params.get("has_condensed_game", "0") == "1"
    start_time = vars.params.get("start_time")
    duration = vars.params.get("duration")
    game_data_json = Request.getJson(vars.config['game_data_endpoint'] % seo_name)
    game_state = game_data_json['gameState']
    game_cameras = []
    if game_data_json['multiCameras']:
        game_cameras = game_data_json['multiCameras'].split(",")

    nba_config = Request.getJson(vars.config['config_endpoint'])
    nba_cameras = {}
    for camera in nba_config['content']['cameras']:
        nba_cameras[ camera['number'] ] = camera['name']

    if has_away_feed:
        # Create the "Home" and "Away" list items
        for ishomefeed in [True, False]:
            listitemname = "Full game, " + ("away feed" if not ishomefeed else "home feed")
            params = {
                'video_id': video_id,
                'video_type': video_type,
                'video_ishomefeed': 1 if ishomefeed else 0,
                'game_state': game_state,
                'start_time': start_time,
                'duration': duration,
            }
            addListItem(listitemname, url="", mode="playgame", iconimage="", customparams=params)
    else:
        #Add a "Home" list item
        params = {
            'video_id': video_id,
            'video_type': video_type,
            'game_state': game_state,
            'start_time': start_time,
            'duration': duration,
        }
        addListItem("Full game", url="", mode="playgame", iconimage="", customparams=params)

    #Add all the cameras available
    for camera_number in game_cameras:
        #Skip camera number 0 (broadcast?) - the full game links are the same
        camera_number = int(camera_number)
        if camera_number == 0:
            continue

        params = {
            'video_id': video_id,
            'video_type': video_type,
            'game_state': game_state,
            'camera_number': camera_number,
            'start_time': start_time,
            'duration': duration,
        }

        name = "Camera %d: %s" % (camera_number, nba_cameras[camera_number])
        addListItem(name
            , url="", mode="playgame", iconimage="", customparams=params)

    #Live games have no condensed or highlight link
    if video_type != "live":
        # Create the "Condensed" list item
        if has_condensed_game:
            params = {
                'video_id': video_id,
                'video_type': 'condensed',
                'game_state': game_state
            }
            addListItem("Condensed game", url="", mode="playgame", iconimage="", customparams=params)

        # Get the highlights video if available
        highlights_url = getHighlightGameUrl(video_id)
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
