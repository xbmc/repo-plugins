# -*- coding: utf-8 -*-
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import json

PY3 = sys.version_info.major >= 3

if PY3:
    import urllib.request as urllib2
    import html.parser as HTMLParser
    import urllib.parse as urlparse
    from urllib.parse import urlencode
    
else:
    import urllib2
    import HTMLParser
    import urlparse
    from urllib import urlencode
    
import datetime

import StorageServer

from resources.lib.tgr import TGR
from resources.lib.search import Search
from resources.lib.raiplay import RaiPlay
from resources.lib.raiplayradio import RaiPlayRadio
from resources.lib.relinker import Relinker
import resources.lib.utils as utils
import re

# plugin constants
__plugin__ = "plugin.video.raitv"
__author__ = "Nightflyer"

Addon = xbmcaddon.Addon(id=__plugin__)

# plugin handle
handle = int(sys.argv[1])

# Cache channels for 1 hour
cache = StorageServer.StorageServer("plugin.video.raitv", 1) # (Your plugin name, Cache time in hours)
tv_stations = cache.cacheFunction(RaiPlay(Addon).getChannels)
radio_stations = cache.cacheFunction(RaiPlayRadio().getChannels)
raisport_keys = cache.cacheFunction(RaiPlay(Addon).fillRaiSportKeys)

# utility functions
def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = dict(urlparse.parse_qsl(parameters[1:]))
    return paramDict
 
def addDirectoryItem(parameters, li):
    url = sys.argv[0] + '?' + urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, 
        listitem=li, isFolder=True)

def addLinkItem(parameters, li, url=""):
    if url == "":
        url = sys.argv[0] + '?' + urlencode(parameters)
    li.setProperty('IsPlayable', 'true')
    return xbmcplugin.addDirectoryItem(handle=handle, url=url, 
        listitem=li, isFolder=False)

