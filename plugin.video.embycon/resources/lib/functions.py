# Gnu General Public License - see LICENSE.TXT

import urllib
import sys
import os
import time
import cProfile
import pstats
import json
import StringIO

import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmc

from downloadutils import DownloadUtils
from utils import getDetailsString, getArt
from kodi_utils import HomeWindow
from clientinfo import ClientInformation
from datamanager import DataManager
from views import DefaultViews, loadSkinDefaults
from server_detect import checkServer
from simple_logging import SimpleLogging
from menu_functions import displaySections, showMovieAlphaList, showGenreList, showWidgets, showSearch
from translation import i18n
from server_sessions import showServerSessions

__addon__ = xbmcaddon.Addon(id='plugin.video.embycon')
__addondir__ = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__cwd__ = __addon__.getAddonInfo('path')
PLUGINPATH = xbmc.translatePath(os.path.join(__cwd__))

log = SimpleLogging(__name__)

kodi_version = int(xbmc.getInfoLabel('System.BuildVersion')[:2])

downloadUtils = DownloadUtils()
dataManager = DataManager()


def mainEntryPoint():
    log.info("===== EmbyCon START =====")

    settings = xbmcaddon.Addon(id='plugin.video.embycon')
    profile_code = settings.getSetting('profile') == "true"
    pr = None
    if (profile_code):
        return_value = xbmcgui.Dialog().yesno("Profiling Enabled", "Do you want to run profiling?")
        if return_value:
            pr = cProfile.Profile()
            pr.enable()

    ADDON_VERSION = ClientInformation().getVersion()
    log.info("Running Python: " + str(sys.version_info))
    log.info("Running EmbyCon: " + str(ADDON_VERSION))
    log.info("Kodi BuildVersion: " + xbmc.getInfoLabel("System.BuildVersion"))
    log.info("Kodi Version: " + str(kodi_version))
    log.info("Script argument data: " + str(sys.argv))

    try:
        params = get_params(sys.argv[2])
    except:
        params = {}

    if (len(params) == 0):
        home_window = HomeWindow()
        windowParams = home_window.getProperty("Params")
        log.info("windowParams : " + windowParams)
        # home_window.clearProperty("Params")
        if (windowParams):
            try:
                params = get_params(windowParams)
            except:
                params = {}

    log.info("Script params = " + str(params))

    param_url = params.get('url', None)

    if param_url:
        param_url = urllib.unquote(param_url)

    mode = params.get("mode", None)
    home_window = HomeWindow()

    if mode == "CHANGE_USER":
        checkServer(change_user=True, notify=False)
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
    elif sys.argv[1] == "delete":
        item_id = sys.argv[2]
        delete(item_id)
    elif mode == "MOVIE_ALPHA":
        showMovieAlphaList()
    elif mode == "MOVIE_GENRA":
        showGenreList()
    elif mode == "WIDGETS":
        showWidgets()
    elif mode == "SHOW_SETTINGS":
        __addon__.openSettings()
        WINDOW = xbmcgui.getCurrentWindowId()
        if WINDOW == 10000:
            log.info("Currently in home - refreshing to allow new settings to be taken")
            xbmc.executebuiltin("ActivateWindow(Home)")
    elif sys.argv[1] == "refresh":
        home_window = HomeWindow()
        home_window.setProperty("force_data_reload", "true")
        xbmc.executebuiltin("Container.Refresh")
    elif mode == "SET_DEFAULT_VIEWS":
        showSetViews()
    elif mode == "WIDGET_CONTENT":
        getWigetContent(int(sys.argv[1]), params)
    elif mode == "PARENT_CONTENT":
        checkService()
        checkServer(notify=False)
        showParentContent(sys.argv[0], int(sys.argv[1]), params)
    elif mode == "SHOW_CONTENT":
        # plugin://plugin.video.embycon?mode=SHOW_CONTENT&item_type=Movie|Series
        checkService()
        checkServer(notify=False)
        showContent(sys.argv[0], int(sys.argv[1]), params)
    elif mode == "SEARCH":
        # plugin://plugin.video.embycon?mode=SEARCH
        checkService()
        checkServer(notify=False)
        xbmcplugin.setContent(int(sys.argv[1]), 'files')
        showSearch()
    elif mode == "NEW_SEARCH":
        # plugin://plugin.video.embycon?mode=NEW_SEARCH&item_type=<Movie|Series|Episode>
        if 'SEARCH_RESULTS' not in xbmc.getInfoLabel('Container.FolderPath'):  # don't ask for input on '..'
            checkService()
            checkServer(notify=False)
            search(int(sys.argv[1]), params)
        else:
            return
    elif mode == "SEARCH_RESULTS":
        # plugin://plugin.video.embycon?mode=SEARCH_RESULTS&item_type=<Movie|Series>&query=<urllib.quote(search query)>&index=<[0-9]+>
        checkService()
        checkServer(notify=False)
        searchResults(params)
    elif mode == "SHOW_SERVER_SESSIONS":
        checkService()
        checkServer(notify=False)
        showServerSessions()
    else:

        checkService()
        checkServer(notify=False)

        pluginhandle = int(sys.argv[1])

        log.info("EmbyCon -> Mode: " + str(mode))
        log.info("EmbyCon -> URL: " + str(param_url))

        # Run a function based on the mode variable that was passed in the URL
        # if ( mode == None or param_url == None or len(param_url) < 1 ):
        #    displaySections(pluginhandle)
        if mode == "GET_CONTENT":
            media_type = params.get("media_type", None)
            if not media_type:
                xbmcgui.Dialog().ok(i18n('error'), i18n('no_media_type'))
            log.info("EmbyCon -> media_type: " + str(media_type))
            getContent(param_url, pluginhandle, media_type)

        elif mode == "PLAY":
            PLAY(params, pluginhandle)

        else:
            displaySections()

    dataManager.canRefreshNow = True

    if (pr):
        pr.disable()

        fileTimeStamp = time.strftime("%Y%m%d-%H%M%S")
        tabFileName = __addondir__ + "profile(" + fileTimeStamp + ").txt"
        f = open(tabFileName, 'wb')

        s = StringIO.StringIO()
        ps = pstats.Stats(pr, stream=s)
        ps = ps.sort_stats('cumulative')
        ps.print_stats()
        ps.strip_dirs()
        ps = ps.sort_stats('cumulative')
        ps.print_stats()
        f.write(s.getvalue())

        '''
        ps = pstats.Stats(pr)
        f.write("NumbCalls\tTotalTime\tCumulativeTime\tFunctionName\tFileName\r\n")
        for (key, value) in ps.stats.items():
            (filename, count, func_name) = key
            (ccalls, ncalls, total_time, cumulative_time, callers) = value
            try:
                f.write(str(ncalls) + "\t" + "{:10.4f}".format(total_time) + "\t" + "{:10.4f}".format(cumulative_time) + "\t" + func_name + "\t" + filename + "\r\n")
            except ValueError:
                f.write(str(ncalls) + "\t" + "{0}".format(total_time) + "\t" + "{0}".format(cumulative_time) + "\t" + func_name + "\t" + filename + "\r\n")
        '''

        f.close()

    log.info("===== EmbyCon FINISHED =====")


