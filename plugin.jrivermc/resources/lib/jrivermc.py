# Copyright (C) 2026, JRiver
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
from pathlib import Path
from urllib.parse import urlencode, parse_qsl
import datetime as dt

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
from xbmcvfs import translatePath

import resources.lib.mcws as MCWS

# Get the plugin url in plugin:// notation.
URL = sys.argv[0]
# Get a plugin handle as an integer number.
HANDLE = int(sys.argv[1])

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :return: plugin call URL
    :rtype: str
    """
    return f"{URL}?{urlencode(kwargs)}"


def listChildren(parent_id, parent_name):
    #Get child views
    children = MCWS.getLibChildren(parent_id)

    # If no children, show files. If at root level, there is something wrong with the server connection.
    if not children:
        if parent_id > 0:
            listFiles(parent_id, parent_name)
        else:
            MCWS.reset()
            list_item = xbmcgui.ListItem(label=xbmcaddon.Addon().getLocalizedString(30202))
            list_item.setArt({ "icon": "DefaultIconWarning.png" })
            url = get_url(action="show_settings")
            xbmcplugin.addDirectoryItem(HANDLE, url, list_item, True)
            xbmcplugin.endOfDirectory(HANDLE)
        return

    if parent_name:
        xbmcplugin.setPluginCategory(HANDLE, parent_name)

    # Iterate through children
    for index, child in enumerate(children):
        # Create a list item with a text label.
        list_item = xbmcgui.ListItem(label=child["Name"])

        # Set images for the list item.
        list_item.setArt({
            "icon": child["Icon"],
           # 'fanart': str(FANART_DIR / genre_info['fanart']),
        })
        
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&genre_index=0
        url = get_url(action="browse_lib", id=child["ID"], name=child["Name"])

        # Custom context menu items for "folder" levels
        if parent_id > 0:
            play_url = get_url(action="play_files", parent_id=child["ID"], replace="1")
            add_url = get_url(action="play_files", parent_id=child["ID"], replace="0")
            context_menu_items = [
                (MCWS.getDisplayString(30175), f"RunPlugin({play_url}&index=0)"),  # Play All
                (MCWS.getDisplayString(30176), f"RunPlugin({play_url}&index=-1)"), # Shuffle + Play All
                (MCWS.getDisplayString(30177), f"RunPlugin({add_url}&index=0)")    # Add All
            ]

            list_item.addContextMenuItems(context_menu_items, True);
    
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, True)

    # Add sort methods for the virtual folder items
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_PLAYLIST_ORDER)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)

    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(HANDLE)


def listFiles(parent_id, parent_name):
    # Get files for current view
    files = MCWS.getLibFiles(parent_id)

    if parent_name:
        xbmcplugin.setPluginCategory(HANDLE, parent_name)

    if not files:
        empty_item = xbmcgui.ListItem(label="Empty")
        xbmcplugin.addDirectoryItem(HANDLE, "", empty_item, False)
        xbmcplugin.endOfDirectory(HANDLE)
        return
    
    content_type = getContentType(files[0])
    xbmcplugin.setContent(HANDLE, content_type)
    
    # Iterate through files
    n = 0
    for file in files:
        # Create a list item with a text label
        list_item = getListItem(file, content_type)

        # Custom context menu items        
        play_single = get_url(action="play_file", key=file["Key"], replace="1")
        play_all = get_url(action="play_files", parent_id=parent_id, index=n, replace="1")
        add_single = get_url(action="play_file", key=file["Key"], replace="0")
        add_all = get_url(action="play_files", parent_id=parent_id, index=n, replace="0")
        context_menu_items = [
            (MCWS.getDisplayString(30178), f"RunPlugin({play_single})"), # Play Single
            (MCWS.getDisplayString(30175), f"RunPlugin({play_all})"),    # Play All
            (MCWS.getDisplayString(30179), f"RunPlugin({add_single})"),  # Play Single
            (MCWS.getDisplayString(30177), f"RunPlugin({add_all})")      # Add All
        ]
        list_item.addContextMenuItems(context_menu_items, True)

        if file.get("Media Type", "") == "Video":
            list_item.setProperty("IsPlayable", "True")
            url = get_url(action="play_video", key=file["Key"], lib_id=MCWS.getLoadedLibrary())
        else:
            url = play_all

        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, False)
        n = n + 1
       
    # Add sort methods for the virtual folder items
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_PLAYLIST_ORDER)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    #xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_VIDEO_YEAR)

    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(HANDLE)

def getContentType(file):
    media_type = file.get("Media Type", "")
    if media_type == "Audio":
        return "songs"
    elif media_type == "Video":
        sub_type = file.get("Media Sub Type", "")
        if sub_type == "Movie":
            return "movies"
        elif sub_type == "TV Show":
            return "tvshows"
        else:
            return "videos"
    else:
        return "files"

def getListItem(file, content_type):
    # Create a list item
    list_item = xbmcgui.ListItem(label=file["Name"])

    # Set art for list item
    art =  MCWS.getFileImageURL(file["Key"])
    list_item.setArt({"icon": art})
    list_item.setArt({"thumb": art})
    list_item.setArt({"poster": art})

    # Get date and year
    d = dt.date(1899, 12, 30)
    try:
        d += dt.timedelta(days=float(file.get("Date")))
        year = d.year
        # year = int(rd[-4:])
    except Exception as e:
        year = 0

    # Set additional info for the list item via InfoTag.
    if content_type == "songs":
        info_tag = list_item.getMusicInfoTag()
        info_tag.setMediaType("song")
        info_tag.setTitle(file.get("Name", ""))
        info_tag.setAlbum(file.get("Album", ""))
        info_tag.setArtist(file.get("Artist", ""))
        info_tag.setDuration(int(file.get("Duration","0")))
        info_tag.setYear(year)
        rating = int(file.get("Rating", "0"))
        info_tag.setUserRating(rating * 2)
        genres = file.get("Genre","").split(",")
        if genres:
            info_tag.setGenres(genres)
        # track = file.get("Track #", "")
        # if track:
        #    info_tag.setTrack(int(track))

    else:  # movies, tv shows, other videos
        info_tag = list_item.getVideoInfoTag()
        info_tag.setMediaType("movie")
        info_tag.setTitle(file.get("Name", ""))
        info_tag.setDuration(int(file.get("Duration","0")))
        if year > 0:
            info_tag.setPremiered(d.isoformat())
        description = file.get("Description", "")
        info_tag.setPlot(description)
        info_tag.setPlotOutline(description)
        info_tag.setYear(year)
        genres = file.get("Genre","").split(",")
        if genres:
            info_tag.setGenres(genres)
        series = file.get("Series", "")
        if series:
            info_tag.setTvShowTitle(series)
        season = file.get("Season", "")
        if season:
            info_tag.setSeason(int(season))
        episode = file.get("Episode", "")
        if episode:
            info_tag.setEpisode(int(episode))
        rating = int(file.get("Rating", "0"))
        info_tag.setUserRating(rating * 2)
        if content_type == "movies":
            info_tag.setMediaType("movie")
        elif content_type == "tvshows":
            info_tag.setMediaType("episode")
        else:
            info_tag.setMediaType("video")

    return list_item

def playVideo(key):
    if not MCWS.connect():
        return
    
    play_item = xbmcgui.ListItem(offscreen=True)
    convert = getVideoConversion(xbmcaddon.Addon().getSettingInt("video_convert"))
    path = MCWS.getFileContentURL(key, convert)
    play_item.setPath(path)
    xbmcplugin.setResolvedUrl(HANDLE, True, play_item)

def playAudio(key):
    if not MCWS.connect():
        return
    
    play_item = xbmcgui.ListItem(offscreen=True)
    convert = getAudioConversion(xbmcaddon.Addon().getSettingInt("audio_convert"))
    path = MCWS.getFileContentURL(key, convert)
    play_item.setPath(path)
    xbmcplugin.setResolvedUrl(HANDLE, True, play_item)

def playFile(key, replace):
    
    file = MCWS.getFileInfo(key)

    if not file:
        return

    files = [file]
    playlist = queueFiles(files, replace)
    if playlist and replace:
        xbmc.Player().play(playlist)

def playFiles(parent_id, index, replace):
   
    files = MCWS.getLibFiles(parent_id)
    if not files:
        return
    
    result = queueFiles(files, replace, index)
    playlist = result["playlist"]
    start_index = result["startIndex"]
    if playlist:
        if start_index == -1:
            playlist.shuffle()
        if replace:
            xbmc.Player().play(playlist, startpos=start_index)

def queueFiles(files, replace, index=0):
    if not files:
        return

    mtype = files[index]["Media Type"]
    if mtype == "Audio":
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        isVideo = False
    elif mtype == "Video":
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        isVideo = True
    else:
        return

    if replace:
        playlist.clear()

    for file in files:
        if file["Media Type"] != mtype:
            if index > 0:
                index = index - 1
            continue

        if isVideo:
            url = get_url(action="play_video", key=file["Key"])
        else:
            url = get_url(action="play_audio", key=file["Key"])

        list_item = getListItem(file, getContentType(file))
      
        playlist.add(url=url, listitem=list_item)

    return { "playlist" : playlist, "startIndex" : index }

def getAudioConversion(index):
    AudioQualities = {
        1 : "25", # WAV
        2 : "4",  # MP3 High
        3 : "3",  # MP3 Medium
        4 : "2"   # MP3 Low
    }
    quality = AudioQualities.get(index, "")
    if quality:
        return "&Conversion=" + quality
    else:
        return ""

def getVideoConversion(index):
    VideoQualities = {
        1 : "high",
        2 : "medium",
        3 : "low"
    }
    quality = VideoQualities.get(index, "")
    if quality:
        return "&Conversion=Android&Quality=" + quality + "&HLSVOD=1"
    else:
        return ""

def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    
    # Check the parameters passed to the plugin
    if not params or not params.get("action", ""):   # root
        listChildren(-1, "")
    elif params["action"] == "browse_lib":
        listChildren(int(params["id"]), params["name"])
    elif params["action"] == "play_file":
        playFile(int(params["key"]), params["replace"]=="1")
    elif params["action"] == "play_files":
        playFiles(int(params["parent_id"]), int(params["index"]), params["replace"]=="1")
    elif params["action"] == "play_video":
        playVideo(int(params["key"]))
    elif params["action"] == "play_audio":
        playAudio(int(params["key"]))
    elif params["action"] == "show_settings":
        xbmc.executebuiltin("Addon.OpenSettings(plugin.jrivermc)")
    elif params["action"] == "connect":
        MCWS.reset()
        MCWS.connect(True)
        xbmc.executebuiltin("Container.Refresh")
    else:
        # If the provided paramstring does not contain a supported action
        # we raise an exception. This helps to catch coding errors,
        # e.g. typos in action names.
        raise ValueError(f'Invalid paramstring: {paramstring}!')


def run(args):
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
