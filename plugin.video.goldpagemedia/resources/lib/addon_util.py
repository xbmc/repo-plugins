import sys
import urllib
import base64
import m3u8
import time

import xbmc
import xbmcgui
import xbmcplugin

import adobe_activate_api
import util
import player_config
import events
from globals import defaultfanart, pluginhandle, selfAddon, translation, LOG_LEVEL
from constants import *

TAG = 'Addon_Util: '

def addLink(name, url, iconimage, fanart=None, infoLabels=None):
    u = sys.argv[0] + '?' + urllib.urlencode(url)
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)

    if infoLabels is None:
        infoLabels={"Title": name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    liz.setProperty('IsPlayable', 'true')
    liz.setIconImage(iconimage)
    if fanart is None:
        fanart=defaultfanart
    liz.setProperty('fanart_image',fanart)
    video_streaminfo = dict()
    liz.addStreamInfo('video', video_streaminfo)
    ok = xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz)
    return ok


def addDir(name, url, iconimage, fanart=None, infoLabels=None):
    u = sys.argv[0] + '?' + urllib.urlencode(url)
    xbmc.log(TAG + 'Made url to %s' % u, LOG_LEVEL)
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    if infoLabels is None:
        infoLabels={"Title": name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    if fanart is None:
        fanart=defaultfanart
    liz.setProperty('fanart_image',fanart)
    ok = xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)
    return ok

def check_error(session_json):
    status = session_json['status']
    if not status == 'success':
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30037), translation(30500) % session_json['message'])
        return True
    return False

def does_requires_auth(network_name):
    xbmc.log(TAG + 'Checking auth of ' + network_name, LOG_LEVEL)
    requires_auth = not (network_name == 'espn3' or network_name.find('free') >= 0 or network_name == '')
    if not requires_auth:
        free_content_check = player_config.can_access_free_content()
        if not free_content_check:
            xbmc.log('ESPN3: User needs login to ESPN3', LOG_LEVEL)
            requires_auth = True
    return requires_auth

def get_url(url):
    if 'listingsUrl' not in url and 'tz' not in url:
        tz = player_config.get_timezone()
        if '?' in url:
            sep = '&'
        else:
            sep = '?'
        return url + sep + 'tz=' + urllib.quote_plus(tz)
    return url

def index_item(args):
    if args['type'] == 'over':
        return
    sport = args['sport']
    ename = args['eventName']
    sport2 = args['subcategory'] if 'subcategory' in args else sport
    if sport <> sport2 and len(sport2) > 0:
        sport += ' (' + sport2 + ')'
    starttime = args['starttime'] if 'starttime' in args else None
    length = int(args['duration'])
    xbmc.log(TAG + 'startime %s' % starttime, LOG_LEVEL)
    xbmc.log(TAG + 'type %s' % args['type'], LOG_LEVEL)

    if starttime is not None:
        now = time.time()
        etime = time.strftime("%I:%M %p", starttime)
        if 'replay' in args['type']:
            etime_local = starttime
            if etime_local.tm_hour == 0 and etime_local.tm_min == 0:
                etime = time.strftime("%m/%d/%Y", starttime)
            else:
                etime = time.strftime("%m/%d %I:%M %p", starttime)
            if selfAddon.getSetting('NoColors') == 'true':
                ename = etime + ' ' + ename
            else:
                ename = '[COLOR=FFB700EB]' + etime + '[/COLOR] ' + ename
        elif args['type'] == 'live':
            starttime_time = time.mktime(starttime)
            length -= (time.time() - starttime_time)
            if selfAddon.getSetting('NoColors') == 'true':
                ename = ename + ' ' + etime
            else:
                ename += ' [COLOR=FFB700EB]' + etime + '[/COLOR]'
        else:
            now_time = time.localtime(now)
            if now_time.tm_year == starttime.tm_year and \
                            now_time.tm_mon == starttime.tm_mon and \
                            now_time.tm_mday == starttime.tm_mday:
                etime = time.strftime("%I:%M %p", starttime)
            else:
                etime = time.strftime("%m/%d %I:%M %p", starttime)
            if selfAddon.getSetting('NoColors') == 'true':
                ename = etime + ' ' + ename
            else:
                ename = '[COLOR=FFB700EB]' + etime + '[/COLOR] ' + ename
        aired = time.strftime("%Y-%m-%d", starttime)
    else:
        aired = 0

    network_id = args['networkId'] if 'networkId' in args else ''
    if network_id == 'longhorn':
        channel_color = 'BF5700'
    elif network_id == 'sec' or network_id == 'secplus':
        channel_color = '004C8D'
    else:
        channel_color = 'CC0000'
    if 'networkName' in args:
        network = args['networkName']
    else:
        network = network_id
    blackout = args['blackout'] if 'blackout' in args else False
    blackout_text = ''
    if blackout:
        blackout_text = translation(30580)
    if len(blackout_text) > 0:
        ename = blackout_text + ' ' + ename
    if len(network) > 0:
        if selfAddon.getSetting('NoColors') == 'true':
            ename = network + ' ' + ename
        else:
            ename = '[COLOR=FF%s]%s[/COLOR] ' % (channel_color, network) + ename

    description = args['description']
    requires_auth = does_requires_auth(network_id)
    if requires_auth and not adobe_activate_api.is_authenticated():
        ename = '*' + ename

    mpaa = args['parentalRating'] if 'parentRating' in args else 'U'
    infoLabels = {'title': ename,
                  'genre': sport,
                  'duration': length,
                  'studio': network,
                  'mpaa': mpaa,
                  'plot': description,
                  'aired': aired,
                  'premiered': aired}

    authurl = dict()
    if args['type'] == 'upcoming':
        authurl[MODE] = UPCOMING_MODE
    else:
        adobeRSS = args['adobeRSS'] if 'adobeRSS' in args else None
        guid = args['guid'] if 'guid' in args else None
        if adobeRSS is None and guid is None:
            authurl[PLAYBACK_URL] = args['sessionUrl']
            authurl[MODE] = PLAY_ITEM_MODE
        else:
            authurl[MODE] = PLAY_TV_MODE
            authurl[EVENT_ID] = args['eventId']
            authurl[SESSION_URL] = args['sessionUrl']
            authurl[NETWORK_NAME] = args['networkId']
            if 'adobeRSS' in args:
                authurl[ADOBE_RSS] = args['adobeRSS'].encode('iso-8859-1')
            else:
                authurl[EVENT_NAME] = args['eventName'].encode('iso-8859-1')
                authurl[EVENT_GUID] = args['guid'].encode('iso-8859-1')
                authurl[EVENT_PARENTAL_RATING] = mpaa
    fanart = args['imageHref']
    addLink(ename.encode('iso-8859-1'), authurl, fanart, fanart, infoLabels=infoLabels)