def markWatched(item_id):
    log.info("Mark Item Watched : " + item_id)
    url = "{server}/emby/Users/{userid}/PlayedItems/" + item_id
    downloadUtils.downloadUrl(url, postBody="", method="POST")
    home_window = HomeWindow()
    home_window.setProperty("force_data_reload", "true")
    xbmc.executebuiltin("Container.Refresh")


def markUnwatched(item_id):
    log.info("Mark Item UnWatched : " + item_id)
    url = "{server}/emby/Users/{userid}/PlayedItems/" + item_id
    downloadUtils.downloadUrl(url, method="DELETE")
    home_window = HomeWindow()
    home_window.setProperty("force_data_reload", "true")
    xbmc.executebuiltin("Container.Refresh")


def markFavorite(item_id):
    log.info("Add item to favourites : " + item_id)
    url = "{server}/emby/Users/{userid}/FavoriteItems/" + item_id
    downloadUtils.downloadUrl(url, postBody="", method="POST")
    home_window = HomeWindow()
    home_window.setProperty("force_data_reload", "true")
    xbmc.executebuiltin("Container.Refresh")


def unmarkFavorite(item_id):
    log.info("Remove item from favourites : " + item_id)
    url = "{server}/emby/Users/{userid}/FavoriteItems/" + item_id
    downloadUtils.downloadUrl(url, method="DELETE")
    home_window = HomeWindow()
    home_window.setProperty("force_data_reload", "true")
    xbmc.executebuiltin("Container.Refresh")


def delete(item_id):
    return_value = xbmcgui.Dialog().yesno(i18n('confirm_file_delete'), i18n('file_delete_confirm'))
    if return_value:
        log.info('Deleting Item : ' + item_id)
        url = '{server}/emby/Items/' + item_id
        progress = xbmcgui.DialogProgress()
        progress.create(i18n('deleting'), i18n('waiting_server_delete'))
        downloadUtils.downloadUrl(url, method="DELETE")
        progress.close()
        xbmc.executebuiltin("Container.Refresh")


