
import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmc
import json
import urllib
import hashlib

from downloadutils import DownloadUtils
from utils import getArt
from datamanager import DataManager
from simple_logging import SimpleLogging
from kodi_utils import HomeWindow

log = SimpleLogging(__name__)
downloadUtils = DownloadUtils()
dataManager = DataManager()
kodi_version = int(xbmc.getInfoLabel('System.BuildVersion')[:2])

def checkForNewContent():
    log.debug("checkForNewContent Called")

    added_url = ('{server}/emby/Users/{userid}/Items' +
                    '?Recursive=true' +
                    '&limit=1' +
                    '&Fields=DateCreated,Etag' +
                    '&SortBy=DateCreated' +
                    '&SortOrder=Descending' +
                    '&IncludeItemTypes=Movie,Episode' +
                    '&ImageTypeLimit=0' +
                    '&format=json')

    added_result = downloadUtils.downloadUrl(added_url, suppress=True)
    result = json.loads(added_result)
    log.debug("LATEST_ADDED_ITEM:" + str(result))

    last_added_date = ""
    if result is not None:
        items = result.get("Items", [])
        if len(items) > 0:
            item = items[0]
            last_added_date = item.get("Etag", "")
    log.debug("last_added_date: " + last_added_date)

    played_url = ('{server}/emby/Users/{userid}/Items' +
                    '?Recursive=true' +
                    '&limit=1' +
                    '&Fields=DateCreated,Etag' +
                    '&SortBy=DatePlayed' +
                    '&SortOrder=Descending' +
                    '&IncludeItemTypes=Movie,Episode' +
                    '&ImageTypeLimit=0' +
                    '&format=json')

    played_result = downloadUtils.downloadUrl(played_url, suppress=True)
    result = json.loads(played_result)
    log.debug("LATEST_PLAYED_ITEM:" + str(result))

    last_played_date = ""
    if result is not None:
        items = result.get("Items", [])
        if len(items) > 0:
            item = items[0]
            last_played_date = item.get("Etag", "")
    log.debug("last_played_date: " + last_played_date)

    home_window = HomeWindow()
    current_widget_hash = home_window.getProperty("embycon_widget_reload")
    log.debug("Current Widget Hash: " + str(current_widget_hash))

    m = hashlib.md5()
    m.update(last_played_date + last_added_date)
    new_widget_hash = m.hexdigest()
    log.debug("New Widget Hash: " + str(new_widget_hash))

    if current_widget_hash != new_widget_hash:
        home_window.setProperty("embycon_widget_reload", new_widget_hash)
        log.debug("Setting New Widget Hash: " + str(new_widget_hash))


def getWidgetUrlContent(handle, params):
    log.debug("getWidgetUrlContent Called" + str(params))

    request = params["url"]
    request = urllib.unquote(request)
    request = "{server}/emby/" + request + "&ImageTypeLimit=1&format=json"
    log.debug("getWidgetUrlContent URL:" + request)

    select_action = params.get("action", None)

    listItems = populateWidgetItems(request, override_select_action=select_action)

    xbmcplugin.addDirectoryItems(handle, listItems)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)


def getSuggestions(handle, params):
    log.debug("getSuggestions Called" + str(params))

    itemsUrl = ("{server}/emby/Movies/Recommendations" +
                "?userId={userid}" +
                "&categoryLimit=1" +
                "&ItemLimit=8" +
                "&format=json" +
                "&ImageTypeLimit=1" +
                "&IsMissing=False")

    listItems = populateWidgetItems(itemsUrl)

    xbmcplugin.addDirectoryItems(handle, listItems)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)

def getWidgetContentNextUp(handle, params):
    log.debug("getWidgetContentNextUp Called" + str(params))

    itemsUrl = ("{server}/emby/Shows/NextUp?SeriesId=" + params["id"] +
                "&userId={userid}" +
                "&Limit={ItemLimit}" +
                "&format=json" +
                "&ImageTypeLimit=1" +
                "&IsMissing=False")

    listItems = populateWidgetItems(itemsUrl)

    xbmcplugin.addDirectoryItems(handle, listItems)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)


def getWidgetContentSimilar(handle, params):
    log.debug("getWisgetContentSimilarMovies Called" + str(params))

    itemsUrl = ("{server}/emby/Items/" + params["id"] + "/Similar"
                "?userId={userid}" +
                "&Limit={ItemLimit}" +
                "&format=json" +
                "&ImageTypeLimit=1" +
                "&IsMissing=False" +
                "&fields=PrimaryImageAspectRatio,UserData,CanDelete")

    listItems = populateWidgetItems(itemsUrl)

    xbmcplugin.addDirectoryItems(handle, listItems)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)


