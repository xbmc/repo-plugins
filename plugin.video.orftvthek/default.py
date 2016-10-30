#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket,datetime,time,os,os.path,urlparse,json
import CommonFunctions as common

from resources.lib.base import *
from resources.lib.helpers import *
from resources.lib.serviceapi import *
from resources.lib.htmlscraper import *
from resources.lib.Scraper import *

try:
   import StorageServer
except:
   import storageserverdummy as StorageServer

socket.setdefaulttimeout(30) 
cache = StorageServer.StorageServer("plugin.video.orftvthek", 999999)

version = "0.5.9"
plugin = "ORF-TVthek-" + version
author = "sofaking,Rechi"

#initial
common.plugin = plugin
settings = xbmcaddon.Addon(id='plugin.video.orftvthek') 
pluginhandle = int(sys.argv[1])
basepath = settings.getAddonInfo('path')
translation = settings.getLocalizedString

current_skin = xbmc.getSkinDir();

if 'confluence' in current_skin:
   debugLog("Confluence Found - Setting View","Info")
   defaultViewMode = 'Container.SetViewMode(503)'
else:
   debugLog("Confluence Not Found - Setting Fallback View","Info")
   defaultViewMode = 'Container.SetViewMode(518)'

thumbViewMode = 'Container.SetViewMode(500)'
smallListViewMode = 'Container.SetViewMode(51)'
playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO) 
 
#hardcoded
video_quality_list = ["Q1A", "Q4A", "Q6A", "Q8C"]
videoProtocol = "http"
videoDelivery = "progressive"

#media resources
resource_path = os.path.join( basepath, "resources" )
media_path = os.path.join( resource_path, "media" )
defaultbanner =  os.path.join(media_path,"default_banner_v2.jpg")
news_banner =  os.path.join(media_path,"news_banner_v2.jpg")
recently_added_banner =  os.path.join(media_path,"recently_added_banner_v2.jpg")
shows_banner =  os.path.join(media_path,"shows_banner_v2.jpg")
topics_banner =  os.path.join(media_path,"topics_banner_v2.jpg")
live_banner =  os.path.join(media_path,"live_banner_v2.jpg")
tips_banner =  os.path.join(media_path,"tips_banner_v2.jpg")
most_popular_banner =  os.path.join(media_path,"most_popular_banner_v2.jpg")
archive_banner =  os.path.join(media_path,"archive_banner_v2.jpg")
search_banner =  os.path.join(media_path,"search_banner_v2.jpg")
trailer_banner =  os.path.join(media_path,"trailer_banner_v2.jpg")
blacklist_banner =  os.path.join(media_path,"blacklist_banner.jpg")
defaultbackdrop = os.path.join(media_path,"fanart.jpg")

#load settings
forceView = settings.getSetting("forceView") == "true"
useServiceAPI = settings.getSetting('useServiceAPI') == 'true'
useSubtitles = settings.getSetting("useSubtitles") == "true"
videoQuality = settings.getSetting("videoQuality")
enableBlacklist = settings.getSetting("enableBlacklist") == "true"
autoPlayPrompt = settings.getSetting("autoPlayPrompt") == "true"

try:
    videoQuality = video_quality_list[int(videoQuality)]
except:
    videoQuality = video_quality_list[2]
    

#init player
tvthekplayer = xbmc.Player()

#init scrapers
jsonScraper = serviceAPI(xbmc, settings, pluginhandle, videoQuality, videoProtocol, videoDelivery, defaultbanner, defaultbackdrop, useSubtitles, defaultViewMode)
htmlScraper = htmlScraper(xbmc, settings, pluginhandle, videoQuality, videoProtocol, videoDelivery, defaultbanner, defaultbackdrop, useSubtitles, defaultViewMode)

#parameters
params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
link=params.get('link')
title=params.get('title')
banner=params.get('banner')
videourl=params.get('videourl')
url=params.get('url')

scraper = jsonScraper if useServiceAPI else htmlScraper

if mode:
    debugLog("Mode: %s" % mode,'Info')
if link:
    debugLog("Link: %s" % urllib.unquote(link),'Info')
if url:
    debugLog("Url: %s" % urllib.unquote(url),'Info')
if videourl:
    debugLog("Videourl: %s" % urllib.unquote(videourl),'Info')
if title:
    debugLog("Title: %s" % title.encode('UTF-8'),'Info')
    

