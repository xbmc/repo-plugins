# -*- coding: utf-8 -*-

#############################################################################################
#
# Name: plugin.video.gfq
# Author: Bawitdaba
# Description: Guys From Queens Network live video streams and podcast episodes
# Type: Video Addon
# Comments: Original release derived from the TWiT addon made by divingmule and Adam B
#
#############################################################################################

import urllib
import urllib2
import re
import os
import json
import time
from datetime import datetime
from dateutil.parser import parse
from traceback import format_exc
from urlparse import urlparse, parse_qs
from math import ceil

import StorageServer
from bs4 import BeautifulSoup

import xbmcplugin
import xbmcgui
import xbmcaddon

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_version = addon.getAddonInfo('version')
addon_fanart = addon.getAddonInfo('fanart')
addon_icon = addon.getAddonInfo('icon')
addon_path = xbmc.translatePath(addon.getAddonInfo('path')).encode('utf-8')
language = addon.getLocalizedString
cache = StorageServer.StorageServer("gfq", 24)


def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log: %s' %format_exc()
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message), level=xbmc.LOGDEBUG)


def cache_shows_file():
    ''' creates an initial cache from the shows file '''
    show_file = os.path.join(addon_path, 'resources', 'shows')
    cache.set("shows", open(show_file, 'r').read())


def make_request(url, locate=False):
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        data = response.read()
        response.close()
        if locate:
            return response.geturl()
        return data
    except urllib2.URLError, e:
        addon_log( 'We failed to open "%s".' %url)
        if hasattr(e, 'reason'):
            addon_log('We failed to reach a server.')
            addon_log('Reason: %s' %e.reason)
        if hasattr(e, 'code'):
            addon_log('We failed with error code - %s.' %e.code)


def set_resolved_url(resolved_url):
    success = False
    if resolved_url:
        success = True
    else:
        resolved_url = ''
    item = xbmcgui.ListItem(path=resolved_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)


def get_justintv():
    token_url = 'https://api.twitch.tv/api/channels/guysfromqueens/access_token?as3=t'
    data = json.loads(make_request(token_url))
    url_params = [
        'nauthsig=%s' %data['sig'],
        'player=jtvweb',
        'private_code=null',
        'type=any',
        'nauth=%s' %urllib2.quote(data['token']),
        'allow_source=true',
            ]
    resolved_url = 'http://usher.twitch.tv/select/guysfromqueens.json?' + '&'.join(url_params)
    set_resolved_url(resolved_url)


def get_dailymotion():
    # User ID = x14gtas
    req = urllib2.Request("http://www.dailymotion.com/sequence/x14gtas")
    response = urllib2.urlopen(req)
    content = response.read()
    response.close()

    if content.find('"statusCode":410') > 0 or content.find('"statusCode":403') > 0:
        xbmc.executebuiltin('XBMC.Notification(Unable to find live stream.)')
    else:
        matchFullHD = re.compile('"hd1080URL":"(.+?)"', re.DOTALL).findall(content)
        matchHD = re.compile('"hd720URL":"(.+?)"', re.DOTALL).findall(content)
        matchHQ = re.compile('"hqURL":"(.+?)"', re.DOTALL).findall(content)
        matchSD = re.compile('"sdURL":"(.+?)"', re.DOTALL).findall(content)
        matchLD = re.compile('"video_url":"(.+?)"', re.DOTALL).findall(content)
        url = ""
        if matchFullHD:
            url = urllib.unquote_plus(matchFullHD[0]).replace("\\", "")
        elif matchHD:
            url = urllib.unquote_plus(matchHD[0]).replace("\\", "")
        elif matchHQ:
            url = urllib.unquote_plus(matchHQ[0]).replace("\\", "")
        elif matchSD:
            url = urllib.unquote_plus(matchSD[0]).replace("\\", "")
        elif matchLD:
            url = urllib.unquote_plus(matchSD2[0]).replace("\\", "")
        if url:
            req = urllib2.Request(url)
            response = urllib2.urlopen(req)
            url = response.read()
            response.close()

            set_resolved_url(url)