def getWidgetContentCast(handle, params):
    log.debug("getWigetContentCast Called" + str(params))
    server = downloadUtils.getServer()

    id = params["id"]
    jsonData = downloadUtils.downloadUrl("{server}/emby/Users/{userid}/Items/" + id + "?format=json",
                                         suppress=False, popup=1)
    result = json.loads(jsonData)
    log.debug("ItemInfo: " + str(result))

    listItems = []
    people = result.get("People")
    if (people != None):
        for person in people:
            #if (person.get("Type") == "Director"):
            #    director = director + person.get("Name") + ' '
            #if (person.get("Type") == "Writing"):
            #    writer = person.get("Name")
            #if (person.get("Type") == "Writer"):
            #    writer = person.get("Name")
            if (person.get("Type") == "Actor"):
                person_name = person.get("Name")
                person_role = person.get("Role")
                person_id = person.get("Id")
                person_tag = person.get("PrimaryImageTag")
                person_thumbnail = downloadUtils.imageUrl(person_id, "Primary", 0, 400, 400, person_tag, server=server)

                if kodi_version > 17:
                    list_item = xbmcgui.ListItem(label=person_name, iconImage=person_thumbnail, offscreen=True)
                else:
                    list_item = xbmcgui.ListItem(label=person_name, iconImage=person_thumbnail)

                artLinks = {}
                artLinks["thumb"] = person_thumbnail
                artLinks["poster"] = person_thumbnail
                list_item.setArt(artLinks)

                if person_role:
                    list_item.setLabel2(person_role)

                itemTupple = ("", list_item, False)
                listItems.append(itemTupple)

    xbmcplugin.addDirectoryItems(handle, listItems)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)


def populateWidgetItems(itemsUrl, override_select_action=None):

    server = downloadUtils.getServer()
    settings = xbmcaddon.Addon(id='plugin.video.embycon')
    select_action = settings.getSetting("widget_select_action")

    if override_select_action is not None:
        select_action = str(override_select_action)

    log.debug("WIDGET_DATE_URL: " + itemsUrl)

    # get the items
    jsonData = downloadUtils.downloadUrl(itemsUrl, suppress=False, popup=1)
    log.debug("Widget(Items) jsonData: " + jsonData)
    result = json.loads(jsonData)

    if result is not None and isinstance(result, dict) and result.get("Items") is not None:
        simmilarTo = result.get("BaselineItemName", None)
        result = result.get("Items")
    elif result is not None and isinstance(result, list) and len(result) > 0:
        simmilarTo = result[0].get("BaselineItemName", None)
        result = result[0].get("Items")
    else:
        result = []

    itemCount = 1
    listItems = []
    for item in result:
        item_id = item.get("Id")
        name = item.get("Name")
        episodeDetails = ""
        log.debug("WIDGET_DATE_NAME: " + name)

        title = item.get("Name")
        tvshowtitle = ""

        if (item.get("Type") == "Episode" and item.get("SeriesName") != None):

            eppNumber = "X"
            tempEpisodeNumber = "0"
            if (item.get("IndexNumber") != None):
                eppNumber = item.get("IndexNumber")
                if eppNumber < 10:
                    tempEpisodeNumber = "0" + str(eppNumber)
                else:
                    tempEpisodeNumber = str(eppNumber)

            seasonNumber = item.get("ParentIndexNumber")
            if seasonNumber < 10:
                tempSeasonNumber = "0" + str(seasonNumber)
            else:
                tempSeasonNumber = str(seasonNumber)

            episodeDetails = "S" + tempSeasonNumber + "E" + tempEpisodeNumber
            name = item.get("SeriesName") + " " + episodeDetails
            tvshowtitle = episodeDetails
            title = item.get("SeriesName")

        art = getArt(item, server, widget=True)

        if kodi_version > 17:
            list_item = xbmcgui.ListItem(label=name, iconImage=art['thumb'], offscreen=True)
        else:
            list_item = xbmcgui.ListItem(label=name, iconImage=art['thumb'])

        # list_item.setLabel2(episodeDetails)

        production_year = item.get("ProductionYear")
        if not production_year and item.get("PremiereDate"):
            production_year = int(item.get("PremiereDate")[:4])

        overlay = "0"
        playCount = "0"

        # add progress percent
        userData = item.get("UserData")
        if (userData != None):
            if userData.get("Played") == True:
                playCount = "1"
                overlay = "5"
            else:
                overlay = "6"

            playBackTicks = float(userData.get("PlaybackPositionTicks"))
            if (playBackTicks != None and playBackTicks > 0):
                runTimeTicks = float(item.get("RunTimeTicks", "0"))
                if (runTimeTicks > 0):
                    playBackPos = int(((playBackTicks / 1000) / 10000) / 60)
                    list_item.setProperty('ResumeTime', str(playBackPos))

                    percentage = int((playBackTicks / runTimeTicks) * 100.0)
                    list_item.setProperty("complete_percentage", str(percentage))

        video_info_label = {"title": title,
                            "tvshowtitle": tvshowtitle,
                            "year": production_year,
                            "Overlay": overlay,
                            "playcount": playCount}

        list_item.setInfo(type="Video", infoLabels=video_info_label)
        list_item.setProperty('fanart_image', art['fanart'])  # back compat
        list_item.setProperty('discart', art['discart'])  # not avail to setArt
        list_item.setArt(art)
        # add count
        list_item.setProperty("item_index", str(itemCount))
        itemCount = itemCount + 1

        list_item.setProperty('IsPlayable', 'true')

        totalTime = str(int(float(item.get("RunTimeTicks", "0")) / (10000000 * 60)))
        list_item.setProperty('TotalTime', str(totalTime))

        list_item.setProperty('id', item_id)

        if simmilarTo is not None:
            list_item.setProperty('suggested_from_watching', simmilarTo)

        if select_action == "1":
            playurl = "plugin://plugin.video.embycon/?item_id=" + item_id + '&mode=PLAY'
        elif select_action == "0":
            playurl = "plugin://plugin.video.embycon/?item_id=" + item_id + '&mode=SHOW_MENU'

        itemTupple = (playurl, list_item, False)
        listItems.append(itemTupple)

    return listItems