def addGUIItem(url, details, extraData, folder=True):
    settings = xbmcaddon.Addon(id='plugin.video.embycon')

    url = url.encode('utf-8')

    log.debug("Adding GuiItem for [%s]" % details.get('title', i18n('unknown')))
    log.debug("Passed details: " + str(details))
    log.debug("Passed extraData: " + str(extraData))

    if details.get('title', '') == '':
        return

    if extraData.get('mode', None) is None:
        mode = "&mode=0"
    else:
        mode = "&mode=%s" % extraData['mode']

    # Create the URL to pass to the item
    if folder:
        u = sys.argv[0] + "?url=" + urllib.quote(url) + mode + "&media_type=" + extraData["itemtype"]
    else:
        u = sys.argv[0] + "?item_id=" + url + "&mode=PLAY"

    # Create the ListItem that will be displayed
    thumbPath = str(extraData.get('thumb', ''))

    listItemName = details.get('title', i18n('unknown'))

    # calculate percentage
    cappedPercentage = None
    if (extraData.get('resumetime') != None and int(extraData.get('resumetime')) > 0):
        duration = float(extraData.get('duration'))
        if (duration > 0):
            resume = float(extraData.get('resumetime'))
            percentage = int((resume / duration) * 100.0)
            cappedPercentage = percentage

    if (extraData.get('TotalEpisodes') != None and extraData.get('TotalEpisodes') != "0"):
        totalItems = int(extraData.get('TotalEpisodes'))
        watched = int(extraData.get('WatchedEpisodes'))
        percentage = int((float(watched) / float(totalItems)) * 100.0)
        cappedPercentage = percentage
        if (cappedPercentage == 0):
            cappedPercentage = None
        if (cappedPercentage == 100):
            cappedPercentage = None

    countsAdded = False
    addCounts = settings.getSetting('addCounts') == 'true'
    if addCounts and extraData.get('UnWatchedEpisodes') != "0":
        countsAdded = True
        listItemName = listItemName + " (" + extraData.get('UnWatchedEpisodes') + ")"

    addResumePercent = settings.getSetting('addResumePercent') == 'true'
    if (countsAdded == False and addResumePercent and details.get('title') != None and cappedPercentage != None):
        listItemName = listItemName + " (" + str(cappedPercentage) + "%)"

    # update title with new name, this sets the new name in the deailts that are later passed to video info
    details['title'] = listItemName

    if kodi_version > 17:
        list_item = xbmcgui.ListItem(listItemName, iconImage=thumbPath, thumbnailImage=thumbPath, offscreen=True)
    else:
        list_item = xbmcgui.ListItem(listItemName, iconImage=thumbPath, thumbnailImage=thumbPath)

    log.debug("Setting thumbnail as " + thumbPath)

    # calculate percentage
    if (cappedPercentage != None):
        list_item.setProperty("complete_percentage", str(cappedPercentage))

    # For all end items
    if (not folder):
        # list_item.setProperty('IsPlayable', 'true')
        if extraData.get('type', 'video').lower() == "video":
            list_item.setProperty('TotalTime', str(extraData.get('duration')))
            list_item.setProperty('ResumeTime', str(int(extraData.get('resumetime'))))

    # StartPercent

    artTypes = ['thumb', 'poster', 'fanart', 'clearlogo', 'discart', 'banner', 'clearart', 'landscape', 'tvshow.poster']
    artLinks = {}
    for artType in artTypes:
        artLinks[artType] = extraData.get(artType, '')
        log.debug("Setting " + artType + " as " + artLinks[artType])
    list_item.setProperty('fanart_image', artLinks['fanart'])  # back compat
    list_item.setProperty('discart', artLinks['discart'])  # not avail to setArt
    list_item.setProperty('tvshow.poster', artLinks['tvshow.poster'])  # not avail to setArt
    list_item.setArt(artLinks)

    menuItems = addContextMenu(details, extraData, folder)
    if (len(menuItems) > 0):
        list_item.addContextMenuItems(menuItems, True)

    # new way
    videoInfoLabels = {}

    # add cast
    people = extraData.get('cast')
    if people is not None:
        if kodi_version >= 17:
            list_item.setCast(people)
        else:
            videoInfoLabels['cast'] = videoInfoLabels['castandrole'] = [(cast_member['name'], cast_member['role']) for cast_member in people]

    if (extraData.get('type') == None or extraData.get('type') == "Video"):
        videoInfoLabels.update(details)
    else:
        list_item.setInfo(type=extraData.get('type', 'Video'), infoLabels=details)

    videoInfoLabels["duration"] = extraData.get("duration")
    videoInfoLabels["playcount"] = extraData.get("playcount")
    if (extraData.get('favorite') == 'true'):
        videoInfoLabels["top250"] = "1"

    videoInfoLabels["mpaa"] = extraData.get('mpaa')
    videoInfoLabels["rating"] = extraData.get('rating')
    videoInfoLabels["director"] = extraData.get('director')
    videoInfoLabels["writer"] = extraData.get('writer')
    videoInfoLabels["year"] = extraData.get('year')
    videoInfoLabels["studio"] = extraData.get('studio')
    videoInfoLabels["genre"] = extraData.get('genre')

    item_type = extraData.get('itemtype').lower()
    mediatype = 'video'

    if (item_type == 'movie') or (item_type == 'boxset'):
        mediatype = 'movie'
    elif (item_type == 'series'):
        mediatype = 'tvshow'
    elif (item_type == 'season'):
        mediatype = 'season'
    elif (item_type == 'episode'):
        mediatype = 'episode'

    videoInfoLabels["mediatype"] = mediatype

    if mediatype == 'episode':
        videoInfoLabels["episode"] = details.get('episode')

    if (mediatype == 'season') or (mediatype == 'episode'):
        videoInfoLabels["season"] = details.get('season')

    list_item.setInfo('video', videoInfoLabels)

    list_item.addStreamInfo('video',
                            {'duration': extraData.get('duration'), 'aspect': extraData.get('aspectratio'),
                             'codec': extraData.get('videocodec'), 'width': extraData.get('width'),
                             'height': extraData.get('height')})
    list_item.addStreamInfo('audio', {'codec': extraData.get('audiocodec'), 'channels': extraData.get('channels')})

    list_item.setProperty('CriticRating', str(extraData.get('criticrating')))
    list_item.setProperty('ItemType', extraData.get('itemtype'))

    if extraData.get('totaltime') != None:
        list_item.setProperty('TotalTime', extraData.get('totaltime'))
    if extraData.get('TotalSeasons') != None:
        list_item.setProperty('TotalSeasons', extraData.get('TotalSeasons'))
    if extraData.get('TotalEpisodes') != None:
        list_item.setProperty('TotalEpisodes', extraData.get('TotalEpisodes'))
    if extraData.get('WatchedEpisodes') != None:
        list_item.setProperty('WatchedEpisodes', extraData.get('WatchedEpisodes'))
    if extraData.get('UnWatchedEpisodes') != None:
        list_item.setProperty('UnWatchedEpisodes', extraData.get('UnWatchedEpisodes'))
    if extraData.get('NumEpisodes') != None:
        list_item.setProperty('NumEpisodes', extraData.get('NumEpisodes'))

    list_item.setProperty('ItemGUID', extraData.get('guiid'))
    list_item.setProperty('id', extraData.get('id'))

    return (u, list_item, folder)