def get_league(listing):
    if 'categories' in listing:
        for category in listing['categories']:
            if 'type' in category and category['type'] == 'league':
                return category['description']
    return ''


def get_subcategory(listing):
    if 'subcategories' in listing:
        for subcategory in listing['subcategories']:
            return subcategory['name']
    return ''


def check_json_blackout(listing):
    blackout_dmas = list()
    for blackout in listing['blackouts']:
        if blackout['type'] == 'dma':
            for dma in blackout['detail']:
                blackout_dmas.append(dma)
    user_dma = player_config.get_dma()
    for blackout_dma in blackout_dmas:
        if blackout_dma == user_dma:
            return True
    return False

def index_listing(listing):
    # 2016-06-06T18:00:00EDT
    # EDT is discarded due to http://bugs.python.org/issue22377
    time_format = '%Y-%m-%dT%H:%M:%S'
    starttime = time.strptime(listing['startTime'][:-3], time_format)
    endtime = time.strptime(listing['endTime'][:-3], time_format)
    duration = (time.mktime(endtime) - time.mktime(starttime))
    xbmc.log(TAG + ' Duration: %s' % duration, LOG_LEVEL)

    index_item({
        'sport': get_league(listing),
        'eventName': listing['name'],
        'subcategory': get_subcategory(listing),
        'imageHref': listing['thumbnails']['large']['href'],
        'parentalRating': listing['parentalRating'],
        'starttime': starttime,
        'duration': duration,
        'type': listing['type'],
        'networkId': listing['broadcasts'][0]['adobeResource'],
        'networkName': listing['broadcasts'][0]['name'],
        'blackout': check_json_blackout(listing),
        'description': listing['keywords'],
        'eventId': listing['eventId'],
        'sessionUrl': listing['links']['source']['hls']['default']['href'],
        'guid': listing['guid']
    })


def index_video(listing):
    starttime = None
    duration = listing['duration']
    index_item({
        'sport': get_league(listing),
        'eventName': listing['headline'],
        'imageHref': listing['posterImages']['default']['href'],
        'starttime': starttime,
        'duration': duration,
        'type': 'live',
        'networkId': '',
        'description': listing['description'],
        'eventId': listing['id'],
        'sessionUrl': listing['links']['source']['HLS']['HD']['href']
    })

def compare(lstart, lnetwork, lstatus, rstart, rnetwork, rstatus):
    xbmc.log(TAG + 'lstart %s lnetwork %s lstatus %s rstart %s rnetwork %s rstatus %s' %
             (lstart, lnetwork, lstatus, rstart, rnetwork, rstatus), LOG_LEVEL)
    if lnetwork != rnetwork:
        return 0
    if lstart is None and rstart is None:
        return 0
    if lstart is None:
        return 1
    if rstart is None:
        return -1
    ltime = int(time.mktime(lstart))
    rtime = int(time.mktime(rstart))
    if 'replay' in lstatus and 'replay' in rstatus:
        return int(rtime - ltime)
    if lstatus == rstatus:
        return int(ltime - rtime)
    elif lstatus == 'live':
        return -1
    elif rstatus == 'live':
        return 1
    return int(rtime - ltime)
