# -*- coding: utf-8 -*-

#############################################################################################
#
# Name: plugin.video.gfq
# Author: Nicholas Stinzianni
# Description: Guys From Queens (GFQ) Network is a producer of talk-radio style podcasts covering "everything from news, pop-culture, technology, opinion, and entertainment on a daily basis."
# Type: Video Addon
# Version: 3.0.0
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

global shows
shows = {}

def addon_log(string):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except:
        log_message = 'addonException: addon_log: %s' %format_exc()
    xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message), level=xbmc.LOGDEBUG)

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

def set_resolved_url(resolved_url, name):
    success = False
    if resolved_url:
        success = True
    else:
        resolved_url = ''
    
    if name == '':
        item = xbmcgui.ListItem(path=resolved_url)
    else:
        # ' // Replace Watch GFQ Live with GFQ Live on Now Playing Screen
        if name == language(30200) or name == language(30300):
            name = language(30000)
        item = xbmcgui.ListItem(name, path=resolved_url)
    
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)

def add_dir(name, url, iconimage, mode, info={}, VideoStreamInfo={}, AudioStreamInfo={}):
    item_params = {'name': name, 'url': url, 'mode': mode,
                   'iconimage': iconimage, 'content_type': content_type}
    plugin_url = '%s?%s' %(sys.argv[0], urllib.urlencode(item_params))
    listitem = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    isfolder = True
    if mode == 'resolve_url':
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

# ' // Parses XML File with Listing of GFQ Show Titles, Show Cover Art, and RSS Feed for Show
def get_shows():
    try:
        soup = BeautifulSoup(make_request('http://www.gfqnetwork.com/roku/config.opml'), 'html.parser')
        outlines = soup.findAll('outline')
    except:
        addon_log('Error: Unable to Load GFQ Shows from Roku OPML File. URL: http://www.gfqnetwork.com/roku/config.opml')

    show_titles = re.compile('title="(.+?)"').findall(str(outlines))
    show_icons = re.compile('img="(.+?)"').findall(str(outlines))
    show_urls = re.compile('url="(.+?)"').findall(str(outlines))

    for index in range(len(show_titles)):
        try:
            shows[show_titles[index]] = {'show_icon': show_icons[index], 'show_url': show_urls[index], 'show_desc': ''}
            addon_log('Found GFQ Show: %s' %show_titles[index])
        except:
            addon_log('addonException loading new show: %s' %format_exc)
    return "True"

# ' // Displays Main Menu with GFQ Live Stream Links and GFQ Shows
def display_shows():
    VideoStreamInfo = {'codec': 'h264', 'aspect': 1.78, 'width': 1280, 'height': 720}
    AudioStreamInfo = {'codec': 'aac', 'language': 'en', 'channels': 2}

    get_shows()
    # // Watch Live - HLS Feed
    add_dir(language(30200), 'http://live.shiftyland.net/hls/gfq.m3u8', addon_icon, 'resolve_url', [], VideoStreamInfo, AudioStreamInfo)
    # // Listen Live - Audio Only Feed
    add_dir(language(30300), 'http://s25.streamerportal.com:8235/live', addon_icon, 'resolve_url', [], [], AudioStreamInfo)
    # // Latest GFQ Episodes -- Feed retired by GFQ
    #add_dir(language(30100), 'http://feeds.feedburner.com/GfqNetworkallVideo', addon_icon, 'latest_episodes')
    items = sorted(shows.keys(), key=str.lower)
    for i in items:
        show = shows[i]
        add_dir(i, show['show_url'], show['show_icon'], 'episodes', {'plot': show['show_desc']})

