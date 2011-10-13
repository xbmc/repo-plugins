import weblogin, gethtml, hs_rss

import urllib, re, os, datetime, sys
from BeautifulSoup import BeautifulSoup
import xbmcplugin, xbmcaddon, xbmcgui

super_verbose_logging = False

__addonname__ = 'plugin.video.hockeystreams'
__datapath__ = 'special://profile/addon_data/' +__addonname__

#important! deals with a bug where errors are thrown if directory does not exist.
if not os.path.exists: os.makedirs(__datapath__)
cookiepath = __datapath__


__plugin__ = "Hockeystreams"
__author__ = "wotever"
__version__ = "1.7.1"
__url__ = "https://github.com/jlongman/xbmc-hockeystreams-plugin/"
__settings__ = xbmcaddon.Addon(id='plugin.video.hockeystreams')

__dbg__ = __settings__.getSetting("debug") == "true"
__mark_broken_cdn4_links__ = __settings__.getSetting("mark_cdn4") == "true"

hockeystreams = 'http://www.hockeystreams.com'
archivestreams = hockeystreams + '/hockey_archives'

hqStreams = re.compile('/live_streams/.*')
hqArchives = re.compile('/hockey_archives/0/.*/[0-9]+')
archivePlaybackTypes = re.compile('/hockey_archives/0/.*/[0-9]+/[a-z_]+')
livePlaybackTypes = re.compile('/live_streams/.*/[0-9]+/[a-z_]+')

today = datetime.date.today()

ARCHIVE_STRIP = " hockey archives 0 "
LIVE_STRIP = " live streams "

empty = None
directLinks = {}
games = {}

def get_date(day, month, year):
    archiveMonth = str(month)
    if len(archiveMonth) == 1:
        archiveMonth = '0' + archiveMonth
    archiveDay = str(day)
    if len(archiveDay) == 1:
        archiveDay = '0' + archiveDay
    archiveDate = '-'.join([archiveMonth, archiveDay, str(year)])
    return archiveDate

archiveDate = get_date(today.day, today.month, today.year)

def YEAR(url, mode):
    addDir("Last 15 games", url, 6, '', 1)
    for year in range(today.year, 2009, -1):
        if year == today.year:
            monthsCount = today.month
        else:
            monthsCount = 12
        addDir(str(year), url, mode, '', monthsCount, year)

def MONTH(url, year, mode):
    if year == today.year:
        startmonth = today.month
    else:
        startmonth = 12
    for month in range(startmonth, 0, -1):
        patsy = datetime.date(int(year), int(month), 1)
        days_in_month = int(patsy.strftime("%d"))
        if month == patsy.month:
            daysCount = today.day
        else:
            daysCount = days_in_month
        addDir(patsy.strftime("%B"), url, mode, '', daysCount, year, month)

def DAY(url, year, month, mode):
    startday = 31
    if year == today.year and month == today.month:
        startday = today.day

    for day in range(startday, 0, -1):
        try:
            patsy = datetime.date(year, month, day)
            addDir(patsy.strftime("%x"), url, mode, '', 1, year, month, day)
        except ValueError:
            pass # skip day


