# Gnu General Public License - see LICENSE.TXT

import binascii

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

from datetime import timedelta
from datetime import datetime
import json
import os

from .simple_logging import SimpleLogging
from .downloadutils import DownloadUtils
from .resume_dialog import ResumeDialog
from .utils import PlayUtils, getArt, id_generator, send_event_notification
from .kodi_utils import HomeWindow
from .translation import string_load
from .datamanager import DataManager
from .item_functions import get_next_episode, extract_item_info, add_gui_item
from .clientinfo import ClientInformation
from .functions import delete
from .cache_images import CacheArtwork
from .picture_viewer import PictureViewer

log = SimpleLogging(__name__)
download_utils = DownloadUtils()

def playAllFiles(items, monitor):
    log.debug("playAllFiles called with items: {0}", items)
    server = download_utils.getServer()

    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()

    for item in items:

        item_id = item.get("Id")
        sources = item.get("MediaSources")
        selected_media_source = sources[0]
        source_id = selected_media_source.get("Id")

        listitem_props = []
        playback_type = "0"
        playurl = None
        play_session_id = id_generator()
        log.debug("play_session_id: {0}", play_session_id)

        # check if strm file, path will contain contain strm contents
        if selected_media_source.get('Container') == 'strm':
            playurl, listitem_props = PlayUtils().getStrmDetails(selected_media_source)
            if playurl is None:
                return

        if not playurl:
            playurl, playback_type = PlayUtils().getPlayUrl(item_id, selected_media_source, False, play_session_id)

        log.debug("Play URL: {0} ListItem Properties: {1}", playurl, listitem_props)

        playback_type_string = "DirectPlay"
        if playback_type == "2":
            playback_type_string = "Transcode"
        elif playback_type == "1":
            playback_type_string = "DirectStream"

        # add the playback type into the overview
        if item.get("Overview", None) is not None:
            item["Overview"] = playback_type_string + "\n" + item.get("Overview")
        else:
            item["Overview"] = playback_type_string

        # add title decoration is needed
        item_title = item.get("Name", string_load(30280))
        list_item = xbmcgui.ListItem(label=item_title)

        # add playurl and data to the monitor
        data = {}
        data["item_id"] = item_id
        data["source_id"] = source_id
        data["playback_type"] = playback_type_string
        data["play_session_id"] = play_session_id
        data["play_action_type"] = "play_all"
        monitor.played_information[playurl] = data
        log.debug("Add to played_information: {0}", monitor.played_information)

        list_item.setPath(playurl)
        list_item = setListItemProps(item_id, list_item, item, server, listitem_props, item_title)

        playlist.add(playurl, list_item)

    xbmc.Player().play(playlist)


def playListOfItems(id_list, monitor):
    log.debug("Loading  all items in the list")
    data_manager = DataManager()
    items = []

    for id in id_list:
        url = "{server}/emby/Users/{userid}/Items/%s?format=json"
        url = url % (id,)
        result = data_manager.GetContent(url)
        if result is None:
            log.debug("Playfile item was None, so can not play!")
            return
        items.append(result)

    return playAllFiles(items, monitor)