# ' // Parses RSS XML Feeds and Returns Array of Episodes with Show Titles, Numbers, Dates, Durations, Genre, Plot, Size, and Stream Information
def get_episodes(url, iconimage):
    ''' return array of episodes of a specific show '''
    soup = BeautifulSoup(make_request(url), 'html.parser')
    soup = soup.prettify().encode('utf-8').strip()
    soup = BeautifulSoup(soup, 'html.parser')

    # ' // Find All <item> tags (1 Tag per Episode)
    items = soup.find_all("item")

    episodes = []

    # ' // Loop Through Each <item> Tag and Scan HTML Within Tag
    for item in items:
        # ' // Get Podcast Title
        try:
            show_title = str(item.find_next("title").get_text("", strip=True).encode('utf-8'))
        except:
            show_title = ""
        # ' // Get Podcast Episode Number
        show_number = re.compile('.* Ep. (.+?) - .*').findall(show_title)
        if len(show_number) != 1:
            show_number = re.compile('.* Ep. (.+?) – .*').findall(show_title)
        if len(show_number) == 1:
            show_number = int(show_number[0])
        else:
            show_number = 0
        # ' // Get Podcast Air Date
        try:
            show_date = parse(str(item.find_next("pubdate").get_text("", strip=True).encode('utf-8')), fuzzy=True)
        except:
            show_date = ""
        show_icon = addon_icon
        # ' // Get Podcast Duration
        try:
            show_duration = str(item.find_next("itunes:duration").get_text("", strip=True).encode('utf-8'))
        except:
            show_duration = "0:0:0"
        show_duration = sum(int(x) * 60 ** i for i,x in enumerate(reversed(show_duration.split(":"))))

        # ' // Populate Kodi Media Information Array from Above Podcast Variables
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

        # ' // Attempt 1: Obtain Video URL and Size from <enclosure> Tag
        try:
            media_content = re.compile('<enclosure length="(.+?)" type="video/mp4" url="(.+?)">').findall(str(item.find_next("enclosure").encode('utf-8')))
        except:
            media_content = ""

        # ' // Attempt 2: Obtain Video URL and Size from <media:content> Tag
        if len(media_content) != 1:
            try:
                media_content = re.compile('<media:content filesize="(.+?)" type="video/mp4" url="(.+?)">').findall(str(item.find_next("media:content").encode('utf-8')))
            except:
                media_content = ""

        # ' // Attempt 3: Obtain Video URL and Size from <media:content> Tag w/Blip.TV Metadata
        if len(media_content) != 1:
            try:
                media_content = re.compile('<media:content blip:acodec="ffaac" blip:role="Source" blip:vcodec="ffh264" expression="full" filesize="(.+?)" height="720" isdefault="true" type="video/mp4" url="(.+?)" width="1280">').findall(str(item.find_next("media:content", attrs={"blip:role": "Source"}).encode('utf-8')))
            except:
                media_content = ""

        # ' // Add Completed Kodi Menu Item
        if len(media_content) == 1:
            media_content = media_content[0]
            info['Size'] = int(media_content[0])
            VideoStreamInfo = {'codec': 'h264', 'aspect': 1.78, 'width': 1280, 'height': 720, 'duration': show_duration}
            AudioStreamInfo = {'codec': 'aac', 'language': 'en', 'channels': 2}

            episodes.append({'url': media_content[1], 'thumb': iconimage, 'info': info, 'VideoStreamInfo': VideoStreamInfo, 'AudioStreamInfo': AudioStreamInfo})
    return episodes

# ' // Add Array of Episodes from RSS to Kodi Menu Items
def display_episodes(url, iconimage):
    episodes = get_episodes(url, iconimage)
    for i in episodes:
        add_dir(i['info']['Title'], i['url'], i['thumb'], 'resolve_url', i['info'], i['VideoStreamInfo'], i['AudioStreamInfo'])

def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p

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
        if isinstance(shows, dict):
            display_shows()
        else:
            raise
    except:
        if isinstance(shows, dict):
            display_shows()
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'episodes':
    display_episodes(params['url'], params['iconimage'])
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'latest_episodes':
    display_episodes(params['url'], addon_icon)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == 'resolve_url':
    set_resolved_url(params['url'], params['name'])