def get_params():
    param = {}
    paramstring = sys.argv[2]
    if(len(paramstring) >= 2):
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if(params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsOfParams = cleanedparams.split('&')
        for i in range(len(pairsOfParams)):
            splitParams = pairsOfParams[i].split('=')
            if(len(splitParams) == 2):
                param[splitParams[0]] = splitParams[1]
    return param

def soupIt(currentUrl, selector, gameType, loginRequired = False):
    if (__dbg__):
        if gameType != empty:
            print ("hockeystreams: enter soupIt url %s selector %s gameType %s" % (
            currentUrl, selector, gameType.pattern))
        else:
            print (
            "hockeystreams: enter soupIt  url %s selector %s gameType %s" % (currentUrl, selector, "empty"))
    if loginRequired:
        try:
            html = gethtml.get(currentUrl, cookiepath=cookiepath, debug=__dbg__)
        except IndexError:
            __settings__.openSettings()
            login()
            return soupIt(currentUrl, selector, gameType, loginRequired)
    else:
        html = gethtml.get(currentUrl, debug=__dbg__)

    if (__dbg__ and super_verbose_logging):
        print ("hockeystreams: \t\tfetch browser result %s " % html)

    
    if (__dbg__):
        print ("hockeystreams: \t\t soupIt %s " % html)
    soup = BeautifulSoup(''.join(html))

    if selector == 'input':
        found = soup.findAll('input')
        found.extend(soup.findAll('href'))
    else:
        found = soup.findAll(attrs={'href': gameType})
    del selector
    print "hockeystreams: soupit: found count " + str(len(found))
    return found


def addDir(name, url, mode, icon, count, year=-1, month=-1, day=-1, gamename = None, fullDate = None):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
    if gamename is not None:
        u += "&gamename=" + urllib.quote_plus(gamename)
    if year > 0:
        u += "&year=" + str(year)
        if month > 0:
            u += "&month=" + str(month)
            if day > 0:
                u += "&day=" + str(day)
    liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=icon)
    if fullDate is not None:
        liz.setInfo(type="Video", infoLabels={"Title": name, "Date" : str(fullDate)})
    else:
        liz.setInfo(type="Video", infoLabels={"Title": name})

    if (__dbg__):
        print str("about to add url %s modes %s name %s  directory" % (u, str(mode), name))
        print str("about to add icon: " + icon)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=str(u), listitem=liz, isFolder=True, totalItems=count)
    return ok

def addLink(name, gamename, date, url, icon, count, mode = 2001):
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name) + \
        "&gamename=" + urllib.quote_plus(gamename)
    liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=icon)
    liz.setInfo(type="Video", infoLabels={"Title": gamename, "Date": date})
    liz.setProperty('isPlayable', 'true')
    if (__dbg__):
        print ("about to add %s %s %d link" % (name, u, int(count)))
    ok = xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, isFolder=False, totalItems=count)
    return ok

def find_hockey_game_names(url, gameType):
    foundGames = soupIt(url, 'attrs', gameType)
    for test in foundGames:
        if (__dbg__):
            print ("hockeystreams: \t\t foundGames %s" % str(test))

        ending = str(test['href'])
        gamePage = hockeystreams + ending
        gameName = os.path.dirname(gamePage)
        if "archive" in url and gameName.endswith(archiveDate):
            if (__dbg__): print "\t\t\tskipping " + str(ending)
            continue
        gameName = re.sub('_|/', ' ', gameName)

        if (__dbg__):
            print ("hockeystreams: \t\t gamename %s" % gameName)
        games[gameName] = gamePage
    del foundGames
    return games


def login():
    if (__dbg__):
        print ("hockeystreams: login attempt")
    if not __settings__.getSetting('username') or not __settings__.getSetting('password'):
        __settings__.openSettings()
        return False
    if not weblogin.doLogin(cookiepath, __settings__.getSetting('username'), __settings__.getSetting('password'), __dbg__):
        if (__dbg__):
            print ("hockeystreams: login fail")
        return False
    return True


def find_qualities(url):
    if (__dbg__):
        print ("hockeystreams: \t\t find qs ")

    if 'archive' in url:
        foundQs = soupIt(url, 'attrs', archivePlaybackTypes, True)
    else:
        foundQs = soupIt(url, 'attrs', livePlaybackTypes, True)
    for test in foundQs:
        if (__dbg__):
            print ("hockeystreams: \t\t soupfound qs %s" % (str(test)))

        ending = str(test['href'])
        gamePage = hockeystreams + ending
        gameName = os.path.basename(gamePage)
        gameName = re.sub('_|/', ' ', gameName)
        if (__dbg__):
            print ("hockeystreams: \t\t q: %s" % gameName)
        games[gameName] = gamePage
    del foundQs
    return games

def CATEGORIES():
    if (__dbg__):
        print ("hockeystreams: enter categories")
    addDir('Today\'s Streams', hockeystreams, 1, '', 1)
    addDir('Archived By Date', hockeystreams, 2, '', 1)
    addDir('Archived By Team', hockeystreams, 30, '', 1)
    addDir('  Login', hockeystreams, 66, '', 1)
    addDir('  IP Exception', hockeystreams, 99, '', 1)
    
    #addDir('RSS Streams', hockeystreams, 3, '', 1)

