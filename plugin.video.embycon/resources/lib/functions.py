# Gnu General Public License - see LICENSE.TXT

import urllib
import sys
import os
import time
import cProfile
import pstats
import json
import StringIO
import encodings
import binascii
import re

import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmc

from downloadutils import DownloadUtils
from utils import getArt, send_event_notification
from kodi_utils import HomeWindow
from clientinfo import ClientInformation
from datamanager import DataManager
from server_detect import checkServer
from simple_logging import SimpleLogging
from menu_functions import displaySections, showMovieAlphaList, showGenreList, showWidgets, showSearch, showYearsList, showMoviePages
from translation import i18n
from server_sessions import showServerSessions
from action_menu import ActionMenu
from widgets import getWidgetContent, get_widget_content_cast, getWidgetContentSimilar, getWidgetContentNextUp, getSuggestions, getWidgetUrlContent, checkForNewContent
import trakttokodi
from item_functions import add_gui_item, extract_item_info, ItemDetails
from cache_images import CacheArtwork

__addon__ = xbmcaddon.Addon()
__addondir__ = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__cwd__ = __addon__.getAddonInfo('path')
PLUGINPATH = xbmc.translatePath(os.path.join(__cwd__))

log = SimpleLogging(__name__)

kodi_version = int(xbmc.getInfoLabel('System.BuildVersion')[:2])

downloadUtils = DownloadUtils()
dataManager = DataManager()


def mainEntryPoint():
    log.debug("===== EmbyCon START =====")

    settings = xbmcaddon.Addon()
    profile_code = settings.getSetting('profile') == "true"
    pr = None
    if (profile_code):
        return_value = xbmcgui.Dialog().yesno("Profiling Enabled", "Do you want to run profiling?")
        if return_value:
            pr = cProfile.Profile()
            pr.enable()

    ADDON_VERSION = ClientInformation().getVersion()
    log.debug("Running Python: {0}", sys.version_info)
    log.debug("Running EmbyCon: {0}", ADDON_VERSION)
    log.debug("Kodi BuildVersion: {0}", xbmc.getInfoLabel("System.BuildVersion"))
    log.debug("Kodi Version: {0}", kodi_version)
    log.debug("Script argument data: {0}", sys.argv)

    try:
        params = get_params(sys.argv[2])
    except:
        params = {}

    home_window = HomeWindow()

    if (len(params) == 0):
        windowParams = home_window.getProperty("Params")
        log.debug("windowParams: {0}", windowParams)
        # home_window.clearProperty("Params")
        if (windowParams):
            try:
                params = get_params(windowParams)
            except:
                params = {}

    log.debug("Script params: {0}", params)

    param_url = params.get('url', None)

    if param_url:
        param_url = urllib.unquote(param_url)

    mode = params.get("mode", None)

    if mode == "CHANGE_USER":
        checkServer(change_user=True, notify=False)
    elif mode== "CACHE_ARTWORK":
        CacheArtwork().cache_artwork_interactive()
    elif mode == "DETECT_SERVER":
        checkServer(force=True, notify=True)
    elif mode == "DETECT_SERVER_USER":
        checkServer(force=True, change_user=True, notify=False)
    elif sys.argv[1] == "markWatched":
        item_id = sys.argv[2]
        markWatched(item_id)
    elif sys.argv[1] == "markUnwatched":
        item_id = sys.argv[2]
        markUnwatched(item_id)
    elif sys.argv[1] == "markFavorite":
        item_id = sys.argv[2]
        markFavorite(item_id)
    elif sys.argv[1] == "unmarkFavorite":
        item_id = sys.argv[2]
        unmarkFavorite(item_id)
    #elif sys.argv[1] == "delete":
    #    item_id = sys.argv[2]
    #    delete(item_id)
    elif mode == "playTrailer":
        item_id = params["id"]
        playTrailer(item_id)
    elif mode == "MOVIE_ALPHA":
        showMovieAlphaList()
    elif mode == "GENRES":
        showGenreList(params)
    elif mode == "MOVIE_PAGES":
        showMoviePages(params)
    elif mode == "MOVIE_YEARS":
        showYearsList()
    elif mode == "WIDGETS":
        showWidgets()
    elif mode == "SHOW_MENU":
        showMenu(params)
    elif mode == "SHOW_SETTINGS":
        __addon__.openSettings()
        WINDOW = xbmcgui.getCurrentWindowId()
        if WINDOW == 10000:
            log.debug("Currently in home - refreshing to allow new settings to be taken")
            xbmc.executebuiltin("ActivateWindow(Home)")
    elif sys.argv[1] == "refresh":
        home_window.setProperty("force_data_reload", "true")
        xbmc.executebuiltin("Container.Refresh")
    elif mode == "WIDGET_CONTENT":
        getWidgetContent(int(sys.argv[1]), params)
    elif mode == "WIDGET_CONTENT_CAST":
        get_widget_content_cast(int(sys.argv[1]), params)
    elif mode == "WIDGET_CONTENT_SIMILAR":
        getWidgetContentSimilar(int(sys.argv[1]), params)
    elif mode == "WIDGET_CONTENT_NEXTUP":
        getWidgetContentNextUp(int(sys.argv[1]), params)
    elif mode == "WIDGET_CONTENT_SUGGESTIONS":
        getSuggestions(int(sys.argv[1]), params)
    elif mode == "WIDGET_CONTENT_URL":
        getWidgetUrlContent(int(sys.argv[1]), params)
    elif mode == "PARENT_CONTENT":
        checkServer(notify=False)
        showParentContent(params)
    elif mode == "SHOW_CONTENT":
        # plugin://plugin.video.embycon?mode=SHOW_CONTENT&item_type=Movie|Series
        checkServer(notify=False)
        showContent(sys.argv[0], int(sys.argv[1]), params)
    elif mode == "SEARCH":
        # plugin://plugin.video.embycon?mode=SEARCH
        checkServer(notify=False)
        xbmcplugin.setContent(int(sys.argv[1]), 'files')
        showSearch()
    elif mode == "NEW_SEARCH":
        checkServer(notify=False)
        searchResults(params)
    elif mode == "SHOW_SERVER_SESSIONS":
        checkServer(notify=False)
        showServerSessions()
    elif mode == "TRAKTTOKODI":
        checkServer(notify=False)
        trakttokodi.entry_point(params)
    else:
        checkServer(notify=False)
        log.debug("EmbyCon -> Mode: {0}", mode)
        log.debug("EmbyCon -> URL: {0}", param_url)

        if mode == "GET_CONTENT":
            getContent(param_url, params)
        elif mode == "PLAY":
            PLAY(params)
        else:
            displaySections()

    dataManager.canRefreshNow = True

    if (pr):
        pr.disable()

        fileTimeStamp = time.strftime("%Y%m%d-%H%M%S")
        tabFileName = __addondir__ + "profile(" + fileTimeStamp + ").txt"
        s = StringIO.StringIO()
        ps = pstats.Stats(pr, stream=s)
        ps = ps.sort_stats('cumulative')
        ps.print_stats()
        ps.strip_dirs()
        ps = ps.sort_stats('tottime')
        ps.print_stats()
        with open(tabFileName, 'wb') as f:
            f.write(s.getvalue())

    log.debug("===== EmbyCon FINISHED =====")