def playFile(play_info, monitor):

    id = play_info.get("item_id")

    # if this is a list of items them add them all to the play list
    if isinstance(id, list):
        return playListOfItems(id, monitor)

    auto_resume = play_info.get("auto_resume", "-1")
    force_transcode = play_info.get("force_transcode", False)
    media_source_id = play_info.get("media_source_id", "")
    subtitle_stream_index = play_info.get("subtitle_stream_index", None)
    audio_stream_index = play_info.get("audio_stream_index", None)

    log.debug("playFile id({0}) resume({1}) force_transcode({2})", id, auto_resume, force_transcode)

    settings = xbmcaddon.Addon()
    addon_path = settings.getAddonInfo('path')
    force_auto_resume = settings.getSetting('forceAutoResume') == 'true'
    jump_back_amount = int(settings.getSetting("jump_back_amount"))

    server = download_utils.getServer()

    url = "{server}/emby/Users/{userid}/Items/%s?format=json" % (id,)
    data_manager = DataManager()
    result = data_manager.GetContent(url)
    log.debug("Playfile item: {0}", result)

    if result is None:
        log.debug("Playfile item was None, so can not play!")
        return

    # if this is a season, tv show or album then play all items in that parent
    if result.get("Type") == "Season" or result.get("Type") == "MusicAlbum":
        log.debug("PlayAllFiles for parent item id: {0}", id)
        url = ('{server}/emby/Users/{userid}/items' +
               '?ParentId=%s' +
               '&Fields=MediaSources' +
               '&format=json')
        url = url % (id,)
        result = data_manager.GetContent(url)
        log.debug("PlayAllFiles items: {0}", result)

        # process each item
        items = result["Items"]
        if items is None:
            items = []
        return playAllFiles(items, monitor)

    # select the media source to use
    media_sources = result.get('MediaSources')
    selected_media_source = None

    if result.get("Type") == "Photo":
        play_url = "%s/emby/Items/%s/Images/Primary"
        play_url = play_url % (server, id)

        plugin_path = xbmc.translatePath(os.path.join(xbmcaddon.Addon().getAddonInfo('path')))
        action_menu = PictureViewer("PictureViewer.xml", plugin_path, "default", "720p")
        action_menu.setPicture(play_url)
        action_menu.doModal()
        return

    if media_sources is None or len(media_sources) == 0:
        log.debug("Play Failed! There is no MediaSources data!")
        return

    elif len(media_sources) == 1:
        selected_media_source = media_sources[0]

    elif media_source_id != "":
        for source in media_sources:
            if source.get("Id", "na") == media_source_id:
                selected_media_source = source
                break

    elif len(media_sources) > 1:
        sourceNames = []
        for source in media_sources:
            sourceNames.append(source.get("Name", "na"))

        dialog = xbmcgui.Dialog()
        resp = dialog.select(string_load(30309), sourceNames)
        if resp > -1:
            selected_media_source = media_sources[resp]
        else:
            log.debug("Play Aborted, user did not select a MediaSource")
            return

    if selected_media_source is None:
        log.debug("Play Aborted, MediaSource was None")
        return

    source_id = selected_media_source.get("Id")
    seekTime = 0
    auto_resume = int(auto_resume)

    # process user data for resume points
    if auto_resume != -1:
        seekTime = (auto_resume / 1000) / 10000

    elif force_auto_resume:
        userData = result.get("UserData")
        reasonableTicks = int(userData.get("PlaybackPositionTicks")) / 1000
        seekTime = reasonableTicks / 10000

    else:
        userData = result.get("UserData")
        if userData.get("PlaybackPositionTicks") != 0:

            reasonableTicks = int(userData.get("PlaybackPositionTicks")) / 1000
            seekTime = reasonableTicks / 10000
            displayTime = str(timedelta(seconds=seekTime))

            resumeDialog = ResumeDialog("ResumeDialog.xml", addon_path, "default", "720p")
            resumeDialog.setResumeTime("Resume from " + displayTime)
            resumeDialog.doModal()
            resume_result = resumeDialog.getResumeAction()
            del resumeDialog
            log.debug("Resume Dialog Result: {0}", resume_result)

            # check system settings for play action
            # if prompt is set ask to set it to auto resume
            # remove for now as the context dialog is now handeled in the monitor thread
            # params = {"setting": "myvideos.selectaction"}
            # setting_result = json_rpc('Settings.getSettingValue').execute(params)
            # log.debug("Current Setting (myvideos.selectaction): {0}", setting_result)
            # current_value = setting_result.get("result", None)
            # if current_value is not None:
            #     current_value = current_value.get("value", -1)
            # if current_value not in (2,3):
            #     return_value = xbmcgui.Dialog().yesno(string_load(30276), string_load(30277))
            #     if return_value:
            #         params = {"setting": "myvideos.selectaction", "value": 2}
            #         json_rpc_result = json_rpc('Settings.setSettingValue').execute(params)
            #         log.debug("Save Setting (myvideos.selectaction): {0}", json_rpc_result)

            if resume_result == 1:
                seekTime = 0
            elif resume_result == -1:
                return

    listitem_props = []
    playback_type = "0"
    playurl = None
    play_session_id = id_generator()
    log.debug("play_session_id: {0}", play_session_id)

    # check if strm file, path will contain contain strm contents
    if selected_media_source.get('Container') == 'strm':
        playurl, listitem_props = PlayUtils().getStrmDetails(selected_media_source)
        if playurl is None:
            return

    if not playurl:
        playurl, playback_type = PlayUtils().getPlayUrl(id, selected_media_source, force_transcode, play_session_id)

    log.debug("Play URL: {0} ListItem Properties: {1}", playurl, listitem_props)

    playback_type_string = "DirectPlay"
    if playback_type == "2":
        playback_type_string = "Transcode"
    elif playback_type == "1":
        playback_type_string = "DirectStream"

    # add the playback type into the overview
    if result.get("Overview", None) is not None:
        result["Overview"] = playback_type_string + "\n" + result.get("Overview")
    else:
        result["Overview"] = playback_type_string

    # add title decoration is needed
    item_title = result.get("Name", string_load(30280))

    # extract item info from result
    gui_options = {}
    gui_options["server"] = server
    gui_options["name_format"] = None
    gui_options["name_format_type"] = ""
    item_details = extract_item_info(result, gui_options)

    # create ListItem
    display_options = {}
    display_options["addCounts"] = False
    display_options["addResumePercent"] = False
    display_options["addSubtitleAvailable"] = False

    gui_item = add_gui_item("", item_details, display_options, False)
    list_item = gui_item[1]
    #list_item = xbmcgui.ListItem(label=item_title)

    if playback_type == "2": # if transcoding then prompt for audio and subtitle
        playurl = audioSubsPref(playurl, list_item, selected_media_source, id, audio_stream_index, subtitle_stream_index)
        log.debug("New playurl for transcoding: {0}", playurl)

    elif playback_type == "1": # for direct stream add any streamable subtitles
        externalSubs(selected_media_source, list_item, id)

    # add playurl and data to the monitor
    data = {}
    data["item_id"] = id
    data["source_id"] = source_id
    data["playback_type"] = playback_type_string
    data["play_session_id"] = play_session_id
    data["play_action_type"] = "play"
    monitor.played_information[playurl] = data
    log.debug("Add to played_information: {0}", monitor.played_information)

    list_item.setPath(playurl)
    list_item = setListItemProps(id, list_item, result, server, listitem_props, item_title)

    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    playlist.add(playurl, list_item)
    xbmc.Player().play(playlist)

    send_next_episode_details(result)

    if seekTime == 0:
        return

    count = 0
    while not xbmc.Player().isPlaying():
        log.debug("Not playing yet...sleep for 1 sec")
        count = count + 1
        if count >= 10:
            return
        else:
            xbmc.Monitor().waitForAbort(1)

    seekTime = seekTime - jump_back_amount

    target_seek = (seekTime - 5)
    current_position = 0
    while current_position < target_seek:
        # xbmc.Player().pause()
        xbmc.sleep(100)
        xbmc.Player().seekTime(seekTime)
        xbmc.sleep(100)
        # xbmc.Player().play()
        current_position = xbmc.Player().getTime()
        log.debug("Playback_Start_Seek target:{0} current:{1}", target_seek, current_position)


