#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import socket
import sys
import urllib
import xbmcaddon
import xbmcgui
import xbmcplugin

import CommonFunctions as common

from resources.lib.base import *
from resources.lib.helpers import *
from resources.lib.serviceapi import *
from resources.lib.htmlscraper import *
from resources.lib.Scraper import *

try:
   import StorageServer
except ImportError:
   import storageserverdummy as StorageServer

socket.setdefaulttimeout(30)
cache = StorageServer.StorageServer("plugin.video.orftvthek", 999999)

plugin = "ORF-TVthek-" + xbmcaddon.Addon().getAddonInfo('version')

#initial
common.plugin = plugin
settings = xbmcaddon.Addon()
pluginhandle = int(sys.argv[1])
basepath = settings.getAddonInfo('path')
translation = settings.getLocalizedString
userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"

#video playback
tvthekplayer = xbmc.Player()
playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)

#hardcoded
video_quality_list = ["Q1A", "Q4A", "Q6A", "Q8C"]
videoProtocol = "http"
videoDelivery = "progressive"

#media resources
resource_path = os.path.join( basepath, "resources" )
media_path = os.path.join( resource_path, "media" )
defaultbanner =  os.path.join(media_path,"default_banner.jpg")
news_banner =  os.path.join(media_path,"news_banner.jpg")
recently_added_banner =  os.path.join(media_path,"recently_added_banner.jpg")
shows_banner =  os.path.join(media_path,"shows_banner.jpg")
topics_banner =  os.path.join(media_path,"topics_banner.jpg")
live_banner =  os.path.join(media_path,"live_banner.jpg")
tips_banner =  os.path.join(media_path,"tips_banner.jpg")
most_popular_banner =  os.path.join(media_path,"most_popular_banner.jpg")
schedule_banner =  os.path.join(media_path,"schedule_banner.jpg")
archive_banner =  os.path.join(media_path,"archive_banner.jpg")
search_banner =  os.path.join(media_path,"search_banner.jpg")
trailer_banner =  os.path.join(media_path,"trailer_banner.jpg")
blacklist_banner =  os.path.join(media_path,"blacklist_banner.jpg")
defaultbackdrop = os.path.join(media_path,"fanart.jpg")

#load settings
useServiceAPI = Settings.serviceAPI()
videoQuality = Settings.videoQuality(video_quality_list)
autoPlayPrompt = Settings.autoPlayPrompt()


#init scrapers
if useServiceAPI:
    debugLog("Service API activated",'Info')
    scraper = serviceAPI(xbmc, settings, pluginhandle, videoQuality, videoProtocol, videoDelivery, defaultbanner, defaultbackdrop)
else:
    debugLog("HTML Scraper activated",'Info')
    scraper = htmlScraper(xbmc, settings, pluginhandle, videoQuality, videoProtocol, videoDelivery, defaultbanner, defaultbackdrop)

#parameters
params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
link=params.get('link')
banner=params.get('banner')
videourl=params.get('videourl')
url=params.get('url')


if mode:
    debugLog("Mode: %s" % mode,'Info')
if link:
    debugLog("Link: %s" % urllib.unquote(link),'Info')
if url:
    debugLog("Url: %s" % urllib.unquote(url),'Info')
if videourl:
    debugLog("Videourl: %s" % urllib.unquote(videourl),'Info')


def getMainMenu():
    debugLog("Building Main Menu","Info")
    addDirectory((translation(30001)).encode("utf-8"),news_banner,defaultbackdrop, "","","getAktuelles",pluginhandle)
    addDirectory((translation(30000)).encode("utf-8"),recently_added_banner,defaultbackdrop, "","","getNewShows",pluginhandle)
    addDirectory((translation(30002)).encode("utf-8"),shows_banner,defaultbackdrop, "","","getSendungen",pluginhandle)
    addDirectory((translation(30003)).encode("utf-8"),topics_banner,defaultbackdrop, "","","getThemen",pluginhandle)
    addDirectory((translation(30004)).encode("utf-8"),live_banner,defaultbackdrop, "","","getLive",pluginhandle)
    addDirectory((translation(30005)).encode("utf-8"),tips_banner,defaultbackdrop, "","","getTipps",pluginhandle)
    addDirectory((translation(30006)).encode("utf-8"),most_popular_banner,defaultbackdrop, "","","getMostViewed",pluginhandle)
    addDirectory((translation(30018)).encode("utf-8"),schedule_banner,defaultbackdrop, "","","getSchedule",pluginhandle)
    if not useServiceAPI:
        addDirectory((translation(30049)).encode("utf-8"),schedule_banner,defaultbackdrop, "","","getArchiv",pluginhandle)
    else:
        addDirectory((translation(30027)).encode("utf-8"),trailer_banner,defaultbackdrop, "","","openTrailers",pluginhandle)
    addDirectory((translation(30007)).encode("utf-8"),search_banner,defaultbackdrop, "","","getSearchHistory",pluginhandle)
    if Settings.blacklist():
        addDirectory((translation(30037)).encode("utf-8"),blacklist_banner,defaultbackdrop, "","","openBlacklist",pluginhandle)
    listCallback(False,pluginhandle)


