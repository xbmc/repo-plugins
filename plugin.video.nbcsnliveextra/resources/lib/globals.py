import os, re, sys
import string
import urllib, requests
import time
import base64
import calendar
import codecs
from datetime import datetime, timedelta
from kodi_six import xbmc, xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs

if sys.version_info[0] > 2:
    import http
    cookielib = http.cookiejar
    urllib = urllib.parse
else:
    import cookielib


# KODI ADDON GLOBALS
ADDON_HANDLE = int(sys.argv[1])
if sys.version_info[0] > 2:
    ADDON_PATH_PROFILE = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
else:
    ADDON_PATH_PROFILE = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
LOCAL_STRING = xbmcaddon.Addon().getLocalizedString
ROOTDIR = xbmcaddon.Addon().getAddonInfo('path')
ICON = os.path.join(ROOTDIR,"icon.png")
FANART = os.path.join(ROOTDIR,"fanart.jpg")
ROOT_URL = 'http://stream.nbcsports.com/data/mobile'
CONFIG_URL = 'https://stream.nbcsports.com/data/mobile/apps/NBCSports/configuration-vjs.json'

# Main settings
settings = xbmcaddon.Addon()
FREE_ONLY = str(settings.getSetting("free_only"))
KODI_VERSION = float(re.findall(r'\d{2}\.\d{1}', xbmc.getInfoLabel("System.BuildVersion"))[0])

filter_ids = [
    "show-all",
    "nfl",
    "premier-league",
    "nascar",
    "nhl",
    "golf",
    "pga",
    "nbc-nd",
    "college football",
    "nba",
    "mlb",
    "rugby",
    "horses",
    "tennis",
    "indy",
    "moto",
    "olympic sports",
    "nbc-csn-bay-area",
    "nbc-csn-california",
    "nbc-csn-chicago",
    "nbc-csn-mid-atlantic",
    "nbc-csn-new-england",
    "nbc-csn-philadelphia"

]

# Create a filter list
filter_list = []
for fid in filter_ids:
    if str(settings.getSetting(id=fid)) == "true":
        filter_list.append(fid)

# User Agents
UA_NBCSN = 'Adobe Primetime/1.4 Dalvik/2.1.0 (Linux; U; Android 6.0.1; Hub Build/MHC19J)'

# Event Colors
FREE = 'FF43CD80'
LIVE = 'FF00B7EB'
UPCOMING = 'FFFFB266'
FREE_UPCOMING = 'FFCC66FF'

VERIFY = True
# Add-on specific Adobepass variables
SERVICE_VARS = {
    'public_key': 'nTWqX10Zj8H0q34OHAmCvbRABjpBk06w',
    'private_key': 'Q0CAFe5TSCeEU86t',
    'registration_url': 'activate.nbcsports.com',
    'requestor_id': 'nbcsports',
    'resource_id': urllib.quote(
        '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>NBCOlympics</title><item><title>NBC Sports PGA Event</title><guid>123456789</guid><media:rating scheme="urn:vchip">TV-PG</media:rating></item></channel></rss>')
}


def stringToDate(string, date_format):
    try:
        date = datetime.strptime(str(string), date_format)
    except TypeError:
        date = datetime(*(time.strptime(str(string), date_format)[0:6]))

    return date


def get_resource_id():
    #########################
    # Get resource_id
    #########################
    """
    GET http://stream.nbcsports.com/data/mobile/passnbc.xml HTTP/1.1
    Host: stream.nbcsports.com
    Connection: keep-alive
    Accept: */*
    User-Agent: NBCSports/1030 CFNetwork/711.3.18 Darwin/14.0.0
    Accept-Language: en-us
    Accept-Encoding: gzip, deflate
    Connect
    """
    # req = urllib2.Request(ROOT_URL+'passnbc.xml')
    # req.add_header('User-Agent',  UA_NBCSN)
    # response = urllib2.urlopen(req)
    # resource_id = response.read()
    # response.close()
    # resource_id = resource_id.replace('\n', ' ').replace('\r', '')
    #resource_id = '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>nbcsports</title><item><title>NBC Sports PGA Event</title><guid>123456789</guid><media:rating scheme="urn:vchip">TV-PG</media:rating></item></channel></rss>'
    #resource_id = '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>golf</title><item><title>RSM%20Classic%20-%20Rd%201</title><guid>nbcs_100188</guid><media:rating scheme="urn:v-chip"></media:rating></item></channel></rss>'
    resource_id = '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>NBCOlympics</title><item><title>NBC Sports PGA Event</title><guid>123456789</guid><media:rating scheme="urn:vchip">TV-PG</media:rating></item></channel></rss>'

    return resource_id


def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    xbmc.log(str(timestamp))
    if timestamp < 1:
        timestamp = 1
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


def save_cookies(cookiejar):
    cookie_file = os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')
    cj = cookielib.LWPCookieJar()
    try:
        cj.load(cookie_file, ignore_discard=True)
    except:
        pass
    for c in cookiejar:
        args = dict(vars(c).items())
        args['rest'] = args['_rest']
        del args['_rest']
        c = cookielib.Cookie(**args)
        cj.set_cookie(c)
    cj.save(cookie_file, ignore_discard=True)


def load_cookies():
    cookie_file = os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')
    cj = cookielib.LWPCookieJar()
    try:
        cj.load(cookie_file, ignore_discard=True)
    except:
        pass

    return cj


def add_link(name, url, title, icon=None, fanart=None, info=None):
    ok = True
    liz = xbmcgui.ListItem(name)
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    liz.setProperty("IsPlayable", "true")
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    liz.setInfo(type="Video", infoLabels={"Title": title})
    if info is not None:
        liz.setInfo(type="Video", infoLabels=info)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)
    xbmcplugin.setContent(ADDON_HANDLE, 'episodes')
    return ok


def add_free_link(name, link_url, icon=None, fanart=None, info=None):
    ok = True
    u = sys.argv[0] + "?url=" + urllib.quote_plus(link_url) + "&mode=6&icon_image=" + urllib.quote_plus(icon)
    liz = xbmcgui.ListItem(name)
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    liz.setProperty("IsPlayable", "true")
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if info is not None:
        liz.setInfo(type="Video", infoLabels=info)
    ok = xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=u, listitem=liz)
    xbmcplugin.setContent(ADDON_HANDLE, 'episodes')
    return ok


def add_premium_link(name, link_url, icon, stream_info, fanart=None, info=None):
    ok = True
    u = sys.argv[0] + "?url=" + urllib.quote_plus(link_url) + "&mode=5&icon_image=" + urllib.quote_plus(icon)
    for key in stream_info:
        u += '&%s=%s' % (key, stream_info[key])
    liz = xbmcgui.ListItem(name)
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    liz.setProperty("IsPlayable", "true")
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if info is not None:
        liz.setInfo(type="Video", infoLabels=info)

    ok = xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=u, listitem=liz)
    xbmcplugin.setContent(ADDON_HANDLE, 'episodes')
    return ok


def add_dir(name, url, mode, icon, fanart=None, isFolder=True, info=None):
    ok = True
    u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name) \
        + "&icon_image=" + urllib.quote_plus(str(icon))
    liz = xbmcgui.ListItem(name)
    if icon is None: icon = ICON
    if fanart is None: fanart = FANART
    liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
    if info is not None:
        liz.setInfo(type="Video", infoLabels=info)

    ok = xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=u, listitem=liz, isFolder=isFolder)
    xbmcplugin.setContent(ADDON_HANDLE, 'episodes')
    return ok


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param
