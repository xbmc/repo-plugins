import urllib
import urllib2
import re
import os
import json
import time
import htmlentitydefs
from traceback import format_exc
from urlparse import urlparse, parse_qs

from bs4 import BeautifulSoup
import StorageServer

import xbmcplugin
import xbmcgui
import xbmcaddon

base_url = 'http://www.aol.com'
cache = StorageServer.StorageServer("onaol", 6)
addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_version = addon.getAddonInfo('version')
addon_fanart = addon.getAddonInfo('fanart')
addon_icon = addon.getAddonInfo('icon')
language = addon.getLocalizedString


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log: %s' %format_exc()
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message),
                             level=xbmc.LOGDEBUG)


def make_request(url):
    addon_log('Request URL: %s' %url)
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        return data
    except urllib2.URLError, e:
        addon_log( 'We failed to open "%s".' %url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' %e.reason)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' %e.code)


def cache_categories():
    soup = BeautifulSoup(make_request(base_url + '/video'), 'html.parser')
    topics_tag = soup.find('div', class_='m-video-discover-bar-content')
    items = topics_tag('div', class_='item')
    playlist_items = soup('div', class_='m-video-show-section')
    categories = [(i.a.img['alt'], '%s%s' %(base_url, i.a['href']),
            i.a.img['data-original']) for i in items]
    categories.extend([(i.h2.a.string, '%s%s' %(base_url, i.h2.a['href']),
                        i.div['style'][i.div['style'].find('(') + 1:
                        i.div['style'].find(')')]) for i in playlist_items])
    return categories


def cache_category(url):
    soup = BeautifulSoup(make_request(url), 'html.parser')
    playlists_tab = soup.find('div', class_='m-video-channel-playlists-header')
    playlists = []
    for i in playlists_tab('a'):
        playlist = {}
        playlist['name'] = i.string.strip()
        playlist_tab = (soup.find('div', attrs={'data-tab': i['data-tab']})
                            ('div', class_='items')[0]('div', class_='item'))
        playlist['items'] = [(y.a['data-title'], y.a['href'],
                              y.img['data-original'], unescape(y.a['data-desc']
                              ).encode('utf-8')) for y in playlist_tab]
        playlists.append(playlist)
    cache.set('current', repr({'url': url,
            'playlists': playlists, 'time': time.time()}))
    return playlists


def cache_shows():
    soup = BeautifulSoup(make_request('%s%s' %(base_url, '/video/shows/')
                         ), 'html.parser')
    items = soup.find('div', class_='m-video-show-listing full'
                      )('div', class_='item')
    return [(i.p.string, '%s%s' %(base_url, i.a['href']),
             i.img['data-original']) for i in items]


def display_shows():
    data = cache.cacheFunction(cache_shows)
    for i in data:
        add_dir(i[0].encode('utf-8'), i[1], 'category', i[2])


def display_categories():
    add_dir('Shows', 'shows', 'shows', addon_icon)
    data = cache.cacheFunction(cache_categories)
    for i in data:
        add_dir(i[0].encode('utf-8'), i[1], 'category', i[2])


def diaplay_category(url):
    current = None
    try:
        current = eval(cache.get('current'))
    except SyntaxError:
        # cache has not been set
        addon_log('No "current" cache')
    if current and current['url'] == url and (current['time'] <
            (time.time() - 14400)):
        playlists = current['playlists']
    else:
        playlists = cache_category(url)
    if len(playlists) > 1:
        for i in playlists:
            add_dir(i['name'].encode('utf-8'), url, 'playlist', addon_icon)
    elif playlists:
        display_playlist(url, playlists[0]['name'])


def display_playlist(url, playlist_name):
    current = eval(cache.get('current'))
    playlist = [i['items'] for i in current['playlists'] if
            i['name'] == playlist_name]
    if playlist:
        for i in playlist[0]:
            add_dir(i[0].encode('utf-8'), i[1], 'resolve',
                    i[2], {'plot': i[3]})


def add_dir(name, url, mode, iconimage, info={}, fanart=addon_fanart):
    item_params = {'name': name, 'url': url, 'mode': mode}
    plugin_url = '%s?%s' %(sys.argv[0], urllib.urlencode(item_params))
    listitem = xbmcgui.ListItem(name, iconImage=iconimage,
                                thumbnailImage=iconimage)
    isfolder = True
    if mode == 'resolve':
        isfolder = False
        listitem.setProperty('IsPlayable', 'true')
    listitem.setProperty('Fanart_Image', fanart)
    listitem.setInfo(type = 'video', infoLabels = info)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), plugin_url,
                                listitem, isfolder)


def resolve_url(url):
    resolved_url = ''
    success = False
    try:
        page_url = '%s%s' %(base_url, url)
        soup = BeautifulSoup(make_request(page_url), 'html.parser')
        script_url = 'http:%s' %soup.find('div', class_='vdb_player'
                ).script['src']
        data = make_request(script_url)
        d = json.loads(data[(data.find('"bid":') + 6):
                       data.find(',"playerTemplate"')])
        resolved_url = d['videos'][0]['videoUrls'][0]
    except:
        addon_log(format_exc())
    if resolved_url:
        success = True
    item = xbmcgui.ListItem(path=resolved_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)


## Thanks to Fredrik Lundh for this function -
## http://effbot.org/zone/re-sub.htm#unescape-html
def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p

params = get_params()

mode = None

try:
    mode = params['mode']
    addon_log('Mode: %s, Name: %s, URL: %s' %
              (params['mode'], params['name'], params['url']))
except:
    addon_log('Get root directory')

if mode is None:
    display_categories()
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'category':
    diaplay_category(params['url'])
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'playlist':
    display_playlist(params['url'], params['name'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'shows':
    display_shows()
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'resolve':
    resolve_url(params['url'])