def addContextMenu(details, extraData, folder):
    commands = []

    item_id = extraData.get('id')
    if item_id != None:
        scriptToRun = PLUGINPATH + "/default.py"

        if not folder:
            argsToPass = "?mode=PLAY&item_id=" + item_id + "&force_transcode=true"
            commands.append((i18n('emby_force_transcode'), "RunPlugin(plugin://plugin.video.embycon" + argsToPass + ")"))

        # watched/unwatched
        if extraData.get("playcount") == "0":
            argsToPass = 'markWatched,' + item_id
            commands.append((i18n('emby_mark_watched'), "RunScript(" + scriptToRun + ", " + argsToPass + ")"))
        elif extraData.get("playcount"):
            argsToPass = 'markUnwatched,' + item_id
            commands.append((i18n('emby_mark_unwatched'), "RunScript(" + scriptToRun + ", " + argsToPass + ")"))

        # favourite add/remove
        if extraData.get('favorite') == 'false':
            argsToPass = 'markFavorite,' + item_id
            commands.append((i18n('emby_set_favorite'), "RunScript(" + scriptToRun + ", " + argsToPass + ")"))
        elif extraData.get('favorite') == 'true':
            argsToPass = 'unmarkFavorite,' + item_id
            commands.append((i18n('emby_unset_favorite'), "RunScript(" + scriptToRun + ", " + argsToPass + ")"))

        # delete
        argsToPass = 'delete,' + item_id
        commands.append((i18n('emby_delete'), "RunScript(" + scriptToRun + ", " + argsToPass + ")"))

    return (commands)


def get_params(paramstring):
    log.debug("Parameter string: " + paramstring)
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

    log.debug("EmbyCon -> Detected parameters: " + str(param))
    return param


def setSort(pluginhandle, viewType):
    defaultData = loadSkinDefaults()

    # set the default sort order
    defaultSortData = defaultData.get("sort", {})
    sortName = defaultSortData.get(viewType)
    log.info("SETTING_SORT : " + str(viewType) + " : " + str(sortName))
    if sortName == "title":
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
    elif sortName == "date":
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    else:
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_GENRE)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)


def setView(viewType):
    defaultData = loadSkinDefaults()

    defaultViewData = defaultData.get("view", {})
    viewNum = defaultViewData.get(viewType)
    log.info("SETTING_VIEW : " + str(viewType) + " : " + str(viewNum))
    if viewNum is not None and viewNum != -1:
        xbmc.executebuiltin("Container.SetViewMode(%s)" % int(viewNum))


def getContent(url, pluginhandle, media_type):
    log.info("== ENTER: getContent ==")
    log.info("URL: " + str(url))
    log.info("MediaType: " + str(media_type))

    settings = xbmcaddon.Addon(id='plugin.video.embycon')
    # determine view type, map it from media type to view type
    viewType = ""
    media_type = str(media_type).lower().strip()
    if media_type.startswith("movie"):
        viewType = "Movies"
        xbmcplugin.setContent(pluginhandle, 'movies')
    elif media_type.startswith("boxset"):
        viewType = "BoxSets"
        xbmcplugin.setContent(pluginhandle, 'movies')
    elif media_type == "tvshows":
        viewType = "Series"
        xbmcplugin.setContent(pluginhandle, 'tvshows')
    elif media_type == "series":
        viewType = "Seasons"
        xbmcplugin.setContent(pluginhandle, 'seasons')
    elif media_type == "season":
        viewType = "Episodes"
        xbmcplugin.setContent(pluginhandle, 'episodes')
    log.info("ViewType: " + viewType)

    setSort(pluginhandle, viewType)

    # show a progress indicator if needed
    progress = None
    if (settings.getSetting('showLoadProgress') == "true"):
        progress = xbmcgui.DialogProgress()
        progress.create(i18n('loading_content'))
        progress.update(0, i18n('retrieving_data'))

    # use the data manager to get the data
    result = dataManager.GetContent(url)

    if result == None or len(result) == 0:
        if (progress != None):
            progress.close()
        return

    dirItems = processDirectory(url, result, progress, pluginhandle)
    xbmcplugin.addDirectoryItems(pluginhandle, dirItems)

    # set the view mode based on what the user wanted for this view type
    setView(viewType)

    xbmcplugin.endOfDirectory(pluginhandle, cacheToDisc=False)

    if (progress != None):
        progress.update(100, i18n('done'))
        progress.close()

    return