def LIVE_GAMES(mode):
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    if (__dbg__):
        print ("hockeystreams: enter live games")
    html = urllib.urlopen("http://www4.hockeystreams.com/rss/streams.php")
    games = hs_rss.get_rss_streams(html, _debug_ = __dbg__)
    for gameName, url, date, real_date in sorted(games, key = lambda game: game[3]):
        if '-' in date:
            gameName = gameName + " " + date.split(' - ', 1)[1]
        addDir(gameName, url, mode, '', 1, gamename = gameName, fullDate = real_date)

def LAST_15_GAMES(mode):
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
    if (__dbg__):
        print ("hockeystreams: enter live games")
    html = urllib.urlopen("http://www6.hockeystreams.com/rss/archives.php")
    games = hs_rss.get_archive_rss_streams(html, _debug_ = __dbg__)
    for gameName, url, date, real_date in sorted(games, key = lambda game: game[3], reverse=True):
        gameName = gameName + " " + date
        url = hockeystreams + url
        addDir(gameName, url, mode, '', 1, gamename = gameName, fullDate = real_date)

def ARCHIVE_GAMES_BY_DATE(year, month, day, mode):
    if (__dbg__):
        print ("hockeystreams: enter archive games")
    archiveDate = get_date(day, month, year)
    url = archivestreams + '/' + archiveDate + '/'
    strip = ARCHIVE_STRIP
    games = find_hockey_game_names(url, hqArchives)
    for k, v in games.iteritems():
        gameName = k
        offset = gameName.index(strip) + len(strip)
        gameName = gameName[offset:]
        addDir(gameName, v, mode, '', 1, gamename = gameName)

def BY_TEAM(url, mode):
    if (__dbg__):
        print ("hockeystreams: enter team")
    archiveDate = get_date(today.day, today.month, today.year)
    teamNames = re.compile('/hockey_archives/'+ archiveDate + '/[a-z]+_?[a-z]?') #simplified
    foundTeams = soupIt(url + "/" + archiveDate, "attrs", teamNames)
    for team in foundTeams:
        if (__dbg__):
            print ("hockeystreams: \t\t soupfound team %s" % (str(team)))

        ending = str(team['href'])
        teamPage = hockeystreams + ending
        teamName = os.path.basename(teamPage)
        teamName = re.sub('_|/', ' ', teamName)
        if (__dbg__):
            print ("hockeystreams: \t\t team %s" % teamName)

        image_name = teamName[0:teamName.rfind(' ')]
        image_name = image_name.replace(' ','')
#        teamGIF = "http://www5.hockeystreams.com/images/teams/big/" + image_name + ".gif"
        teamGIF = "http://www5.hockeystreams.com/images/teams/" + image_name + ".gif"
        if (__dbg__): print ("hockeystreams: \t\t team %s %s" % (teamName, teamGIF))
        addDir(teamName, teamPage, mode, teamGIF, 82)

def ARCHIVE_GAMES_BY_TEAM(url, mode):
    if (__dbg__):
        print ("hockeystreams: enter archive games")
    strip = ARCHIVE_STRIP
    games = find_hockey_game_names(url, hqArchives)
    for k, v in games.iteritems():
        gameName = k
        offset = gameName.find(strip) + len(strip)
        gameName = gameName[offset:]
        addDir(gameName, v, mode, '', 1000, gamename = gameName)

def QUALITY(url, gamename):
    if (__dbg__):
        print ("hockeystreams: enter quality")
    games = find_qualities(url)
    if not __mark_broken_cdn4_links__:
        return QUALITY_quick(games, gamename)
    else:
        return QUALITY_slow(games, gamename)

def QUALITY_slow(games, gamename):
    silverLinks = {}
    for k, v in games.iteritems():
        if (__dbg__):
            print "game qs: " + str(games)
        
        foundGames = soupIt(v,'input',empty, True)
        for test in foundGames:                                 ##get rid of this 'busy loop' in the next minor revision
            if (__dbg__):
                print("hockeystreams: \t\t soupfound directs %s" % test)
            if 'direct_link' in test.get('id',''):
                directLink = test['value']
                directLinks[k] = directLink
            if 'silverlight' in test.get('href','') and 'archive' in test.get('href',''):
                if (__dbg__):
                    print "silverBOO"
                silverLink = test.get('href','')
                silverLinks["silverlight"] = silverLink

    for name,url in directLinks.iteritems():
        qualityName = name #name[name.rindex('/'):]
        if __mark_broken_cdn4_links__ and 'cdn-a-4' in url:
            qualityName += "*"
        addLink(qualityName, gamename, '', url, '', 1)
    for name,url in silverLinks.iteritems():
        addLink("has " + name, name, '', url, '', 1)