def send_next_episode_details(item):

    next_episode = get_next_episode(item)

    if next_episode is None:
        log.debug("No next episode")
        return

    gui_options = {}
    gui_options["server"] = download_utils.getServer()

    gui_options["name_format"] = None
    gui_options["name_format_type"] = ""

    item_details = extract_item_info(item, gui_options)
    next_item_details = extract_item_info(next_episode, gui_options)

    current_item = {}
    current_item["episodeid"] = item_details.id
    current_item["tvshowid"] = item_details.series_name
    current_item["title"] = item_details.name
    current_item["art"] = {}
    current_item["art"]["tvshow.poster"] = item_details.art.get('tvshow.poster', '')
    current_item["art"]["thumb"] = item_details.art.get('thumb', '')
    current_item["art"]["tvshow.fanart"] = item_details.art.get('tvshow.fanart', '')
    current_item["art"]["tvshow.landscape"] = item_details.art.get('tvshow.landscape', '')
    current_item["art"]["tvshow.clearart"] = item_details.art.get('tvshow.clearart', '')
    current_item["art"]["tvshow.clearlogo"] = item_details.art.get('tvshow.clearlogo', '')
    current_item["plot"] = item_details.plot
    current_item["showtitle"] = item_details.series_name
    current_item["playcount"] = item_details.play_count
    current_item["season"] = item_details.season_number
    current_item["episode"] = item_details.episode_number
    current_item["rating"] = item_details.critic_rating
    current_item["firstaired"] = item_details.year


    next_item = {}
    next_item["episodeid"] = next_item_details.id
    next_item["tvshowid"] = next_item_details.series_name
    next_item["title"] = next_item_details.name
    next_item["art"] = {}
    next_item["art"]["tvshow.poster"] = next_item_details.art.get('tvshow.poster', '')
    next_item["art"]["thumb"] = next_item_details.art.get('thumb', '')
    next_item["art"]["tvshow.fanart"] = next_item_details.art.get('tvshow.fanart', '')
    next_item["art"]["tvshow.landscape"] = next_item_details.art.get('tvshow.landscape', '')
    next_item["art"]["tvshow.clearart"] = next_item_details.art.get('tvshow.clearart', '')
    next_item["art"]["tvshow.clearlogo"] = next_item_details.art.get('tvshow.clearlogo', '')
    next_item["plot"] = next_item_details.plot
    next_item["showtitle"] = next_item_details.series_name
    next_item["playcount"] = next_item_details.play_count
    next_item["season"] = next_item_details.season_number
    next_item["episode"] = next_item_details.episode_number
    next_item["rating"] = next_item_details.critic_rating
    next_item["firstaired"] = next_item_details.year

    next_info = {
        "current_episode": current_item,
        "next_episode": next_item,
        "play_info": {
            "item_id": next_item_details.id,
            "auto_resume": False,
            "force_transcode": False
        }
    }
    send_event_notification("upnext_data", next_info)