def processDirectory(url, results, progress, pluginhandle):
    log.info("== ENTER: processDirectory ==")
    userid = downloadUtils.getUserId()

    settings = xbmcaddon.Addon(id='plugin.video.embycon')
    server = downloadUtils.getServer()

    detailsString = getDetailsString()

    dirItems = []
    result = results.get("Items")
    if (result == None):
        result = []
    item_count = len(result)
    current_item = 1

    for item in result:

        if (progress != None):
            percentDone = (float(current_item) / float(item_count)) * 100
            progress.update(int(percentDone), i18n('processing_item:') + str(current_item))
            current_item = current_item + 1

        if (item.get("Name") != None):
            tempTitle = item.get("Name").encode('utf-8')
        else:
            tempTitle = i18n('missing_title')

        id = str(item.get("Id")).encode('utf-8')
        guiid = id
        isFolder = item.get("IsFolder")

        item_type = str(item.get("Type")).encode('utf-8')

        tempEpisode = ""
        if (item.get("IndexNumber") != None):
            episodeNum = item.get("IndexNumber")
            if episodeNum < 10:
                tempEpisode = "0" + str(episodeNum)
            else:
                tempEpisode = str(episodeNum)

        tempSeason = ""
        if (str(item.get("ParentIndexNumber")) != None):
            tempSeason = str(item.get("ParentIndexNumber"))
            if item.get("ParentIndexNumber") < 10:
                tempSeason = "0" + tempSeason

        if item.get("Type") == "Season":
            guiid = item.get("SeriesId")
        elif item.get("Type") == "Episode":
            prefix = ''
            if settings.getSetting('addSeasonNumber') == 'true':
                prefix = "S" + str(tempSeason)
                if settings.getSetting('addEpisodeNumber') == 'true':
                    prefix = prefix + "E"
                    # prefix = str(tempEpisode)
            if settings.getSetting('addEpisodeNumber') == 'true':
                prefix = prefix + str(tempEpisode)
            if prefix != '':
                tempTitle = prefix + ' - ' + tempTitle
            guiid = item.get("SeriesId")

        if (item.get("PremiereDate") != None):
            premieredatelist = (item.get("PremiereDate")).split("T")
            premieredate = premieredatelist[0]
        else:
            premieredate = ""

        # add the premiered date for Upcoming TV    
        if item.get("LocationType") == "Virtual":
            airtime = item.get("AirTime")
            tempTitle = tempTitle + ' - ' + str(premieredate) + ' - ' + str(airtime)

            # Process MediaStreams
        channels = ''
        videocodec = ''
        audiocodec = ''
        height = ''
        width = ''
        aspectratio = '1:1'
        aspectfloat = 0.0
        mediaStreams = item.get("MediaStreams")
        if (mediaStreams != None):
            for mediaStream in mediaStreams:
                if (mediaStream.get("Type") == "Video"):
                    videocodec = mediaStream.get("Codec")
                    height = str(mediaStream.get("Height"))
                    width = str(mediaStream.get("Width"))
                    aspectratio = mediaStream.get("AspectRatio")
                    if aspectratio != None and len(aspectratio) >= 3:
                        try:
                            aspectwidth, aspectheight = aspectratio.split(':')
                            aspectfloat = float(aspectwidth) / float(aspectheight)
                        except:
                            aspectfloat = 1.85
                if (mediaStream.get("Type") == "Audio"):
                    audiocodec = mediaStream.get("Codec")
                    channels = mediaStream.get("Channels")

        # Process People
        director = ''
        writer = ''
        cast = None
        people = item.get("People")
        if (people != None):
            cast = []
            for person in people:
                if (person.get("Type") == "Director"):
                    director = director + person.get("Name") + ' '
                if (person.get("Type") == "Writing"):
                    writer = person.get("Name")
                if (person.get("Type") == "Writer"):
                    writer = person.get("Name")
                if (person.get("Type") == "Actor"):
                    person_name = person.get("Name")
                    person_role = person.get("Role")
                    if person_role == None:
                        person_role = ''
                    person_id = person.get("Id")
                    person_tag = person.get("PrimaryImageTag")
                    person_thumbnail = downloadUtils.imageUrl(person_id, "Primary", 0, 400, 400, person_tag, server=server)
                    person = {"name": person_name, "role": person_role, "thumbnail": person_thumbnail}
                    cast.append(person)

        # Process Studios
        studio = ""
        studios = item.get("Studios")
        if (studios != None):
            for studio_string in studios:
                if studio == "":  # Just take the first one
                    temp = studio_string.get("Name")
                    studio = temp.encode('utf-8')

        # Process Genres
        genre = ""
        genres = item.get("Genres")
        if (genres != None and genres != []):
            for genre_string in genres:
                if genre == "":  # Just take the first genre
                    genre = genre_string
                elif genre_string != None:
                    genre = genre + " / " + genre_string

        # Process UserData
        userData = item.get("UserData")
        PlaybackPositionTicks = '100'
        overlay = "0"
        favorite = "false"
        seekTime = 0
        if (userData != None):
            if userData.get("Played") != True:
                overlay = "7"
                watched = "true"
            else:
                overlay = "6"
                watched = "false"

            if userData.get("IsFavorite") == True:
                overlay = "5"
                favorite = "true"
            else:
                favorite = "false"

            if userData.get("PlaybackPositionTicks") != None:
                PlaybackPositionTicks = str(userData.get("PlaybackPositionTicks"))
                reasonableTicks = int(userData.get("PlaybackPositionTicks")) / 1000
                seekTime = reasonableTicks / 10000

        playCount = 0
        if (userData != None and userData.get("Played") == True):
            playCount = 1
        # Populate the details list
        details = {'title': tempTitle,
                   'plot': item.get("Overview"),
                   'Overlay': overlay,
                   'playcount': str(playCount),
                   # 'aired'       : episode.get('originallyAvailableAt','') ,
                   'TVShowTitle': item.get("SeriesName"),
                   }

        if item_type == "Episode":
            details['episode'] = tempEpisode
        if item_type == "Episode" or item_type == "Season":
            details['season'] = tempSeason

        try:
            tempDuration = str(int(item.get("RunTimeTicks", "0")) / (10000000))
            RunTimeTicks = str(item.get("RunTimeTicks", "0"))
        except TypeError:
            try:
                tempDuration = str(int(item.get("CumulativeRunTimeTicks")) / (10000000))
                RunTimeTicks = str(item.get("CumulativeRunTimeTicks"))
            except TypeError:
                tempDuration = "0"
                RunTimeTicks = "0"

        TotalSeasons = 0 if item.get("ChildCount") == None else item.get("ChildCount")
        TotalEpisodes = 0 if item.get("RecursiveItemCount") == None else item.get("RecursiveItemCount")
        WatchedEpisodes = 0 if userData.get("UnplayedItemCount") == None else TotalEpisodes - userData.get("UnplayedItemCount")
        UnWatchedEpisodes = 0 if userData.get("UnplayedItemCount") == None else userData.get("UnplayedItemCount")
        NumEpisodes = TotalEpisodes

        art = getArt(item, server)
        # Populate the extraData list
        extraData = {'thumb': art['thumb'],
                     'fanart': art['fanart'],
                     'poster': art['poster'],
                     'banner': art['banner'],
                     'clearlogo': art['clearlogo'],
                     'discart': art['discart'],
                     'clearart': art['clearart'],
                     'landscape': art['landscape'],
                     'tvshow.poster': art['tvshow.poster'],
                     'id': id,
                     'guiid': guiid,
                     'mpaa': item.get("OfficialRating"),
                     'rating': item.get("CommunityRating"),
                     'criticrating': item.get("CriticRating"),
                     'year': item.get("ProductionYear"),
                     'locationtype': item.get("LocationType"),
                     'premieredate': premieredate,
                     'studio': studio,
                     'genre': genre,
                     'playcount': str(playCount),
                     'director': director,
                     'writer': writer,
                     'channels': channels,
                     'videocodec': videocodec,
                     'aspectratio': str(aspectfloat),
                     'audiocodec': audiocodec,
                     'height': height,
                     'width': width,
                     'cast': cast,
                     'favorite': favorite,
                     'parenturl': url,
                     'resumetime': str(seekTime),
                     'totaltime': tempDuration,
                     'duration': tempDuration,
                     'RecursiveItemCount': item.get("RecursiveItemCount"),
                     'RecursiveUnplayedItemCount': userData.get("UnplayedItemCount"),
                     'TotalSeasons': str(TotalSeasons),
                     'TotalEpisodes': str(TotalEpisodes),
                     'WatchedEpisodes': str(WatchedEpisodes),
                     'UnWatchedEpisodes': str(UnWatchedEpisodes),
                     'NumEpisodes': str(NumEpisodes),
                     'itemtype': item_type}

        extraData["Path"] = item.get("Path")

        extraData['mode'] = "GET_CONTENT"

        if isFolder == True:
            u = ('{server}/emby/Users/{userid}' +
                 '/items?ParentId=' + id +
                 '&IsVirtualUnAired=false&IsMissing=false&Fields=' +
                 detailsString + '&format=json')

            if (item.get("RecursiveItemCount") != 0):
                dirItems.append(addGUIItem(u, details, extraData))
        else:
            u = id
            dirItems.append(addGUIItem(u, details, extraData, folder=False))

    return dirItems