def markWatched(item_id):
    log.debug("Mark Item Watched: {0}", item_id)
    url = "{server}/emby/Users/{userid}/PlayedItems/" + item_id
    downloadUtils.downloadUrl(url, postBody="", method="POST")
    home_window = HomeWindow()
    home_window.setProperty("force_data_reload", "true")
    home_window.setProperty("embycon_widget_reload", str(time.time()))
    xbmc.executebuiltin("Container.Refresh")


def markUnwatched(item_id):
    log.debug("Mark Item UnWatched: {0}", item_id)
    url = "{server}/emby/Users/{userid}/PlayedItems/" + item_id
    downloadUtils.downloadUrl(url, method="DELETE")
    home_window = HomeWindow()
    home_window.setProperty("force_data_reload", "true")
    home_window.setProperty("embycon_widget_reload", str(time.time()))
    xbmc.executebuiltin("Container.Refresh")


def markFavorite(item_id):
    log.debug("Add item to favourites: {0}", item_id)
    url = "{server}/emby/Users/{userid}/FavoriteItems/" + item_id
    downloadUtils.downloadUrl(url, postBody="", method="POST")
    home_window = HomeWindow()
    home_window.setProperty("force_data_reload", "true")
    home_window.setProperty("embycon_widget_reload", str(time.time()))
    xbmc.executebuiltin("Container.Refresh")


def unmarkFavorite(item_id):
    log.debug("Remove item from favourites: {0}", item_id)
    url = "{server}/emby/Users/{userid}/FavoriteItems/" + item_id
    downloadUtils.downloadUrl(url, method="DELETE")
    home_window = HomeWindow()
    home_window.setProperty("force_data_reload", "true")
    home_window.setProperty("embycon_widget_reload", str(time.time()))
    xbmc.executebuiltin("Container.Refresh")


