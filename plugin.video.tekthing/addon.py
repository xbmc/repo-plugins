#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import sys

from BeautifulSoup import BeautifulSoup
from urlparse import parse_qs
import urllib
import requests

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

__addon__       = "plugin.video.tekthing"
__settings__    = xbmcaddon.Addon(id=__addon__ )
__language__    = __settings__.getLocalizedString
__images_path__ = os.path.join( xbmcaddon.Addon(id=__addon__ ).getAddonInfo('path'), 'resources', 'images' )
__date__        = "6 august 2015"
__version__     = "1.0.0"

DEBUG = __settings__.getSetting('debug')
RSS_URL = "http://feeds.feedburner.com/Tekthing"


def getParams():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
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
    # Get HTML page...
    #
    response = requests.get(RSS_URL)
    html_source = response.text
    html_source = html_source.encode('utf-8', 'ignore')
    
    soup = BeautifulSoup( html_source )
    
#<title>TekThing 31: Epson WorkForce ET-4550 Means Cheap Ink! New Intel Skylake Core i7-6700K, Turn On Windows 10 Privacy!</title>    
    titles = soup.findAll('title')
    
    if (DEBUG) == 'true':
        xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(titles):", str(len(titles)) ), xbmc.LOGNOTICE )

# <content:encoded><![CDATA[&lt;iframe scrolling="no" allowfullscreen="" src="//www.youtube.com/embed/hA4MUWYEsHo?wmode=opaque&amp;enablejsapi=1" width="854" frameborder="0" height="480"&gt;
# ... an&gt;Download the&nbsp;&lt;/span&gt;&lt;a href="http://tekthing.podbean.com/mf/web/gbjpky/tekthing--0031--epson-ecotank-means-cheap-ink-new-intel-skylake-corei7-6700k-cpu-more.mp4"&gt;video&l...
    shows = soup.findAll('content:encoded')
    
    if (DEBUG) == 'true':
        xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "len(shows):", str(len(shows)) ), xbmc.LOGNOTICE )
    
    for show in shows:
        youtube_id = findString('//www.youtube.com/embed/', str(show), '?')
        # Skip video if youtube-id can't be found
        if youtube_id == '':
            title_index = title_index + 1
            continue
            
        youtube_plugin_url = makeYouTubePluginUrl(youtube_id)
        url = youtube_plugin_url
   
        if (DEBUG) == 'true':
            xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "url:", str(url) ), xbmc.LOGNOTICE )

        try:
            title = str(titles[title_index])
            title = title.replace('<title>', '')
            title = title.replace('</title>', '')   
        except:
            title = 'Unknown title'
            
        if (DEBUG) == 'true':
            xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "title:", str(title) ), xbmc.LOGNOTICE )            
            
        thumbnail_url = ''

        # Add to list...
        parameters = {"mode" : "play", "title" : title, "url" : url, "next_page_possible": "False"}
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
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


# Mainline

params = getParams()
try:
    mode = params['mode']
except:
    mode = 'list'

if (DEBUG) == 'true':
    xbmc.log( "[ADDON] %s v%s (%s) debug mode, %s = %s" % ( __addon__, __version__, __date__, "mode:", str(mode) ), xbmc.LOGNOTICE )
 
if mode == 'list':
    getVideos()
elif mode == 'play':
    title = params ['title']
    url = params ['url'] 
    playVideo(title, url)