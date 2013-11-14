import urllib
import urllib2
import re
import json
from urlparse import urlparse, parse_qs

import StorageServer
from BeautifulSoup import BeautifulSoup

import xbmcplugin
import xbmcgui
import xbmcaddon

cache = StorageServer.StorageServer("flwoutdoors", 6)
addon = xbmcaddon.Addon()
addon_version = addon.getAddonInfo('version')
addon_id = addon.getAddonInfo('id')
icon = addon.getAddonInfo('icon')


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log'
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message),level=xbmc.LOGNOTICE)


def make_request(url, post_data=None):
    addon_log('Request URL: %s' %url)
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0',
        'Referer': 'http://www.flwoutdoors.com'
        }
    try:
        req = urllib2.Request(url, post_data, headers)
        response = urllib2.urlopen(req)
        response_url = urllib.unquote_plus(response.geturl())
        data = response.read()
        response.close()
        return data
    except urllib2.URLError, e:
        addon_log('We failed to open "%s".' % url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' %e.reason)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' % e.code)


def cache_categories():
    url = 'http://www.flwoutdoors.com/flwondemand.cfm'
    soup = BeautifulSoup(make_request(url))
    items = soup.find('ul', attrs={'class': 'menu'})('a')
    cats = []
    for i in items:
        cats.append({'callsign': i['id'].lstrip('divTab'),
                     'title': i.string.encode('utf-8')})
    return repr(cats)


def display_categories():
    cats = eval(cache.cacheFunction(cache_categories))
    for i in cats:
        add_dir(i['title'], i['callsign'], 'category', icon)


def display_category(callsign):
    url = 'http://www.flwoutdoors.com/flwMedia/ajax.cfm'
    post_data = {'method': 'getVideosInChannel',
                 'callsign': callsign}
    data = json.loads(make_request(url, urllib.urlencode(post_data)))
    items = data['CHANNEL']['AFILE']
    for i in items:
        youtube_embed = None
        path = None
        if i.has_key('YOUTUBEEMBED') and len(i['YOUTUBEEMBED']) > 0:
            pattern = re.compile('src="(.+?)"')
            youtube_embed = pattern.findall(i['YOUTUBEEMBED'])
        if youtube_embed:
            try:
                youtube_id = youtube_embed[0].split('/embed/')[1]
                path = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' %youtube_id
            except:
                pass
        if not path:
            keys = ['PATH_ORIGINAL','STREAMING_PATH', 'PODCAST_PATH', 'MOBILE_PATH']
            for x in keys:
                if i.has_key(x) and len(i[x]) > 0:
                    path = i[x]
                    break
            if path.startswith('mp4:') and i.has_key('FILENAME_HD') and len(i['FILENAME_HD']) > 0:
                path = path.replace(i['FILENAME'], i['FILENAME_HD'])
        duration = get_duration(i['DURATION'].split('.')[0])
        meta = {'Duration': duration}
        if i.has_key('DESCRIPTION') and len(i['DESCRIPTION']) > 0:
            meta['Plot'] = i['DESCRIPTION']
        add_dir(i['TITLE'].encode('utf-8'), path, 'resolve', i['THUMBNAIL'], meta, False)


def add_dir(name, url, mode, iconimage, meta={}, isfolder=True):
    params = {'name': name, 'url': url, 'mode': mode}
    url = '%s?%s' %(sys.argv[0], urllib.urlencode(params))
    listitem = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    meta["Title"] = name
    if not isfolder:
        listitem.setProperty('IsPlayable', 'true')
    listitem.setInfo(type="Video", infoLabels=meta)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isfolder)


def get_rtmp_url(path):
    rtmp_url = (
        '%s %s %s %s' %
        ('rtmp://flwoutdoorsfs.fplive.net/flwoutdoors',
        'swfUrl=http://www.flwoutdoors.com/FLWMedia/FLWVideoPlayer.swf',
        'playpath=' + path,
        'app=flwoutdoors')
        )
    return rtmp_url


def get_duration(duration):
    if duration is None:
        return 1
    d_split = duration.split(':')
    if len(d_split) == 4:
        del d_split[-1]
    minutes = int(d_split[-2])
    if int(d_split[-1]) >= 30:
        minutes += 1
    if len(d_split) >= 3:
        minutes += (int(d_split[-3]) * 60)
    if minutes < 1:
        minutes = 1
    return minutes


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


params = get_params()

try:
    mode = params['mode']
except:
    mode = None

addon_log(repr(params))

if not mode:
    display_categories()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'category':
    display_category(params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmc.executebuiltin('Container.SetViewMode(503)')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'resolve':
    path = params['url']
    if path.startswith('mp4:'):
        path = get_rtmp_url(path)
    item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)