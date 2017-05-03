import json,urllib2
import datetime, time
from datetime import timedelta
import xbmc,xbmcgui
import traceback

from utils import *
from common import * 
import vars

def addFavTeamGameLinks(fromDate, favTeam, video_type = 'archive'):
    try:
        if type(fromDate) is datetime.datetime:
            fromDate = "%04d/%d_%d" % (fromDate.year, fromDate.month, fromDate.day)
        schedule = 'http://smb.cdnak.neulion.com/fs/nba/feeds_s2012/schedule/' + fromDate +  '.js?t=' + "%d"  %time.time()
        log('Requesting %s' % schedule, xbmc.LOGDEBUG)

        now_datetime_est = nowEST()

        # http://smb.cdnak.neulion.com/fs/nba/feeds_s2012/schedule/2013/10_7.js?t=1381054350000
        req = urllib2.Request(schedule, None);
        response = str(urllib2.urlopen(req).read())
        js = json.loads(response[response.find("{"):])

        for game in reversed(js['games']):
            log(game, xbmc.LOGDEBUG)
            for details in game:
                h = details.get('h', '')
                v = details.get('v', '')
                game_id = details.get('id', '')
                game_start_date_est = details.get('d', '')
                vs = details.get('vs', '')
                hs = details.get('hs', '')
                gs = details.get('gs', '')

                video_has_away_feed = False
                video_details = details.get('video', {})
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

                if game_id != '' and (v.lower() == favTeam or h.lower() == favTeam):
                    # Get pretty names for the team names
                    if v.lower() in vars.config['teams']:
                        visitor_name = vars.config['teams'][v.lower()]
                    else:
                        visitor_name = v
                    if h.lower() in vars.config['teams']:
                        host_name = vars.config['teams'][h.lower()]
                    else:
                        host_name = h

                    has_video = "video" in details
                    future_video = game_start_datetime_est > now_datetime_est and \
                        game_start_datetime_est.date() == now_datetime_est.date()
                    live_video = game_start_datetime_est < now_datetime_est < game_end_datetime_est

                    # Create the title
                    name = game_start_datetime_est.strftime("%Y-%m-%d")
                    if video_type == "live":
                        name = toLocalTimezone(game_start_datetime_est).strftime("%Y-%m-%d (at %I:%M %p)")

                    #Add the teams' names and the scores if needed
                    name += ' %s vs %s' % (visitor_name, host_name)
                    if vars.scores == '1' and not future_video:
                        name += ' %s:%s' % (str(vs), str(hs))

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
                        awayFeed = video_has_away_feed and favTeam == v.lower()
                        params = {
                            'video_id': game_id,
                            'video_type': video_type,
                            'video_ishomefeed': 0 if awayFeed else 1
                        }
                        name = name + (' (away)' if awayFeed else ' (home)')
                                
                        addListItem(name, url="", mode="playgame", iconimage="", customparams=params)

    except Exception, e:
        xbmc.executebuiltin('Notification(NBA League Pass,'+str(e)+',5000,)')
        log(traceback.format_exc(), xbmc.LOGDEBUG)
        pass

def getCurrentMonday():
    tday = nowEST()
    return tday - timedelta(tday.isoweekday() - 1) # start on Monday

def favTeamMenu():
    updateFavTeam()

    if vars.fav_team is None:
        xbmcgui.Dialog().ok(vars.__addon_name__, 'Set your favourite team in the settings')
        xbmcaddon.Addon().openSettings()
        updateFavTeam()
        if vars.fav_team is None:
            addListItem('Set your favourite team in the settings', '', 'favteam', '', False)
            return

    log("Loading games for: " + vars.fav_team)
    tday = getCurrentMonday()
    addFavTeamGameLinks(tday, vars.fav_team, 'live')
    weeksBack = 0
    while monthIsInSeason(tday.month) and weeksBack < 3:
        addFavTeamGameLinks(tday, vars.fav_team)
        tday = tday - timedelta(7)
        weeksBack = weeksBack + 1

    if tday.month >= 10:
        addListItem('Older games', 'older', 'favteam', '', True)

def favTeamOlderMenu():
    updateFavTeam()
    
    log("Loading older games for: " + vars.fav_team)
    tday = getCurrentMonday() - timedelta(14)
    while monthIsInSeason(tday.month):
        addFavTeamGameLinks(tday, vars.fav_team)
        tday = tday - timedelta(7)

def monthIsInSeason(month):
    return month >= 10 or month <= 6
