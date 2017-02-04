# -*- coding: utf-8 -*-
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import urlparse
import datetime
import StorageServer
from resources.lib.tgr import TGR
from resources.lib.search import Search
from resources.lib.raiplay import RaiPlay
from resources.lib.radiorai import RadioRai
from resources.lib.relinker import Relinker
import resources.lib.utils as utils

# plugin constants
__plugin__ = "plugin.video.raitv"
__author__ = "Nightflyer"

Addon = xbmcaddon.Addon(id=__plugin__)

# plugin handle
handle = int(sys.argv[1])

# Cache channels for 1 hour
cache = StorageServer.StorageServer("plugin.video.raitv", 1) # (Your plugin name, Cache time in hours)
tv_stations = cache.cacheFunction(RaiPlay().getChannels)
radio_stations = cache.cacheFunction(RadioRai().getChannels)

# utility functions
def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = dict(urlparse.parse_qsl(parameters[1:]))
    return paramDict
 
def addDirectoryItem(parameters, li):
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, 
        listitem=li, isFolder=True)

def addLinkItem(parameters, li, url=""):
    if url == "":
        url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, 
        listitem=li, isFolder=False)

# UI builder functions
def show_root_menu():
    ''' Show the plugin root menu '''
    liStyle = xbmcgui.ListItem("Dirette TV")
    addDirectoryItem({"mode": "live_tv"}, liStyle)
    liStyle = xbmcgui.ListItem("Dirette Radio")
    addDirectoryItem({"mode": "live_radio"}, liStyle)
    liStyle = xbmcgui.ListItem("Replay")
    addDirectoryItem({"mode": "replay"}, liStyle)
    liStyle = xbmcgui.ListItem("Programmi On Demand")
    addDirectoryItem({"mode": "ondemand"}, liStyle)
    liStyle = xbmcgui.ListItem("Archivio Telegiornali")
    addDirectoryItem({"mode": "tg"}, liStyle)
    liStyle = xbmcgui.ListItem("Videonotizie")
    addDirectoryItem({"mode": "news"}, liStyle)
    liStyle = xbmcgui.ListItem("Aree tematiche")
    addDirectoryItem({"mode": "themes"}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_tg_root():
    search = Search()
    for k, v in search.newsArchives.iteritems():
        liStyle = xbmcgui.ListItem(k)
        addDirectoryItem({"mode": "get_last_content_by_tag",
            "tags": search.newsArchives[k]}, liStyle)    
    liStyle = xbmcgui.ListItem("TGR",
        thumbnailImage="http://www.tgr.rai.it/dl/tgr/mhp/immagini/splash.png")
    addDirectoryItem({"mode": "tgr"}, liStyle)  
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_tgr_root():
    #xbmcplugin.setContent(handle=handle, content='tvshows')
    
    tgr = TGR()
    programmes = tgr.getProgrammes()
    for programme in programmes:
        liStyle = xbmcgui.ListItem(programme["title"],
            thumbnailImage=programme["image"])
        addDirectoryItem({"mode": "tgr",
            "behaviour": programme["behaviour"],
            "url": programme["url"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_tgr_list(mode, url):
    #xbmcplugin.setContent(handle=handle, content='episodes')
    
    tgr = TGR()
    itemList = tgr.getList(url)
    for item in itemList:
        behaviour = item["behaviour"]
        if behaviour != "video":
            liStyle = xbmcgui.ListItem(item["title"])
            addDirectoryItem({"mode": "tgr",
                "behaviour": behaviour,
                "url": item["url"]}, liStyle)
        else:
            liStyle = xbmcgui.ListItem(item["title"])
            liStyle.setProperty('IsPlayable', 'true')
            addLinkItem({"mode": "play",
                "url": item["url"]}, liStyle)            
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def play(url, pathId=""):
    xbmc.log("Playing...")
        
    if pathId != "":
        xbmc.log("PathID: " + pathId)
        raiplay = RaiPlay()
        url = raiplay.getVideoUrl(pathId)

    # Handle RAI relinker
    if url[:53] == "http://mediapolis.rai.it/relinker/relinkerServlet.htm" or \
        url[:56] == "http://mediapolisvod.rai.it/relinker/relinkerServlet.htm" or \
        url[:58] == "http://mediapolisevent.rai.it/relinker/relinkerServlet.htm":
        xbmc.log("Relinker URL: " + url)
        relinker = Relinker()
        url = relinker.getURL(url)
        
    # Add the server to the URL if missing
    if url !="" and url.find("://") == -1:
        url = raiplay.baseUrl + url
    xbmc.log("Media URL: " + url)

    # It seems that all .ram files I found are not working
    # because upstream file is no longer present
    if url[-4:].lower() == ".ram":
        dialog = xbmcgui.Dialog()
        dialog.ok("Errore", "I file RealAudio (.ram) non sono supportati.")
        return
    
    # Play the item
    item=xbmcgui.ListItem(path=url + '|User-Agent=' + urllib.quote_plus(Relinker.UserAgent))
    xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=item)

def show_tv_channels():
    raiplay = RaiPlay()
    for station in tv_stations:
        liStyle = xbmcgui.ListItem(station["channel"], thumbnailImage=raiplay.getThumbnailUrl(station["transparent-icon"]))
        liStyle.setProperty('IsPlayable', 'true')
        addLinkItem({"mode": "play",
            "url": station["video"]["contentUrl"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_radio_stations():
    for station in radio_stations:
        if station["flussi"]["liveAndroid"] != "":
            liStyle = xbmcgui.ListItem(station["nome"], thumbnailImage="http://www.rai.it" + station["chImage"])
            liStyle.setProperty('IsPlayable', 'true')
            addLinkItem({"mode": "play",
                "url": station["flussi"]["liveAndroid"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_replay_dates():
    days = ["Domenica", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"]
    months = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", 
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    
    epgEndDate = datetime.date.today()
    epgStartDate = datetime.date.today() - datetime.timedelta(days=7)
    for day in utils.daterange(epgStartDate, epgEndDate):
        day_str = days[int(day.strftime("%w"))] + " " + day.strftime("%d") + " " + months[int(day.strftime("%m"))-1]
        liStyle = xbmcgui.ListItem(day_str)
        addDirectoryItem({"mode": "replay",
            "date": day.strftime("%d-%m-%Y")}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_replay_channels(date):
    raiplay = RaiPlay()
    for station in tv_stations:
        liStyle = xbmcgui.ListItem(station["channel"], thumbnailImage=raiplay.getThumbnailUrl(station["transparent-icon"]))
        addDirectoryItem({"mode": "replay",
            "channel_id": station["channel"],
            "date": date}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_replay_epg(channelId, date):
    xbmc.log("Showing EPG for " + channelId + " on " + date)
    raiplay = RaiPlay()
    programmes = raiplay.getProgrammes(channelId, date)
    
    for programme in programmes:
        if not programme:
            continue
    
        startTime = programme["timePublished"]
        title = programme["name"]
        
        if programme["images"]["landscape"] != "":
            thumb = raiplay.getThumbnailUrl(programme["images"]["landscape"])
        elif programme["isPartOf"] and programme["isPartOf"]["images"]["landscape"] != "":
            thumb = raiplay.getThumbnailUrl(programme["isPartOf"]["images"]["landscape"])
        else:
            thumb = raiplay.noThumbUrl
        
        plot = programme["description"]
        
        if programme["hasVideo"]:
            videoUrl = programme["pathID"]
        else:
            videoUrl = None
        
        if videoUrl is None:
            # programme is not available
            liStyle = xbmcgui.ListItem(startTime + " [I]" + title + "[/I]",
                thumbnailImage=thumb)
            liStyle.setProperty('IsPlayable', 'true')
            addLinkItem({"mode": "nop"}, liStyle)
        else:
            liStyle = xbmcgui.ListItem(startTime + " " + title,
                thumbnailImage=thumb)
            liStyle.setProperty('IsPlayable', 'true')
            addLinkItem({"mode": "play",
                "path_id": videoUrl}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_root():
    raiplay = RaiPlay()
    items = raiplay.getMainMenu()
    for item in items:
        if item["sub-type"] in ("RaiPlay Tipologia Page", "RaiPlay Genere Page"):
            liStyle = xbmcgui.ListItem(item["name"])
            addDirectoryItem({"mode": "ondemand", "path_id": item["PathID"], "sub_type": item["sub-type"]}, liStyle)
    liStyle = xbmcgui.ListItem("Cerca")
    addDirectoryItem({"mode": "ondemand_search_by_name"}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_ondemand_programmes(pathId):
    xbmc.log("PathID: " + pathId)
    raiplay = RaiPlay()
    blocchi = raiplay.getCategory(pathId)

    if len(blocchi) > 1:
        xbmc.log("Blocchi: " + str(len(blocchi)))
        
    for item in blocchi[0]["lanci"]:
        liStyle = xbmcgui.ListItem(item["name"], thumbnailImage=raiplay.getThumbnailUrl(item["images"]["landscape"]))
        addDirectoryItem({"mode": "ondemand", "path_id": item["PathID"], "sub_type": item["sub-type"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_list(pathId):
    xbmc.log("PathID: " + pathId)
    liStyle = xbmcgui.ListItem("0-9")
    addDirectoryItem({"mode": "ondemand_list", "index": "0-9", "path_id": pathId}, liStyle)
    for i in range(26):
        liStyle = xbmcgui.ListItem(chr(ord('A')+i))
        addDirectoryItem({"mode": "ondemand_list", "index": chr(ord('A')+i), "path_id": pathId}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_index(index, pathId):
    xbmc.log("PathID: " + pathId)
    xbmc.log("Index: " + index)
    raiplay = RaiPlay()
    dir = raiplay.getProgrammeList(pathId)
    for item in dir[index]:
        liStyle = xbmcgui.ListItem(item["name"], thumbnailImage=raiplay.getThumbnailUrl(item["images"]["landscape"]))
        addDirectoryItem({"mode": "ondemand", "path_id": item["PathID"], "sub_type": "PLR programma Page"}, liStyle)
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_programme(pathId):
    xbmc.log("PathID: " + pathId)
    raiplay = RaiPlay()
    blocks = raiplay.getProgramme(pathId)
    for block in blocks:
        for set in block["Sets"]:
            liStyle = xbmcgui.ListItem(set["Name"])
            addDirectoryItem({"mode": "ondemand_items", "url": set["url"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_items(url):
    xbmc.log("ContentSet URL: " + url)
    raiplay = RaiPlay()
    items = raiplay.getContentSet(url)
    for item in items:
        title = item["name"]
        if "subtitle" in item and item["subtitle"] != "" and item["subtitle"] != item["name"]:
            title = title + " (" + item["subtitle"] + ")"
        liStyle = xbmcgui.ListItem(title, thumbnailImage=raiplay.getThumbnailUrl(item["images"]["landscape"]))
        liStyle.setProperty('IsPlayable', 'true')
        addLinkItem({"mode": "play",
            "path_id": item["pathID"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def search_ondemand_programmes():
    kb = xbmc.Keyboard()
    kb.setHeading("Cerca un programma")
    kb.doModal()
    if kb.isConfirmed():
        name = kb.getText().decode('utf8')
        xbmc.log("Searching for programme: " + name)
        raiplay = RaiPlay()
        dir = raiplay.getProgrammeList(raiplay.AzTvShowPath)
        for letter in dir:
            for item in dir[letter]:
                if item["name"].lower().find(name) != -1:
                    liStyle = xbmcgui.ListItem(item["name"], thumbnailImage=raiplay.getThumbnailUrl(item["images"]["landscape"]))
                    addDirectoryItem({"mode": "ondemand", "path_id": item["PathID"], "sub_type": "PLR programma Page"}, liStyle)
        xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_news_providers():
    search = Search()
    for k, v in search.newsProviders.iteritems():
        liStyle = xbmcgui.ListItem(k)
        addDirectoryItem({"mode": "get_last_content_by_tag",
            "tags": search.newsProviders[k]}, liStyle)
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_themes():
    search = Search()
    for position, tematica in enumerate(search.tematiche):
        liStyle = xbmcgui.ListItem(tematica)
        addDirectoryItem({"mode": "get_last_content_by_tag",
            "tags": "Tematica:"+search.tematiche[int(position)]}, liStyle)
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def get_last_content_by_tag(tags):
    xbmc.log("Get latest content for tags: " + tags)
    search = Search()
    items = search.getLastContentByTag(tags)
    show_search_result(items)

def get_most_visited(tags):
    xbmc.log("Get most visited for tags: " + tags)
    search = Search()
    items = search.getMostVisited(tags)
    show_search_result(items)

def show_search_result(items):
    raiplay = RaiPlay()
    
    for item in items:
        liStyle = xbmcgui.ListItem(item["name"], thumbnailImage=raiplay.getThumbnailUrl(item["images"]["landscape"]))
        liStyle.setProperty('IsPlayable', 'true')
        addLinkItem({"mode": "play", "url": item["Url"]}, liStyle)

    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def log_country():
    raiplay = RaiPlay()
    country = raiplay.getCountry()
    xbmc.log("RAI geolocation: %s" % country)

# parameter values
params = parameters_string_to_dict(sys.argv[2])
# TODO: support content_type parameter, provided by XBMC Frodo.
content_type = str(params.get("content_type", ""))
mode = str(params.get("mode", ""))
behaviour = str(params.get("behaviour", ""))
url = str(params.get("url", ""))
date = str(params.get("date", ""))
channelId = str(params.get("channel_id", ""))
index = str(params.get("index", ""))
pathId = str(params.get("path_id", ""))
subType = str(params.get("sub_type", ""))
tags = str(params.get("tags", ""))

if mode == "live_tv":
    show_tv_channels()

elif mode == "live_radio":
    show_radio_stations()

elif mode == "replay":
    if date == "":
        show_replay_dates()
    elif channelId == "":
        show_replay_channels(date)
    else:
        show_replay_epg(channelId, date)
        
elif mode == "nop":
    dialog = xbmcgui.Dialog()
    dialog.ok("Replay", "Elemento non disponibile")

elif mode == "ondemand":
    if subType == "":
        show_ondemand_root()
    elif subType in ("RaiPlay Tipologia Page", "RaiPlay Genere Page"):
        show_ondemand_programmes(pathId)
    elif subType == "Raiplay Tipologia Item":
            show_ondemand_list(pathId)
    elif subType == "PLR programma Page":
        show_ondemand_programme(pathId)
    else:
        xbmc.log("Unhandled sub-type: " + subType)
elif mode == "ondemand_list":
        show_ondemand_index(index, pathId)
elif mode == "ondemand_items":
    show_ondemand_items(url)
elif mode == "ondemand_search_by_name":
    search_ondemand_programmes()

elif mode == "tg":
    show_tg_root()
elif mode == "tgr":
    if url != "":
        show_tgr_list(mode, url)        
    else:
        show_tgr_root()        

elif mode == "news":
    show_news_providers()
elif mode == "themes":
    show_themes()

elif mode == "get_last_content_by_tag":
     get_last_content_by_tag(tags)
elif mode == "get_most_visited":
     get_most_visited(tags)

elif mode == "play":
    play(url, pathId)

else:
    log_country()
    show_root_menu()