def setListItemProps(id, listItem, result, server, extra_props, title):
    # set up item and item info

    art = getArt(result, server=server)
    listItem.setIconImage(art['thumb'])  # back compat
    listItem.setProperty('fanart_image', art['fanart'])  # back compat
    listItem.setProperty('discart', art['discart'])  # not avail to setArt
    listItem.setArt(art)

    listItem.setProperty('IsPlayable', 'false')
    listItem.setProperty('IsFolder', 'false')
    listItem.setProperty('id', result.get("Id"))

    for prop in extra_props:
        listItem.setProperty(prop[0], prop[1])

    item_type = result.get("Type", "").lower()
    mediatype = 'video'

    if item_type == 'movie' or item_type == 'boxset':
        mediatype = 'movie'
    elif item_type == 'series':
        mediatype = 'tvshow'
    elif item_type == 'season':
        mediatype = 'season'
    elif item_type == 'episode':
        mediatype = 'episode'
    elif item_type == 'audio':
        mediatype = 'song'

    if item_type == "audio":

        details = {
            'title': title,
            'mediatype': mediatype
        }
        listItem.setInfo("Music", infoLabels=details)

    else:

        details = {
            'title': title,
            'plot': result.get("Overview"),
            'mediatype': mediatype
        }

        tv_show_name = result.get("SeriesName")
        if tv_show_name is not None:
            details['tvshowtitle'] = tv_show_name

        if item_type == "episode":
            episode_number = result.get("IndexNumber", -1)
            details["episode"] = str(episode_number)
            season_number = result.get("ParentIndexNumber", -1)
            details["season"] = str(season_number)
        elif item_type == "season":
            season_number = result.get("IndexNumber", -1)
            details["season"] = str(season_number)

        details["plotoutline"] = "emby_id:%s" % (id,)
        #listItem.setUniqueIDs({'emby': id})

        listItem.setInfo("Video", infoLabels=details)

    return listItem


