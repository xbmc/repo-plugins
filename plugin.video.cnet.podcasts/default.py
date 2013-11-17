import urllib
import urllib2
import time
from datetime import datetime
from urlparse import urlparse, parse_qs

import xmltodict
import StorageServer
from bs4 import BeautifulSoup

import xbmcplugin
import xbmcgui
import xbmcaddon

cache = StorageServer.StorageServer("cnetpodcasts", 6)
addon = xbmcaddon.Addon()
addon_version = addon.getAddonInfo('version')
addon_id = addon.getAddonInfo('id')
icon = addon.getAddonInfo('icon')
language = addon.getLocalizedString


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log'
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message),level=xbmc.LOGDEBUG)


def make_request(url, post_data=None):
    addon_log('Request URL: %s' %url)
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0',
        'Referer': 'http://www.cnet.com'
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
    url = 'http://www.cnet.com/podcasts/'
    soup = BeautifulSoup(make_request(url), 'html.parser')
    items = soup.find_all('div', class_='podcast')
    cats = [{'thumb': i.img['src'],
             'name': i.h3('a')[-1].string,
             'desc': i.find('div', class_='desc').get_text(),
             'links': [{x.string: x['href']} for x in i.find('div', class_='rss')('a') if
                           x.string]} for
            i in items]
    return cats


def display_categories():
    cats = cache.cacheFunction(cache_categories)
    for i in cats:
        if i['name'] == 'All Audio Podcasts': continue
        add_dir(i['name'], i['links'], 'category', i['thumb'], {'Plot': i['desc']})


def display_category(links_list):
    links_list = eval(links_list)
    settings = {'0': 'Audio', '1': 'HD', '2': 'Video'}
    preferred_type = settings[addon.getSetting('playback_type')]
    feed_url = None
    for i in links_list:
        if i.has_key(preferred_type):
            feed_url = i[preferred_type]
    if not feed_url:
        dialog = xbmcgui.Dialog()
        ret = dialog.select(language(30013)+':%s' %preferred_type,
                            [i.keys()[0] for i in links_list])
        if ret > -1:
            feed_url = [i.values()[0] for i in links_list][ret]
        else:
            return
    pod_dict = xmltodict.parse(make_request(feed_url+'?format=xml'))
    iconimage = pod_dict['rss']['channel']['itunes:image']['@href']
    items = pod_dict['rss']['channel']['item']
    for i in items:
        date_patterns = ['%a, %d %b %Y %H:%M:%S PST', '%a, %d %b %Y %H:%M:%S PDT']
        for pattern in date_patterns:
            try:
                date_time = datetime(*(time.strptime(i['pubDate'], pattern)[0:6]))
                item_date = date_time.strftime('%d.%m.%Y')
                premiered = date_time.strftime('%d-%m-%Y')
                break
            except ValueError:
                item_date = ''
                premiered = ''
        meta = {'Plot': i['itunes:summary'],
                'Duration': int(i['itunes:duration']) / 60,
                'Date': item_date,
                'Premiered': premiered}
        add_dir(i['title'], i['media:content']['@url'], 'resolve', iconimage, meta, False)


def resolve_url(video_id):
    params = {
        'iod': 'images,videoMedia,relatedLink,breadcrumb,relatedAssets,broadcast,lowcache',
        'partTag': 'cntv',
        'players': 'Download,RTMP',
        'showBroadcast': 'true',
        'videoIds': video_id,
        'videoMediaType': 'preferred'
        }
    data = make_request('http://api.cnet.com/restApi/v1.0/videoSearch?' + urllib.urlencode(params))
    pod_dict = xmltodict.parse(data)
    item = pod_dict['CNETResponse']['Videos']['Video']
    thumb = [i['ImageURL'] for i in item['Images']['Image'] if i['@width'] == '360'][0]
    media_items = item['VideoMedias']['VideoMedia']
    stream_urls = [i['DeliveryUrl'] for i in media_items if i['Height'] == '720']
    if stream_urls:
        return stream_urls[0]


def add_dir(name, url, mode, iconimage, meta={}, isfolder=True):
    params = {'name': name, 'url': url, 'mode': mode}
    url = '%s?%s' %(sys.argv[0], urllib.urlencode(params))
    listitem = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    meta["Title"] = name
    if not isfolder:
        listitem.setProperty('IsPlayable', 'true')
        listitem.setProperty('Fanart_Image', iconimage)
    listitem.setInfo(type="Video", infoLabels=meta)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isfolder)


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


def set_view_mode():
    view_modes = {
        '0': '502',
        '1': '51',
        '2': '3',
        '3': '504',
        '4': '503',
        '5': '515'
        }
    view_mode = addon.getSetting('view_mode')
    if view_mode == '6':
        return
    xbmc.executebuiltin('Container.SetViewMode(%s)' %view_modes[view_mode])


params = get_params()

try:
    mode = params['mode']
except:
    mode = None

addon_log(repr(params))

if not mode:
    display_categories()
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'category':
    display_category(params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    set_view_mode()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'resolve':
    item = xbmcgui.ListItem(path=params['url'])
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)