def delete(item):

    item_id = item.get("Id")
    item_name = item.get("Name")
    series_name = item.get("SeriesName")
    if series_name:
        final_name = series_name + " - " + item_name
    else:
        final_name = item_name

    return_value = xbmcgui.Dialog().yesno(i18n('confirm_file_delete'), final_name, i18n('file_delete_confirm'))
    if return_value:
        log.debug('Deleting Item: {0}', item_id)
        url = '{server}/emby/Items/' + item_id
        progress = xbmcgui.DialogProgress()
        progress.create(i18n('deleting'), i18n('waiting_server_delete'))
        downloadUtils.downloadUrl(url, method="DELETE")
        progress.close()
        home_window = HomeWindow()
        home_window.setProperty("force_data_reload", "true")
        home_window.setProperty("embycon_widget_reload", str(time.time()))
        xbmc.executebuiltin("Container.Refresh")


def get_params(paramstring):
    log.debug("Parameter string: {0}", paramstring)
    param = {}
    if len(paramstring) >= 2:
        params = paramstring

        if params[0] == "?":
            cleanedparams = params[1:]
        else:
            cleanedparams = params

        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]

        pairsofparams = cleanedparams.split('&')
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
            elif (len(splitparams)) == 3:
                param[splitparams[0]] = splitparams[1] + "=" + splitparams[2]

    log.debug("EmbyCon -> Detected parameters: {0}", param)
    return param


def setSort(pluginhandle, viewType):
    log.debug("SETTING_SORT for media type: {0}", viewType)
    if viewType == "BoxSets":
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
    elif viewType == "Episodes":
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_EPISODE)
    elif viewType == "Music":
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_TRACKNUM)
    else:
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)

    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_DATEADDED)
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_GENRE)
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)

def getContent(url, params):
    log.debug("== ENTER: getContent ==")

    media_type = params.get("media_type", None)
    if not media_type:
        xbmcgui.Dialog().ok(i18n('error'), i18n('no_media_type'))

    log.debug("URL: {0}", url)
    log.debug("MediaType: {0}", media_type)
    pluginhandle = int(sys.argv[1])

    settings = xbmcaddon.Addon()
    # determine view type, map it from media type to view type
    view_type = ""
    content_type = ""
    media_type = str(media_type).lower().strip()
    if media_type.startswith("movie"):
        view_type = "Movies"
        content_type = 'movies'
    elif media_type == "musicalbums":
        view_type = "Albums"
        content_type = 'albums'
    elif media_type == "musicartists":
        view_type = "Artists"
        content_type = 'artists'
    elif media_type == "musicartist":
        view_type = "Albums"
        content_type = 'albums'
    elif media_type == "music" or media_type == "audio" or media_type == "musicalbum":
        view_type = "Music"
        content_type = 'songs'
    elif media_type.startswith("boxsets"):
        view_type = "Movies"
        content_type = 'sets'
    elif media_type.startswith("boxset"):
        view_type = "BoxSets"
        content_type = 'movies'
    elif media_type == "tvshows":
        view_type = "Series"
        content_type = 'tvshows'
    elif media_type == "series":
        view_type = "Seasons"
        content_type = 'seasons'
    elif media_type == "season" or media_type == "episodes":
        view_type = "Episodes"
        content_type = 'episodes'

    log.debug("media_type:{0} content_type:{1} view_type:{2} ", media_type, content_type, view_type)

    # show a progress indicator if needed
    progress = None
    if (settings.getSetting('showLoadProgress') == "true"):
        progress = xbmcgui.DialogProgress()
        progress.create(i18n('loading_content'))
        progress.update(0, i18n('retrieving_data'))

    # update url for paging
    start_index = 0
    page_limit = int(settings.getSetting('moviePageSize'))
    if page_limit > 0 and media_type.startswith("movie"):
        url_prev = None
        m = re.search('StartIndex=([0-9]{1,4})', url)
        if m and m.group(1):
            log.debug("UPDATING NEXT URL: {0}", url)
            start_index = int(m.group(1))
            log.debug("current_start : {0}", start_index)
            if start_index > 0:
                prev_index = start_index - page_limit
                if prev_index < 0:
                    prev_index = 0
                url_prev = re.sub('StartIndex=([0-9]{1,4})', 'StartIndex=' + str(prev_index), url)
            url_next = re.sub('StartIndex=([0-9]{1,4})', 'StartIndex=' + str(start_index + page_limit), url)
            log.debug("UPDATING NEXT URL: {0}", url_next)

        else:
            log.debug("ADDING NEXT URL: {0}", url)
            url_next = url + "&StartIndex=" + str(start_index + page_limit) + "&Limit=" + str(page_limit)
            url = url + "&StartIndex=" + str(start_index) + "&Limit=" + str(page_limit)
            log.debug("ADDING NEXT URL: {0}", url_next)

    # use the data manager to get the data
    result = dataManager.GetContent(url)

    total_records = 0
    if result is not None and isinstance(result, dict):
        total_records = result.get("TotalRecordCount", 0)

    dir_items, detected_type = processDirectory(result, progress, params)
    if dir_items is None:
        return

    # add paging items
    if page_limit > 0 and media_type.startswith("movie"):
        if url_prev:
            list_item = xbmcgui.ListItem("Prev Page (" + str(start_index - page_limit + 1) + "-" + str(start_index) +
                                         " of " + str(total_records) + ")")
            u = sys.argv[0] + "?url=" + urllib.quote(url_prev) + "&mode=GET_CONTENT&media_type=movies"
            dir_items.insert(0, (u, list_item, True))

        if start_index + page_limit < total_records:
            upper_count = start_index + (page_limit * 2)
            if upper_count > total_records:
                upper_count = total_records
            list_item = xbmcgui.ListItem("Next Page (" + str(start_index + page_limit + 1) + "-" +
                                         str(upper_count) + " of " + str(total_records) + ")")
            u = sys.argv[0] + "?url=" + urllib.quote(url_next) + "&mode=GET_CONTENT&media_type=movies"
            dir_items.append((u, list_item, True))

    # set the Kodi content type
    if content_type:
        xbmcplugin.setContent(pluginhandle, content_type)
    elif detected_type is not None:
        # if the media type is not set then try to use the detected type
        log.debug("Detected content type: {0}", detected_type)
        if detected_type == "Movie":
            view_type = "Movies"
            content_type = 'movies'
        if detected_type == "Episode":
            view_type = "Episodes"
            content_type = 'episodes'
        xbmcplugin.setContent(pluginhandle, content_type)

    # set the sort items
    if page_limit > 0 and media_type.startswith("movie"):
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_UNSORTED)
    else:
        setSort(pluginhandle, view_type)

    xbmcplugin.addDirectoryItems(pluginhandle, dir_items)
    xbmcplugin.endOfDirectory(pluginhandle, cacheToDisc=False)

    # send display items event
    display_items_notification = {"view_type": view_type}
    send_event_notification("display_items", display_items_notification)

    if (progress != None):
        progress.update(100, i18n('done'))
        progress.close()

    return