# For transcoding only
# Present the list of audio and subtitles to select from
# for external streamable subtitles add the URL to the Kodi item and let Kodi handle it
# else ask for the subtitles to be burnt in when transcoding
def audioSubsPref(url, list_item, media_source, item_id, audio_stream_index, subtitle_stream_index):

    dialog = xbmcgui.Dialog()
    audioStreamsList = {}
    audioStreams = []
    audioStreamsChannelsList = {}
    subtitleStreamsList = {}
    subtitleStreams = ['No subtitles']
    downloadableStreams = []
    selectAudioIndex = audio_stream_index
    selectSubsIndex = subtitle_stream_index
    playurlprefs = "%s" % url
    default_audio = media_source.get('DefaultAudioStreamIndex', 1)
    default_sub = media_source.get('DefaultSubtitleStreamIndex', "")
    source_id = media_source["Id"]

    media_streams = media_source['MediaStreams']

    for stream in media_streams:
        # Since Emby returns all possible tracks together, have to sort them.
        index = stream['Index']

        if 'Audio' in stream['Type']:
            codec = stream['Codec']
            channelLayout = stream.get('ChannelLayout', "")

            try:
                track = "%s - %s - %s %s" % (index, stream['Language'], codec, channelLayout)
            except:
                track = "%s - %s %s" % (index, codec, channelLayout)

            audioStreamsChannelsList[index] = stream['Channels']
            audioStreamsList[track] = index
            audioStreams.append(track)

        elif 'Subtitle' in stream['Type']:
            try:
                track = "%s - %s" % (index, stream['Language'])
            except:
                track = "%s - %s" % (index, stream['Codec'])

            default = stream['IsDefault']
            forced = stream['IsForced']
            downloadable = stream['IsTextSubtitleStream'] and stream['IsExternal'] and stream['SupportsExternalStream']

            if default:
                track = "%s - Default" % track
            if forced:
                track = "%s - Forced" % track
            if downloadable:
                downloadableStreams.append(index)

            subtitleStreamsList[track] = index
            subtitleStreams.append(track)

    # set audio index
    if selectAudioIndex is not None:
        playurlprefs += "&AudioStreamIndex=%s" % selectAudioIndex

    elif len(audioStreams) > 1:
        resp = dialog.select(string_load(30291), audioStreams)
        if resp > -1:
            # User selected audio
            selected = audioStreams[resp]
            selectAudioIndex = audioStreamsList[selected]
            playurlprefs += "&AudioStreamIndex=%s" % selectAudioIndex
        else:  # User backed out of selection
            playurlprefs += "&AudioStreamIndex=%s" % default_audio

    # set subtitle index
    if selectSubsIndex is not None:
        # Load subtitles in the listitem if downloadable
        if selectSubsIndex in downloadableStreams:
            url = [("%s/emby/Videos/%s/%s/Subtitles/%s/Stream.srt"
                    % (download_utils.getServer(), item_id, source_id, selectSubsIndex))]
            log.debug("Streaming subtitles url: {0} {1}", selectSubsIndex, url)
            list_item.setSubtitles(url)
        else:
            # Burn subtitles
            playurlprefs += "&SubtitleStreamIndex=%s" % selectSubsIndex

    elif len(subtitleStreams) > 1:
        resp = dialog.select(string_load(30292), subtitleStreams)
        if resp == 0:
            # User selected no subtitles
            pass
        elif resp > -1:
            # User selected subtitles
            selected = subtitleStreams[resp]
            selectSubsIndex = subtitleStreamsList[selected]

            # Load subtitles in the listitem if downloadable
            if selectSubsIndex in downloadableStreams:
                url = [("%s/emby/Videos/%s/%s/Subtitles/%s/Stream.srt"
                        % (download_utils.getServer(), item_id, source_id, selectSubsIndex))]
                log.debug("Streaming subtitles url: {0} {1}", selectSubsIndex, url)
                list_item.setSubtitles(url)
            else:
                # Burn subtitles
                playurlprefs += "&SubtitleStreamIndex=%s" % selectSubsIndex

        else:  # User backed out of selection
            playurlprefs += "&SubtitleStreamIndex=%s" % default_sub

    # Get number of channels for selected audio track
    audioChannels = audioStreamsChannelsList.get(selectAudioIndex, 0)
    if audioChannels > 2:
        playurlprefs += "&AudioBitrate=384000"
    else:
        playurlprefs += "&AudioBitrate=192000"

    return playurlprefs


