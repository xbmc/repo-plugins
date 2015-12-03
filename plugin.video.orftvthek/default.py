#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket,datetime,time,os,os.path,urlparse,json
import CommonFunctions as common

from resources.lib.base import *
from resources.lib.helpers import *
from resources.lib.serviceapi import *
from resources.lib.htmlscraper import *

try:
   import StorageServer
except:
   import storageserverdummy as StorageServer

socket.setdefaulttimeout(30) 
cache = StorageServer.StorageServer("plugin.video.orftvthek", 999999)

version = "0.5.1"
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
   defaultViewMode = 'Container.SetViewMode(503)'
else:
   defaultViewMode = 'Container.SetViewMode(518)'

thumbViewMode = 'Container.SetViewMode(500)'
smallListViewMode = 'Container.SetViewMode(51)'
playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO) 
 
#hardcoded
video_quality_list = ["Q1A", "Q4A", "Q6A"]
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
useServiceAPI = settings.getSetting("useServiceAPI") == "true"
autoPlay = settings.getSetting("autoPlay") == "true"
useSubtitles = settings.getSetting("useSubtitles") == "true"
videoQuality = settings.getSetting("videoQuality")
enableBlacklist = settings.getSetting("enableBlacklist") == "true"

try:
    videoQuality = video_quality_list[int(videoQuality)]
except:
    videoQuality = video_quality_list[2]
    


#init scrapers
jsonScraper = serviceAPI(xbmc,settings,pluginhandle,videoQuality,videoProtocol,videoDelivery,defaultbanner,defaultbackdrop,useSubtitles,defaultViewMode)
htmlScraper = htmlScraper(xbmc,settings,pluginhandle,videoQuality,videoProtocol,videoDelivery,defaultbanner,defaultbackdrop,useSubtitles,defaultViewMode)


def getMainMenu():
    addDirectory((translation(30001)).encode("utf-8"),news_banner,defaultbackdrop,translation,"","","getAktuelles",pluginhandle)
    addDirectory((translation(30000)).encode("utf-8"),recently_added_banner,defaultbackdrop,translation,"","","getNewShows",pluginhandle)
    addDirectory((translation(30002)).encode("utf-8"),shows_banner,defaultbackdrop,translation,"","","getSendungen",pluginhandle)
    addDirectory((translation(30003)).encode("utf-8"),topics_banner,defaultbackdrop,translation,"","","getThemen",pluginhandle)
    addDirectory((translation(30004)).encode("utf-8"),live_banner,defaultbackdrop,translation,"","","getLive",pluginhandle)
    addDirectory((translation(30005)).encode("utf-8"),tips_banner,defaultbackdrop,translation,"","","getTipps",pluginhandle)
    addDirectory((translation(30006)).encode("utf-8"),most_popular_banner,defaultbackdrop,translation,"","","getMostViewed",pluginhandle)
    addDirectory((translation(30018)).encode("utf-8"),archive_banner,defaultbackdrop,translation,"","","getArchiv",pluginhandle)
    addDirectory((translation(30007)).encode("utf-8"),search_banner,defaultbackdrop,translation,"","","getSearchHistory",pluginhandle)
    addDirectory((translation(30027)).encode("utf-8"),trailer_banner,defaultbackdrop,translation,"","","openTrailers",pluginhandle)
    #blacklist
    if enableBlacklist:
        addDirectory((translation(30037)).encode("utf-8"),blacklist_banner,defaultbackdrop,translation,"","","openBlacklist",pluginhandle)
    listCallback(False,thumbViewMode,pluginhandle)
    
    
def listCallback(sort,viewMode,pluginhandle):
    xbmcplugin.setContent(pluginhandle,'episodes')
    if sort:
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
        xbmc.executebuiltin(viewMode)
    
		
def search():
    addDirectory((translation(30007)).encode("utf-8")+" ...",defaultbanner,defaultbackdrop,translation,' ',"","searchNew",pluginhandle)
    cache.table_name = "searchhistory"
    some_dict = cache.get("searches").split("|")
    for str in reversed(some_dict):
        if str.strip() != '':
            addDirectory(str.encode('UTF-8'),defaultbanner,defaultbackdrop,translation," ",str.replace(" ","+"),"searchNew",pluginhandle)
    listCallback(False,defaultViewMode,pluginhandle)
	