def processDirectory(results, progress, params):
    log.debug("== ENTER: processDirectory ==")

    settings = xbmcaddon.Addon()
    server = downloadUtils.getServer()

    name_format = params.get("name_format", None)
    name_format_type = None
    if name_format is not None:
        name_format = urllib.unquote(name_format)
        tokens = name_format.split("|")
        if len(tokens) == 2:
            name_format_type = tokens[0]
            name_format = settings.getSetting(tokens[1])
        else:
            name_format_type = None
            name_format = None

    dirItems = []
    if results is None:
        results = []

    baseline_name = None
    if isinstance(results, dict) and results.get("Items") is not None:
        baseline_name = results.get("BaselineItemName")
        results = results.get("Items", [])
    elif isinstance(results, list) and len(results) > 0 and results[0].get("Items") is not None:
        baseline_name = results[0].get("BaselineItemName")
        results = results[0].get("Items")

    # flatten single season
    # if there is only one result and it is a season and you have flatten signle season turned on then
    # build a new url, set the content media type and call get content again
    flatten_single_season = settings.getSetting("flatten_single_season") == "true"
    if flatten_single_season and len(results) == 1 and results[0].get("Type", "") == "Season":
        season_id = results[0].get("Id")
        season_url = ('{server}/emby/Users/{userid}/items' +
                      '?ParentId=' + season_id +
                      '&IsVirtualUnAired=false' +
                      '&IsMissing=false' +
                      '&Fields={field_filters}' +
                      '&format=json')
        if progress is not None:
            progress.close()
        params["media_type"] = "Episodes"
        getContent(season_url, params)
        return None, None

    hide_unwatched_details = settings.getSetting('hide_unwatched_details') == 'true'

    display_options = {}
    display_options["addCounts"] = settings.getSetting("addCounts") == 'true'
    display_options["addResumePercent"] = settings.getSetting("addResumePercent") == 'true'
    display_options["addSubtitleAvailable"] = settings.getSetting("addSubtitleAvailable") == 'true'

    show_empty_folders = settings.getSetting("show_empty_folders") == 'true'

    item_count = len(results)
    current_item = 1
    first_season_item = None
    total_unwatched = 0
    total_episodes = 0
    total_watched = 0

    gui_options = {}
    gui_options["server"] = server

    gui_options["name_format"] = name_format
    gui_options["name_format_type"] = name_format_type
    detected_type = None

    for item in results:

        if progress is not None:
            percent_done = (float(current_item) / float(item_count)) * 100
            progress.update(int(percent_done), i18n('processing_item:') + str(current_item))
            current_item = current_item + 1

        # get the infofrom the item
        item_details = extract_item_info(item, gui_options)
        item_details.baseline_itemname = baseline_name

        if detected_type is not None:
            if item_details.item_type != detected_type:
                detected_type = "mixed"
        else:
            detected_type = item_details.item_type

        if item_details.item_type == "Season" and first_season_item is None:
            first_season_item = item

        total_unwatched += item_details.unwatched_episodes
        total_episodes += item_details.total_episodes
        total_watched += item_details.watched_episodes

        # if set, for unwatched episodes dont show some of the info
        if hide_unwatched_details and item_details.item_type == "Episode" and item_details.play_count == 0:
            item_details.plot = "[Spoiler Alert]"
            item_details.art["poster"] = item_details.art["tvshow.poster"]
            item_details.art["thumb"] = item_details.art["tvshow.poster"]

        if item["IsFolder"] is True:
            if item_details.item_type == "Series":
                u = ('{server}/emby/Shows/' + item_details.id +
                     '/Seasons'
                     '?userId={userid}' +
                     '&Fields={field_filters}' +
                     '&format=json')

            else:
                u = ('{server}/emby/Users/{userid}/items' +
                     '?ParentId=' + item_details.id +
                     '&IsVirtualUnAired=false' +
                     '&IsMissing=false' +
                     '&Fields={field_filters}' +
                     '&format=json')

            if show_empty_folders or item["RecursiveItemCount"] != 0:
                dirItems.append(add_gui_item(u, item_details, display_options))

        elif item_details.item_type == "MusicArtist":
            u = ('{server}/emby/Users/{userid}/items' +
                 '?ArtistIds=' + item_details.id +
                 '&IncludeItemTypes=MusicAlbum' +
                 '&CollapseBoxSetItems=false' +
                 '&Recursive=true' +
                 '&format=json')
            dirItems.append(add_gui_item(u, item_details, display_options))

        else:
            u = item_details.id
            dirItems.append(add_gui_item(u, item_details, display_options, folder=False))

    # add the all episodes item
    show_all_episodes = settings.getSetting('show_all_episodes') == 'true'
    if (show_all_episodes
            and first_season_item is not None
            and len(dirItems) > 1
            and first_season_item.get("SeriesId") is not None):
        series_url = ('{server}/emby/Users/{userid}/items' +
                      '?ParentId=' + first_season_item.get("SeriesId") +
                      '&IsVirtualUnAired=false' +
                      '&IsMissing=false' +
                      '&Fields={field_filters}' +
                      '&Recursive=true' +
                      '&IncludeItemTypes=Episode' +
                      '&format=json')
        played = 0
        overlay = "7"
        if total_unwatched == 0:
            played = 1
            overlay = "6"

        item_details = ItemDetails()

        item_details.id = first_season_item.get("Id")
        item_details.name = i18n('all')
        item_details.art = getArt(first_season_item, server)
        item_details.play_count = played
        item_details.overlay = overlay
        item_details.name_format = "Episode|episode_name_format"
        item_details.series_name = first_season_item.get("SeriesName")
        item_details.item_type = "Season"
        item_details.unwatched_episodes = total_unwatched
        item_details.total_episodes = total_episodes
        item_details.watched_episodes = total_watched
        item_details.mode = "GET_CONTENT"

        dirItems.append(add_gui_item(series_url, item_details, display_options, folder=True))

    return dirItems, detected_type


