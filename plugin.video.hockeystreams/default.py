import urllib,  os, sys, datetime

import xbmc, xbmcplugin, xbmcaddon, xbmcgui

from legacy import LegacyHockey
from util import HockeyUtil

import gethtml

__addonname__ = 'plugin.video.hockeystreams'
__datapath__ = 'special://profile/addon_data/' +__addonname__

#important! deals with a bug where errors are thrown if directory does not exist.
if not os.path.exists: os.makedirs(__datapath__)
cookiepath = __datapath__

__plugin__ = "Hockeystreams"
__author__ = "wotever"
__version__ = "1.8.0"
__url__ = "https://github.com/jlongman/xbmc-hockeystreams-plugin/"
__settings__ = xbmcaddon.Addon(id='plugin.video.hockeystreams')

hockeyUtil = HockeyUtil(__settings__, cookiepath)

__dbg__ = __settings__.getSetting("debug") == "true"
__mark_broken_cdn4_links__ = __settings__.getSetting("mark_cdn4") == "true"

empty = None

hockeystreams = 'http://www.hockeystreams.com'
today = datetime.date.today()

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

def CATEGORIES():
    if __dbg__:
        print ("hockeystreams: enter categories")
    hockeyUtil.addDir(__settings__.getLocalizedString(40100), hockeystreams, 1, '', 1)
    hockeyUtil.addDir(__settings__.getLocalizedString(40101), hockeystreams, 2, '', 1)
    hockeyUtil.addDir(__settings__.getLocalizedString(40102), hockeystreams, 30, '', 1)
    hockeyUtil.addDir('  '+__settings__.getLocalizedString(40103), hockeystreams, 66, '', 1)
    hockeyUtil.addDir('  '+__settings__.getLocalizedString(40104), hockeystreams, 99, '', 1)
    
    #addDir('RSS Streams', hockeystreams, 3, '', 1)

def QUICK_PLAY_VIDEO(almost_video_url):
    directLinks = {}
    foundGames = hockeyUtil.soupIt(almost_video_url,'input',empty, True)
    for test in foundGames:                                 ##get rid of this 'busy loop' in the next minor revision
        if __dbg__:
            print("hockeystreams: \t\t quick directs %s" % test)
        if 'direct_link' in test.get('id',''):
            directLink = test['value']
            directLinks[almost_video_url] = directLink
            PLAY_VIDEO(directLink)


def PLAY_VIDEO(video_url):
    if __dbg__:
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

if __dbg__:
    print ("url %s name %s mode %s" % (url, name, mode))
    print ("year %s month %s day %s" % (year, month, day))



hockey = LegacyHockey(hockeyUtil, __mark_broken_cdn4_links__, __dbg__)

cache = True
if mode is None or mode == 0 or url is None or len(url) < 1:
    CATEGORIES()
elif mode == 1:
    cache = False
    hockey.LIVE_GAMES(1000)
elif mode == 2:
    cache = False
    hockey.YEAR(hockeystreams, 3)
elif mode == 3:
    cache = today.year != year
    hockey.MONTH(hockeystreams, year, 4)
elif mode == 4:
    cache = not (today.year == year and today.month == month)
    hockey.DAY(hockeystreams, year, month, 5)
elif mode == 5:
    cache = not (today.year == year and today.month == month and today.day == day)
    hockey.ARCHIVE_GAMES_BY_DATE(year, month, day, 1000)
elif mode == 6:
    cache = False
    hockey.LAST_15_GAMES(1000)
elif mode == 30:
    hockey.BY_TEAM(31)
elif mode == 31:
    cache = False
    hockey.ARCHIVE_GAMES_BY_TEAM(url, 1000)
elif mode == 1000:
    cache = False
    hockey.QUALITY(url, gamename)
elif mode == 2000:
    cache = not (today.year == year and today.month == month and today.day == day)
    QUICK_PLAY_VIDEO(url)
elif mode == 2001:
    cache = not (today.year == year and today.month == month and today.day == day)
    PLAY_VIDEO(url)


elif mode == 66:
    cache = False
    if not hockeyUtil.login():
        print "failed"
        hockeyUtil.addDir(__settings__.getLocalizedString(40001), hockeystreams, 0, '', 5)
    else:
        hockeyUtil.addDir(__settings__.getLocalizedString(40000), hockeystreams, 0, '', 5)
elif mode == 99:
    cache = False
    if not hockeyUtil.login():
        hockeyUtil.addDir(__settings__.getLocalizedString(40001), hockeystreams, 0, '', 5)
    else:
        exception_data = urllib.urlencode({'update': 'Update Exception'})
        exception_url = hockeystreams + "/include/exception.inc.php?" + exception_data
        try:
            read = gethtml.get(exception_url, cookiepath, __dbg__)
            hockeyUtil.addDir(__settings__.getLocalizedString(40000), hockeystreams, 0, '', 5)
        except:
            hockeyUtil.addDir(__settings__.getLocalizedString(40001), hockeystreams, 0, '', 5)

xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc = cache)