def add_dir(name, url, iconimage, mode, info={}, VideoStreamInfo={}, AudioStreamInfo={}):
    item_params = {'name': name, 'url': url, 'mode': mode,
                   'iconimage': iconimage, 'content_type': content_type}
    plugin_url = '%s?%s' %(sys.argv[0], urllib.urlencode(item_params))
    listitem = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    isfolder = True
    if mode == 'resolve_url' or mode == 'justintv' or mode == 'dailymotion':
        isfolder = False
        listitem.setProperty('IsPlayable', 'true')
    listitem.setProperty('Fanart_Image', addon_fanart)
    info_type = 'video'
    if content_type == 'audio':
        info_type = 'music'
        listitem.setInfo(type=info_type, infoLabels=info)
    else:
        listitem.setInfo(type=info_type, infoLabels=info)

    if hasattr(listitem, 'addStreamInfo'):
        listitem.addStreamInfo('audio', AudioStreamInfo)
        listitem.addStreamInfo('video', VideoStreamInfo)

    xbmcplugin.addDirectoryItem(int(sys.argv[1]), plugin_url, listitem, isfolder)


def shows_cache():
    ''' this function checks for shows that haven't been cached '''
    soup = BeautifulSoup(make_request('http://www.gfqnetwork.com/roku/config.opml'), 'html.parser')
    outlines = soup.findAll('outline')

    show_titles = re.compile('title="(.+?)"').findall(str(outlines))
    show_icons = re.compile('img="(.+?)"').findall(str(outlines))
    show_urls = re.compile('url="(.+?)"').findall(str(outlines))

    for index in range(len(show_titles)):
        if not shows.has_key(show_titles[index]):
            addon_log('Show not in cache: %s' %show_titles[index])
            try:
                shows[show_titles[index]] = {'show_icon': show_icons[index], 'show_url': show_urls[index], 'show_desc': ''}
                cache.set('shows', repr(shows))
                addon_log('Cached new show: %s' %show_titles[index])
            except:
                addon_log('addonException cache new show: %s' %format_exc)
    return "True"


def display_shows():
    ''' display the main menu '''
    # check for new shows at the set cacheFunction interval
    cache_shows = eval(cache.cacheFunction(shows_cache))
    add_dir(language(30000), 'gfq_live', addon_icon, 'gfq_live')
    add_dir(language(30100), 'http://feeds.feedburner.com/GfqNetworkallVideo', addon_icon, 'latest_episodes')
    items = sorted(shows.keys(), key=str.lower)
    for i in items:
        show = shows[i]
        add_dir(i, show['show_url'], show['show_icon'], 'episodes', {'plot': show['show_desc']})


def display_live():
    UstreamVideoStreamInfo = {'codec': 'h264', 'aspect': 1.78, 'width': 426, 'height': 240} #UStream
    VideoStreamInfo = {'codec': 'h264', 'aspect': 1.78, 'width': 1280, 'height': 720}
    AudioStreamInfo = {'codec': 'aac', 'language': 'en', 'channels': 2}

    # // Dailymotion
    add_dir(language(30001), 'get_dailymotion', addon_icon, 'dailymotion', [],VideoStreamInfo, AudioStreamInfo)
    # // Ustream
    add_dir(language(30002), 'http://iphone-streaming.ustream.tv/ustreamVideo/3068635/streams/live/playlist.m3u8', addon_icon, 'resolve_url', [],UstreamVideoStreamInfo, AudioStreamInfo)
    # // Justin.tv
    add_dir(language(30003), 'get_justintv', addon_icon, 'justintv', [],VideoStreamInfo, AudioStreamInfo)
    # // Audio Only
    add_dir(language(30004), 'http://s25.streamerportal.com:8235/live', addon_icon, 'resolve_url', [],VideoStreamInfo, AudioStreamInfo)


def display_episodes(url, iconimage):
    episodes = get_episodes(url, iconimage)
    for i in episodes:
        add_dir(i['info']['Title'], i['url'], i['thumb'], 'resolve_url', i['info'], i['VideoStreamInfo'], i['AudioStreamInfo'])