def showMenu(params):
    log.debug("showMenu(): {0}", params)

    item_id = params["item_id"]

    url = "{server}/emby/Users/{userid}/Items/" + item_id + "?format=json"
    data_manager = DataManager()
    result = data_manager.GetContent(url)
    log.debug("Playfile item info: {0}", result)

    if result is None:
        return

    action_items = []
    
    if result["Type"] in ["Episode", "Movie", "Music"]:
        li = xbmcgui.ListItem(i18n('play'))
        li.setProperty('menu_id', 'play')
        action_items.append(li)

    if result["Type"] in ["Season", "MusicAlbum"]:
        li = xbmcgui.ListItem(i18n('play_all'))
        li.setProperty('menu_id', 'play_all')
        action_items.append(li)

    if result["Type"] in ["Episode", "Movie"]:
        li = xbmcgui.ListItem(i18n('emby_force_transcode'))
        li.setProperty('menu_id', 'transcode')
        action_items.append(li)

    if result["Type"] == "Movie":
        li = xbmcgui.ListItem(i18n('play_trailer'))
        li.setProperty('menu_id', 'play_trailer')
        action_items.append(li)

    if result["Type"] == "Episode" and result["ParentId"] is not None:
        li = xbmcgui.ListItem(i18n('view_season'))
        li.setProperty('menu_id', 'view_season')
        action_items.append(li)

    user_data = result["UserData"]
    if user_data.get("Played", False) is False:
        li = xbmcgui.ListItem(i18n('emby_mark_watched'))
        li.setProperty('menu_id', 'mark_watched')
        action_items.append(li)
    else:
        li = xbmcgui.ListItem(i18n('emby_mark_unwatched'))
        li.setProperty('menu_id', 'mark_unwatched')
        action_items.append(li)

    if user_data["IsFavorite"] == False:
        li = xbmcgui.ListItem(i18n('emby_set_favorite'))
        li.setProperty('menu_id', 'emby_set_favorite')
        action_items.append(li)
    else:
        li = xbmcgui.ListItem(i18n('emby_unset_favorite'))
        li.setProperty('menu_id', 'emby_unset_favorite')
        action_items.append(li)

    li = xbmcgui.ListItem(i18n('emby_delete'))
    li.setProperty('menu_id', 'delete')
    action_items.append(li)

    #xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)

    action_menu = ActionMenu("ActionMenu.xml", PLUGINPATH, "default", "720p")
    action_menu.setActionItems(action_items)
    action_menu.doModal()
    selected_action_item = action_menu.getActionItem()
    selected_action = ""
    if selected_action_item is not None:
        selected_action = selected_action_item.getProperty('menu_id')
    log.debug("Menu Action Selected: {0}", selected_action_item)
    del action_menu

    if selected_action == "play":
        log.debug("Play Item")
        #list_item = populate_listitem(params["item_id"])
        #result = xbmcgui.Dialog().info(list_item)
        #log.debug("xbmcgui.Dialog().info: {0}", result)
        PLAY(params)

    elif selected_action == "play_all":
        PLAY(params)

    elif selected_action == "play_trailer":
        playTrailer(item_id)

    elif selected_action == "transcode":
        params['force_transcode'] = 'true'
        PLAY(params)

    elif selected_action == "emby_set_favorite":
        markFavorite(item_id)

    elif selected_action == "emby_unset_favorite":
        unmarkFavorite(item_id)

    elif selected_action == "mark_watched":
        markWatched(item_id)

    elif selected_action == "mark_unwatched":
        markUnwatched(item_id)

    elif selected_action == "delete":
        delete(result)

    elif selected_action == "view_season":
        parent_id = result["ParentId"]
        xbmc.executebuiltin(
            'ActivateWindow(Videos, plugin://plugin.video.embycon/?mode=PARENT_CONTENT&ParentId={0}&media_type=episodes, return)'.format(parent_id))