def listCallback(sort,pluginhandle):
    xbmcplugin.setContent(pluginhandle,'episodes')
    if sort:
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.endOfDirectory(pluginhandle)

def startPlaylist(player,playlist):
    if playlist != None:
        player.play(playlist)
    else:
        d = xbmcgui.Dialog()
        d.ok((translation(30051)).encode("utf-8"), (translation(30050)).encode("utf-8"),'')


#modes
if mode == 'openSeries':
    playlist.clear()
    playlist = scraper.getLinks(link,banner,playlist)
    if not autoPlayPrompt:
        listCallback(False,pluginhandle)
    elif playlist != None:
        ok = xbmcgui.Dialog().yesno((translation(30047)).encode("utf-8"),(translation(30048)).encode("utf-8"))
        if ok:
            debugLog("Starting Playlist for %s" % urllib.unquote(link),'Info')
            tvthekplayer.play(playlist)
    else:
        listCallback(False,pluginhandle)

elif mode == 'unblacklistShow':
    heading = translation(30040).encode('UTF-8') % urllib.unquote(link).replace('+', ' ').strip()
    if xbmcgui.Dialog().yesno(heading, heading):
        unblacklistItem(link)
        xbmc.executebuiltin('Container.Refresh')
elif mode == 'blacklistShow':
    blacklistItem(link)
    xbmc.executebuiltin('Container.Refresh')
if mode == 'openBlacklist':
    printBlacklist(defaultbanner,defaultbackdrop,translation,pluginhandle)
    xbmcplugin.endOfDirectory(pluginhandle)
elif mode == 'getSendungen':
    scraper.getCategories()
    listCallback(True,pluginhandle)
elif mode == 'getAktuelles':
    scraper.getHighlights()
    listCallback(False,pluginhandle)
elif mode == 'getLive':
    scraper.getLiveStreams()
    listCallback(False,pluginhandle)
elif mode == 'getTipps':
    scraper.getTips()
    listCallback(False,pluginhandle)
elif mode == 'getNewShows':
    scraper.getNewest()
    listCallback(False,pluginhandle)
elif mode == 'getMostViewed':
    scraper.getMostViewed()
    listCallback(False,pluginhandle)
elif mode == 'getThemen':
    scraper.getThemen()
    listCallback(True,pluginhandle)
elif mode == 'getSendungenDetail':
    scraper.getCategoriesDetail(link,banner)
    listCallback(False,pluginhandle)
elif mode == 'getThemenDetail':
    scraper.getArchiveDetail(link)
    listCallback(False,pluginhandle)
elif mode == 'getArchiveDetail':
    scraper.getArchiveDetail(link)
    listCallback(False,pluginhandle)
elif mode == 'getSchedule':
    scraper.getSchedule()
    listCallback(False,pluginhandle)
elif mode == 'getArchiv':
    scraper.getArchiv()
    listCallback(False,pluginhandle)
elif mode == 'getScheduleDetail':
    scraper.openArchiv(link)
    listCallback(True,pluginhandle)
elif mode == 'openTrailers':
    scraper.getTrailers()
    listCallback(False,pluginhandle)
elif mode == 'getSearchHistory':
    scraper.getSearchHistory(cache);
    listCallback(False,pluginhandle)
elif mode == 'getSearchResults':
    if not link == None:
        scraper.getSearchResults(urllib.unquote(link),cache)
    else:
        scraper.getSearchResults("",cache)
    listCallback(False,pluginhandle)
elif mode == 'openDate':
    scraper.getDate(link, params.get('from'))
    listCallback(False,pluginhandle)
elif mode == 'openProgram':
    scraper.getProgram(link,playlist)
    listCallback(False,pluginhandle)
elif mode == 'openTopic':
    scraper.getTopic(link)
    listCallback(False,pluginhandle)
elif mode == 'openEpisode':
    scraper.getEpisode(link,playlist)
    listCallback(False,pluginhandle)
elif mode == 'liveStreamNotOnline':
    scraper.getLiveNotOnline(link)
    listCallback(False,pluginhandle)
elif mode == 'liveStreamRestart':
    scraper.liveStreamRestart(link)
elif mode == 'playlist':
    startPlaylist(tvthekplayer,playlist)
elif mode == 'play':
    videourl = "%s|User-Agent=%s" % (videourl,userAgent)
    debugLog(videourl,'Info')
    play_item = xbmcgui.ListItem(path=videourl)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem=play_item)
    listCallback(False,pluginhandle)                         
elif sys.argv[2] == '':
    getMainMenu()
else:
    listCallback(False,pluginhandle)