def getMainMenu():
    debugLog("Building Main Menu","Info")
    addDirectory((translation(30001)).encode("utf-8"),news_banner,defaultbackdrop, "","","getAktuelles",pluginhandle)
    addDirectory((translation(30000)).encode("utf-8"),recently_added_banner,defaultbackdrop, "","","getNewShows",pluginhandle)
    addDirectory((translation(30002)).encode("utf-8"),shows_banner,defaultbackdrop, "","","getSendungen",pluginhandle)
    addDirectory((translation(30003)).encode("utf-8"),topics_banner,defaultbackdrop, "","","getThemen",pluginhandle)
    addDirectory((translation(30004)).encode("utf-8"),live_banner,defaultbackdrop, "","","getLive",pluginhandle)
    addDirectory((translation(30005)).encode("utf-8"),tips_banner,defaultbackdrop, "","","getTipps",pluginhandle)
    addDirectory((translation(30006)).encode("utf-8"),most_popular_banner,defaultbackdrop, "","","getMostViewed",pluginhandle)
    addDirectory((translation(30018)).encode("utf-8"),archive_banner,defaultbackdrop, "","","getArchiv",pluginhandle)
    addDirectory((translation(30007)).encode("utf-8"),search_banner,defaultbackdrop, "","","getSearchHistory",pluginhandle)
    if useServiceAPI:
        addDirectory((translation(30027)).encode("utf-8"),trailer_banner,defaultbackdrop, "","","openTrailers",pluginhandle)
    if enableBlacklist:
        addDirectory((translation(30037)).encode("utf-8"),blacklist_banner,defaultbackdrop, "","","openBlacklist",pluginhandle)
    listCallback(False,thumbViewMode,pluginhandle)
    
    
def listCallback(sort,viewMode,pluginhandle):
    xbmcplugin.setContent(pluginhandle,'episodes')
    if sort:
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
        xbmc.executebuiltin(viewMode)     
    
def startPlaylist(player,playlist):
    if playlist != None:
        player.play(playlist)
    else:
        d = xbmcgui.Dialog()
        d.ok('VIDEO QUEUE EMPTY', 'The XBMC video queue is empty.','Add more links to video queue.')

    
#modes
if mode == 'openSeries':
    playlist.clear()
    playlist = htmlScraper.getLinks(link,banner,playlist)
    if not autoPlayPrompt:
        listCallback(False,defaultViewMode,pluginhandle)
    elif playlist != None:
        ok = xbmcgui.Dialog().yesno((translation(30047)).encode("utf-8"),(translation(30048)).encode("utf-8"))
        if ok:
            debugLog("Starting Playlist for %s" % urllib.unquote(link),'Info')
            tvthekplayer.play(playlist)
            xbmc.executebuiltin(defaultViewMode) 
    else:
        listCallback(False,defaultViewMode,pluginhandle)
        
elif mode == 'unblacklistShow':
    title=params.get('title')
    unblacklistItem(title)
    addDirectory(">> %s <<" % (translation(30039)).encode("utf-8"),defaultbanner,defaultbackdrop, "","","",pluginhandle)
    printBlacklist(defaultbanner,defaultbackdrop,translation,pluginhandle)
    xbmcplugin.endOfDirectory(pluginhandle)
elif mode == 'blacklistShow':
    title=params.get('title')
    blacklistItem(title)
    xbmc.executebuiltin('Container.Refresh')
if mode == 'openBlacklist':
    addDirectory(">> %s <<" % (translation(30039)).encode("utf-8"),defaultbanner,defaultbackdrop, "","","",pluginhandle)
    printBlacklist(defaultbanner,defaultbackdrop,translation,pluginhandle)
    xbmcplugin.endOfDirectory(pluginhandle)
elif mode == 'getSendungen':
    scraper.getCategories()
    listCallback(True,thumbViewMode,pluginhandle)
elif mode == 'getAktuelles':
    scraper.getHighlights()
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getLive':
    scraper.getLiveStreams()
    listCallback(False,smallListViewMode,pluginhandle)
elif mode == 'getTipps':
    scraper.getTips()
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getNewShows':
    scraper.getNewest()
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getMostViewed':
    scraper.getMostViewed()
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getThemen':
    scraper.getThemen()
    listCallback(True,defaultViewMode,pluginhandle)
elif mode == 'getSendungenDetail':
    htmlScraper.getCategoriesDetail(link,banner)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getThemenDetail':
    htmlScraper.getThemenDetail(link)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getArchiv':
    scraper.getArchiv()
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getArchivDetail':
    htmlScraper.openArchiv(link)
    listCallback(True,defaultViewMode,pluginhandle)
elif mode == 'openTrailers':
    jsonScraper.getTrailers()
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getSearchHistory':
    htmlScraper.getSearchHistory(cache);
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getSearchResults':
    if not link == None:
        htmlScraper.getSearchResults(urllib.unquote(link),cache)
    else:
        htmlScraper.getSearchResults("",cache)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'openDate':
    jsonScraper.getDate(link, params.get('from'))
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'openProgram':
    jsonScraper.getProgram(link,playlist)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'openTopic':
    jsonScraper.getTopic(link)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'openEpisode':
    jsonScraper.getEpisode(link,playlist)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'liveStreamNotOnline':
    jsonScraper.getLiveNotOnline(link)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'playlist':
    startPlaylist(tvthekplayer,playlist)
elif sys.argv[2] == '':
    getMainMenu()
else:
    listCallback(False,defaultViewMode,pluginhandle)