def getWidgetContent(handle, params):
    log.debug("getWigetContent Called" + str(params))

    type = params.get("type")
    if (type == None):
        log.error("getWigetContent type not set")
        return

    itemsUrl = ("{server}/emby/Users/{userid}/Items" +
                "?Limit={ItemLimit}" +
                "&format=json" +
                "&ImageTypeLimit=1" +
                "&IsMissing=False")

    if (type == "recent_movies"):
        xbmcplugin.setContent(handle, 'movies')
        itemsUrl += ("&Recursive=true" +
                     "&SortBy=DateCreated" +
                     "&SortOrder=Descending" +
                     "&Filters={IsUnplayed,}IsNotFolder" +
                     "&IsVirtualUnaired=false" +
                     "&IsMissing=False" +
                     "&IncludeItemTypes=Movie")
    elif (type == "inprogress_movies"):
        xbmcplugin.setContent(handle, 'movies')
        itemsUrl += ("&Recursive=true" +
                     "&SortBy=DatePlayed" +
                     "&SortOrder=Descending" +
                     "&Filters=IsResumable" +
                     "&IsVirtualUnaired=false" +
                     "&IsMissing=False" +
                     "&IncludeItemTypes=Movie")
    elif (type == "random_movies"):
        xbmcplugin.setContent(handle, 'movies')
        watched = params.get("watched", "") == "true"
        if watched:
            itemsUrl += "&Filters=IsPlayed,IsNotFolder"
        else:
            itemsUrl += "&Filters={IsUnplayed,}IsNotFolder"
        itemsUrl += ("&Recursive=true" +
                     "&SortBy=Random" +
                     "&SortOrder=Descending" +
                     "&IsVirtualUnaired=false" +
                     "&IsMissing=False" +
                     "&IncludeItemTypes=Movie")
    elif (type == "recent_episodes"):
        xbmcplugin.setContent(handle, 'episodes')
        itemsUrl += ("&Recursive=true" +
                     "&SortBy=DateCreated" +
                     "&SortOrder=Descending" +
                     "&Filters={IsUnplayed,}IsNotFolder" +
                     "&IsVirtualUnaired=false" +
                     "&IsMissing=False" +
                     "&IncludeItemTypes=Episode")
    elif (type == "inprogress_episodes"):
        xbmcplugin.setContent(handle, 'episodes')
        itemsUrl += ("&Recursive=true" +
                     "&SortBy=DatePlayed" +
                     "&SortOrder=Descending" +
                     "&Filters=IsResumable" +
                     "&IsVirtualUnaired=false" +
                     "&IsMissing=False" +
                     "&IncludeItemTypes=Episode")
    elif (type == "nextup_episodes"):
        xbmcplugin.setContent(handle, 'episodes')
        itemsUrl = ("{server}/emby/Shows/NextUp" +
                        "?Limit={ItemLimit}"
                        "&userid={userid}" +
                        "&Recursive=true" +
                        "&format=json" +
                        "&ImageTypeLimit=1")

    listItems = populateWidgetItems(itemsUrl)

    xbmcplugin.addDirectoryItems(handle, listItems)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)

