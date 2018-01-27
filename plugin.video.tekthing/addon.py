#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from future import standard_library
standard_library.install_aliases()
from builtins import str
import os
import sys
import re
from bs4 import BeautifulSoup
from urllib.parse import parse_qs
import urllib.request, urllib.parse, urllib.error
import requests
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

ADDON = "plugin.video.tekthing"
SETTINGS = xbmcaddon.Addon()
LANGUAGE = SETTINGS.getLocalizedString
IMAGES_PATH = os.path.join( xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'images' )
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
RSS_URL = "http://feeds.feedburner.com/Tekthing"
DATE = "2018-01-21"
VERSION = "1.0.3"


def getParams():
    p = parse_qs(sys.argv[2][1:])
    for i in list(p.keys()):
        p[i] = p[i][0]
    return p

#Example:
#search_for_string: '//www.youtube.com/embed/'
#string_to_be_searched: '<content:encoded><![CDATA[&lt;iframe scrolling="no" allowfullscreen="" src="//www.youtube.com/embed/hA4MUWYEsHo?wmode=opaque&amp;'
#search_for_string_delimiter = '?'. 
#search_for_string_delimiter is the first character that does NOT belong to the search_for_string.
def findString(search_for_string, string_to_be_searched, search_for_string_delimiter) :
    begin_pos_search_for_string = str(string_to_be_searched).find(search_for_string)
    if begin_pos_search_for_string >= 0:
        begin_pos_search_for_string = begin_pos_search_for_string + len(search_for_string)
        rest = str(string_to_be_searched)[begin_pos_search_for_string:]
        length_search_for_string = rest.find(search_for_string_delimiter)
        end_pos_search_for_string = begin_pos_search_for_string + length_search_for_string
        found_string = str(string_to_be_searched)[begin_pos_search_for_string:end_pos_search_for_string]     
        return found_string
    else:
        return ''


def makeYouTubePluginUrl(youtube_id):
    return 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube_id


def getVideos() :
    #
    # Init
    #
    title_index = 0
    # Skip the first title
    title_index = title_index + 1

    #
    # Get HTML page
    #
    response = requests.get(RSS_URL, headers=HEADERS)

    html_source = response.text
    html_source = convertToUnicodeString(html_source)

    # Parse response
    soup = getSoup(html_source)

    # log("soup", soup)

#<title>TekThing 31: Epson WorkForce ET-4550 Means Cheap Ink! New Intel Skylake Core i7-6700K, Turn On Windows 10 Privacy!</title>    
    titles = soup.findAll('title')

    log("len(titles)", len(titles))

    # <content:encoded><![CDATA[&lt;iframe scrolling="no" allowfullscreen="" src="//www.youtube.com/embed/hA4MUWYEsHo?wmode=opaque&amp;enablejsapi=1" width="854" frameborder="0" height="480"&gt;
    # ... an&gt;Download the&nbsp;&lt;/span&gt;&lt;a href="http://tekthing.podbean.com/mf/web/gbjpky/tekthing--0031--epson-ecotank-means-cheap-ink-new-intel-skylake-corei7-6700k-cpu-more.mp4"&gt;video&l...

    # ends with .mp4
    shows = soup.findAll('a', attrs={'href': re.compile("\w*.mp4")})

    log("len(shows)", len(shows))

    for show in shows:

        log("show", show)

        #<a href="https://tekthing.podbean.com/mf/web/jtrj6h/tekthing--0158--new-dell-xps-13-hp-chromebooks-ces-2018-kill-a-watt.mp4">Download Episode 158</a>
        url = findString('href="', show, '"')

        log("url", url)

        try:
            title = str(titles[title_index])
            title = title.replace('<title>', '')
            title = title.replace('</title>', '')   
        except:
            title = 'Unknown title'

        log("title", title)

        thumbnail_url = ''

        # Add to list...
        parameters = {"mode" : "play", "title" : title, "url" : url, "next_page_possible": "False"}
        url = sys.argv[0] + '?' + urllib.parse.urlencode(parameters)
        listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
        listitem.setInfo( "video", { "Title" : title, "Studio" : "roosterteeth" } )
        folder = False
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
        
        title_index = title_index + 1
        
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
     
    # End of list...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )


def playVideo (title, video_url):
    playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
    playlist.clear()

    thumbnail_url = ''
    listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
    xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
    listitem.setInfo( "video", { "Title": title, "Studio" : "Tekthing", "Plot" : title, "Genre" : "It-news" } )
    playlist.add( video_url, listitem )

    xbmcPlayer = xbmc.Player()
    xbmcPlayer.play( playlist )


if sys.version_info[0] > 2:
    unicode = str


def convertToUnicodeString(s, encoding='utf-8'):
    """Safe decode byte strings to Unicode"""
    if isinstance(s, bytes):  # This works in Python 2.7 and 3+
        s = s.decode(encoding)
    return s


def convertToByteString(s, encoding='utf-8'):
    """Safe encode Unicode strings to bytes"""
    if isinstance(s, unicode):
        s = s.encode(encoding)
    return s


def log(name_object, object):
    try:
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, name_object, convertToUnicodeString(object)), xbmc.LOGDEBUG)
    except:
        xbmc.log("[ADDON] %s v%s (%s) debug mode, %s = %s" % (
            ADDON, VERSION, DATE, name_object,
            "Unable to log the object due to an error while converting it to an unicode string"), xbmc.LOGDEBUG)


def getSoup(html, default_parser="html5lib"):
    soup = BeautifulSoup(html, default_parser)
    return soup


# Mainline

params = getParams()
try:
    mode = params['mode']
except:
    mode = 'list'

if mode == 'list':
    getVideos()
elif mode == 'play':
    title = params ['title']
    url = params ['url'] 
    playVideo(title, url)