def QUALITY_quick(games, gamename):
    for quality, url in games.iteritems():
        if (__dbg__):
            print "game qs: " + str(games)
        addLink(quality, gamename, '', url, '', 1, 2000)

def QUICK_PLAY_VIDEO(almost_video_url):
    foundGames = soupIt(almost_video_url,'input',empty, True)
    for test in foundGames:                                 ##get rid of this 'busy loop' in the next minor revision
        if (__dbg__):
            print("hockeystreams: \t\t quick directs %s" % test)
        if 'direct_link' in test.get('id',''):
            directLink = test['value']
            directLinks[almost_video_url] = directLink
            PLAY_VIDEO(directLink)


def PLAY_VIDEO(video_url):
    if (__dbg__):
        print ("hockeystreams: enter play (gamename " + gamename + ")")
    # cool, got it, now create and open the video
    liz = xbmcgui.ListItem(gamename, path = video_url)
    liz.setInfo(type = "Video", infoLabels = {"Title": gamename})
    liz.setProperty('isPlayable', 'true')
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

params = get_params()
gamename = None
url = None
name = None
mode = None
year = None
month = None
day = None

try:
    url = urllib.unquote_plus(params['url'])
except:
    pass
try:
    name = urllib.unquote_plus(params['name'])
except:
    pass
try:
    gamename = urllib.unquote_plus(params['gamename'])
except:
    pass

try:
    mode = int(params['mode'])
except:
    pass

try:
    year = int(params['year'])
    month = int(params['month'])
    day = int(params['day'])
except:
    pass

if (__dbg__):
    print ("url %s name %s mode %s" % (url, name, mode))
    print ("year %s month %s day %s" % (year, month, day))

cache = True
if mode is None or mode == 0 or url is None or len(url) < 1:
    CATEGORIES()
elif mode == 1:
    cache = False
    LIVE_GAMES(1000)
elif mode == 2:
    cache = False
    YEAR(hockeystreams, 3)
elif mode == 3:
    cache = today.year != year
    MONTH(hockeystreams, year, 4)
elif mode == 4:
    cache = not (today.year == year and today.month == month)
    DAY(hockeystreams, year, month, 5)
elif mode == 5:
    cache = not (today.year == year and today.month == month and today.day == day)
    ARCHIVE_GAMES_BY_DATE(year, month, day, 1000)
elif mode == 6:
    cache = False
    LAST_15_GAMES(1000)
elif mode == 30:
    BY_TEAM(archivestreams, 31)
elif mode == 31:
    cache = False
    ARCHIVE_GAMES_BY_TEAM(url, 1000)
elif mode == 1000:
    cache = False
    QUALITY(url, gamename)
elif mode == 2000:
    cache = not (today.year == year and today.month == month and today.day == day)
    QUICK_PLAY_VIDEO(url)
elif mode == 2001:
    cache = not (today.year == year and today.month == month and today.day == day)
    PLAY_VIDEO(url)


elif mode == 66:
    cache = False
    if not login():
        print "failed"
        addDir('failed!', hockeystreams, 0, '', 5)
    else:
        addDir('succeeded!', hockeystreams, 0, '', 5)
elif mode == 99:
    cache = False
    if not login():
        addDir('failed!', hockeystreams, 0, '', 5)
    else:
        exception_data = urllib.urlencode({'update': 'Update Exception'})
        exception_url = hockeystreams + "/include/exception.inc.php?" + exception_data
        try:
            read = gethtml.get(exception_url, cookiepath, __dbg__)
            addDir('succeeded!', hockeystreams, 0, '', 5)
        except:
            addDir('failed!', hockeystreams, 0, '', 5)

if mode == 69:
    #xbmcplugin.openSettings(sys.argv[0])
    pass
else:
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc = cache)