# direct stream, set any available subtitle streams
def externalSubs(media_source, list_item, item_id):

    externalsubs = []
    media_streams = media_source['MediaStreams']

    if media_streams is None:
        return

    for stream in media_streams:

        if (stream['Type'] == "Subtitle"
                and stream['IsExternal']
                and stream['IsTextSubtitleStream']
                and stream['SupportsExternalStream']):

            index = stream['Index']
            source_id = media_source['Id']
            url = ("%s/emby/Videos/%s/%s/Subtitles/%s/Stream.%s"
                   % (download_utils.getServer(), item_id, source_id, index, stream['Codec']))

            externalsubs.append(url)

    log.debug("External Subtitles : {0}", externalsubs)
    list_item.setSubtitles(externalsubs)


def sendProgress(monitor):
    playing_file = xbmc.Player().getPlayingFile()

    '''
    video_tag_info = xbmc.Player().getVideoInfoTag()
    plotoutline = video_tag_info.getPlotOutline()
    log.debug("Player().getVideoInfoTag().getPlotOutline(): {0}", plotoutline)
    emby_id = None
    if plotoutline is not None and plotoutline.startswith("emby_id:"):
        emby_id = plotoutline[8:]
    log.debug("EmbyId: {0}", emby_id)
    '''

    play_data = monitor.played_information.get(playing_file)

    if play_data is None:
        return

    log.debug("Sending Progress Update")

    play_time = xbmc.Player().getTime()
    play_data["currentPossition"] = play_time
    play_data["currently_playing"] = True

    item_id = play_data.get("item_id")
    if item_id is None:
        return

    source_id = play_data.get("source_id")

    ticks = int(play_time * 10000000)
    paused = play_data.get("paused", False)
    playback_type = play_data.get("playback_type")
    play_session_id = play_data.get("play_session_id")

    postdata = {
        'QueueableMediaTypes': "Video",
        'CanSeek': True,
        'ItemId': item_id,
        'MediaSourceId': source_id,
        'PositionTicks': ticks,
        'IsPaused': paused,
        'IsMuted': False,
        'PlayMethod': playback_type,
        'PlaySessionId': play_session_id
    }

    log.debug("Sending POST progress started: {0}", postdata)

    url = "{server}/emby/Sessions/Playing/Progress"
    download_utils.downloadUrl(url, postBody=postdata, method="POST")