# UI builder functions
def show_root_menu():
    ''' Show the plugin root menu '''
    liStyle = xbmcgui.ListItem("Home Page")
    addDirectoryItem({"mode": "home"}, liStyle)
    liStyle = xbmcgui.ListItem(Addon.getLocalizedString(32002))
    addDirectoryItem({"mode": "live_tv"}, liStyle)
    liStyle = xbmcgui.ListItem(Addon.getLocalizedString(32003))
    addDirectoryItem({"mode": "live_radio"}, liStyle)
    liStyle = xbmcgui.ListItem(Addon.getLocalizedString(32004))
    addDirectoryItem({"mode": "replay", "media": "tv"}, liStyle)
    liStyle = xbmcgui.ListItem(Addon.getLocalizedString(32005))
    addDirectoryItem({"mode": "replay", "media": "radio"}, liStyle)
    liStyle = xbmcgui.ListItem(Addon.getLocalizedString(32006))
    addDirectoryItem({"mode": "ondemand"}, liStyle)
    liStyle = xbmcgui.ListItem(Addon.getLocalizedString(32007))
    addDirectoryItem({"mode": "tg"}, liStyle)
    liStyle = xbmcgui.ListItem(Addon.getLocalizedString(32008))
    addDirectoryItem({"mode": "news"}, liStyle)
    liStyle = xbmcgui.ListItem(Addon.getLocalizedString(32010))
    addDirectoryItem({"mode": "raisport_main"}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_tg_root():
    search = Search()
    try:
        for k, v in search.newsArchives.items():
            liStyle = xbmcgui.ListItem(k)
            addDirectoryItem({"mode": "get_last_content_by_tag",
                "tags": search.newsArchives[k]}, liStyle)
    except:
        for k, v in list(search.newsArchives.items()):
            liStyle = xbmcgui.ListItem(k)
            addDirectoryItem({"mode": "get_last_content_by_tag",
                "tags": search.newsArchives[k]}, liStyle)
    liStyle = xbmcgui.ListItem("TGR")
    liStyle.setArt({"thumb": "http://www.tgr.rai.it/dl/tgr/mhp/immagini/splash.png"})
    addDirectoryItem({"mode": "tgr"}, liStyle)  
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_tgr_root():
    #xbmcplugin.setContent(handle=handle, content='tvshows')
    
    tgr = TGR()
    programmes = tgr.getProgrammes()
    for programme in programmes:
        liStyle = xbmcgui.ListItem(programme["title"])
        liStyle.setArt({"thumb": programme["image"]})
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
            liStyle.setInfo("video", {})
            addLinkItem({"mode": "play",
                "url": item["url"]}, liStyle)            
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def play(url, pathId="", srt=[]):
    KODI_VERSION_MAJOR = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])
    xbmc.log("*******************************************************************************************************************") 
    xbmc.log("************************   plugin.video.raitv    Playing.... ******************************************************") 
    
    ct = ""
    key = ""
    if pathId != "":
        xbmc.log("PathID: " + pathId)

        # Ugly hack
        if pathId[:7] == "/audio/":
            raiplayradio = RaiPlayRadio()
            metadata = raiplayradio.getAudioMetadata(pathId)
            url = metadata["contentUrl"]
        else:
            raiplay = RaiPlay(Addon)
            metadata = raiplay.getVideoMetadata(pathId)
            url = metadata["content_url"]
            srt = [raiplay.baseUrl[:-1] + sub['url'] for sub in metadata.get("subtitlesArray", [])]

        if srt:
            srt2 = []
            for s in srt:
                s= urlparse.quote(s, safe=':/')
                srt2.append(s)
            
            srt = srt2
            xbmc.log("Subtitles Url: {}".format(srt))


    if "relinkerServlet" in url:
        url = url.replace ("https:", "http:")
        xbmc.log("Relinker URL: " + url)
        relinker = Relinker()
        params = relinker.getURL(url)
        url = params.get('url','')
        ct = params.get('ct','')
        key = params.get('key','')
        
    # Add the server to the URL if missing
    if url[0] == "/":
        url = raiplay.baseUrl[:-1] + url
    
    xbmc.log("Media URL: " + url)
    xbmc.log("Media format: %s - License Url: %s" % (ct,key))
    
    # Play the item
    try: 
        item=xbmcgui.ListItem(path=url + '|User-Agent=' + urllib.quote_plus(Relinker.UserAgent))
    except: 
        item=xbmcgui.ListItem(path=url + '|User-Agent=' + urllib.parse.quote_plus(Relinker.UserAgent))
    
    if "dash" in ct or "mpd" in ct :
        if KODI_VERSION_MAJOR >= 19:
            item.setProperty('inputstream', 'inputstream.adaptive')
        else:
            item.setProperty('inputstreamaddon', 'inputstream.adaptive')

        item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        item.setMimeType('application/dash+xml')
        if key:
            
            if "anycast.nagra.com" in key:
                posAuth = key.find("?Authorization")     
                key1 = key[:posAuth]
                
                license_headers = {
                    "Accept":"application/octet-stream",
                    "Content-Type":"application/octet-stream",
                    'Nv-Authorizations': key[posAuth + 15:]  ,
                    "Referer":"https://www.raiplay.it/",
                    'Origin': 'https://www.raiplay.it',
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
                }
                
                key_string = key1 + "|" + urlencode(license_headers) + "|R{SSM}|"

            else:
                key_string = key + "||R{SSM}|"
            
            item.setProperty("inputstream.adaptive.license_type", 'com.widevine.alpha')
            item.setProperty("inputstream.adaptive.license_key",  key_string)
            xbmc.log("Key string: %s" % key_string) 

    if srt:
        item.setSubtitles(srt)

    xbmc.log("*******************************************************************************************************************") 
    xbmcplugin.setResolvedUrl(handle=handle, succeeded=True, listitem=item)