def showSetViews():
    log.info("showSetViews Called")

    defaultViews = DefaultViews("DefaultViews.xml", __cwd__, "default", "720p")
    defaultViews.doModal()
    del defaultViews


def getWigetContent(handle, params):
    log.info("getWigetContent Called" + str(params))
    server = downloadUtils.getServer()

    type = params.get("type")
    if (type == None):
        log.error("getWigetContent type not set")
        return

    itemsUrl = ("{server}/emby/Users/{userid}/Items"
                "?Limit=20"
                "&format=json"
                "&ImageTypeLimit=1"
                "&IsMissing=False")

    if (type == "recent_movies"):
        xbmcplugin.setContent(handle, 'movies')
        itemsUrl += ("&Recursive=true"
                     "&SortBy=DateCreated"
                     "&SortOrder=Descending"
                     "&Filters=IsUnplayed,IsNotFolder"
                     "&IsVirtualUnaired=false"
                     "&IsMissing=False"
                     "&IncludeItemTypes=Movie")
    elif (type == "inprogress_movies"):
        xbmcplugin.setContent(handle, 'movies')
        itemsUrl += ("&Recursive=true"
                     "&SortBy=DatePlayed"
                     "&SortOrder=Descending"
                     "&Filters=IsResumable"
                     "&IsVirtualUnaired=false"
                     "&IsMissing=False"
                     "&IncludeItemTypes=Movie")
    elif (type == "random_movies"):
        xbmcplugin.setContent(handle, 'movies')
        itemsUrl += ("&Recursive=true"
                     "&SortBy=Random"
                     "&SortOrder=Descending"
                     "&Filters=IsUnplayed,IsNotFolder"
                     "&IsVirtualUnaired=false"
                     "&IsMissing=False"
                     "&IncludeItemTypes=Movie")
    elif (type == "recent_episodes"):
        xbmcplugin.setContent(handle, 'episodes')
        itemsUrl += ("&Recursive=true"
                     "&SortBy=DateCreated"
                     "&SortOrder=Descending"
                     "&Filters=IsUnplayed,IsNotFolder"
                     "&IsVirtualUnaired=false"
                     "&IsMissing=False"
                     "&IncludeItemTypes=Episode")
    elif (type == "inprogress_episodes"):
        xbmcplugin.setContent(handle, 'episodes')
        itemsUrl += ("&Recursive=true"
                     "&SortBy=DatePlayed"
                     "&SortOrder=Descending"
                     "&Filters=IsResumable"
                     "&IsVirtualUnaired=false"
                     "&IsMissing=False"
                     "&IncludeItemTypes=Episode")
    elif (type == "nextup_episodes"):
        xbmcplugin.setContent(handle, 'episodes')
        itemsUrl = ("{server}/emby/Shows/NextUp"
                        "?Limit=20" 
                        "&userid={userid}"
                        "&Recursive=true"
                        "&format=json"
                        "&ImageTypeLimit=1")

    log.debug("WIDGET_DATE_URL: " + itemsUrl)

    # get the items
    jsonData = downloadUtils.downloadUrl(itemsUrl, suppress=False, popup=1)
    log.debug("Recent(Items) jsonData: " + jsonData)
    result = json.loads(jsonData)

    if result is None:
        return []

    result = result.get("Items")
    if (result == None):
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
        list_item.setInfo(type="Video", infoLabels={"title": title, "tvshowtitle": tvshowtitle})
        list_item.setProperty('fanart_image', art['fanart'])  # back compat
        list_item.setProperty('discart', art['discart'])  # not avail to setArt
        list_item.setArt(art)
        # add count
        list_item.setProperty("item_index", str(itemCount))
        itemCount = itemCount + 1

        list_item.setProperty('IsPlayable', 'true')

        totalTime = str(int(float(item.get("RunTimeTicks", "0")) / (10000000 * 60)))
        list_item.setProperty('TotalTime', str(totalTime))

        # add progress percent
        userData = item.get("UserData")
        if (userData != None):
            playBackTicks = float(userData.get("PlaybackPositionTicks"))
            if (playBackTicks != None and playBackTicks > 0):
                runTimeTicks = float(item.get("RunTimeTicks", "0"))
                if (runTimeTicks > 0):
                    playBackPos = int(((playBackTicks / 1000) / 10000) / 60)
                    list_item.setProperty('ResumeTime', str(playBackPos))

                    percentage = int((playBackTicks / runTimeTicks) * 100.0)
                    list_item.setProperty("complete_percentage", str(percentage))

        playurl = "plugin://plugin.video.embycon/?item_id=" + item_id + '&mode=PLAY'

        itemTupple = (playurl, list_item, False)
        listItems.append(itemTupple)

    xbmcplugin.addDirectoryItems(handle, listItems)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)


