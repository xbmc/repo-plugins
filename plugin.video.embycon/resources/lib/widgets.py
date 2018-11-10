
import xbmcaddon
import xbmcplugin
import xbmcgui
import xbmc
import json
import urllib
import hashlib
import time

from downloadutils import DownloadUtils
from utils import getArt
from datamanager import DataManager
from simple_logging import SimpleLogging
from kodi_utils import HomeWindow

log = SimpleLogging(__name__)
downloadUtils = DownloadUtils()
dataManager = DataManager()
kodi_version = int(xbmc.getInfoLabel('System.BuildVersion')[:2])

background_items = []
background_current_item = 0

def set_background_image():
    log.debug("set_background_image Called")

    global background_current_item
    global background_items

    if len(background_items) == 0 or background_current_item >= len(background_items):
        log.debug("set_background_image: Need to load more backgrounds {0} - {1}",
                  len(background_items), background_current_item)
        url = ('{server}/emby/Users/{userid}/Items' +
               '?Recursive=true' +
               '&limit=60' +
               '&SortBy=Random' +
               '&IncludeItemTypes=Movie,Series' +
               '&ImageTypeLimit=1')

        server = downloadUtils.getServer()
        results = downloadUtils.downloadUrl(url, suppress=True)
        results = json.loads(results)

        if results is not None:
            items = results.get("Items", [])
            background_current_item = 0
            background_items = []
            for item in items:
                bg_image = downloadUtils.getArtwork(item, "Backdrop", server=server)
                label = item.get("Name")
                item_background = {}
                item_background["image"] = bg_image
                item_background["name"] = label
                background_items.append(item_background)

        log.debug("set_background_image: Loaded {0} more backgrounds", len(background_items))

    if len(background_items) > 0 and background_current_item < len(background_items):

        bg_image = background_items[background_current_item].get("image")
        label = background_items[background_current_item].get("name")
        log.debug("set_background_image: {0} - {1} - {2}", background_current_item, label, bg_image)

        background_current_item += 1

        home_window = HomeWindow()
        home_window.setProperty("random-gb", bg_image)
        home_window.setProperty("random-gb-label", label)



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
    log.debug("LATEST_ADDED_ITEM: {0}", result)

    last_added_date = ""
    if result is not None:
        items = result.get("Items", [])
        if len(items) > 0:
            item = items[0]
            last_added_date = item.get("Etag", "")
    log.debug("last_added_date: {0}", last_added_date)

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
    log.debug("LATEST_PLAYED_ITEM: {0}", result)

    last_played_date = ""
    if result is not None:
        items = result.get("Items", [])
        if len(items) > 0:
            item = items[0]
            last_played_date = item.get("Etag", "")
    log.debug("last_played_date: {0}", last_played_date)

    home_window = HomeWindow()
    current_widget_hash = home_window.getProperty("embycon_widget_reload")
    log.debug("Current Widget Hash: {0}", current_widget_hash)

    m = hashlib.md5()
    m.update(last_played_date + last_added_date)
    new_widget_hash = m.hexdigest()
    log.debug("New Widget Hash: {0}", new_widget_hash)

    if current_widget_hash != new_widget_hash:
        home_window.setProperty("embycon_widget_reload", new_widget_hash)
        log.debug("Setting New Widget Hash: {0}", new_widget_hash)


def getWidgetUrlContent(handle, params):
    log.debug("getWidgetUrlContent Called: {0}", params)

    request = params["url"]
    request = urllib.unquote(request)
    request = "{server}/emby/" + request + "&ImageTypeLimit=1&format=json"
    log.debug("getWidgetUrlContent URL: {0}", request)

    select_action = params.get("action", None)

    listItems = populateWidgetItems(request, override_select_action=select_action)

    xbmcplugin.addDirectoryItems(handle, listItems)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)