def promptForStopActions(item_id, current_possition):

    settings = xbmcaddon.Addon()

    prompt_next_percentage = int(settings.getSetting('promptPlayNextEpisodePercentage'))
    play_prompt = settings.getSetting('promptPlayNextEpisodePercentage_prompt') == "true"
    prompt_delete_episode_percentage = int(settings.getSetting('promptDeleteEpisodePercentage'))
    prompt_delete_movie_percentage = int(settings.getSetting('promptDeleteMoviePercentage'))

    # everything is off so return
    if (prompt_next_percentage == 100 and
            prompt_delete_episode_percentage == 100 and
            prompt_delete_movie_percentage == 100):
        return

    jsonData = download_utils.downloadUrl("{server}/emby/Users/{userid}/Items/" + item_id + "?format=json")
    result = json.loads(jsonData)

    if result is None:
        log.debug("promptForStopActions failed! no result from server.")
        return

    prompt_to_delete = False
    runtime = result.get("RunTimeTicks", 0)

    # if no runtime we cant calculate perceantge so just return
    if runtime == 0:
        log.debug("No runtime so returing")
        return

    # item percentage complete
    percenatge_complete = int(((current_possition * 10000000) / runtime) * 100)
    log.debug("Episode Percentage Complete: {0}", percenatge_complete)

    if (prompt_delete_episode_percentage < 100 and
                result.get("Type", "na") == "Episode" and
                percenatge_complete > prompt_delete_episode_percentage):
            prompt_to_delete = True

    if (prompt_delete_movie_percentage < 100 and
                result.get("Type", "na") == "Movie" and
                percenatge_complete > prompt_delete_movie_percentage):
            prompt_to_delete = True

    if prompt_to_delete:
        log.debug("Prompting for delete")
        delete(result)

    # prompt for next episode
    if (prompt_next_percentage < 100 and
                result.get("Type", "na") == "Episode" and
                percenatge_complete > prompt_next_percentage):

        next_episode = get_next_episode(result)

        if next_episode is not None:
            resp = True
            index = next_episode.get("IndexNumber", -1)
            if play_prompt:
                next_epp_name = "%02d - %s" % (index, next_episode.get("Name", "n/a"))
                resp = xbmcgui.Dialog().yesno(string_load(30283), string_load(30284), next_epp_name, autoclose=10000)

            if resp:
                next_item_id = next_episode.get("Id")
                log.debug("Playing Next Episode: {0}", next_item_id)

                play_info = {}
                play_info["item_id"] = next_item_id
                play_info["auto_resume"] = "-1"
                play_info["force_transcode"] = False
                send_event_notification("embycon_play_action", play_info)


def stopAll(played_information):
    if len(played_information) == 0:
        return

    log.debug("played_information: {0}", played_information)

    home_screen = HomeWindow()
    home_screen.clearProperty("currently_playing_id")

    for item_url in played_information:
        data = played_information.get(item_url)
        if data.get("currently_playing", False) is True:
            log.debug("item_url: {0}", item_url)
            log.debug("item_data: {0}", data)

            current_possition = data.get("currentPossition", 0)
            emby_item_id = data.get("item_id")
            emby_source_id = data.get("source_id")

            if emby_item_id is not None and current_possition >= 0:
                log.debug("Playback Stopped at: {0}", current_possition)

                url = "{server}/emby/Sessions/Playing/Stopped"
                postdata = {
                    'ItemId': emby_item_id,
                    'MediaSourceId': emby_source_id,
                    'PositionTicks': int(current_possition * 10000000)
                }
                download_utils.downloadUrl(url, postBody=postdata, method="POST")
                data["currently_playing"] = False

                if data.get("play_action_type", "") == "play":
                    promptForStopActions(emby_item_id, current_possition)

    device_id = ClientInformation().getDeviceId()
    url = "{server}/emby/Videos/ActiveEncodings?DeviceId=%s" % device_id
    download_utils.downloadUrl(url, method="DELETE")