def showContent(pluginName, handle, params):
    log.info("showContent Called: " + str(params))

    item_type = params.get("item_type")
    media_type = params.get("media_type", None)
    if not media_type:
        xbmcgui.Dialog().ok(i18n('error'), i18n('no_media_type'))

    contentUrl = ("{server}/emby/Users/{userid}/Items"
                  "?format=json"
                  "&ImageTypeLimit=1"
                  "&IsMissing=False"
                  "&Fields=" + getDetailsString() + ""
                  "&Recursive=true"
                  "&IsVirtualUnaired=false"
                  "&IsMissing=False"
                  "&IncludeItemTypes=" + item_type)

    log.info("showContent Content Url : " + str(contentUrl))
    getContent(contentUrl, handle, media_type)

def showParentContent(pluginName, handle, params):
    log.info("showParentContent Called: " + str(params))

    settings = xbmcaddon.Addon(id='plugin.video.embycon')
    server = downloadUtils.getServer()

    show_collections = "false"
    if settings.getSetting('show_collections') == "true":
        show_collections = "true"

    parentId = params.get("ParentId")
    name = params.get("Name")
    detailsString = getDetailsString()
    userid = downloadUtils.getUserId()
    media_type = params.get("media_type", None)

    if not media_type:
        xbmcgui.Dialog().ok(i18n('error'), i18n('no_media_type'))

    contentUrl = (
        "{server}/emby/Users/{userid}/items?ParentId=" + parentId +
        "&IsVirtualUnaired=false" +
        "&IsMissing=False" +
        "&ImageTypeLimit=1" +
        "&CollapseBoxSetItems=" + show_collections +
        "&Fields=" + detailsString +
        "&format=json")

    log.info("showParentContent Content Url : " + str(contentUrl))
    getContent(contentUrl, handle, media_type)

def checkService():
    home_window = HomeWindow()
    timeStamp = home_window.getProperty("Service_Timestamp")
    loops = 0
    while (timeStamp == ""):
        timeStamp = home_window.getProperty("Service_Timestamp")
        loops = loops + 1
        if (loops == 40):
            log.error("EmbyCon Service Not Running, no time stamp, exiting")
            xbmcgui.Dialog().ok(i18n('error'), i18n('service_not_running'), i18n('restart_kodi'))
            sys.exit()
        xbmc.sleep(200)

    log.info("EmbyCon Service Timestamp: " + timeStamp)
    log.info("EmbyCon Current Timestamp: " + str(int(time.time())))

    if ((int(timeStamp) + 240) < int(time.time())):
        log.error("EmbyCon Service Not Running, time stamp to old, exiting")
        xbmcgui.Dialog().ok(i18n('error'), i18n('service_not_running'), i18n('restart_kodi'))
        sys.exit()


def search(handle, params):
    log.info('search Called: ' + str(params))
    item_type = params.get('item_type')
    if not item_type:
        return
    kb = xbmc.Keyboard()
    if item_type.lower() == 'movie':
        heading_type = i18n('movies')
    elif item_type.lower() == 'series':
        heading_type = i18n('tvshows')
    elif item_type.lower() == 'episode':
        heading_type = i18n('episodes')
    else:
        heading_type = item_type
    kb.setHeading(heading_type.capitalize() + ' ' + i18n('search').lower())
    kb.doModal()
    if kb.isConfirmed():
        user_input = kb.getText().strip()
        if user_input:
            xbmcplugin.endOfDirectory(handle, cacheToDisc=False)
            user_input = urllib.quote(user_input)
            xbmc.executebuiltin('Container.Update(plugin://plugin.video.embycon/?mode=SEARCH_RESULTS&query={user_input}&item_type={item_type}&index=0)'
                                .format(user_input=user_input, item_type=item_type))  # redirect for results to avoid page refreshing issues
        else:
            return
    else:
        return