def populate_listitem(item_id):
    log.debug("populate_listitem: {0}", item_id)

    url = "{server}/emby/Users/{userid}/Items/" + item_id + "?format=json"
    jsonData = downloadUtils.downloadUrl(url)
    result = json.loads(jsonData)
    log.debug("populate_listitem item info: {0}", result)

    '''
    server = downloadUtils.getServer()
    gui_options = {}
    gui_options["server"] = server

    gui_options["name_format"] = None
    gui_options["name_format_type"] = None

    details, extraData = extract_item_info(result,gui_options )
    u, list_item, folder = add_gui_item(result["Id"], details, extraData, {}, folder=False)

    log.debug("list_item path: {0}", u)

    #list_item.setProperty('IsPlayable', 'false')
    #list_item.setPath(u)
    '''

    item_title = result.get("Name", i18n('missing_title'))

    list_item = xbmcgui.ListItem(label=item_title)

    server = downloadUtils.getServer()

    art = getArt(result, server=server)
    list_item.setIconImage(art['thumb'])  # back compat
    list_item.setProperty('fanart_image', art['fanart'])  # back compat
    list_item.setProperty('discart', art['discart'])  # not avail to setArt
    list_item.setArt(art)

    list_item.setProperty('IsPlayable', 'false')
    list_item.setProperty('IsFolder', 'false')
    list_item.setProperty('id', result.get("Id"))

    # play info
    details = {
        'title': item_title,
        'plot': result.get("Overview")
    }

    list_item.setInfo("Video", infoLabels=details)

    return list_item