def get_widget_content_cast(handle, params):
    log.debug("getWigetContentCast Called: {0}", params)
    server = downloadUtils.getServer()

    item_id = params["id"]
    data_manager = DataManager()
    result = data_manager.GetContent("{server}/emby/Users/{userid}/Items/" + item_id + "?format=json")
    log.debug("ItemInfo: {0}", result)

    if not result:
        return

    if result.get("Type", "") in ["Episode", "Season"] and params.get("auto", "true") == "true":
        series_id = result.get("SeriesId")
        if series_id:
            params["id"] = series_id
            return get_widget_content_cast(handle, params)

    list_items = []
    if result is not None:
        people = result.get("People", [])
    else:
        people = []

    for person in people:
        # if (person.get("Type") == "Director"):
        #     director = director + person.get("Name") + ' '
        # if (person.get("Type") == "Writing"):
        #     writer = person.get("Name")
        # if (person.get("Type") == "Writer"):
        #    writer = person.get("Name")
        if person.get("Type") == "Actor":
            person_name = person.get("Name")
            person_role = person.get("Role")
            person_id = person.get("Id")
            person_tag = person.get("PrimaryImageTag")
            person_thumbnail = None
            if person_tag:
                person_thumbnail = downloadUtils.imageUrl(person_id, "Primary", 0, 400, 400, person_tag, server=server)

            if kodi_version > 17:
                list_item = xbmcgui.ListItem(label=person_name, offscreen=True)
            else:
                list_item = xbmcgui.ListItem(label=person_name)

            list_item.setProperty("id", person_id)

            if person_thumbnail:
                art_links = {}
                art_links["thumb"] = person_thumbnail
                art_links["poster"] = person_thumbnail
                list_item.setArt(art_links)

            labels = {}
            labels["mediatype"] = "artist"
            list_item.setInfo(type="music", infoLabels=labels)

            if person_role:
                list_item.setLabel2(person_role)

            item_tupple = ("", list_item, False)
            list_items.append(item_tupple)

    xbmcplugin.setContent(handle, 'artists')
    xbmcplugin.addDirectoryItems(handle, list_items)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)


def populateWidgetItems(itemsUrl, override_select_action=None):

    server = downloadUtils.getServer()
    if server is None:
        return []

    settings = xbmcaddon.Addon()
    select_action = settings.getSetting("widget_select_action")

    if override_select_action is not None:
        select_action = str(override_select_action)

    log.debug("WIDGET_DATE_URL: {0}", itemsUrl)

    home_window = HomeWindow()

    # get the items
    data_manager = DataManager()
    result = data_manager.GetContent(itemsUrl)

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
        item_id = item["Id"]
        name = item["Name"]
        episodeDetails = ""
        log.debug("name: {0}", name)

        title = name
        tvshowtitle = ""
        item_type = item["Type"]
        series_name = item["SeriesName"]

        if item_type == "Episode" and series_name is not None:

            episode_number = item["IndexNumber"]
            if episode_number is None:
                episode_number = 0

            season_number = item["ParentIndexNumber"]
            if season_number is None:
                season_number = 0

            # name = series_name + " " + episodeDetails
            name = "%s S%02dE%02d" % (series_name, season_number, episode_number)
            tvshowtitle = "S%02dE%02d" % (season_number, episode_number)
            title = series_name

        art = getArt(item, server)

        if kodi_version > 17:
            list_item = xbmcgui.ListItem(label=name, iconImage=art['thumb'], offscreen=True)
        else:
            list_item = xbmcgui.ListItem(label=name, iconImage=art['thumb'])

        # list_item.setLabel2(episodeDetails)

        production_year = item["ProductionYear"]
        prem_year = item["PremiereDate"]
        if production_year is None and prem_year is not None:
            production_year = int(prem_year[:4])

        # add progress percent
        userData = item["UserData"]
        if userData["Played"] == True:
            playCount = "1"
            overlay = "5"
        else:
            playCount = "0"
            overlay = "6"

        runtime = item["RunTimeTicks"]
        playBackTicks = userData["PlaybackPositionTicks"]

        if playBackTicks is not None and runtime is not None and runtime > 0:
            runtime = float(runtime)
            playBackTicks = float(playBackTicks)
            playBackPos = int(((playBackTicks / 1000) / 10000) / 60)
            list_item.setProperty('ResumeTime', str(playBackPos))
            percentage = int((playBackTicks / runtime) * 100.0)
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
        #list_item.setProperty("item_index", str(itemCount))
        #itemCount = itemCount + 1

        list_item.setProperty('IsPlayable', 'false')

        if runtime is not None:
            totalTime = str(int(float(runtime) / (10000000 * 60)))
            list_item.setProperty('TotalTime', str(totalTime))

        list_item.setContentLookup(False)
        list_item.setProperty('id', item_id)

        if simmilarTo is not None:
            list_item.setProperty('suggested_from_watching', simmilarTo)

        session_id =  "&session_id=" + home_window.getProperty("session_id")

        if select_action == "1":
            playurl = "plugin://plugin.video.embycon/?item_id=" + item_id + '&mode=PLAY' + session_id
        elif select_action == "0":
            playurl = "plugin://plugin.video.embycon/?item_id=" + item_id + '&mode=SHOW_MENU' + session_id

        itemTupple = (playurl, list_item, False)
        listItems.append(itemTupple)

    return listItems


def getWidgetContent(handle, params):
    log.debug("getWigetContent Called: {0}", params)

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

