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
from resources.lib.onair import onAir
from resources.lib.replay import Replay
from resources.lib.ondemand import OnDemand
from resources.lib.relinker import Relinker
from resources.lib.podcast import Podcast
import resources.lib.stations as stations
import resources.lib.utils as utils

# plugin constants
__plugin__ = "plugin.video.raitv"
__author__ = "Nightflyer"

Addon = xbmcaddon.Addon(id=__plugin__)

# plugin handle
handle = int(sys.argv[1])

# Cache channels for 1 hour
cache = StorageServer.StorageServer("plugin.video.raitv", 0) # (Your plugin name, Cache time in hours)
tv_stations = cache.cacheFunction(stations.get_tv_stations)
radio_stations = cache.cacheFunction(stations.get_radio_station)

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
    liStyle = xbmcgui.ListItem("Rai Replay")
    addDirectoryItem({"mode": "replay"}, liStyle)
    liStyle = xbmcgui.ListItem("Programmi On Demand")
    addDirectoryItem({"mode": "ondemand"}, liStyle)
    liStyle = xbmcgui.ListItem("Archivio Telegiornali")
    addDirectoryItem({"mode": "tg"}, liStyle)
    liStyle = xbmcgui.ListItem("Videonotizie")
    addDirectoryItem({"mode": "news"}, liStyle)
    liStyle = xbmcgui.ListItem("Aree tematiche")
    addDirectoryItem({"mode": "themes"}, liStyle)
    liStyle = xbmcgui.ListItem("Cerca...")
    addDirectoryItem({"mode": "search"}, liStyle)
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
            addLinkItem({"mode": "play",
                "title": item["title"],        
                "url": item["url"]}, liStyle)            
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def play(title, url, thumbailUrl="", uniquename="", mediatype="RaiTv Media Video Item"):
    # Retrieve the file URL if missing
    if uniquename != "":
        ondemand = OnDemand()
        (url, mediatype) = ondemand.getMediaUrl(uniquename)

    # Handle RAI relinker
    if url[:53] == "http://mediapolis.rai.it/relinker/relinkerServlet.htm" or \
        url[:56] == "http://mediapolisvod.rai.it/relinker/relinkerServlet.htm":
        relinker = Relinker()
        url = relinker.getURL(url)
        
    # Add the server to the URL if missing
    if url !="" and url.find("://") == -1:
        url = ondemand.baseUrl + url
    print "Playing URL: %s" % url

    # It seems that all .ram files I found are not working
    # because upstream file is no longer present
    if url[-4:].lower() == ".ram":
        dialog = xbmcgui.Dialog()
        dialog.ok("Errore", "I file RealAudio (.ram) non sono supportati.")
        return
    
    # Play the item
    item=xbmcgui.ListItem(title, thumbnailImage=thumbailUrl)
    if mediatype == "RaiTv Media Video Item":
        item.setInfo(type="Video", infoLabels={"Title": title})
    elif mediatype == "RaiTv Media Audio Item":
        item.setInfo(type="Audio", infoLabels={"Title": title})
    xbmc.Player().play(url, item)