def searchResults(params):
    log.info('searchResults Called: ' + str(params))

    handle = int(sys.argv[1])
    query = params.get('query')
    item_type = params.get('item_type')
    if (not item_type) or (not query):
        return

    limit = int(params.get('limit', 50))
    index = 0

    settings = xbmcaddon.Addon(id='plugin.video.embycon')
    server = downloadUtils.getServer()
    userid = downloadUtils.getUserId()
    details_string = getDetailsString()

    content_url = ('{server}/emby/Search/Hints?searchTerm=' + query +
                  '&IncludeItemTypes=' + item_type +
                  '&UserId={userid}'
                  '&StartIndex=' + str(index) +
                  '&Limit=' + str(limit) +
                  '&IncludePeople=false&IncludeMedia=true&IncludeGenres=false&IncludeStudios=false&IncludeArtists=false')

    if item_type.lower() == 'movie':
        xbmcplugin.setContent(handle, 'movies')
        view_type = 'Movies'
        media_type = 'movie'
    elif item_type.lower() == 'series':
        xbmcplugin.setContent(handle, 'tvshows')
        view_type = 'Series'
        media_type = 'tvshow'
    elif item_type.lower() == 'episode':
        xbmcplugin.setContent(handle, 'episodes')
        view_type = 'Episodes'
        media_type = 'episode'
    else:
        xbmcplugin.setContent(handle, 'videos')
        view_type = ''
        media_type = 'video'

    setSort(handle, view_type)

    # show a progress indicator if needed
    progress = None
    if (settings.getSetting('showLoadProgress') == "true"):
        progress = xbmcgui.DialogProgress()
        progress.create(i18n('loading_content'))
        progress.update(0, i18n('retrieving_data'))

    result = dataManager.GetContent(content_url)
    log.debug('SearchHints jsonData: ' + str(result))

    results = result.get('SearchHints')
    if results is None:
        results = []

    item_count = 1
    total_results = int(result.get('TotalRecordCount', 0))
    log.debug('SEARCH_TOTAL_RESULTS: ' + str(total_results))
    list_items = []

    for item in results:
        item_id = item.get('ItemId')
        name = title = item.get('Name')
        log.debug('SEARCH_RESULT_NAME: ' + name)

        if progress is not None:
            percent_complete = (float(item_count) / float(total_results)) * 100
            progress.update(int(percent_complete), i18n('processing_item:') + str(item_count))

        tvshowtitle = ''
        season = episode = None

        if (item.get('Type') == 'Episode') and (item.get('Series') is not None):
            episode = '0'
            if item.get('IndexNumber') is not None:
                ep_number = item.get('IndexNumber')
                if ep_number < 10:
                    episode = '0' + str(ep_number)
                else:
                    episode = str(ep_number)

            season = '0'
            season_number = item.get('ParentIndexNumber')
            if season_number < 10:
                season = '0' + str(season_number)
            else:
                season = str(season_number)

            tvshowtitle = item.get('Series')
            title = tvshowtitle + ' - ' + title

        primary_image = thumb_image = backdrop_image = ''
        primary_tag = item.get('PrimaryImageTag')
        if primary_tag:
            primary_image = downloadUtils.imageUrl(item_id, 'Primary', 0, 0, 0, imageTag=primary_tag, server=server)
        thumb_id = item.get('ThumbImageId')
        thumb_tag = item.get('ThumbImageTag')
        if thumb_tag and thumb_id:
            thumb_image = downloadUtils.imageUrl(thumb_id, 'Thumb', 0, 0, 0, imageTag=thumb_tag, server=server)
        backdrop_id = item.get('BackdropImageItemId')
        backdrop_tag = item.get('BackdropImageTag')
        if backdrop_tag and backdrop_id:
            backdrop_image = downloadUtils.imageUrl(backdrop_id, 'Backdrop', 0, 0, 0, imageTag=backdrop_tag, server=server)

        art = {
            'thumb': thumb_image or primary_image,
            'fanart': backdrop_image,
            'poster': primary_image or thumb_image,
            'banner': '',
            'clearlogo': '',
            'clearart': '',
            'discart': '',
            'landscape': backdrop_image,
            'tvshow.poster': primary_image
        }

        if kodi_version > 17:
            list_item = xbmcgui.ListItem(label=name, iconImage=art['thumb'], offscreen=True)
        else:
            list_item = xbmcgui.ListItem(label=name, iconImage=art['thumb'])

        info = {'title': title, 'tvshowtitle': tvshowtitle, 'mediatype': media_type}
        log.debug('SEARCH_RESULT_ART: ' + str(art))
        list_item.setProperty('fanart_image', art['fanart'])
        list_item.setProperty('discart', art['discart'])
        list_item.setArt(art)

        # add count
        list_item.setProperty('item_index', str(item_count))
        item_count += 1

        if item.get('MediaType') == 'Video':
            total_time = str(int(float(item.get('RunTimeTicks', '0')) / (10000000 * 60)))
            list_item.setProperty('TotalTime', str(total_time))
            list_item.setProperty('IsPlayable', 'true')
            list_item_url = 'plugin://plugin.video.embycon/?item_id=' + item_id + '&mode=PLAY'
            is_folder = False
        else:
            item_url = ('{server}/emby/Users/{userid}' +
                        '/items?ParentId=' + item_id +
                        '&IsVirtualUnAired=false&IsMissing=false' +
                        '&Fields=' + details_string +
                        '&format=json')
            list_item_url = 'plugin://plugin.video.embycon/?mode=GET_CONTENT&media_type={item_type}&url={item_url}'\
                .format(item_type=item_type, item_url=urllib.quote(item_url))
            list_item.setProperty('IsPlayable', 'false')
            is_folder = True

        menu_items = addContextMenu({}, {'id': item_id}, is_folder)
        if len(menu_items) > 0:
            list_item.addContextMenuItems(menu_items, True)

        if (season is not None) and (episode is not None):
            info['episode'] = episode
            info['season'] = season

        info['year'] = item.get('ProductionYear', '')

        log.debug('SEARCH_RESULT_INFO: ' + str(info))
        list_item.setInfo('Video', infoLabels=info)

        item_tuple = (list_item_url, list_item, is_folder)
        list_items.append(item_tuple)

    xbmcplugin.addDirectoryItems(handle, list_items)
    setView(view_type)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)

    if progress is not None:
        progress.update(100, i18n('done'))
        progress.close()


def PLAY(params, handle):
    log.info("== ENTER: PLAY ==")

    log.info("PLAY ACTION PARAMS: " + str(params))
    item_id = params.get("item_id")

    auto_resume = int(params.get("auto_resume", "-1"))
    log.info("AUTO_RESUME: " + str(auto_resume))

    forceTranscode = params.get("force_transcode", None) is not None
    log.info("FORCE_TRANSCODE: " + str(forceTranscode))

    # set the current playing item id
    # set all the playback info, this will be picked up by the service
    # the service will then start the playback

    play_info = {}
    play_info["item_id"] =  item_id
    play_info["auto_resume"] = str(auto_resume)
    play_info["force_transcode"] = forceTranscode
    play_data = json.dumps(play_info)

    home_window = HomeWindow()
    home_window.setProperty("item_id", item_id)
    home_window.setProperty("play_item_message", play_data)