def showContent(pluginName, handle, params):
    log.debug("showContent Called: {0}", params)

    item_type = params.get("item_type")

    contentUrl = ("{server}/emby/Users/{userid}/Items"
                  "?format=json" +
                  "&SortBy=Name" +
                  "&SortOrder=Ascending" +
                  "&ImageTypeLimit=1" +
                  "&IsMissing=False" +
                  "&Fields={field_filters}" +
                  "&Recursive=true" +
                  "&IsVirtualUnaired=false" +
                  "&IsMissing=False" +
                  "&IncludeItemTypes=" + item_type)

    log.debug("showContent Content Url: {0}", contentUrl)
    getContent(contentUrl, params)


def showParentContent(params):
    log.debug("showParentContent Called: {0}", params)

    parentId = params.get("ParentId")

    contentUrl = (
        "{server}/emby/Users/{userid}/items?ParentId=" + parentId +
        "&IsVirtualUnaired=false" +
        "&IsMissing=False" +
        "&ImageTypeLimit=1" +
        "&Fields={field_filters}" +
        "&format=json")

    log.debug("showParentContent Content Url: {0}", contentUrl)
    getContent(contentUrl, params)


def searchResults(params):

    item_type = params.get('item_type')
    query_string = params.get('query')
    if query_string:
        log.debug("query_string : {0}", query_string)
        query_string = urllib.unquote(query_string)
        log.debug("query_string : {0}", query_string)
        query_string = urllib.quote(query_string)
        log.debug("query_string : {0}", query_string)

    item_type = item_type.lower()

    if item_type == 'movie':
        heading_type = i18n('movies')
        content_type = 'movies'
    elif item_type == 'series':
        heading_type = i18n('tvshows')
        content_type = 'tvshows'
    elif item_type == 'episode':
        heading_type = i18n('episodes')
        content_type = 'episodes'
        params["name_format"] = "Episode|episode_name_format"
    elif item_type == "music" or item_type == "audio" or item_type == "musicalbum":
        heading_type = 'Music'
        content_type = 'songs'
    elif item_type == "musicartists":
        heading_type = 'Artists'
        content_type = 'artists'
    else:
        heading_type = item_type
        content_type = 'video'

    handle = int(sys.argv[1])

    if not query_string:
        home_window = HomeWindow()
        last_search = home_window.getProperty("last_search")
        kb = xbmc.Keyboard()
        kb.setHeading(heading_type.capitalize() + ' ' + i18n('search').lower())
        kb.setDefault(last_search)
        kb.doModal()

        if kb.isConfirmed():
            user_input = kb.getText().strip()
        else:
            return

        home_window.setProperty("last_search", user_input)
        log.debug('searchResults Called: {0}', params)
        query = user_input

    else:
        query = query_string

    if (not item_type) or (not query):
        return

    limit = int(params.get('limit', 20))
    content_url = ('{server}/emby/Search/Hints?searchTerm=' + query +
                   '&UserId={userid}' +
                   '&Limit=' + str(limit) +
                   '&IncludeItemTypes=' + item_type +
                   '&ExcludeItemTypes=LiveTvProgram' +
                   '&IncludePeople=false' +
                   '&IncludeMedia=true' +
                   '&IncludeGenres=false' +
                   '&IncludeStudios=false' +
                   '&IncludeArtists=false')

    if item_type == "musicartists":
        content_url = ('{server}/emby/Search/Hints?searchTerm=' + query +
                       '&UserId={userid}' +
                       '&Limit=' + str(limit) +
                       '&IncludePeople=false' +
                       '&IncludeMedia=false' +
                       '&IncludeGenres=false' +
                       '&IncludeStudios=false' +
                       '&IncludeArtists=true')

    # set content type
    xbmcplugin.setContent(handle, content_type)

    # show a progress indicator if needed
    settings = xbmcaddon.Addon()
    progress = None
    if settings.getSetting('showLoadProgress') == "true":
        progress = xbmcgui.DialogProgress()
        progress.create(i18n('loading_content'))
        progress.update(0, i18n('retrieving_data'))

    search_hints_result = dataManager.GetContent(content_url)
    log.debug('SearchHints jsonData: {0}', search_hints_result)

    if search_hints_result is None:
        search_hints_result = {}

    search_hints = search_hints_result.get('SearchHints')
    if search_hints is None:
        search_hints = []

    total_results = int(search_hints_result.get('TotalRecordCount', 0))
    log.debug('SEARCH_TOTAL_RESULTS: {0}', total_results)

    # extract IDs for details query
    id_list = []
    for item in search_hints:
        item_id = item.get('ItemId')
        id_list.append(item_id)

    if len(id_list) > 0:
        Ids = ",".join(id_list)
        details_url = ('{server}/emby/Users/{userid}/items' +
                       '?Ids=' + Ids +
                       '&Fields={field_filters}' +
                       '&format=json')
        details_result = dataManager.GetContent(details_url)
        log.debug("Search Results Details: {0}", details_result)

        dir_items, detected_type = processDirectory(details_result, progress, params)
        if dir_items is not None:
            xbmcplugin.addDirectoryItems(handle, dir_items)
            xbmcplugin.endOfDirectory(handle, cacheToDisc=False)
    elif not query_string:
        xbmcgui.Dialog().ok("No Matches", "No items match your search.")

    if progress is not None:
        progress.update(100, i18n('done'))
        progress.close()