def show_tv_channels():
    for station in tv_stations:
        if station["diretta"] == "YES":
            liStyle = xbmcgui.ListItem(station["name"], thumbnailImage=station["icon"])
            addLinkItem({"mode": "play",
                "title": station["name"],
                "url": station["direttaLink"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_radio_stations():
    for station in radio_stations:
        liStyle = xbmcgui.ListItem(station["nome"], thumbnailImage=station["logo_menu"])
        addLinkItem({"mode": "play",
            "title": station["nome"],
            "url": station["link_diretta"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_replay_channels():
    for station in tv_stations:
        if station["hasReplay"] == "YES":
            liStyle = xbmcgui.ListItem(station["name"], thumbnailImage=station["icon"])
            addDirectoryItem({"mode": "replay",
                "channel_id": station["id"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_replay_dates(channelId):
    days = ["Domenica", "Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"]
    months = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", 
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    
    epgEndDate = datetime.date.today() - datetime.timedelta(days=1)
    epgStartDate = datetime.date.today() - datetime.timedelta(days=7)
    for day in utils.daterange(epgStartDate, epgEndDate):
        day_str = days[int(day.strftime("%w"))] + " " + day.strftime("%d") + " " + months[int(day.strftime("%m"))-1]
        liStyle = xbmcgui.ListItem(day_str)
        addDirectoryItem({"mode": "replay",
            "channel_id": channelId,
            "date": day.strftime("%Y_%m_%d")}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_replay_epg(channelId, date):
    replay = Replay()
    
    for station in tv_stations:
        if station["id"] == channelId:
            channelTag = station["tag"]
            break
    
    programmes = replay.getProgrammes(channelId, channelTag, date)
    
    # sort timetable
    timetable = utils.sortedDictKeys(programmes)

    for entry in timetable:
        recording = programmes[entry]
        
        title = recording["t"]
        plot = recording["d"]
        thumbnail = recording["image"]
        
        if recording["urlTablet"] != "":
            videoUrl = recording["urlTablet"]
        elif recording["h264"] != "":
            videoUrl = recording["h264"]
        else:
            videoUrl = None
        
        if videoUrl is None:
            # programme is not available
            liStyle = xbmcgui.ListItem(entry + " " + title,
                thumbnailImage=thumbnail)
            liStyle.setInfo(type="Video", infoLabels={"Title" : title,
                "Label": title,
                "Plot": plot})
            addLinkItem({"mode": "nop",
                "title": title.encode('utf8'),
                "thumbnail": thumbnail}, liStyle)
        else:
            liStyle = xbmcgui.ListItem("[COLOR blue]" + entry + " " + title + "[/COLOR]",
                thumbnailImage=thumbnail)
            liStyle.setInfo(type="Video", infoLabels={"Title" : title,
                "Label": title,
                "Plot": plot})
            addLinkItem({"mode": "play",
                "title": title.encode('utf8'),
                "url": videoUrl,
                "thumbnail": thumbnail}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_root():
    liStyle = xbmcgui.ListItem("Elenco programmi")
    addDirectoryItem({"mode": "ondemand_list"}, liStyle)
    liStyle = xbmcgui.ListItem("Cerca un programma")
    addDirectoryItem({"mode": "ondemand_search_by_name"}, liStyle)
    liStyle = xbmcgui.ListItem("Cerca programma per canale o editore")
    addDirectoryItem({"mode": "ondemand_search_by_channel"}, liStyle)
    liStyle = xbmcgui.ListItem("Cerca programmi per tematica")
    addDirectoryItem({"mode": "ondemand_search_by_theme"}, liStyle)
    liStyle = xbmcgui.ListItem("Nuovi programmi")
    addDirectoryItem({"mode": "ondemand_search_new"}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_list():
    liStyle = xbmcgui.ListItem("0-9")
    addDirectoryItem({"mode": "ondemand_list", "index": "0"}, liStyle)
    for i in range(26):
        liStyle = xbmcgui.ListItem(chr(ord('A')+i))
        addDirectoryItem({"mode": "ondemand_list", "index": chr(ord('a')+i)}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_index(index):
    ondemand = OnDemand()
    programmes = ondemand.searchByIndex(index)
    show_ondemand_programmes(programmes)

def search_ondemand_programmes():
    kb = xbmc.Keyboard()
    kb.setHeading("Cerca un programma")
    kb.doModal()
    if kb.isConfirmed():
        name = kb.getText().decode('utf8')
        ondemand = OnDemand()
        programmes = ondemand.searchByName(name)
        show_ondemand_programmes(programmes)

def show_ondemand_channels():
    ondemand = OnDemand()
    for k, v in ondemand.editori.iteritems():
        liStyle = xbmcgui.ListItem(k)
        addDirectoryItem({"mode": "ondemand_search_by_channel", "channel_id": v}, liStyle)
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_channel(channel):
    ondemand = OnDemand()
    programmes = ondemand.searchByChannel(channel)
    show_ondemand_programmes(programmes)

def show_ondemand_themes():
    ondemand = OnDemand()
    for position, tematica in enumerate(ondemand.tematiche):
        liStyle = xbmcgui.ListItem(tematica)
        addDirectoryItem({"mode": "ondemand_search_by_theme", 
            "index": position}, liStyle)
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_theme(index):
    ondemand = OnDemand()
    programmes = ondemand.searchByTheme(ondemand.tematiche[int(index)])
    show_ondemand_programmes(programmes)

def show_ondemand_new():
    ondemand = OnDemand()
    programmes = ondemand.searchNewProgrammes()
    for programme in programmes:
        liStyle = xbmcgui.ListItem(programme["title"])
        addDirectoryItem({"mode": "ondemand",
            "url": programme["linkDemand"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_programmes(programmes):
    for programme in programmes:
        liStyle = xbmcgui.ListItem(programme["title"])
        addDirectoryItem({"mode": "ondemand",
            "url": programme["linkDemand"]}, liStyle)
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_programme(url):
    pageId = url[-46:-5]

    liStyle = xbmcgui.ListItem("Più recenti")
    addDirectoryItem({"mode": "get_last_content_by_tag",
        "tags": "PageOB:"+pageId}, liStyle)

    liStyle = xbmcgui.ListItem("Più visti")
    addDirectoryItem({"mode": "get_most_visited",
        "tags": "PageOB:"+pageId}, liStyle)

    ondemand = OnDemand()
    psets = ondemand.getProgrammeSets(url)
    for pset in psets:
        liStyle = xbmcgui.ListItem(pset["name"])
        addDirectoryItem({"mode": "ondemand",
            "uniquename": pset["uniquename"],
            "mediatype": pset["mediatype"]
            }, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_items(uniquename, mediatype):
    ondemand = OnDemand()
    items = ondemand.getItems(uniquename, mediatype)
    for item in items:
        # Change date format
        item["date"] = item["date"].replace("/",".")
        item["date"] = item["date"].replace("-",".")
        
        # Get best thumbnail available
        if "image_medium" in item and item["image_medium"] != "":
            thumb = item["image_medium"]
        elif "image" in item and item["image"] != "":
            thumb = item["image"]
        else:
            thumb = ondemand.nothumb
        
        # Add the server to the URL if missing
        if thumb[:7] != "http://":
            thumb = ondemand.baseUrl + thumb

        if mediatype == "V":
            # Get best video available
            if "h264" in item and item["h264"] != "":
                url = item["h264"]
            elif "wmv" in item and item["wmv"] != "":
                url = item["wmv"]
            else:
                url = item["mediaUri"]
            
            labels = {"title": item["name"],
                "plot": item["desc"],
                "date": item["date"]}
            
            # Get length, if present
            if item["length"] != "":
                labels["duration"] = int(item["length"][:2]) * 60 + int(item["length"][3:5])

            liStyle = xbmcgui.ListItem(item["name"], thumbnailImage=thumb)
            liStyle.setInfo(type="Video", infoLabels=labels)
            if url != "":
                addLinkItem({"mode": "play",
                    "title": item["name"].encode('utf8'),
                    "url": url,
                    "thumbnail": thumb}, liStyle)
            else:
                addLinkItem({"mode": "play",
                    "title": item["name"].encode('utf8'),
                    "uniquename": item["itemId"],
                    "thumbnail": thumb}, liStyle)
        
        elif mediatype == "A":
            liStyle = xbmcgui.ListItem(item["name"], thumbnailImage=thumb)
            liStyle.setInfo(type="Audio", 
                infoLabels={"title": item["name"], "date": item["date"]})
            addLinkItem({"mode": "play",
                "title": item["name"].encode('utf8'),
                "uniquename": item["itemId"],
                "thumbnail": thumb,
                "mediatype": "RaiTv Media Audio Item"}, liStyle)
        
        elif mediatype == "P":
            (url, mediatype) = ondemand.getMediaUrl(item["itemId"])
            podcast = Podcast()
            poditems = podcast.getItems(url)
            
            for poditem in poditems:
                if poditem["thumbnail"] == "":
                    poditem["thumbnail"] = thumb
                
                labels = {"title": item["name"],
                    "plot": item["desc"],
                    "date": item["date"]}
                
                # Get length, if present
                if poditem["length"] != "":
                    labels["duration"]  = int(poditem["length"][:2]) * 60 + int(poditem["length"][3:5])
                
                liStyle = xbmcgui.ListItem(poditem["title"], thumbnailImage=poditem["thumbnail"])
                liStyle.setInfo(type="Audio", infoLabels=labels)
                addLinkItem({"mode": "play",
                    "title": poditem["title"].encode('utf8'),
                    "url": poditem["url"],
                    "thumbnail":  poditem["thumbnail"],
                    "mediatype": "RaiTv Media Audio Item"}, liStyle)
        
    #xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_DATE)
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
    search = Search()
    items = search.getLastContentByTag(tags)
    show_search_result(items)

def get_most_visited(tags):
    search = Search()
    items = search.getMostVisited(tags)
    show_search_result(items)

def search():
    kb = xbmc.Keyboard()
    kb.setHeading("Cerca un programma")
    kb.doModal()
    if kb.isConfirmed():
        text = kb.getText().decode('utf8')
        search = Search()
        items = search.searchText(text.encode('utf8'))
        show_search_result(items)

def show_search_result(items):
    for item in items:
        # We don't handle photos
        if "type" in item and item["type"] == "Foto":
            continue
    
        if item["image"] != "":
            # Add baseurl if needed
            if item["image"][:4] != "http":
                item["image"] = Search._baseurl + item["image"]
            # Always use bigger thumbnail available
            if item["image"].find("/dl/img/") != -1 or item["image"].find("/dl/video/") != -1:
                item["image"] = item["image"].replace("/105x79","/")
        else:
            item["image"] = Search._nothumb
        
        item["date"] = item["date"].replace("/",".")
        
        liStyle = xbmcgui.ListItem(item["name"], thumbnailImage=item["image"])
        liStyle.setInfo(type="Video", 
            infoLabels={"title": item["name"],
                "date": item["date"],
                "plot": item["desc"],
                "tvshowtitle": item["from"]})
        
        # Check if Video URL is present
        if item["h264"] != "":
            addLinkItem({"mode": "play",
                "title": item["name"].encode('utf8'),
                "url":  item["h264"],
                "thumbnail": item["image"]}, liStyle)
        else:
            addLinkItem({"mode": "play",
                "title": item["name"].encode('utf8'),
                "uniquename": item["itemId"],
                "thumbnail": item["image"]}, liStyle)
    
    #xbmc.executebuiltin("Container.SetViewMode(502)")
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

# parameter values
params = parameters_string_to_dict(sys.argv[2])
# TODO: support content_type parameter, provided by XBMC Frodo.
content_type = str(params.get("content_type", ""))
mode = str(params.get("mode", ""))
behaviour = str(params.get("behaviour", ""))
url = str(params.get("url", ""))
title = str(params.get("title", ""))
thumbnail = str(params.get("thumbnail", ""))
date = str(params.get("date", ""))
channelId = str(params.get("channel_id", ""))
index = str(params.get("index", ""))
uniquename = str(params.get("uniquename", ""))
mediatype = str(params.get("mediatype", ""))
tags = str(params.get("tags", ""))

if mode == "live_tv":
    show_tv_channels()

elif mode == "live_radio":
    show_radio_stations()

elif mode == "replay":
    if channelId == "":
        show_replay_channels()
    elif date == "":
        show_replay_dates(channelId)
    else:
        show_replay_epg(channelId, date)
        
elif mode == "nop":
    dialog = xbmcgui.Dialog()
    dialog.ok("Rai Replay", "Elemento non disponibile")

elif mode == "ondemand":
    if url != "":
        show_ondemand_programme(url)
    elif uniquename != "":
        show_ondemand_items(uniquename, mediatype)
    else:
        show_ondemand_root()
elif mode == "ondemand_list":
    if index != "":
        show_ondemand_index(index)
    else:
        show_ondemand_list()
elif mode == "ondemand_search_by_name":
    search_ondemand_programmes()
elif mode == "ondemand_search_by_channel":
    if channelId != "":
        show_ondemand_channel(channelId)
    else:
        show_ondemand_channels()
elif mode == "ondemand_search_by_theme":
    if index != "":
        show_ondemand_theme(index)
    else:
        show_ondemand_themes()
elif mode == "ondemand_search_new":
    show_ondemand_new()

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

elif mode == "search":
    search()

elif mode == "play":
    play(title, url, thumbnail, uniquename)

else:
    show_root_menu()