def searchTV():
    keyboard = xbmc.Keyboard('')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
      cache.table_name = "searchhistory"
      keyboard_in = keyboard.getText()
      some_dict = cache.get("searches") + "|"+keyboard_in
      cache.set("searches",some_dict);
      searchurl = "%s/search?q=%s"%(base_url,keyboard_in.replace(" ","+").replace("Ö","O").replace("ö","o").replace("Ü","U").replace("ü","u").replace("Ä","A").replace("ä","a"))
      searchurl = searchurl
      getTableResults(searchurl,cache)
    else:
      addDirectory((translation(30014)).encode("utf-8"),defaultbanner,defaultbackdrop,translation,"","","",pluginhandle)
    listCallback(False,defaultViewMode,pluginhandle)

    
def startPlaylist():
    if playlist != None:
        xbmc.Player().play(playlist)
    else:
        d = xbmcgui.Dialog()
        d.ok('VIDEO QUEUE EMPTY', 'The XBMC video queue is empty.','Add more links to video queue.')
    	
#parameters
params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
link=params.get('link')
banner=params.get('banner')

#modes
if mode == 'openSeries':
    playlist = htmlScraper.getLinks(link,banner,playlist)
    if autoPlay and playlist != None:
        xbmc.Player().play(playlist)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'unblacklistShow':
    title=params.get('title')
    unblacklistItem(title)
    addDirectory(">> %s <<" % (translation(30039)).encode("utf-8"),defaultbanner,defaultbackdrop,translation,"","","",pluginhandle)
    printBlacklist(defaultbanner,defaultbackdrop,translation,pluginhandle)
    xbmcplugin.endOfDirectory(pluginhandle)
elif mode == 'blacklistShow':
    title=params.get('title')
    blacklistItem(title)
    xbmc.executebuiltin('Container.Refresh')
if mode == 'openBlacklist':
    addDirectory(">> %s <<" % (translation(30039)).encode("utf-8"),defaultbanner,defaultbackdrop,translation,"","","",pluginhandle)
    printBlacklist(defaultbanner,defaultbackdrop,translation,pluginhandle)
    xbmcplugin.endOfDirectory(pluginhandle)
elif mode == 'getSendungen':
    if useServiceAPI:
        jsonScraper.getCategories()
    else:
        htmlScraper.getCategories()
    listCallback(True,thumbViewMode,pluginhandle)
elif mode == 'getAktuelles':
    if useServiceAPI:
        jsonScraper.getTableResults(jsonScraper.serviceAPIHighlights)
    else:
        htmlScraper.getRecentlyAdded(htmlScraper.base_url)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getLive':
    if useServiceAPI:
        jsonScraper.getLiveStreams()
    else:
        htmlScraper.getLiveStreams()
    listCallback(False,smallListViewMode,pluginhandle)
elif mode == 'getTipps':
    if useServiceAPI:
        jsonScraper.getTableResults(jsonScraper.serviceAPITip)
    else:
        htmlScraper.getTableResults(htmlScraper.tip_url)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getNewShows':
    if useServiceAPI:
        jsonScraper.getTableResults(jsonScraper.serviceAPIRecent)
    else:
        htmlScraper.getTableResults(htmlScraper.recent_url)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getMostViewed':
    if useServiceAPI:
        jsonScraper.getTableResults(jsonScraper.serviceAPIViewed)
    else:
        htmlScraper.getTableResults(htmlScraper.mostviewed_url)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getThemen':
    if useServiceAPI:
        jsonScraper.getThemen()
    else:
        htmlScraper.getThemen()
    listCallback(True,defaultViewMode,pluginhandle)
elif mode == 'getSendungenDetail':
    htmlScraper.getCategoriesDetail(link,banner)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getThemenDetail':
    htmlScraper.getThemenDetail(link)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'getArchiv':
    if useServiceAPI:
        jsonScraper.getArchiv()
    else:
        htmlScraper.getArchiv(htmlScraper.schedule_url)
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
    if autoPlay and playlist != None:
        xbmc.Player().play(playlist)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'openSegment':
    jsonScraper.getSegment(link, params.get('segmentID'),playlist)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'liveStreamNotOnline':
    jsonScraper.getLiveNotOnline(link)
    listCallback(False,defaultViewMode,pluginhandle)
elif mode == 'playlist':
    startPlaylist()
else:
    getMainMenu()