class Service(xbmc.Player):

    def __init__(self, *args):
        log.debug("Starting monitor service: {0}", args)
        self.played_information = {}
        self.activity = {}

    def save_activity(self):
        addon = xbmcaddon.Addon()
        path = xbmc.translatePath(addon.getAddonInfo('profile')) + "activity.json"
        activity_data = json.dumps(self.activity)
        f = xbmcvfs.File(path, 'w')
        f.write(activity_data)
        f.close()

    def onPlayBackStarted(self):
        # Will be called when xbmc starts playing a file
        stopAll(self.played_information)

        if not xbmc.Player().isPlaying():
            log.debug("onPlayBackStarted: not playing file!")
            return

        current_playing_file = xbmc.Player().getPlayingFile()
        log.debug("onPlayBackStarted: {0}", current_playing_file)
        log.debug("played_information: {0}", self.played_information)

        if current_playing_file not in self.played_information:
            log.debug("This file was not started by EmbyCon")
            return

        data = self.played_information[current_playing_file]
        data["paused"] = False
        data["currently_playing"] = True

        emby_item_id = data["item_id"]
        emby_source_id = data["source_id"]
        playback_type = data["playback_type"]
        play_session_id = data["play_session_id"]

        # if we could not find the ID of the current item then return
        if emby_item_id is None:
            return

        log.debug("Sending Playback Started")
        postdata = {
            'QueueableMediaTypes': "Video",
            'CanSeek': True,
            'ItemId': emby_item_id,
            'MediaSourceId': emby_source_id,
            'PlayMethod': playback_type,
            'PlaySessionId': play_session_id
        }

        log.debug("Sending POST play started: {0}", postdata)

        url = "{server}/emby/Sessions/Playing"
        download_utils.downloadUrl(url, postBody=postdata, method="POST")

        home_screen = HomeWindow()
        home_screen.setProperty("currently_playing_id", str(emby_item_id))

        # record the activity
        utcnow = datetime.utcnow()
        today = "%s-%s-%s" % (utcnow.year, utcnow.month, utcnow.day)
        if today not in self.activity:
            self.activity[today] = {}
        if playback_type not in self.activity[today]:
            self.activity[today][playback_type] = 0
        self.activity[today][playback_type] += 1
        self.save_activity()

    def onPlayBackEnded(self):
        # Will be called when kodi stops playing a file
        log.debug("EmbyCon Service -> onPlayBackEnded")
        stopAll(self.played_information)

    def onPlayBackStopped(self):
        # Will be called when user stops kodi playing a file
        log.debug("onPlayBackStopped")
        stopAll(self.played_information)

    def onPlayBackPaused(self):
        # Will be called when kodi pauses the video
        log.debug("onPlayBackPaused")
        current_file = xbmc.Player().getPlayingFile()
        play_data = self.played_information.get(current_file)

        if play_data is not None:
            play_data['paused'] = True
            sendProgress(self)

    def onPlayBackResumed(self):
        # Will be called when kodi resumes the video
        log.debug("onPlayBackResumed")
        current_file = xbmc.Player().getPlayingFile()
        play_data = self.played_information.get(current_file)

        if play_data is not None:
            play_data['paused'] = False
            sendProgress(self)

    def onPlayBackSeek(self, time, seekOffset):
        # Will be called when kodi seeks in video
        log.debug("onPlayBackSeek")
        sendProgress(self)


class PlaybackService(xbmc.Monitor):

    background_image_cache_thread = None

    def __init__(self, monitor):
        self.monitor = monitor

    def onNotification(self, sender, method, data):
        log.debug("PlaybackService:onNotification:{0}:{1}:{2}", sender, method, data)

        if method == 'GUI.OnScreensaverActivated':
            self.screensaver_activated()
            return

        if method == 'GUI.OnScreensaverDeactivated':
            self.screensaver_deactivated()
            return

        if sender[-7:] != '.SIGNAL':
            return

        signal = method.split('.', 1)[-1]
        if signal != "embycon_play_action":
            return

        data_json = json.loads(data)
        hex_data = data_json[0]
        log.debug("PlaybackService:onNotification:{0}", hex_data)
        decoded_data = binascii.unhexlify(hex_data)
        play_info = json.loads(decoded_data)
        log.info("Received embycon_play_action : {0}", play_info)
        playFile(play_info, self.monitor)

    def screensaver_activated(self):
        log.debug("Screen Saver Activated")

        # stop playback when switching users
        if xbmc.Player().isPlaying():
            xbmc.Player().stop()

        #xbmc.executebuiltin("Dialog.Close(selectdialog, true)")

        settings = xbmcaddon.Addon()

        cache_images = settings.getSetting('cacheImagesOnScreenSaver') == 'true'
        if cache_images:
            self.background_image_cache_thread = CacheArtwork()
            self.background_image_cache_thread.start()

    def screensaver_deactivated(self):
        log.debug("Screen Saver Deactivated")

        if self.background_image_cache_thread:
            self.background_image_cache_thread.stop_all_activity = True
            self.background_image_cache_thread = None

        settings = xbmcaddon.Addon()
        show_change_user = settings.getSetting('changeUserOnScreenSaver') == 'true'
        if show_change_user:
            xbmc.executebuiltin("RunScript(plugin.video.embycon,0,?mode=CHANGE_USER)")