def PLAY(params):
    log.debug("== ENTER: PLAY ==")

    log.debug("PLAY ACTION PARAMS: {0}", params)
    item_id = params.get("item_id")

    auto_resume = int(params.get("auto_resume", "-1"))
    log.debug("AUTO_RESUME: {0}", auto_resume)

    forceTranscode = params.get("force_transcode", None) is not None
    log.debug("FORCE_TRANSCODE: {0}", forceTranscode)

    media_source_id = params.get("media_source_id", "")
    log.debug("media_source_id: {0}", media_source_id)

    use_default = params.get("use_default", "false") == "true"
    log.debug("use_default: {0}", use_default)

    # set the current playing item id
    # set all the playback info, this will be picked up by the service
    # the service will then start the playback

    xbmc.Player().stop()

    play_info = {}
    play_info["item_id"] = item_id
    play_info["auto_resume"] = str(auto_resume)
    play_info["force_transcode"] = forceTranscode
    play_info["media_source_id"] = media_source_id
    play_info["use_default"] = use_default
    send_event_notification("embycon_play_action", play_info)


def playTrailer(id):
    log.debug("== ENTER: playTrailer ==")

    url = ("{server}/emby/Users/{userid}/Items/%s/LocalTrailers?format=json" % id)

    jsonData = downloadUtils.downloadUrl(url)
    result = json.loads(jsonData)

    if result is None:
        return

    log.debug("LocalTrailers {0}", result)
    count = 1

    trailer_names = []
    trailer_list = []
    for trailer in result:
        info = {}
        info["type"] = "local"
        name = trailer.get("Name")
        while not name or name in trailer_names:
            name = "Trailer " + str(count)
            count += 1
        info["name"] = name
        info["id"] = trailer.get("Id")
        count += 1
        trailer_names.append(name)
        trailer_list.append(info)

    url = ("{server}/emby/Users/{userid}/Items/%s?format=json&Fields=RemoteTrailers" % id)
    jsonData = downloadUtils.downloadUrl(url)
    result = json.loads(jsonData)
    log.debug("RemoteTrailers: {0}", result)
    count = 1

    if result is None:
        return

    remote_trailers = result.get("RemoteTrailers", [])
    for trailer in remote_trailers:
        info = {}
        info["type"] = "remote"
        url = trailer.get("Url", "none")
        if url.lower().find("youtube"):
            info["url"] = url
            name = trailer.get("Name")
            while not name or name in trailer_names:
                name = "Trailer " + str(count)
                count += 1
            info["name"] = name
            trailer_names.append(name)
            trailer_list.append(info)

    log.debug("TrailerList: {0}", trailer_list)

    trailer_text = []
    for trailer in trailer_list:
        name = trailer.get("name") + " (" + trailer.get("type") + ")"
        trailer_text.append(name)

    dialog = xbmcgui.Dialog()
    resp = dialog.select(i18n('select_trailer'), trailer_text)
    if resp > -1:
        trailer = trailer_list[resp]
        log.debug("SelectedTrailer: {0}", trailer)

        if trailer.get("type") == "local":
            params = {}
            params["item_id"] = trailer.get("id")
            PLAY(params)

        elif trailer.get("type") == "remote":
            youtube_id = trailer.get("url").rsplit('=', 1)[1]
            log.debug("YoutubeID: {0}", youtube_id)
            youtube_plugin = "PlayMedia(plugin://plugin.video.youtube/?action=play_video&videoid=%s)" % youtube_id
            xbmc.executebuiltin(youtube_plugin)