def show_tv_channels():
    xbmc.log("Raiplay: get Rai channels: ")

    raiplay = RaiPlay(Addon)
    onAirJson = raiplay.getOnAir()
    
    for station in tv_stations:
        chName = station["channel"]
        current = thumb = ""
        for d in onAirJson:
            if chName == d["channel"]:
                current = d["currentItem"].get("name","")
                thumb = d["currentItem"].get("image","")
                chName = "[COLOR yellow]" + chName + "[/COLOR]: " + current
                break
        
        liStyle = xbmcgui.ListItem(chName)
        if thumb:
            liStyle.setArt({"thumb": raiplay.getUrl(thumb)})
        else:
            liStyle.setArt({"thumb": raiplay.getThumbnailUrl(station["transparent-icon"])})
        liStyle.setInfo("video", {})
        addLinkItem({"mode": "play",
            "url": station["video"]["contentUrl"]}, liStyle)
    #rai sport web streams
    xbmc.log("Raiplay: get Rai sport web channels: ")

    chList = raiplay.getRaiSportLivePage()
    xbmc.log(str(chList))
    for ch in chList:
        liStyle = xbmcgui.ListItem("[COLOR green]" + ch['title'] + "[/COLOR]")
        liStyle.setArt({"thumb": ch['icon']})
        liStyle.setInfo("video", {})
        addLinkItem({"mode": "play", "url": ch["url"]}, liStyle)
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_radio_stations():
    for station in radio_stations:
        ch = station["channel"]
        liStyle = xbmcgui.ListItem(ch["name"])
        liStyle.setArt({"thumb": "http://rai.it" + station["images"]["square"]})
        liStyle.setInfo("music", {})
        if 'contentUrl' in station['audio']:
            addLinkItem({"mode": "play", "url": station["audio"]["contentUrl"]}, liStyle)
        else:
            addLinkItem({"mode": "play", "url": station["audio"]["url"]}, liStyle)
        
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_home(defaultUrl="index.json"):
    raiplay = RaiPlay(Addon)
    response = raiplay.getHomePage(defaultUrl)
    
    for item in response:
        item_type = item.get("type","")
        if item_type == "RaiPlay Hero Block":
            for item2 in item["contents"]:
                sub_type = item2["type"]
                item2_name = item2.get("name", "[No name]")

                liStyle = xbmcgui.ListItem("%s: %s" % (Addon.getLocalizedString(32013), item2_name))
                liStyle.setArt({"thumb": raiplay.getThumbnailUrl2(item2)})

                if sub_type == "RaiPlay Diretta Item":
                    liStyle.setInfo("video", {})
                    addLinkItem({"mode": "play", "url": item2["path_id"]}, liStyle)
                elif sub_type == "RaiPlay V2 Lancio Item":
                    if item2["sub_type"] == "RaiPlay Video Item":
                        liStyle.setInfo("video", {})
                        addLinkItem({"mode": "play", "path_id": item2["path_id"]}, liStyle)
                    else:
                        xbmc.log("Not handled sub-type in Hero Block: '%s'" % item2["sub_type"])
                elif sub_type == "RaiPlay Programma Item" :
                    addDirectoryItem({"mode": "ondemand", "path_id": item2["path_id"], "sub_type": sub_type }, liStyle)
                else:                    
                    xbmc.log("Not handled type in Hero Block: '%s'" % sub_type)
                    addDirectoryItem({"mode": "ondemand", "path_id": item2["path_id"], "sub_type": sub_type }, liStyle)

        elif item_type == "RaiPlay Configuratore Fascia Recommendation Item":
            title = item['name']
            if title.find('RCM') > 0:
                title = title[0:title.find('RCM')]
            if title.find('HP') > 0:
                title = title[0:title.find('HP')]
            if title.strip():
                liStyle = xbmcgui.ListItem(title)
                if "fallback_list" in item:
                    if item["fallback_list"]:
                        addDirectoryItem({"mode": "ondemand_collection", "path_id": item["fallback_list"]}, liStyle)
        elif "Slider" in item_type: 
            # populate subItems array
            subItems=[]
            for item2 in item["contents"]:
                item2_name = item2.get("name", "[No name]")
                subItems.append({"mode": "ondemand", "name": item2_name, "path_id": item2["path_id"], "video_url": item2.get("video_url",""), "sub_type": item2["type"], "icon": raiplay.getThumbnailUrl2(item2)})
                
            liStyle = xbmcgui.ListItem(item['name'])
            addDirectoryItem({"mode": "ondemand_slider", "sub_items": json.dumps(subItems)}, liStyle)
        
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_collection(pathId):
    xbmc.log("Raiplay.show_collection with PathID: %s" % pathId )
    raiplay = RaiPlay(Addon)
    xbmc.log("Url: " + raiplay.getUrl(pathId))
   
    response = raiplay.getCategory(pathId)

    for item in response:
        liStyle = xbmcgui.ListItem(item["name"])
        liStyle.setArt({"thumb": raiplay.getThumbnailUrl2(item)})
        addDirectoryItem({"mode": "ondemand", "path_id": item["path_id"], "sub_type": item["type"]}, liStyle)
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_slider_items(subItems):
    xbmc.log("Raiplay.show_slider_items")
    raiplay = RaiPlay(Addon)

    subItems= json.loads(subItems)
    for item in subItems:
        liStyle = xbmcgui.ListItem(item.get("name",""))
        liStyle.setArt({"thumb": item["icon"]})
        if item.get("sub_type","") == "RaiPlay Video Item":
            xbmc.log("Link: " + item.get("name","") + " " + item["video_url"])
            liStyle.setInfo("video", {})
            addLinkItem({"mode": "play", "url": item["video_url"]}, liStyle)
        else:
            pathId = item["path_id"]
            xbmc.log("Directory: " + item.get("name","") + " " + pathId)
            if "tipologia/" in pathId:
                addDirectoryItem({"mode": "ondemand_subhome", "path_id": pathId}, liStyle)
            else:
                addDirectoryItem({"mode": "ondemand", "path_id": item["path_id"], "sub_type": item["sub_type"]}, liStyle)
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
        
    
def show_replay_dates(media):
    days = []
    months = []
    days.append(xbmc.getLocalizedString(17))
    for idxDay in range(11, 17):
        days.append(xbmc.getLocalizedString(idxDay))
        
    for idxMonth in range(21, 33):
        xbmc.log(xbmc.getLocalizedString(idxMonth))
        months.append(xbmc.getLocalizedString(idxMonth))
    
    epgEndDate = datetime.date.today()
    epgStartDate = datetime.date.today() - datetime.timedelta(days=7)
    for day in utils.daterange(epgStartDate, epgEndDate):
        day_str = days[int(day.strftime("%w"))] + " " + day.strftime("%d") + " " + months[int(day.strftime("%m"))-1]
        liStyle = xbmcgui.ListItem(day_str)
        addDirectoryItem({"mode": "replay",
            "media": media,
            "date": day.strftime("%d-%m-%Y")}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_replay_tv_channels(date):
    raiplay = RaiPlay(Addon)
    for station in tv_stations:
        liStyle = xbmcgui.ListItem(station["channel"])
        liStyle.setArt({"thumb": raiplay.getThumbnailUrl(station["transparent-icon"])})
        addDirectoryItem({"mode": "replay",
            "media": "tv",
            "channel_id": station["channel"],
            "date": date}, liStyle)
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_replay_radio_channels(date):
    for station in radio_stations:
        liStyle = xbmcgui.ListItem(station["channel"])
        liStyle.setArt({"thumb": station["stillFrame"]})
        addDirectoryItem({"mode": "replay",
            "media": "radio",
            "channel_id": station["channel"].encode("utf-8"),
            "date": date}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_replay_tv_epg(date, channelId):
    xbmc.log("Showing EPG for " + channelId + " on " + date)
    raiplay = RaiPlay(Addon)
    programmes = raiplay.getProgrammes(channelId, date)
    if(programmes):
        for programme in programmes:
            if not programme:
                continue

            startTime = programme["timePublished"]
            title = programme["name"].replace("\n"," ")

            if programme["images"]:
                thumb = raiplay.getThumbnailUrl2(programme)
            elif programme["isPartOf"] :
                thumb = raiplay.getThumbnailUrl2(programme["isPartOf"])
            else:
                thumb = raiplay.noThumbUrl

            if programme["hasVideo"]:
                videoUrl = programme["pathID"]
            else:
                videoUrl = None

            if videoUrl is None:
                # programme is not available
                liStyle = xbmcgui.ListItem(startTime + " [I]" + title + "[/I]")
                liStyle.setArt({"thumb": thumb})
                liStyle.setInfo("video", {})
                addLinkItem({"mode": "nop"}, liStyle)
            else:
                liStyle = xbmcgui.ListItem(startTime + " " + title)
                liStyle.setArt({"thumb": thumb})
                liStyle.setInfo("video", {})
                addLinkItem({"mode": "play", "path_id": videoUrl}, liStyle)
    else:
        response = raiplay.getProgrammesHtml(channelId, date)
        programmes = re.findall('(<li.*?</li>)', response)
        for i in programmes:
            icon = re.findall('''data-img=['"]([^'^"]+?)['"]''', i)
            if icon:
                icon = raiplay.getUrl(icon[0])
            else:
                icon =''
            
            title = re.findall("<p class=\"info\">([^<]+?)</p>", i)
            if title:
                title = title[0]
            else:
                title = ''

            startTime = re.findall("<p class=\"time\">([^<]+?)</p>", i)
            if startTime:
                title = startTime[0] + " " + title

            desc = re.findall("<p class=\"descProgram\">([^<]+?)</p>", i, re.S)
            if desc:
                desc= desc[0]
            else:
                desc=""
            
            videoUrl = re.findall('''data-href=['"]([^'^"]+?)['"]''', i)

            if not videoUrl:
                # programme is not available
                liStyle = xbmcgui.ListItem(" [I]" + title + "[/I]")
                liStyle.setArt({"thumb": icon})
                liStyle.setInfo("video", {})
                addLinkItem({"mode": "nop"}, liStyle)
            else:
                videoUrl = videoUrl[0]

                liStyle = xbmcgui.ListItem(title )
                liStyle.setArt({"thumb": icon})
                liStyle.setInfo("video", {})
                addLinkItem({"mode": "play", "path_id": videoUrl}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_replay_radio_epg(date, channelId):
    xbmc.log("Showing EPG for " + channelId + " on " + date)
    raiplayradio = RaiPlayRadio()

    programmes = raiplayradio.getProgrammes(channelId.decode("utf-8"), date)
    
    for programme in programmes:
        if not programme:
            continue
    
        startTime = programme["timePublished"]
        title = programme["name"]
        
        if programme["images"]["landscape"] != "":
            thumb = raiplayradio.getThumbnailUrl(programme["images"]["square"])
        elif programme["isPartOf"] and programme["isPartOf"]["images"]["square"] != "":
            thumb = raiplayradio.getThumbnailUrl(programme["isPartOf"]["images"]["square"])
        else:
            thumb = raiplayradio.noThumbUrl
        
        if programme["hasAudio"]:
            audioUrl = programme["pathID"]
        else:
            audioUrl = None
        
        if audioUrl is None:
            # programme is not available
            liStyle = xbmcgui.ListItem(startTime + " [I]" + title + "[/I]")
            liStyle.setArt({"thumb": thumb})
            liStyle.setInfo("music", {})
            addLinkItem({"mode": "nop"}, liStyle)
        else:
            liStyle = xbmcgui.ListItem(startTime + " " + title)
            liStyle.setArt({"thumb": thumb})
            liStyle.setInfo("music", {})
            addLinkItem({"mode": "play", "path_id": audioUrl}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_ondemand_root():
    xbmc.log("Raiplay.show_ondemand_root")
    raiplay = RaiPlay(Addon)
    items = raiplay.getMainMenu()
    for item in items:
        if item["sub-type"] in ("RaiPlay Tipologia Page", "RaiPlay Genere Page", "RaiPlay Tipologia Editoriale Page" ):
 
            if not (item["name"] in ("Teatro", "Musica")):
                
                # new urls 
                # i.e. change "/raiplay/programmi/?json" to "/raiplay/tipologia/programmi/index.json"
                m = re.findall("raiplay/(.*?)/[?]json", item["PathID"])
                if m:
                    
                    if m[0]=="fiction":
                        liStyle = xbmcgui.ListItem("Serie italiane")
                        liStyle.setArt({"thumb": raiplay.getThumbnailUrl("http://www.rai.it/dl/img/2018/06/04/1528107006058_ico-fiction.png")})
                        addDirectoryItem({"mode": "ondemand", "path_id": "/raiplay/tipologia/serieitaliane/index.json", "sub_type": item["sub-type"]}, liStyle)
                        liStyle = xbmcgui.ListItem("Original")
                        liStyle.setArt({"thumb": raiplay.getThumbnailUrl("http://www.rai.it/dl/img/2018/06/04/1528107006058_ico-fiction.png")})
                        addDirectoryItem({"mode": "ondemand_subhome", "path_id": "/raiplay/tipologia/original/index.json", "sub_type": item["sub-type"]}, liStyle)
                    elif m[0]=="serietv":
                        liStyle = xbmcgui.ListItem("Serie internazionali")
                        liStyle.setArt({"thumb": raiplay.getThumbnailUrl("http://www.rai.it/dl/img/2018/06/04/1528107006058_ico-fiction.png")})
                        addDirectoryItem({"mode": "ondemand_subhome", "path_id": "/raiplay/tipologia/serieinternazionali/index.json", "sub_type": item["sub-type"]}, liStyle)
                    elif m[0]=="bambini" or m[0]=="bambini/":
                        liStyle = xbmcgui.ListItem("Bambini")
                        if "image" in item:
                            liStyle.setArt({"thumb": raiplay.getThumbnailUrl(item["image"])})
                        addDirectoryItem({"mode": "ondemand_subhome", "path_id": "/raiplay/tipologia/bambini/index.json", "sub_type": item["sub-type"]}, liStyle)

                        liStyle = xbmcgui.ListItem("Teen")
                        if "image" in item:
                            liStyle.setArt({"thumb": raiplay.getThumbnailUrl(item["image"])})
                        addDirectoryItem({"mode": "ondemand_subhome", "path_id": "/raiplay/tipologia/teen/index.json", "sub_type": item["sub-type"]}, liStyle)

                    else:
                        liStyle = xbmcgui.ListItem(item["name"])
                        if "image" in item:
                            liStyle.setArt({"thumb": raiplay.getThumbnailUrl(item["image"])})
                        item["PathID"] = "/raiplay/tipologia/%s/index.json" % m[0]   
                        addDirectoryItem({"mode": "ondemand", "path_id": item["PathID"], "sub_type": item["sub-type"]}, liStyle)
    
    # add new item not in old json
    liStyle = xbmcgui.ListItem(Addon.getLocalizedString(32012))
    liStyle.setArt({"thumb": raiplay.getThumbnailUrl("/dl/img/2018/06/04/1528115285089_ico-teatro.png")})
    addDirectoryItem({"mode": "ondemand", "path_id": "https://www.raiplay.it/performing-arts/index.json", "sub_type": "RaiPlay Tipologia Page"}, liStyle)

    liStyle = xbmcgui.ListItem("Cerca")
    addDirectoryItem({"mode": "ondemand_search_by_name"}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_ondemand_programmes(pathId):
    xbmc.log("Raiplay.show_ondemand_programmes with PathID: %s" % pathId )
    raiplay = RaiPlay(Addon)
    xbmc.log("Url: " + raiplay.getUrl(pathId))
   
    blocchi = raiplay.getCategory(pathId)

    if len(blocchi) > 1:
        xbmc.log("Blocchi: " + str(len(blocchi)))
        
    for b in blocchi:
        if b["type"] == "RaiPlay Slider Generi Block":
            for item in b["contents"]:
                liStyle = xbmcgui.ListItem(item["name"])
                liStyle.setArt({"thumb": raiplay.getThumbnailUrl(item["image"])})
                liStyle.setArt({"fanart": raiplay.getThumbnailUrl(item["image"])})
                addDirectoryItem({"mode": "ondemand", "path_id": item["path_id"], "sub_type": item["sub_type"]}, liStyle)
    
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_list(pathId):
    xbmc.log("Raiplay.show_ondemand_list with PathID: %s" % pathId )
    # indice ottenuto dal json
    raiplay = RaiPlay(Addon)
    xbmc.log("Url: %s" % raiplay.getUrl(pathId) )

    index = raiplay.getIndexFromJSON(pathId)
    xbmc.log(str(index))

    for i in index:
        liStyle = xbmcgui.ListItem(i)
        addDirectoryItem({"mode": "ondemand_list", "index": i, "path_id": pathId}, liStyle)
    
    addDirectoryItem({"mode": "ondemand_list_all", "index": len(index)+1, "path_id": pathId}, xbmcgui.ListItem(Addon.getLocalizedString(32011)))
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_index(index, pathId):
    xbmc.log("Raiplay.show_ondemand_index with index %s and PathID: %s" % (index, pathId) )

    raiplay = RaiPlay(Addon)
    dir = raiplay.getProgrammeList(pathId)
    for item in dir[index]:
        liStyle = xbmcgui.ListItem(item["name"])
        liStyle.setArt({"thumb": raiplay.getThumbnailUrl2(item)})
        addDirectoryItem({"mode": "ondemand", "path_id": item["path_id"], "sub_type": item["type"]}, liStyle)
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_index_all(index, pathId):
    xbmc.log("Raiplay.show_ondemand_index_all with index from 0 to %sS and PathID: %s" % (index, pathId) )
    raiplay = RaiPlay(Addon)
    dir = raiplay.getProgrammeList(pathId)
    dictKeys = dir.keys();
    for currKey in dictKeys:
        for item in dir[currKey]:
            liStyle = xbmcgui.ListItem(item["name"])
            liStyle.setArt({"thumb": raiplay.getThumbnailUrl2(item)})
            addDirectoryItem({"mode": "ondemand", "path_id": item["path_id"], "sub_type": item["type"]}, liStyle)
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_ondemand_programme(pathId):
    xbmc.log("Raiplay.show_ondemand_programme with PathID: %s" % pathId)
    raiplay = RaiPlay(Addon)
    xbmc.log("Url: %s" % raiplay.getUrl(pathId))
    
    programme = raiplay.getProgramme(pathId)
    
    if (len(programme["program_info"]["typologies"]) > 0) and programme["program_info"]["typologies"][0]["nome"] == "Film":
        # it's a movie
        if "first_item_path" in programme: 
            liStyle = xbmcgui.ListItem(programme["program_info"]["name"])
            liStyle.setArt({"thumb": raiplay.getThumbnailUrl2(programme["program_info"])})
            liStyle.setInfo("video", {
                "Plot": programme["program_info"]["description"],
                "Cast": programme["program_info"]["actors"].split(", "),
                "Director": programme["program_info"]["direction"].split(", "),
                "Country": programme["program_info"]["country"].split(", "),
                "Year": programme["program_info"]["year"],
                })
            addLinkItem({"mode": "play", "path_id": programme["first_item_path"]}, liStyle)
    else:
        # other shows
        blocks = programme["blocks"]
        for block in blocks:
            for set in block["sets"]:
                label = '%s (%s)' % (set["name"], block["name"]) if set["name"] != block["name"] else set["name"]
                try:
                    season = re.search('Stagione (\\d+)', set["name"]).group(1)
                except:
                    season = 1
                liStyle = xbmcgui.ListItem(label)
                liStyle.setInfo("video", {
                    "showtitle": programme["program_info"]["name"],
                    "Year": programme["program_info"]["year"],
                    "season": season,
                    })
                addDirectoryItem({"mode": "ondemand_items", "url": set["path_id"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_ondemand_items(url):
    xbmc.log("Raiplay.show_ondemand_item with ContentSet Url: %s" % url )

    raiplay = RaiPlay(Addon)
    items = raiplay.getContentSet(url)
    for item in items:
        title = item["name"]
        if "subtitle" in item and item["subtitle"] != "" and item["subtitle"] != item["name"]:
            title = title + " (" + item["subtitle"] + ")"
        liStyle = xbmcgui.ListItem(title)
        liStyle.setArt({"thumb": raiplay.getThumbnailUrl2(item)})
        liStyle.setInfo("video", {
            "tvshowtitle": item["program_name"],
            "title": item["episode_title"],
            "season": item["season"],
            "episode": item["episode"],
            "Plot": item["description"],
            })
        addLinkItem({"mode": "play", "path_id": item["path_id"]}, liStyle)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def search_ondemand_programmes():
    kb = xbmc.Keyboard()    
    kb.setHeading(Addon.getLocalizedString(32001))
    kb.doModal()
    if kb.isConfirmed():
        try: name = kb.getText().decode('utf8').lower()
        except: name = kb.getText().lower()
        xbmc.log("Searching for programme: " + name)
        raiplay = RaiPlay(Addon)
        # old style of json
        dir = raiplay.getProgrammeListOld(raiplay.AzTvShowPath)
        for letter in dir:
            for item in dir[letter]:
                if item["name"].lower().find(name) != -1:
                    #fix old version of url
                    if "PathID" in item:
                        url = item["PathID"]
                        if url.endswith('/?json'):
                            url = url.replace('/?json', '.json')
                        
                        liStyle = xbmcgui.ListItem(item["name"])
                        liStyle.setArt({"thumb": raiplay.getThumbnailUrl2(item)})
                        addDirectoryItem({"mode": "ondemand", "path_id": url , "sub_type": "PLR programma Page"}, liStyle)
        xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def show_news_providers():
    search = Search()
    try:
        for k, v in search.newsProviders.iteritems():
            liStyle = xbmcgui.ListItem(k)
            addDirectoryItem({"mode": "get_last_content_by_tag",
                "tags": search.newsProviders[k]}, liStyle)
    except:
        for k, v in search.newsProviders.items():
            liStyle = xbmcgui.ListItem(k)
            addDirectoryItem({"mode": "get_last_content_by_tag",
                "tags": search.newsProviders[k]}, liStyle)
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def get_last_content_by_tag(tags):
    xbmc.log("Get latest content for tags: " + tags)
    search = Search()
    items = search.getLastContentByTag(tags,numContents=50)
    show_search_result(items)

def show_search_result(items):
    raiplay = RaiPlay(Addon)
    
    for item in items:
        if 'url' in item:
            url = item["Url"]
        elif 'h264' in item:
            url = item["h264"]
        elif 'url_h264' in item:        
            url = item["url_h264"]
        elif 'weblink' in item:
            url = item["weblink"]
        else:
            url = ""

        liStyle = xbmcgui.ListItem(item["name"])
        liStyle.setInfo("video", {})

        if 'largePathImmagine' in item:
            liStyle.setArt({"thumb": raiplay.getThumbnailUrl(item["largePathImmagine"])})
        elif 'image' in item:
            liStyle.setArt({"thumb": raiplay.getThumbnailUrl(item["image"])})
                    
        # Using "Url" because "PathID" is broken upstream :-/
        addLinkItem({"mode": "play", "url": url}, liStyle)

    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
    
def get_raisport_main():
    xbmc.log("Build Rai Sport menu with search keys....")
    raiplay = RaiPlay(Addon)
    
    for k in raisport_keys:
        title = k.get("title","")
        
        if title:
            liStyle = xbmcgui.ListItem(title)
            addDirectoryItem({"mode": "raisport_item", "dominio": k["dominio"], "key": k["key"], "sub_keys": k.get("sub_keys",[])}, liStyle)

    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def get_raisport_items(params):
    dominio = params.get('dominio','')
    key = params.get('key','')
    
    sub_keys = eval(params.get("sub_keys","[]"))
    xbmc.log("Build Rai Sport menu of item %s " % sub_keys[0])

    liStyle = xbmcgui.ListItem("Tutti i video")
    addDirectoryItem({"mode": "raisport_subitem", "dominio" : dominio , "key": key}, liStyle)

    for i in range(0, len(sub_keys)):
        key = sub_keys[i]
        title = key.get("title","")
        title = utils.checkStr(HTMLParser.HTMLParser().unescape(title))
        
        liStyle = xbmcgui.ListItem(title)
        addDirectoryItem({"mode": "raisport_subitem", "dominio" : key["dominio"] , "key": key["key"]}, liStyle)

    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)
            
def get_raisport_videos(params):
    xbmc.log("Build Rai Sport video list for %s " % params)
    raiplay = RaiPlay(Addon)

    key = params.get('key','')
    dominio = params.get('dominio','')
    page = params.get('page',0)
    
    response = raiplay.getRaiSportVideos(key, dominio, page)
    for r in response:
        #xbmc.log("Item %s" % r['title'])
        if r['mode'] == "raisport_video":
            liStyle = xbmcgui.ListItem(r['title'])
            liStyle.setArt({'thumb': r['icon']})
            liStyle.setInfo("video", {'duration' : r['duration'], 'aired': r['aired'], 'plot' : r['desc']})
            addLinkItem({"mode": "play", "url": r["url"]}, liStyle)
        elif r['mode'] == "raisport_subitem":
            liStyle = xbmcgui.ListItem(r['title'])
            addDirectoryItem({"mode": "raisport_subitem", 'dominio': dominio, 'key': key, 'page': r['page']}, liStyle)

    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def log_country():
    raiplay = RaiPlay(Addon)
    country = raiplay.getCountry()
    xbmc.log("RAI geolocation: %s" % country)

# parameter values
params = parameters_string_to_dict(sys.argv[2])
# TODO: support content_type parameter, provided by XBMC Frodo.
content_type = str(params.get("content_type", ""))
mode = str(params.get("mode", ""))
media = str(params.get("media", ""))
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

elif mode == "home":
    show_home("index.json")
    
elif mode == "replay":
    if date == "":
        show_replay_dates(media)
    elif channelId == "":
        if media == "tv":
            show_replay_tv_channels(date)
        else:
            show_replay_radio_channels(date)
    else:
        if media == "tv":
            show_replay_tv_epg(date, channelId)
        else:
            show_replay_radio_epg(date, channelId)
        
elif mode == "nop":
    dialog = xbmcgui.Dialog()
    dialog.ok("Replay", "Elemento non disponibile")

elif mode == "ondemand":
    if subType == "":
        show_ondemand_root()
    elif subType in ("RaiPlay Tipologia Page", "RaiPlay Genere Page", "RaiPlay Tipologia Editoriale Page"):
        show_ondemand_programmes(pathId)
    elif subType in ("Raiplay Tipologia Item", "RaiPlay V2 Genere Page"):
            show_ondemand_list(pathId)
    elif subType in ("PLR programma Page", "RaiPlay Programma Item"):
        show_ondemand_programme(pathId)
    else:
        xbmc.log("Unhandled sub-type: " + subType)
elif mode == "ondemand_list":
        show_ondemand_index(index, pathId)
elif mode == "ondemand_list_all":
        show_ondemand_index_all(index, pathId)
elif mode == "ondemand_items":
    show_ondemand_items(url)
elif mode == "ondemand_search_by_name":
    search_ondemand_programmes()
elif mode == "ondemand_collection":
    show_collection(pathId)
elif mode == "ondemand_slider":
    subItems = params.get("sub_items", [])
    show_slider_items(subItems)
elif mode == "ondemand_subhome":
    show_home(pathId)

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

elif mode == "play" or mode =="raiplay_videos":
    play(url, pathId)
elif mode == "raisport_main":
    get_raisport_main()
elif mode == "raisport_item":
    get_raisport_items(params)
elif mode == "raisport_subitem":
    get_raisport_videos(params)
else:
    log_country()
    show_root_menu()