def get_episodes(url, iconimage):
    ''' return array of episodes of a specific show '''
    soup = BeautifulSoup(make_request(url), 'html.parser')
    soup = soup.prettify().encode('utf-8').strip()
    soup = BeautifulSoup(soup, 'html.parser')

    # ' // Find All <item> tags (1 Tag per Episode)
    items = soup.find_all("item")

    episodes = []

    for item in items:
        try:
            show_title = str(item.find_next("title").get_text("", strip=True).encode('utf-8'))
        except:
            show_title = ""
        show_number = re.compile('.* Ep. (.+?) - .*').findall(show_title)
        if len(show_number) != 1:
            show_number = re.compile('.* Ep. (.+?) – .*').findall(show_title)
        if len(show_number) == 1:
            show_number = int(show_number[0])
        else:
            show_number = 0
        try:
            show_date = parse(str(item.find_next("pubdate").get_text("", strip=True).encode('utf-8')), fuzzy=True)
        except:
            show_date = ""
        show_icon = addon_icon
        try:
            show_duration = str(item.find_next("itunes:duration").get_text("", strip=True).encode('utf-8'))
        except:
            show_duration = "0:0:0"
        show_duration = sum(int(x) * 60 ** i for i,x in enumerate(reversed(show_duration.split(":"))))

        info = {}
        # ' // Episode Title
        info['Title'] = show_title
        info['TVShowTitle'] = show_title
        info['Genre'] = 'Podcast'
        # ' // Episode Published Date
        info['Date'] = show_date.strftime('%d-%m-%Y')
        info['Premiered'] = show_date.strftime('%d-%m-%Y')
        info['Aired'] = show_date.strftime('%d-%m-%Y')
        info['Year'] = show_date.strftime('%Y')
        # ' // Episode Number
        info['Episode'] = show_number
        # ' // Episode Duration
        info['Duration'] = show_duration / 60
        # ' // Episode Description
        try:
            info['Plot'] = str(item.find_next("itunes:summary").get_text("", strip=True).encode('utf-8'))
        except:
            info['Plot'] = ""
        try:
            media_content = re.compile('<media:content filesize="(.+?)" type="video/mp4" url="(.+?)">').findall(str(item.find_next("media:content").encode('utf-8')))
        except:
            media_content = ""
        if len(media_content) != 1:
            try:
                media_content = re.compile('<media:content blip:acodec="ffaac" blip:role="Source" blip:vcodec="ffh264" expression="full" filesize="(.+?)" height="720" isdefault="true" type="video/mp4" url="(.+?)" width="1280">').findall(str(item.find_next("media:content", attrs={"blip:role": "Source"}).encode('utf-8')))
            except:
                media_content = ""
        if len(media_content) == 1:
            media_content = media_content[0]
            info['Size'] = int(media_content[0])
            VideoStreamInfo = {'codec': 'h264', 'aspect': 1.78, 'width': 1280, 'height': 720, 'duration': show_duration}
            AudioStreamInfo = {'codec': 'aac', 'language': 'en', 'channels': 2}

            episodes.append({'url': media_content[1], 'thumb': iconimage, 'info': info, 'VideoStreamInfo': VideoStreamInfo, 'AudioStreamInfo': AudioStreamInfo})
    return episodes


def cache_latest_episods(url, iconimage):
    episodes = get_episodes(url, iconimage)
    return episodes


def get_latest_episodes(url, iconimage):
    episodes = cache.cacheFunction(cache_latest_episods, url, iconimage)
    for i in episodes:
        add_dir(i['info']['Title'], i['url'], i['thumb'], 'resolve_url', i['info'], i['VideoStreamInfo'], i['AudioStreamInfo'])


def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


first_run = addon.getSetting('first_run')
if first_run != addon_version:
    cache_shows_file()
    addon_log('first_run, caching shows file')
    xbmc.sleep(1000)
    addon.setSetting('first_run', addon_version)

params = get_params()

if params.has_key('content_type') and params['content_type'] == 'audio':
    content_type = 'audio'
else:
    content_type = 'video'

mode = None
try:
    mode = params['mode']
    addon_log('Mode: %s, Name: %s, URL: %s'
              %(params['mode'], params['name'], params['url']))
except:
    addon_log('Get root directory')

if mode is None:
    try:
        shows = eval(cache.get('shows'))
        if isinstance(shows, dict):
            display_shows()
        else:
            raise
    except:
        addon_log('"shows" cache missing')
        cache_shows_file()
        addon_log('caching shows file,'
                  'this should only happen if common cache db is reset')
        xbmc.sleep(1000)
        shows = eval(cache.get('shows'))
        if isinstance(shows, dict):
            display_shows()
        else:
            addon_log('"shows" cache ERROR')
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 'episodes':
    display_episodes(params['url'], params['iconimage'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'latest_episodes':
    get_latest_episodes(params['url'], addon_icon)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'resolve_url':
    set_resolved_url(params['url'])

elif mode == 'gfq_live':
    display_live()
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'dailymotion':
    get_dailymotion()

elif mode == 'justintv':
    get_justintv()