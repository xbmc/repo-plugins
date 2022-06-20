#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from future import standard_library
standard_library.install_aliases()
from builtins import str
import os
import sys
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
DATE = "2022-06-20"
VERSION = "1.0.5"


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

    # <item>
    #       <title>Alienware m15 Review, RTX 2060 Price, Release Date, CES 2019: What We Expect To See!!! -- TekThing 210</title>
    #       <description>
    # GTX 2060 Date &amp; Bargain Pricing, AMD Ryzen 3000 Rumors, and Everything Else We’re Looking Forward To At CES 2019! Alienware m15 Laptop Review, Smart Lock Recommendation, Bear Tracks!!!
    #     </description>
    #       <link/>http://feeds.rapidfeeds.com/?iid4ct=7594293
    #       <guid ispermalink="true">http://feeds.rapidfeeds.com/?iid4ct=7594293</guid>
    #       <enclosure length="616627447" type="video/mp4" url="http://mcdn.podbean.com/mf/web/44j6vt/tekthing--0210--alienware-m15-review-rtx-2060-price-release-date-ces-2019-what-we-expect-to-see.mp4">
    #       <pubdate>Thu, 03 Jan 2019 16:00:00 EST</pubdate>
    #     <author>ask@tekthing.com</author><media:content filesize="616627447" type="video/mp4" url="http://mcdn.podbean.com/mf/web/44j6vt/tekthing--0210--alienware-m15-review-rtx-2060-price-release-date-ces-2019-what-we-expect-to-see.mp4"><itunes:explicit>no</itunes:explicit><itunes:subtitle> GTX 2060 Date &amp; Bargain Pricing, AMD Ryzen 3000 Rumors, and Everything Else We’re Looking Forward To At CES 2019! Alienware m15 Laptop Review, Smart Lock Recommendation, Bear Tracks!!! </itunes:subtitle><itunes:author>ask@tekthing.com</itunes:author><itunes:summary> GTX 2060 Date &amp; Bargain Pricing, AMD Ryzen 3000 Rumors, and Everything Else We’re Looking Forward To At CES 2019! Alienware m15 Laptop Review, Smart Lock Recommendation, Bear Tracks!!! </itunes:summary><itunes:keywords>tech,questions,tekzilla,patrick,norton,shannon,morse,pc,mac,ios,android,fix,make</itunes:keywords></media:content></enclosure></item>

    items = soup.findAll('item')

    log("len(items)", len(items))

    for item in items:

        # log("item", item)

        url = findString('url="', item, '"')

        # log("url", url)

        item = str(item)
        title_start_pos = item.find("<title>") + len("<title>")
        title_end_pos = item.find("</title>", title_start_pos)
        title = item[title_start_pos:title_end_pos]

        try:
            title = convertToUnicodeString(title)
            title = title.replace('<title>', '')
            title = title.replace('</title>', '')
            title = title.replace('&amp', '&')
            title = title.replace('&AMP', '&')
        except:
            title = 'Unknown title'

        log("title", title)

        thumbnail_url = ''

        # Add to list...
        listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail_url )
        listitem.setInfo( "video", { "Title" : title, "Studio" : "roosterteeth" } )
        listitem.setProperty('IsPlayable', 'true')
        folder = False

        # let's remove any non-ascii characters
        title = title.encode('ascii', 'ignore')

        parameters = {"mode" : "play", "title" : title, "url" : url, "next_page_possible": "False"}
        url = sys.argv[0] + '?' + urllib.parse.urlencode(parameters)
        xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ] ), url = url, listitem=listitem, isFolder=folder)
        
        title_index = title_index + 1
        
    # Disable sorting...
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
     
    # End of list...
    xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=True )


def playVideo (title, video_url):
    # Get the command line arguments
    # Get the plugin url in plugin:// notation
    plugin_url = sys.argv[0]
    # Get the plugin handle as an integer number
    plugin_handle = int(sys.argv[1])

    log("video_url", video_url)

    list_item = xbmcgui.ListItem(path=video_url)
    xbmcplugin.setResolvedUrl(plugin_handle, True, list_item)


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